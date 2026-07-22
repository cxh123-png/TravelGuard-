"""政策与 Rule Gate 应用服务。"""

from datetime import date
from decimal import Decimal

from src.adapters.persistence.policy.repository import PolicyRepository
from src.domain.policy.entities import Policy, PolicyVersion
from src.domain.policy.value_objects import PolicyRuleCondition
from src.domain.travel.entities import TravelRequest
from src.domain.travel.schemas import RuleGateDecision, RuleGateResult, TravelRequestSnapshot


class PolicyService:
    """政策查询服务。"""

    def __init__(self, policy_repo: PolicyRepository) -> None:
        self.policy_repo = policy_repo

    async def get_effective_policy(
        self,
        tenant_id: str,
        org_id: str,
        business_date: date,
    ) -> Policy | None:
        """按租户、组织和业务发生日查询生效政策。"""
        model = await self.policy_repo.get_effective_for_org(tenant_id, org_id)
        if model is None:
            return None
        return self._model_to_entity(model, business_date)

    async def get_policy_version(
        self,
        policy: Policy,
        business_date: date,
    ) -> PolicyVersion | None:
        """获取指定日期适用的政策版本。"""
        return policy.get_version_for_date(business_date)

    @staticmethod
    def _model_to_entity(model: object, business_date: date) -> Policy | None:
        """将 ORM 模型转换为领域实体（仅加载指定日期生效的版本）。"""
        import json

        from src.domain.policy.entities import Policy as DomainPolicy
        from src.domain.policy.entities import PolicyRule as DomainPolicyRule
        from src.domain.policy.entities import PolicyStatus as DomainPolicyStatus

        policy = DomainPolicy(
            id=str(getattr(model, "id", "")),
            tenant_id=str(getattr(model, "tenant_id", "")),
            name=str(getattr(model, "name", "")),
            target_org_ids=_parse_org_ids(str(getattr(model, "target_org_ids", ""))),
            status=DomainPolicyStatus(str(getattr(model, "status", ""))),
        )

        for vm in getattr(model, "versions", []):
            if getattr(vm, "expiry_date", None) and business_date > vm.expiry_date:
                continue
            if business_date < vm.effective_date:
                continue
            version = PolicyVersion(
                id=str(getattr(vm, "id", "")),
                version_number=int(getattr(vm, "version_number", 0)),
                effective_date=getattr(vm, "effective_date", date.today()),
                expiry_date=getattr(vm, "expiry_date", None),
                created_at=getattr(vm, "created_at", None),  # type: ignore[arg-type]
            )
            for rm in getattr(vm, "rules", []):
                condition_data: dict[str, str | None] = {}
                condition_json = getattr(rm, "condition_json", "")
                if condition_json:
                    try:
                        import json
                        parsed = json.loads(str(condition_json))
                        if isinstance(parsed, dict):
                            condition_data = {k: str(v) if v is not None else None for k, v in parsed.items()}
                    except (json.JSONDecodeError, TypeError):
                        pass
                rule = DomainPolicyRule(
                    id=str(getattr(rm, "id", "")),
                    rule_type=str(getattr(rm, "rule_type", "")),
                    condition=PolicyRuleCondition(**condition_data),
                    limit_value=str(getattr(rm, "limit_value", "")),
                    is_exception_allowed=bool(getattr(rm, "is_exception_allowed", False)),
                    exception_approver_roles=_parse_approver_roles(str(getattr(rm, "exception_approver_roles", ""))),
                )
                version.rules.append(rule)
            policy.versions.append(version)

        return policy if policy.versions else None


def _parse_org_ids(raw: str) -> list[str]:
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def _parse_approver_roles(raw: str) -> list[str]:
    if not raw:
        return []
    import json
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return [r.strip() for r in raw.split(",") if r.strip()]


def _get_policy_version_id(policy: Policy | None, business_date: date) -> str:
    if policy is None:
        return ""
    version = policy.get_version_for_date(business_date)
    return version.id if version else ""


