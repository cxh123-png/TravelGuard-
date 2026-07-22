"""差旅应用服务单元测试（使用 Mock 仓储）。"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.policy.services import RuleGateService
from src.application.travel.services import TravelRequestService
from src.domain.travel.entities import TravelItinerary, TravelRequest, TravelStatus
from src.domain.travel.schemas import RuleGateDecision, RuleGateResult, TravelRequestSnapshot
from src.domain.travel.value_objects import Money


@pytest.fixture
def mock_repo():
    """创建 Mock 仓储。"""
    repo = MagicMock()
    repo.add = AsyncMock(return_value=None)
    repo.update = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_rule_gate():
    """创建 Mock Rule Gate 服务。"""
    rg = MagicMock(spec=RuleGateService)
    rg.evaluate = AsyncMock(
        return_value=RuleGateResult(
            decision=RuleGateDecision.DIRECT_APPROVE,
            request_snapshot=TravelRequestSnapshot(
                request_id="req-001",
                tenant_id="t-1",
                user_id="u-1",
                created_at=datetime(2026, 7, 22),
                total_estimated_amount_cny="2000",
            ),
            reasons=["所有规则通过"],
        )
    )
    return rg


@pytest.fixture
def service(mock_repo, mock_rule_gate):
    """创建带 Mock 仓储的服务实例。"""
    return TravelRequestService(request_repo=mock_repo, rule_gate_service=mock_rule_gate)


class TestCreateRequest:
    """测试创建申请。"""

    @pytest.mark.asyncio
    async def test_create_request_returns_travel_request(self, service, mock_repo) -> None:
        itineraries = [
            TravelItinerary(
                city="深圳",
                check_in=date(2026, 8, 1),
                check_out=date(2026, 8, 3),
                estimated_hotel_amount=Money(amount="1200"),
                estimated_transport_amount=Money(amount="800"),
            )
        ]
        result = await service.create_request(
            user_id="u-1",
            tenant_id="t-1",
            itineraries=itineraries,
        )
        assert isinstance(result, TravelRequest)
        assert result.user_id == "u-1"
        assert result.tenant_id == "t-1"
        assert result.status == TravelStatus.DRAFT
        mock_repo.add.assert_awaited_once()


class TestSubmitRequest:
    """测试提交申请。"""

    @pytest.mark.asyncio
    async def test_submit_success(self, service, mock_repo) -> None:
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
        mock_repo.get_by_id = AsyncMock(return_value=request)

        result = await service.submit_request("req-001")
        assert result.status == TravelStatus.PENDING_APPROVAL  # DIRECT_APPROVE
        assert mock_repo.update.call_count == 2  # submit + rule gate state update

    @pytest.mark.asyncio
    async def test_submit_not_found_raises_error(self, service, mock_repo) -> None:
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Request not found"):
            await service.submit_request("req-999")

    @pytest.mark.asyncio
    async def test_submit_empty_itinerary_raises_error(self, service, mock_repo) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        mock_repo.get_by_id = AsyncMock(return_value=request)
        with pytest.raises(ValueError, match="must contain at least one itinerary"):
            await service.submit_request("req-001")

    @pytest.mark.asyncio
    async def test_submit_direct_reject(self, service, mock_repo, mock_rule_gate) -> None:
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
        mock_repo.get_by_id = AsyncMock(return_value=request)
        mock_rule_gate.evaluate = AsyncMock(
            return_value=RuleGateResult(
                decision=RuleGateDecision.DIRECT_REJECT,
                request_snapshot=TravelRequestSnapshot(request_id="req-001", tenant_id="t-1", user_id="u-1", created_at=datetime(2026, 7, 22), total_estimated_amount_cny="2000"),
                reasons=["住宿金额超过上限"],
            )
        )

        result = await service.submit_request("req-001")
        assert result.status == TravelStatus.REJECTED_BY_POLICY

    @pytest.mark.asyncio
    async def test_submit_requires_agent(self, service, mock_repo, mock_rule_gate) -> None:
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
        mock_repo.get_by_id = AsyncMock(return_value=request)
        mock_rule_gate.evaluate = AsyncMock(
            return_value=RuleGateResult(
                decision=RuleGateDecision.REQUIRES_AGENT,
                request_snapshot=TravelRequestSnapshot(request_id="req-001", tenant_id="t-1", user_id="u-1", created_at=datetime(2026, 7, 22), total_estimated_amount_cny="2000"),
                reasons=["展会期间协议酒店满房，需Agent分析"],
            )
        )

        result = await service.submit_request("req-001")
        assert result.status == TravelStatus.AGENT_REVIEWING

    @pytest.mark.asyncio
    async def test_submit_need_more_info(self, service, mock_repo, mock_rule_gate) -> None:
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
        mock_repo.get_by_id = AsyncMock(return_value=request)
        mock_rule_gate.evaluate = AsyncMock(
            return_value=RuleGateResult(
                decision=RuleGateDecision.NEED_MORE_INFO,
                request_snapshot=TravelRequestSnapshot(request_id="req-001", tenant_id="t-1", user_id="u-1", created_at=datetime(2026, 7, 22), total_estimated_amount_cny="2000"),
                reasons=["行程不能为空"],
            )
        )

        result = await service.submit_request("req-001")
        assert result.status == TravelStatus.NEED_MORE_INFO


class TestCancelRequest:
    """测试取消申请。"""

    @pytest.mark.asyncio
    async def test_cancel_success(self, service, mock_repo) -> None:
        request = TravelRequest(id="req-001", tenant_id="t-1", user_id="u-1")
        mock_repo.get_by_id = AsyncMock(return_value=request)

        result = await service.cancel_request("req-001")
        assert isinstance(result, TravelRequest)
        assert result.status == TravelStatus.CANCELLED
        mock_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises_error(self, service, mock_repo) -> None:
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Request not found"):
            await service.cancel_request("req-999")
