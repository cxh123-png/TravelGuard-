"""Approval application services."""

from typing import Any, Protocol
from uuid import uuid4

from src.application.approval.schemas import ApprovalDecisionCommand, ApprovalTaskResult, CreateApprovalTaskCommand
from src.application.budget.schemas import ReleaseBudgetCommand
from src.application.budget.services import BudgetService
from src.domain.approval.entities import ApprovalActionType, ApprovalTask, ApprovalTaskStatus


class ApprovalRepositoryProtocol(Protocol):
    async def add_task(self, model: Any) -> Any: ...
    async def get_task_by_id(self, tenant_id: str, task_id: str) -> Any | None: ...
    async def get_task_for_update(self, tenant_id: str, task_id: str) -> Any | None: ...
    async def get_action_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> Any | None: ...
    async def add_action(self, model: Any) -> Any: ...
    async def update_task(self, model: Any) -> Any: ...


class ApprovalService:
    """Single-step approval service with idempotent actions."""

    def __init__(self, approval_repo: ApprovalRepositoryProtocol, budget_service: BudgetService | None = None) -> None:
        self.approval_repo = approval_repo
        self.budget_service = budget_service

    async def create_task(self, command: CreateApprovalTaskCommand) -> ApprovalTaskResult:
        existing_action = await self.approval_repo.get_action_by_idempotency_key(command.tenant_id, command.idempotency_key)
        if existing_action is not None:
            _assert_existing_action_type(existing_action, ApprovalActionType.CREATED)
            existing_task = await self.approval_repo.get_task_by_id(command.tenant_id, str(getattr(existing_action, "task_id", "")))
            if existing_task is None:
                raise ValueError("Approval task not found for idempotent action")
            return _task_result_from_model(existing_task, duplicated=True)

        task_id = str(uuid4())
        task_model = _build_task_model(task_id, command)
        action_model = _build_action_model(
            tenant_id=command.tenant_id,
            task_id=task_id,
            action_type=ApprovalActionType.CREATED,
            actor_id=command.created_by,
            idempotency_key=command.idempotency_key,
            comment="",
        )
        await self.approval_repo.add_task(task_model)
        await self.approval_repo.add_action(action_model)
        return _task_result_from_model(task_model, duplicated=False)

    async def approve_task(self, command: ApprovalDecisionCommand) -> ApprovalTaskResult:
        existing_action = await self.approval_repo.get_action_by_idempotency_key(command.tenant_id, command.idempotency_key)
        if existing_action is not None:
            _assert_existing_action_type(existing_action, ApprovalActionType.APPROVED)
            task = await self.approval_repo.get_task_by_id(command.tenant_id, command.task_id)
            if task is None:
                raise ValueError("Approval task not found")
            return _task_result_from_model(task, duplicated=True)

        task_model = await self.approval_repo.get_task_for_update(command.tenant_id, command.task_id)
        if task_model is None:
            raise ValueError("Approval task not found")
        task = _model_to_task(task_model)
        task.approve(command.expected_version)
        _sync_task_to_model(task, task_model)
        await self.approval_repo.add_action(
            _build_action_model(
                tenant_id=command.tenant_id,
                task_id=command.task_id,
                action_type=ApprovalActionType.APPROVED,
                actor_id=command.actor_id,
                idempotency_key=command.idempotency_key,
                comment=command.comment,
            )
        )
        await self.approval_repo.update_task(task_model)
        return _task_result_from_model(task_model, duplicated=False)

    async def reject_task(self, command: ApprovalDecisionCommand) -> ApprovalTaskResult:
        return await self._close_task(command, ApprovalActionType.REJECTED)

    async def expire_task(self, command: ApprovalDecisionCommand) -> ApprovalTaskResult:
        return await self._close_task(command, ApprovalActionType.EXPIRED)

    async def _close_task(self, command: ApprovalDecisionCommand, action_type: ApprovalActionType) -> ApprovalTaskResult:
        existing_action = await self.approval_repo.get_action_by_idempotency_key(command.tenant_id, command.idempotency_key)
        if existing_action is not None:
            _assert_existing_action_type(existing_action, action_type)
            task = await self.approval_repo.get_task_by_id(command.tenant_id, command.task_id)
            if task is None:
                raise ValueError("Approval task not found")
            return _task_result_from_model(task, duplicated=True)

        task_model = await self.approval_repo.get_task_for_update(command.tenant_id, command.task_id)
        if task_model is None:
            raise ValueError("Approval task not found")
        task = _model_to_task(task_model)
        if action_type == ApprovalActionType.REJECTED:
            task.reject(command.expected_version)
        elif action_type == ApprovalActionType.EXPIRED:
            task.expire(command.expected_version)
        else:
            raise ValueError("Unsupported approval close action")

        release_ledger_id = await self._release_reserved_budget_if_needed(task, command, action_type)
        _sync_task_to_model(task, task_model)
        await self.approval_repo.add_action(
            _build_action_model(
                tenant_id=command.tenant_id,
                task_id=command.task_id,
                action_type=action_type,
                actor_id=command.actor_id,
                idempotency_key=command.idempotency_key,
                comment=command.comment,
            )
        )
        await self.approval_repo.update_task(task_model)
        result = _task_result_from_model(task_model, duplicated=False)
        result.budget_release_ledger_id = release_ledger_id
        return result

    async def _release_reserved_budget_if_needed(
        self,
        task: ApprovalTask,
        command: ApprovalDecisionCommand,
        action_type: ApprovalActionType,
    ) -> str | None:
        if self.budget_service is None or not task.has_budget_reservation():
            return None
        assert task.budget_account_id is not None
        assert task.reserved_amount is not None
        result = await self.budget_service.release_budget(
            ReleaseBudgetCommand(
                tenant_id=task.tenant_id,
                account_id=task.budget_account_id,
                business_type=task.business_type,
                business_id=task.business_id,
                amount=task.reserved_amount,
                currency=task.currency,
                idempotency_key=f"approval:{task.id}:{action_type.value}:budget-release",
            )
        )
        return result.ledger_id


