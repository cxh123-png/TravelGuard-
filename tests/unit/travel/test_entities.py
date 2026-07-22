"""TravelRequest 领域实体单元测试。"""

from datetime import date

import pytest

from src.domain.travel.entities import TravelItinerary, TravelRequest, TravelStatus
from src.domain.travel.value_objects import Money


class TestTravelRequestCreation:
    """测试差旅申请的创建。"""

    def test_create_request_has_draft_status(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        assert request.status == TravelStatus.DRAFT

    def test_create_request_has_empty_itineraries(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        assert request.itineraries == []


class TestTravelRequestAddItinerary:
    """测试添加行程。"""

    def test_add_itinerary_increases_count(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        itinerary = TravelItinerary(
            city="深圳",
            check_in=date(2026, 8, 1),
            check_out=date(2026, 8, 3),
            estimated_hotel_amount=Money(amount="1200"),
            estimated_transport_amount=Money(amount="800"),
        )
        request.add_itinerary(itinerary)
        assert len(request.itineraries) == 1

    def test_total_amount_with_one_itinerary(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        itinerary = TravelItinerary(
            city="深圳",
            check_in=date(2026, 8, 1),
            check_out=date(2026, 8, 3),
            estimated_hotel_amount=Money(amount="1200"),
            estimated_transport_amount=Money(amount="800"),
        )
        request.add_itinerary(itinerary)
        total = request.total_estimated_amount()
        assert total.to_decimal() == 2000

    def test_total_amount_with_multiple_itineraries(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 2),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.add_itinerary(
            TravelItinerary(
                city="北京",
                check_in=date(2026, 8, 3),
                check_out=date(2026, 8, 4),
                estimated_hotel_amount=Money(amount="600"),
                estimated_transport_amount=Money(amount="400"),
            )
        )
        total = request.total_estimated_amount()
        assert total.to_decimal() == 1800


class TestTravelRequestSubmit:
    """测试提交申请（状态机）。"""

    def test_submit_from_draft_goes_to_rule_checking(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.submit()
        assert request.status == TravelStatus.RULE_CHECKING

    def test_submit_from_non_draft_raises_error(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.submit()  # 先提交到 RULE_CHECKING
        with pytest.raises(ValueError, match="Cannot submit from status"):
            request.submit()  # 再次提交应该报错


class TestTravelRequestCancel:
    """测试取消申请。"""

    def test_cancel_from_draft_sets_cancelled(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.cancel()
        assert request.status == TravelStatus.CANCELLED

    def test_cancel_from_need_more_info_sets_cancelled(self) -> None:
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
        request.submit()
        request.need_more_info()
        request.cancel()
        assert request.status == TravelStatus.CANCELLED

    def test_cancel_from_pending_approval_sets_cancelled(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.approve_pending()
        request.cancel()
        assert request.status == TravelStatus.CANCELLED

    def test_cancel_from_rejected_by_policy_raises_error(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.reject_by_policy()
        with pytest.raises(ValueError, match="Cannot cancel from status"):
            request.cancel()


class TestTravelRequestStateMachine:
    """测试完整状态机转换。"""

    def test_full_path_direct_approve(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        assert request.status == TravelStatus.RULE_CHECKING
        request.approve_pending()
        assert request.status == TravelStatus.PENDING_APPROVAL
        request.approve()
        assert request.status == TravelStatus.APPROVED

    def test_reject_by_policy_path(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.reject_by_policy()
        assert request.status == TravelStatus.REJECTED_BY_POLICY

    def test_agent_reviewing_path(self) -> None:
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
        request.submit()
        request.send_to_agent()
        assert request.status == TravelStatus.AGENT_REVIEWING

    def test_need_more_info_from_rule_checking(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.need_more_info()
        assert request.status == TravelStatus.NEED_MORE_INFO

    def test_resubmit_from_need_info(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.need_more_info()
        request.resubmit_from_need_info()
        assert request.status == TravelStatus.RULE_CHECKING

    def test_reject_from_pending_approval(self) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        request.add_itinerary(
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="500"),
                estimated_transport_amount=Money(amount="300"),
            )
        )
        request.submit()
        request.approve_pending()
        request.reject()
        assert request.status == TravelStatus.REJECTED

    def test_return_to_rule_check_from_agent_reviewing(self) -> None:
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
        request.submit()
        request.send_to_agent()
        request.return_to_rule_check()
        assert request.status == TravelStatus.RULE_CHECKING

    def test_agent_reviewing_to_need_more_info(self) -> None:
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
        request.submit()
        request.send_to_agent()
        request.need_more_info()
        assert request.status == TravelStatus.NEED_MORE_INFO

    def test_agent_reviewing_to_pending_approval(self) -> None:
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
        request.submit()
        request.send_to_agent()
        request.approve_pending()
        assert request.status == TravelStatus.PENDING_APPROVAL


class TestTravelItinerary:
    """测试行程值对象。"""

    def test_itinerary_creation(self) -> None:
        itinerary = TravelItinerary(
            city="上海",
            check_in=date(2026, 9, 1),
            check_out=date(2026, 9, 5),
            estimated_hotel_amount=Money(amount="2000"),
            estimated_transport_amount=Money(amount="500"),
            purpose="客户拜访",
        )
        assert itinerary.city == "上海"
        assert itinerary.purpose == "客户拜访"