class RuleGateService:
    """Rule Gate：确定性分流服务。

    输入：TravelRequest + 生效 PolicyVersion
    输出：RuleGateResult（四种决策之一）
    """

    def __init__(
        self,
        policy_service: PolicyService,
    ) -> None:
        self.policy_service = policy_service

    async def evaluate(
        self,
        request: TravelRequest,
        employee_level: str = "",
        city_tier: str = "",
    ) -> RuleGateResult:
        """执行 Rule Gate 检查，返回确定性决策。"""
        from src.domain.travel.entities import TravelStatus
        from src.domain.travel.schemas import PolicyEvidenceRef

        reasons: list[str] = []
        evidence_refs: list[PolicyEvidenceRef] = []
        requires_agent = False

        # 1. 字段校验
        if not request.itineraries:
            return RuleGateResult(
                decision=RuleGateDecision.NEED_MORE_INFO,
                request_snapshot=self._build_snapshot(request),
                reasons=["行程不能为空"],
            )

        # 2. 状态校验
        if request.status != TravelStatus.RULE_CHECKING:
            return RuleGateResult(
                decision=RuleGateDecision.NEED_MORE_INFO,
                request_snapshot=self._build_snapshot(request),
                reasons=[f"申请状态不是 RULE_CHECKING，当前为 {request.status.value}"],
            )

        # 3. 权限校验（占位，后续由 M1/M3 统一拦截）
        # 4. 硬性政策检查
        business_date = request.created_at.date() if not request.itineraries else request.itineraries[0].check_in
        policy = await self.policy_service.get_effective_policy(request.tenant_id, "", business_date)
        if policy is None:
            reasons.append("未找到适用政策版本，需要人工处理")
            requires_agent = True
        else:
            version = policy.get_version_for_date(business_date)
            if version is None:
                reasons.append("未找到适用政策版本，需要人工处理")
                requires_agent = True
            else:
                for itinerary in request.itineraries:
                    # 检查酒店金额
                    hotel_rules = [r for r in version.rules if r.rule_type == "hotel_limit"]
                    for rule in hotel_rules:
                        if _condition_matches(rule.condition, employee_level=employee_level, city_tier=city_tier, transport_type=""):
                            actual = itinerary.estimated_hotel_amount.to_decimal()
                            limit = _to_decimal(rule.limit_value)
                            if actual > limit:
                                evidence = PolicyEvidenceRef(
                                    policy_version_id=version.id,
                                    rule_id=rule.id,
                                    rule_type=rule.rule_type,
                                    matched_value=f"actual={actual} limit={limit}",
                                    evidence_text=f"住宿金额 {actual} 超过上限 {limit}",
                                )
                                evidence_refs.append(evidence)
                                reasons.append(f"行程 {itinerary.city}: 住宿金额 {actual} 超过上限 {limit}")
                                if not rule.is_exception_allowed:
                                    return RuleGateResult(
                                        decision=RuleGateDecision.DIRECT_REJECT,
                                        request_snapshot=self._build_snapshot(request, policy_version_id=version.id),
                                        reasons=reasons,
                                        evidence_refs=evidence_refs,
                                    )
                                else:
                                    requires_agent = True

                    # 检查交通金额
                    transport_rules = [r for r in version.rules if r.rule_type == "transport_limit"]
                    for rule in transport_rules:
                        if _condition_matches(rule.condition, employee_level=employee_level, city_tier="", transport_type=""):
                            actual = itinerary.estimated_transport_amount.to_decimal()
                            limit = _to_decimal(rule.limit_value)
                            if actual > limit:
                                evidence = PolicyEvidenceRef(
                                    policy_version_id=version.id,
                                    rule_id=rule.id,
                                    rule_type=rule.rule_type,
                                    matched_value=f"actual={actual} limit={limit}",
                                    evidence_text=f"交通金额 {actual} 超过上限 {limit}",
                                )
                                evidence_refs.append(evidence)
                                reasons.append(f"行程 {itinerary.city}: 交通金额 {actual} 超过上限 {limit}")
                                if not rule.is_exception_allowed:
                                    return RuleGateResult(
                                        decision=RuleGateDecision.DIRECT_REJECT,
                                        request_snapshot=self._build_snapshot(request, policy_version_id=version.id),
                                        reasons=reasons,
                                        evidence_refs=evidence_refs,
                                    )
                                else:
                                    requires_agent = True

        # 5. 预算预检（占位，后续由 M3 提供接口）

        # 6. 输出决策
        policy_version_id = _get_policy_version_id(policy, business_date)

        if requires_agent:
            return RuleGateResult(
                decision=RuleGateDecision.REQUIRES_AGENT,
                request_snapshot=self._build_snapshot(request, policy_version_id=policy_version_id),
                reasons=reasons,
                evidence_refs=evidence_refs,
                requires_human=True,
            )

        return RuleGateResult(
            decision=RuleGateDecision.DIRECT_APPROVE,
            request_snapshot=self._build_snapshot(request, policy_version_id=policy_version_id),
            reasons=reasons,
            evidence_refs=evidence_refs,
        )

    def _build_snapshot(self, request: TravelRequest, policy_version_id: str = "") -> TravelRequestSnapshot:
        """构造不可变事实快照。"""
        cities = [it.city for it in request.itineraries]
        date_start = request.itineraries[0].check_in if request.itineraries else None
        date_end = request.itineraries[-1].check_out if request.itineraries else None
        purposes = [it.purpose for it in request.itineraries if it.purpose]
        return TravelRequestSnapshot(
            request_id=request.id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            created_at=request.created_at,
            total_estimated_amount_cny=str(request.total_estimated_amount().to_decimal()),
            city_list=cities,
            date_range_start=date_start,
            date_range_end=date_end,
            purpose_summary="; ".join(purposes),
            policy_version_id=policy_version_id,
        )


def _condition_matches(condition: PolicyRuleCondition, *, employee_level: str = "", city_tier: str = "", transport_type: str = "") -> bool:
    """检查条件是否匹配给定的员工/城市/交通参数。

    条件字段为空或 None 表示不限制该维度。
    """
    if condition.city_tier and condition.city_tier != city_tier:
        return False
    if condition.employee_level and condition.employee_level != employee_level:
        return False
    if condition.transport_type and condition.transport_type != transport_type:
        return False
    return True


def _to_decimal(value: str) -> Decimal:
    return Decimal(value)
