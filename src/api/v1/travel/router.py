"""差旅 API 路由：暴露 HTTP 接口给前端（M7）调用。"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.travel.repository import TravelRequestRepository
from src.api.dependencies import CurrentUser, get_current_user
from src.application.policy.services import PolicyRepository, PolicyService, RuleGateService
from src.application.travel.services import TravelRequestService
from src.core.response import success_response
from src.db.session import get_db_session

router = APIRouter(prefix="/travel-requests", tags=["travel"])


class CreateItineraryDTO(BaseModel):
    city: str = Field(description="目的地城市")
    check_in: date = Field(description="入住日期")
    check_out: date = Field(description="离店日期")
    estimated_hotel_amount: str = Field(description="预估酒店费用")
    estimated_transport_amount: str = Field(description="预估交通费用")
    purpose: str = Field(default="", description="出行事由")


class CreateTravelRequestDTO(BaseModel):
    itineraries: list[CreateItineraryDTO] = Field(min_length=1, description="行程明细列表")


class SubmitRequestDTO(BaseModel):
    employee_level: str = Field(default="", description="员工职级")
    city_tier: str = Field(default="", description="城市等级")


async def get_travel_request_repo(
    session: AsyncSession = Depends(get_db_session),
) -> TravelRequestRepository:
    return TravelRequestRepository(session)


async def get_policy_repo(
    session: AsyncSession = Depends(get_db_session),
) -> PolicyRepository:
    return PolicyRepository(session)


async def get_policy_service(
    policy_repo: Annotated[PolicyRepository, Depends(get_policy_repo)],
) -> PolicyService:
    return PolicyService(policy_repo=policy_repo)


async def get_rule_gate_service(
    policy_service: Annotated[PolicyService, Depends(get_policy_service)],
) -> RuleGateService:
    return RuleGateService(policy_service=policy_service)


async def get_travel_request_service(
    request_repo: Annotated[TravelRequestRepository, Depends(get_travel_request_repo)],
    rule_gate_service: Annotated[RuleGateService, Depends(get_rule_gate_service)],
) -> TravelRequestService:
    return TravelRequestService(request_repo=request_repo, rule_gate_service=rule_gate_service)


@router.post("")
async def create_travel_request(
    data: CreateTravelRequestDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[TravelRequestService, Depends(get_travel_request_service)],
) -> dict[str, object]:
    """创建差旅申请草稿。"""
    from src.domain.travel.entities import TravelItinerary
    from src.domain.travel.value_objects import Money

    itineraries = [
        TravelItinerary(
            city=it.city,
            check_in=it.check_in,
            check_out=it.check_out,
            estimated_hotel_amount=Money(amount=it.estimated_hotel_amount),
            estimated_transport_amount=Money(amount=it.estimated_transport_amount),
            purpose=it.purpose,
        )
        for it in data.itineraries
    ]
    request = await service.create_request(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        itineraries=itineraries,
    )
    return success_response({
        "id": request.id,
        "status": request.status.value,
        "total_estimated_amount": str(request.total_estimated_amount().to_decimal()),
    })


@router.post("/{request_id}/submit")
async def submit_travel_request(
    request_id: str,
    data: SubmitRequestDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[TravelRequestService, Depends(get_travel_request_service)],
) -> dict[str, object]:
    """提交申请，触发 Rule Gate。"""
    request = await service.submit_request(
        request_id=request_id,
        employee_level=data.employee_level,
        city_tier=data.city_tier,
    )
    return success_response({
        "id": request.id,
        "status": request.status.value,
    })


@router.post("/{request_id}/cancel")
async def cancel_travel_request(
    request_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[TravelRequestService, Depends(get_travel_request_service)],
) -> dict[str, object]:
    """取消申请。"""
    request = await service.cancel_request(request_id)
    return success_response({
        "id": request.id,
        "status": request.status.value,
    })


@router.get("/{request_id}/rule-gate")
async def get_rule_gate_result(
    request_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[TravelRequestService, Depends(get_travel_request_service)],
) -> dict[str, object]:
    """查询 Rule Gate 结果。"""
    from src.application.travel.services import _model_to_travel_request
    from src.core.errors import AppError, ErrorCode

    model = await service.request_repo.get_by_id(request_id)
    if model is None:
        raise AppError(ErrorCode.NOT_FOUND, "Request not found", status_code=404)
    request = _model_to_travel_request(model)
    result = await service.rule_gate_service.evaluate(request)
    return success_response({
        "request_id": request_id,
        "decision": result.decision.value,
        "reasons": result.reasons,
        "evidence_refs": [ev.model_dump() for ev in result.evidence_refs],
        "requires_human": result.requires_human,
    })
