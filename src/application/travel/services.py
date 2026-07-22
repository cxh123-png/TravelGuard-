"""差旅应用服务：编排领域对象完成用例。"""

import uuid

from src.adapters.persistence.travel.models import TravelItineraryModel, TravelRequestModel
from src.adapters.persistence.travel.repository import TravelRequestRepository
from src.application.policy.services import RuleGateService
from src.domain.travel.entities import TravelItinerary, TravelRequest, TravelStatus
from src.domain.travel.rules import assert_draft_before_submit, assert_itinerary_not_empty
from src.domain.travel.schemas import RuleGateDecision, RuleGateResult
from src.domain.travel.value_objects import Money


class TravelRequestService:
    """差旅申请应用服务。"""

    def __init__(
        self,
        request_repo: TravelRequestRepository,
        rule_gate_service: RuleGateService,
    ) -> None:
        self.request_repo = request_repo
        self.rule_gate_service = rule_gate_service

    async def create_request(
        self,
        user_id: str,
        tenant_id: str,
        itineraries: list[TravelItinerary],
    ) -> TravelRequest:
        """创建草稿申请。"""
        request_id = str(uuid.uuid4())
        model = TravelRequestModel(
            id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status=TravelStatus.DRAFT.value,
        )
        model.itineraries = [
            TravelItineraryModel(
                id=str(uuid.uuid4()),
                request_id=request_id,
                city=it.city,
                check_in=it.check_in,
                check_out=it.check_out,
                estimated_hotel_amount=it.estimated_hotel_amount.to_decimal(),
                estimated_transport_amount=it.estimated_transport_amount.to_decimal(),
                purpose=it.purpose,
            )
            for it in itineraries
        ]
        await self.request_repo.add(model)
        return _model_to_travel_request(model)

    async def submit_request(
        self,
        request_id: str,
        employee_level: str = "",
        city_tier: str = "",
    ) -> TravelRequest:
        """提交申请，触发 Rule Gate 并更新申请状态。"""
        model = await self.request_repo.get_by_id(request_id)
        if model is None:
            raise ValueError("Request not found")
        request = _model_to_travel_request(model)
        assert_draft_before_submit(request)
        assert_itinerary_not_empty(request)
        request.submit()
        _sync_request_to_model(request, model)
        await self.request_repo.update(model)

        result = await self.rule_gate_service.evaluate(request, employee_level=employee_level, city_tier=city_tier)
        _apply_rule_gate_decision(request, result)
        _sync_request_to_model(request, model)
        await self.request_repo.update(model)
        return request

    async def cancel_request(self, request_id: str) -> TravelRequest:
        """取消申请。"""
        model = await self.request_repo.get_by_id(request_id)
        if model is None:
            raise ValueError("Request not found")
        request = _model_to_travel_request(model)
        request.cancel()
        _sync_request_to_model(request, model)
        await self.request_repo.update(model)
        return request


def _sync_request_to_model(request: TravelRequest, model: TravelRequestModel) -> None:
    """将领域实体的状态变更同步回 ORM 模型。"""
    model.status = request.status.value
    model.version = request.version
    model.updated_at = request.updated_at


def _model_to_travel_request(model: object) -> TravelRequest:
    """将 ORM 模型或领域实体转换为领域实体（兼容测试 Mock）。"""
    from src.domain.travel.entities import TravelItinerary

    itineraries = []
    for it in getattr(model, "itineraries", []):
        hotel_amt = getattr(it, "estimated_hotel_amount", Money(amount="0"))
        if isinstance(hotel_amt, Money):
            hotel_money = hotel_amt
        else:
            hotel_money = Money(amount=str(hotel_amt))

        transport_amt = getattr(it, "estimated_transport_amount", Money(amount="0"))
        if isinstance(transport_amt, Money):
            transport_money = transport_amt
        else:
            transport_money = Money(amount=str(transport_amt))

        check_in = getattr(it, "check_in", None)
        check_out = getattr(it, "check_out", None)
        # ORM 返回 datetime，领域需要 date
        if check_in is not None and hasattr(check_in, "date"):
            check_in = check_in.date()
        if check_out is not None and hasattr(check_out, "date"):
            check_out = check_out.date()

        itineraries.append(
            TravelItinerary(
                city=str(getattr(it, "city", "")),
                check_in=check_in,  # type: ignore[arg-type]
                check_out=check_out,  # type: ignore[arg-type]
                estimated_hotel_amount=hotel_money,
                estimated_transport_amount=transport_money,
                purpose=str(getattr(it, "purpose", "")),
            )
        )
    return TravelRequest(
        id=str(getattr(model, "id", "")),
        tenant_id=str(getattr(model, "tenant_id", "")),
        user_id=str(getattr(model, "user_id", "")),
        status=_parse_status(model),
        created_at=getattr(model, "created_at", None),  # type: ignore[arg-type]
        updated_at=getattr(model, "updated_at", None),  # type: ignore[arg-type]
        itineraries=itineraries,
        version=int(getattr(model, "version", 1) or 1),
    )


def _parse_status(model: object) -> TravelStatus:
    status_val = str(getattr(model, "status", "DRAFT"))
    try:
        return TravelStatus(status_val)
    except ValueError:
        return TravelStatus.DRAFT


def _apply_rule_gate_decision(request: TravelRequest, result: RuleGateResult) -> None:
    """将 Rule Gate 决策应用到申请状态。"""
    if result.decision == RuleGateDecision.DIRECT_APPROVE:
        request.approve_pending()
    elif result.decision == RuleGateDecision.DIRECT_REJECT:
        request.reject_by_policy()
    elif result.decision == RuleGateDecision.NEED_MORE_INFO:
        request.need_more_info()
    elif result.decision == RuleGateDecision.REQUIRES_AGENT:
        request.send_to_agent()
