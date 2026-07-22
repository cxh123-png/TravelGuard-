"""差旅领域规则单元测试。"""

from datetime import date

import pytest

from src.domain.travel.entities import TravelItinerary, TravelRequest
from src.domain.travel.rules import (
    assert_draft_before_submit,
    assert_itinerary_not_empty,
    assert_positive_amount,
)
from src.domain.travel.value_objects import Money


class TestAssertItineraryNotEmpty:
    """测试行程非空规则。"""

    def test_empty_itineraries_raises_error(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        with pytest.raises(ValueError, match="must contain at least one itinerary"):
            assert_itinerary_not_empty(request)

    def test_non_empty_itineraries_passes(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="1200"),
                estimated_transport_amount=Money(amount="800"),
            )
        )
        # 不抛异常即通过
        assert_itinerary_not_empty(request) is None


class TestAssertPositiveAmount:
    """测试金额正数规则。"""

    def test_zero_amount_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Amount must be positive"):
            assert_positive_amount(Money(amount="0"))

    def test_negative_amount_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Amount must be positive"):
            assert_positive_amount(Money(amount="-100"))

    def test_positive_amount_passes(self) -> None:
        # 不抛异常即通过
        assert_positive_amount(Money(amount="100")) is None


class TestAssertDraftBeforeSubmit:
    """测试草稿状态提交规则。"""

    def test_draft_status_passes(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        # 不抛异常即通过
        assert_draft_before_submit(request) is None

    def test_non_draft_status_raises_error(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.submit()  # 变成 RULE_CHECKING
        with pytest.raises(ValueError, match="Only DRAFT requests can be submitted"):
            assert_draft_before_submit(request)
