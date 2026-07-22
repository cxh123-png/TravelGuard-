"""政策领域实体。"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.domain.policy.value_objects import PolicyRuleCondition


class PolicyStatus(StrEnum):
    """政策发布状态。"""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


@dataclass
class PolicyRule:
    """具体规则：如"住宿上限 800 元/晚"。"""

    id: str
    rule_type: str  # e.g. "hotel_limit", "flight_class", "meal_allowance"
    condition: PolicyRuleCondition
    limit_value: str  # 阈值，如 "800"
    is_exception_allowed: bool = False  # 是否允许例外（需要 Agent/人工审批）
    exception_approver_roles: list[str] = field(default_factory=list)


@dataclass
class PolicyVersion:
    """政策版本：历史单据永远绑定当时版本。"""

    id: str
    version_number: int
    effective_date: date
    expiry_date: date | None = None
    rules: list[PolicyRule] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_effective_on(self, business_date: date) -> bool:
        """判断某业务发生日是否适用本版本。"""
        if business_date < self.effective_date:
            return False
        if self.expiry_date and business_date > self.expiry_date:
            return False
        return True


@dataclass
class Policy:
    """政策根实体：一个租户可以有多条政策（按组织、地区区分）。"""

    id: str
    tenant_id: str
    name: str
    target_org_ids: list[str] = field(default_factory=list)  # 适用组织
    status: PolicyStatus = PolicyStatus.DRAFT
    versions: list[PolicyVersion] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def get_version_for_date(self, business_date: date) -> PolicyVersion | None:
        """按业务发生日选择生效版本。"""
        applicable = [v for v in self.versions if v.is_effective_on(business_date)]
        if not applicable:
            return None
        # 取最新版本
        return max(applicable, key=lambda v: v.version_number)