def _build_task_model(task_id: str, command: CreateApprovalTaskCommand) -> Any:
    from src.adapters.persistence.approval.models import ApprovalTaskModel

    return ApprovalTaskModel(
        id=task_id,
        tenant_id=command.tenant_id,
        business_type=command.business_type,
        business_id=command.business_id,
        applicant_id=command.applicant_id,
        approver_role=command.approver_role,
        created_by=command.created_by,
        status=ApprovalTaskStatus.PENDING.value,
        budget_account_id=command.budget_account_id,
        reserved_amount=command.reserved_amount,
        currency=command.currency,
        expires_at=command.expires_at,
        version=1,
    )


def _build_action_model(
    *,
    tenant_id: str,
    task_id: str,
    action_type: ApprovalActionType,
    actor_id: str,
    idempotency_key: str,
    comment: str,
) -> Any:
    from src.adapters.persistence.approval.models import ApprovalActionModel

    return ApprovalActionModel(
        id=str(uuid4()),
        tenant_id=tenant_id,
        task_id=task_id,
        action_type=action_type.value,
        actor_id=actor_id,
        idempotency_key=idempotency_key,
        comment=comment,
    )


def _model_to_task(model: Any) -> ApprovalTask:
    return ApprovalTask(
        id=str(getattr(model, "id", "")),
        tenant_id=str(getattr(model, "tenant_id", "")),
        business_type=str(getattr(model, "business_type", "")),
        business_id=str(getattr(model, "business_id", "")),
        applicant_id=str(getattr(model, "applicant_id", "")),
        approver_role=str(getattr(model, "approver_role", "")),
        created_by=str(getattr(model, "created_by", "")),
        status=ApprovalTaskStatus(str(getattr(model, "status", ApprovalTaskStatus.PENDING.value))),
        budget_account_id=getattr(model, "budget_account_id", None),
        reserved_amount=getattr(model, "reserved_amount", None),
        currency=str(getattr(model, "currency", "CNY")),
        expires_at=getattr(model, "expires_at", None),
        version=int(getattr(model, "version", 1) or 1),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def _sync_task_to_model(task: ApprovalTask, model: Any) -> None:
    model.status = task.status.value
    model.version = task.version


def _task_result_from_model(model: Any, *, duplicated: bool) -> ApprovalTaskResult:
    return ApprovalTaskResult(
        task_id=str(getattr(model, "id", "")),
        tenant_id=str(getattr(model, "tenant_id", "")),
        business_type=str(getattr(model, "business_type", "")),
        business_id=str(getattr(model, "business_id", "")),
        applicant_id=str(getattr(model, "applicant_id", "")),
        approver_role=str(getattr(model, "approver_role", "")),
        status=str(getattr(model, "status", "")),
        version=int(getattr(model, "version", 1) or 1),
        budget_account_id=getattr(model, "budget_account_id", None),
        reserved_amount=getattr(model, "reserved_amount", None),
        currency=str(getattr(model, "currency", "CNY")),
        duplicated=duplicated,
    )


def _assert_existing_action_type(model: Any, expected_type: ApprovalActionType) -> None:
    if str(getattr(model, "action_type", "")) != expected_type.value:
        raise ValueError("Idempotency key already used for another approval action")
