"""Budget API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentUser, get_current_user
from src.api.v1.budgets.dependencies import get_budget_service
from src.application.budget.schemas import (
    CheckBudgetAvailabilityCommand,
    CreateBudgetAccountCommand,
    ReleaseBudgetCommand,
    ReserveBudgetCommand,
)
from src.application.budget.services import BudgetService
from src.core.errors import AppError, ErrorCode
from src.core.response import success_response
from src.db.session import get_db_session

router = APIRouter(prefix="/budgets", tags=["budgets"])


class CreateBudgetAccountDTO(BaseModel):
    budget_center_id: str = Field(description="Budget center identifier")
    allocated_amount: str = Field(description="Initial allocated budget amount")
    currency: str = Field(default="CNY", description="Budget currency")


class ReserveBudgetDTO(BaseModel):
    account_id: str
    business_type: str = "TRAVEL_REQUEST"
    business_id: str
    amount: str
    currency: str = "CNY"


class ReleaseBudgetDTO(BaseModel):
    account_id: str
    business_type: str = "TRAVEL_REQUEST"
    business_id: str
    amount: str
    currency: str = "CNY"


@router.post("/accounts")
async def create_budget_account(
    data: CreateBudgetAccountDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    try:
        result = await service.create_account(
            CreateBudgetAccountCommand(
                tenant_id=current_user.tenant_id,
                budget_center_id=data.budget_center_id,
                allocated_amount=data.allocated_amount,
                currency=data.currency,
            )
        )
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.get("/accounts/{account_id}/availability")
async def check_budget_availability(
    account_id: str,
    amount: Annotated[str, Query(description="Requested amount")],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    currency: Annotated[str, Query(description="Currency")] = "CNY",
) -> dict[str, object]:
    try:
        result = await service.check_availability(
            CheckBudgetAvailabilityCommand(
                tenant_id=current_user.tenant_id,
                account_id=account_id,
                amount=amount,
                currency=currency,
            )
        )
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.post("/reservations")
async def reserve_budget(
    data: ReserveBudgetDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.reserve_budget(
            ReserveBudgetCommand(
                tenant_id=current_user.tenant_id,
                account_id=data.account_id,
                business_type=data.business_type,
                business_id=data.business_id,
                amount=data.amount,
                currency=data.currency,
                idempotency_key=idempotency_key,
            )
        )
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.post("/releases")
async def release_budget(
    data: ReleaseBudgetDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[BudgetService, Depends(get_budget_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.release_budget(
            ReleaseBudgetCommand(
                tenant_id=current_user.tenant_id,
                account_id=data.account_id,
                business_type=data.business_type,
                business_id=data.business_id,
                amount=data.amount,
                currency=data.currency,
                idempotency_key=idempotency_key,
            )
        )
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


def _to_app_error(exc: ValueError) -> AppError:
    message = str(exc)
    if "not found" in message.lower():
        return AppError(ErrorCode.NOT_FOUND, message, status_code=404)
    if "conflict" in message.lower():
        return AppError(ErrorCode.VALIDATION_ERROR, message, status_code=409)
    return AppError(ErrorCode.VALIDATION_ERROR, message, status_code=400)
