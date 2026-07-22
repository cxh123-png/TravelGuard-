"""差旅领域规则：纯函数，无副作用。"""

from src.domain.travel.entities import TravelRequest
from src.domain.travel.value_objects import Money


def assert_itinerary_not_empty(request: TravelRequest) -> None:
    """行程不能为空。"""
    if not request.itineraries:
        raise ValueError("Travel request must contain at least one itinerary")


def assert_positive_amount(amount: Money) -> None:
    """金额必须大于零。"""
    if amount.to_decimal() <= 0:
        raise ValueError("Amount must be positive")


def assert_draft_before_submit(request: TravelRequest) -> None:
    """只有草稿状态才能提交。"""
    from src.domain.travel.entities import TravelStatus
    if request.status != TravelStatus.DRAFT:
        raise ValueError("Only DRAFT requests can be submitted")
