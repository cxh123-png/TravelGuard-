"""政策与 Rule Gate 应用服务单元测试。"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.policy.services import PolicyService, RuleGateService, _condition_matches, _to_decimal
from src.domain.policy.entities import Policy, PolicyRule, PolicyStatus, PolicyVersion
from src.domain.policy.value_objects import PolicyRuleCondition
from src.domain.travel.entities import TravelItinerary, TravelRequest, TravelStatus
from src.domain.travel.schemas import RuleGateDecision
from src.domain.travel.value_objects import Money


@pytest.fixture
def mock_policy_repo():
    """创建 Mock 政策仓储。"""
    repo = MagicMock()
    return repo


@pytest.fixture
def policy_service(mock_policy_repo):
    """创建政策服务实例。"""
    return PolicyService(policy_repo=mock_policy_repo)


class TestPolicyService:
    """测试政策查询服务。"""

    @pytest.mark.asyncio
    async def test_get_policy_version_returns_version(self, policy_service) -> None:
        policy = Policy(id="p-1", tenant_id="t-1", name="差旅政策")
        policy.versions = [
            PolicyVersion(
                id="v-1",
                version_number=1,
                effective_date=date(2026, 1, 1),
                expiry_date=None,
            ),
        ]
        version = await policy_service.get_policy_version(policy, date(2026, 6, 1))
        assert version is not None
        assert version.id == "v-1"


class TestConditionMatches:
    """测试条件匹配逻辑。"""

    def test_empty_condition_matches_any(self) -> None:
        cond = PolicyRuleCondition()
        assert _condition_matches(cond, employee_level="L3", city_tier="一线", transport_type="飞机")

    def test_city_tier_mismatch_returns_false(self) -> None:
        cond = PolicyRuleCondition(city_tier="一线")
        assert _condition_matches(cond, city_tier="二线") is False

    def test_city_tier_match_returns_true(self) -> None:
        cond = PolicyRuleCondition(city_tier="一线")
        assert _condition_matches(cond, city_tier="一线") is True

    def test_employee_level_mismatch_returns_false(self) -> None:
        cond = PolicyRuleCondition(employee_level="L3")
        assert _condition_matches(cond, employee_level="L5") is False

    def test_employee_level_match_returns_true(self) -> None:
        cond = PolicyRuleCondition(employee_level="L3")
        assert _condition_matches(cond, employee_level="L3") is True

    def test_transport_type_mismatch_returns_false(self) -> None:
        cond = PolicyRuleCondition(transport_type="飞机")
        assert _condition_matches(cond, transport_type="高铁") is False

    def test_transport_type_match_returns_true(self) -> None:
        cond = PolicyRuleCondition(transport_type="飞机")
        assert _condition_matches(cond, transport_type="飞机") is True

    def test_multiple_conditions_all_match(self) -> None:
        cond = PolicyRuleCondition(city_tier="一线", employee_level="L3", transport_type="飞机")
        assert _condition_matches(cond, city_tier="一线", employee_level="L3", transport_type="飞机") is True

    def test_multiple_conditions_one_mismatch(self) -> None:
        cond = PolicyRuleCondition(city_tier="一线", employee_level="L3", transport_type="飞机")
        assert _condition_matches(cond, city_tier="一线", employee_level="L5", transport_type="飞机") is False


class TestRuleGateServiceEvaluate:
    """测试 Rule Gate 评估逻辑。"""

    def _make_policy(self, hotel_limit: str = "600", is_exception_allowed: bool = False) -> Policy:
        policy = Policy(id="p-1", tenant_id="t-1", name="差旅政策")
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=None,
        )
        version.rules = [
            PolicyRule(
                id="r-1",
                rule_type="hotel_limit",
                condition=PolicyRuleCondition(city_tier="一线", employee_level="L3"),
                limit_value=hotel_limit,
                is_exception_allowed=is_exception_allowed,
            ),
        ]
        policy.versions = [version]
        return policy

    def _make_request(self, hotel_amount: str = "500") -> TravelRequest:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="北京",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount=hotel_amount),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        return request

    @pytest.mark.asyncio
    async def test_direct_approve_under_limit(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="500")
        policy_service.get_effective_policy = AsyncMock(return_value=self._make_policy(hotel_limit="600"))

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.decision == RuleGateDecision.DIRECT_APPROVE

    @pytest.mark.asyncio
    async def test_direct_reject_over_non_exceptionable_limit(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="800")
        policy_service.get_effective_policy = AsyncMock(return_value=self._make_policy(hotel_limit="600", is_exception_allowed=False))

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.decision == RuleGateDecision.DIRECT_REJECT
        assert len(result.reasons) > 0

    @pytest.mark.asyncio
    async def test_requires_agent_over_exceptionable_limit(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="800")
        policy_service.get_effective_policy = AsyncMock(return_value=self._make_policy(hotel_limit="600", is_exception_allowed=True))

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.decision == RuleGateDecision.REQUIRES_AGENT
        assert result.requires_human is True

    @pytest.mark.asyncio
    async def test_need_more_info_empty_itineraries(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.submit()

        result = await svc.evaluate(request)
        assert result.decision == RuleGateDecision.NEED_MORE_INFO

    @pytest.mark.asyncio
    async def test_direct_approve_no_matching_rules(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="800")
        policy_service.get_effective_policy = AsyncMock(return_value=self._make_policy(hotel_limit="600"))

        # 员工条件不匹配
        result = await svc.evaluate(request, employee_level="L5", city_tier="一线")
        assert result.decision == RuleGateDecision.DIRECT_APPROVE

    @pytest.mark.asyncio
    async def test_no_policy_requires_agent(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="500")
        policy_service.get_effective_policy = AsyncMock(return_value=None)

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.decision == RuleGateDecision.REQUIRES_AGENT

    @pytest.mark.asyncio
    async def test_direct_reject_transport_over_limit(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="500")
        request.itineraries[0].estimated_transport_amount = Money(amount="2000")

        policy = Policy(id="p-1", tenant_id="t-1", name="差旅政策")
        version = PolicyVersion(id="v-1", version_number=1, effective_date=date(2026, 1, 1), expiry_date=None)
        version.rules = [
            PolicyRule(
                id="r-2",
                rule_type="transport_limit",
                condition=PolicyRuleCondition(employee_level="L3"),
                limit_value="1500",
                is_exception_allowed=False,
            ),
        ]
        policy.versions = [version]
        policy_service.get_effective_policy = AsyncMock(return_value=policy)

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.decision == RuleGateDecision.DIRECT_REJECT

    @pytest.mark.asyncio
    async def test_snapshot_includes_cities_and_amounts(self, policy_service) -> None:
        svc = RuleGateService(policy_service=policy_service)
        request = self._make_request(hotel_amount="500")
        policy_service.get_effective_policy = AsyncMock(return_value=self._make_policy(hotel_limit="600"))

        result = await svc.evaluate(request, employee_level="L3", city_tier="一线")
        assert result.request_snapshot.city_list == ["北京"]
        assert result.request_snapshot.date_range_start == date(2026, 8, 1)
        assert result.request_snapshot.date_range_end == date(2026, 8, 3)
