"""Policy 领域实体单元测试。"""

from datetime import date

import pytest

from src.domain.policy.entities import Policy, PolicyRule, PolicyStatus, PolicyVersion
from src.domain.policy.value_objects import PolicyRuleCondition


class TestPolicyVersionEffectiveDate:
    """测试政策版本生效日期判断。"""

    def test_date_within_range_is_effective(self) -> None:
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        assert version.is_effective_on(date(2026, 6, 15)) is True

    def test_date_before_effective_is_not_effective(self) -> None:
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        assert version.is_effective_on(date(2025, 12, 1)) is False

    def test_date_after_expiry_is_not_effective(self) -> None:
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        assert version.is_effective_on(date(2027, 1, 1)) is False

    def test_date_on_boundary_is_effective(self) -> None:
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=date(2026, 12, 31),
        )
        assert version.is_effective_on(date(2026, 1, 1)) is True
        assert version.is_effective_on(date(2026, 12, 31)) is True

    def test_no_expiry_date_means_forever_effective(self) -> None:
        version = PolicyVersion(
            id="v-1",
            version_number=1,
            effective_date=date(2026, 1, 1),
            expiry_date=None,
        )
        assert version.is_effective_on(date(2030, 1, 1)) is True


class TestPolicyGetVersionForDate:
    """测试按日期选择政策版本。"""

    def test_selects_latest_applicable_version(self) -> None:
        policy = Policy(id="p-1", tenant_id="t-1", name="差旅政策")
        policy.versions = [
            PolicyVersion(
                id="v-1",
                version_number=1,
                effective_date=date(2026, 1, 1),
                expiry_date=date(2026, 6, 30),
            ),
            PolicyVersion(
                id="v-2",
                version_number=2,
                effective_date=date(2026, 7, 1),
                expiry_date=None,
            ),
        ]
        selected = policy.get_version_for_date(date(2026, 8, 1))
        assert selected is not None
        assert selected.id == "v-2"

    def test_returns_none_when_no_version_applicable(self) -> None:
        policy = Policy(id="p-1", tenant_id="t-1", name="差旅政策")
        policy.versions = [
            PolicyVersion(
                id="v-1",
                version_number=1,
                effective_date=date(2026, 1, 1),
                expiry_date=date(2026, 6, 30),
            ),
        ]
        selected = policy.get_version_for_date(date(2027, 1, 1))
        assert selected is None


class TestPolicyRule:
    """测试政策规则。"""

    def test_rule_creation(self) -> None:
        rule = PolicyRule(
            id="r-1",
            rule_type="hotel_limit",
            condition=PolicyRuleCondition(city_tier="一线"),
            limit_value="800",
            is_exception_allowed=True,
        )
        assert rule.rule_type == "hotel_limit"
        assert rule.limit_value == "800"
        assert rule.is_exception_allowed is True
