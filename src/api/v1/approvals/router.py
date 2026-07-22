"""Approval API routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.persistence.approval.repository import ApprovalRepository
from src.api.dependencies import CurrentUser, get_current_user
from src.api.v1.budgets.dependencies import get_budget_service
from src.application.approval.schemas import ApprovalDecisionCommand, CreateApprovalTaskCommand
from src.application.approval.services import ApprovalService
from src.application.budget.services import BudgetService
from src.core.errors import AppError, ErrorCode
from src.core.response import success_response
from src.db.session import get_db_session

router = APIRouter(prefix="/approval-tasks", tags=["approvals"])


class CreateApprovalTaskDTO(BaseModel):
    business_type: str = "TRAVEL_REQUEST"
    business_id: str
    applicant_id: str
    approver_role: str
    budget_account_id: str | None = None
    reserved_amount: str | None = None
    currency: str = "CNY"
    expires_at: datetime | None = None


class ApprovalDecisionDTO(BaseModel):
    expected_version: int = Field(description="Current approval task version")
    comment: str = ""


async def get_approval_repo(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ApprovalRepository:
    return ApprovalRepository(session)


async def get_approval_service(
    approval_repo: Annotated[ApprovalRepository, Depends(get_approval_repo)],
    budget_service: Annotated[BudgetService, Depends(get_budget_service)],
) -> ApprovalService:
    return ApprovalService(approval_repo=approval_repo, budget_service=budget_service)


@router.post("")
async def create_approval_task(
    data: CreateApprovalTaskDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.create_task(
            CreateApprovalTaskCommand(
                tenant_id=current_user.tenant_id,
                business_type=data.business_type,
                business_id=data.business_id,
                applicant_id=data.applicant_id,
                approver_role=data.approver_role,
                created_by=current_user.user_id,
                budget_account_id=data.budget_account_id,
                reserved_amount=data.reserved_amount,
                currency=data.currency,
                expires_at=data.expires_at,
                idempotency_key=idempotency_key,
            )
        )
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.post("/{task_id}/approve")
async def approve_task(
    task_id: str,
    data: ApprovalDecisionDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.approve_task(_decision_command(current_user, task_id, data, idempotency_key))
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.post("/{task_id}/reject")
async def reject_task(
    task_id: str,
    data: ApprovalDecisionDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.reject_task(_decision_command(current_user, task_id, data, idempotency_key))
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


@router.post("/{task_id}/expire")
async def expire_task(
    task_id: str,
    data: ApprovalDecisionDTO,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> dict[str, object]:
    try:
        result = await service.expire_task(_decision_command(current_user, task_id, data, idempotency_key))
        await session.commit()
    except ValueError as exc:
        raise _to_app_error(exc) from exc
    return success_response(result.model_dump())


def _decision_command(
    current_user: CurrentUser,
    task_id: str,
    data: ApprovalDecisionDTO,
    idempotency_key: str,
) -> ApprovalDecisionCommand:
    return ApprovalDecisionCommand(
        tenant_id=current_user.tenant_id,
        task_id=task_id,
        actor_id=current_user.user_id,
        expected_version=data.expected_version,
        idempotency_key=idempotency_key,
        comment=data.comment,
    )


def _to_app_error(exc: ValueError) -> AppError:
    message = str(exc)
    if "not found" in message.lower():
        return AppError(ErrorCode.NOT_FOUND, message, status_code=404)
    if "conflict" in message.lower():
        return AppError(ErrorCode.VALIDATION_ERROR, message, status_code=409)
    return AppError(ErrorCode.VALIDATION_ERROR, message, status_code=400)
