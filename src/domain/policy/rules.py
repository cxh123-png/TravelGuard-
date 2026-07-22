"""政策领域规则。"""

from src.domain.policy.entities import Policy, PolicyStatus


def assert_policy_published_before_use(policy: Policy) -> None:
    """只有已发布政策才能用于 Rule Gate 检查。"""
    if policy.status != PolicyStatus.PUBLISHED:
        raise ValueError("Policy must be published before use")


def assert_version_exists_for_date(policy: Policy, business_date: object) -> None:
    """业务发生日必须有对应政策版本。"""
    from datetime import date
    if not isinstance(business_date, date):
        raise TypeError("business_date must be a date")
    version = policy.get_version_for_date(business_date)
    if version is None:
        raise ValueError(f"No policy version effective for date {business_date}")
