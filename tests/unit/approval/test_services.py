"""Approval service tests."""

import asyncio

import pytest

from src.application.approval.schemas import ApprovalDecisionCommand, CreateApprovalTaskCommand
from src.application.approval.services import ApprovalService


class FakeApprovalRepository:
    def __init__(self) -> None:
        self.tasks: dict[str, object] = {}
        self.actions_by_key: dict[str, object] = {}

    async def add_task(self, model: object) -> object:
        self.tasks[model.id] = model
        return model

    async def get_task_by_id(self, tenant_id: str, task_id: str) -> object | None:
        task = self.tasks.get(task_id)
        if task is not None and task.tenant_id == tenant_id:
            return task
        return None

    async def get_task_for_update(self, tenant_id: str, task_id: str) -> object | None:
        return await self.get_task_by_id(tenant_id, task_id)

    async def get_action_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> object | None:
        action = self.actions_by_key.get(idempotency_key)
        if action is not None and action.tenant_id == tenant_id:
            return action
        return None

    async def add_action(self, model: object) -> object:
        self.actions_by_key[model.idempotency_key] = model
        return model

    async def update_task(self, model: object) -> object:
        self.tasks[model.id] = model
        return model


class FakeBudgetService:
    def __init__(self) -> None:
        self.release_calls = 0

    async def release_budget(self, command: object) -> object:
        self.release_calls += 1
        return type("BudgetReleaseResult", (), {"ledger_id": "ledger-release-1"})()


def test_create_approval_task_is_idempotent() -> None:
    asyncio.run(_test_create_approval_task_is_idempotent())


async def _test_create_approval_task_is_idempotent() -> None:
    repo = FakeApprovalRepository()
    service = ApprovalService(repo)
    command = CreateApprovalTaskCommand(
        tenant_id="tenant-1",
        business_id="travel-1",
        applicant_id="user-1",
        approver_role="manager",
        created_by="user-1",
        idempotency_key="idem-create-task",
    )

    first = await service.create_task(command)
    second = await service.create_task(command)

    assert first.duplicated is False
    assert second.duplicated is True
    assert first.task_id == second.task_id
    assert len(repo.tasks) == 1
    assert len(repo.actions_by_key) == 1


def test_approve_task_checks_expected_version() -> None:
    asyncio.run(_test_approve_task_checks_expected_version())


async def _test_approve_task_checks_expected_version() -> None:
    repo = FakeApprovalRepository()
    service = ApprovalService(repo)
    created = await service.create_task(
        CreateApprovalTaskCommand(
            tenant_id="tenant-1",
            business_id="travel-1",
            applicant_id="user-1",
            approver_role="manager",
            created_by="user-1",
            idempotency_key="idem-create-task",
        )
    )

    result = await service.approve_task(
        ApprovalDecisionCommand(
            tenant_id="tenant-1",
            task_id=created.task_id,
            actor_id="manager-1",
            expected_version=1,
            idempotency_key="idem-approve-task",
        )
    )

    assert result.status == "APPROVED"
    assert result.version == 2


def test_reject_task_releases_reserved_budget_once_on_idempotent_retry() -> None:
    asyncio.run(_test_reject_task_releases_reserved_budget_once_on_idempotent_retry())


async def _test_reject_task_releases_reserved_budget_once_on_idempotent_retry() -> None:
    repo = FakeApprovalRepository()
    budget_service = FakeBudgetService()
    service = ApprovalService(repo, budget_service=budget_service)  # type: ignore[arg-type]
    created = await service.create_task(
        CreateApprovalTaskCommand(
            tenant_id="tenant-1",
            business_id="travel-1",
            applicant_id="user-1",
            approver_role="manager",
            created_by="user-1",
            budget_account_id="budget-1",
            reserved_amount="300",
            idempotency_key="idem-create-task",
        )
    )
    command = ApprovalDecisionCommand(
        tenant_id="tenant-1",
        task_id=created.task_id,
        actor_id="manager-1",
        expected_version=1,
        idempotency_key="idem-reject-task",
    )

    first = await service.reject_task(command)
    second = await service.reject_task(command)

    assert first.status == "REJECTED"
    assert first.budget_release_ledger_id == "ledger-release-1"
    assert second.duplicated is True
    assert budget_service.release_calls == 1


def test_reject_with_stale_version_fails() -> None:
    asyncio.run(_test_reject_with_stale_version_fails())


async def _test_reject_with_stale_version_fails() -> None:
    repo = FakeApprovalRepository()
    service = ApprovalService(repo)
    created = await service.create_task(
        CreateApprovalTaskCommand(
            tenant_id="tenant-1",
            business_id="travel-1",
            applicant_id="user-1",
            approver_role="manager",
            created_by="user-1",
            idempotency_key="idem-create-task",
        )
    )

    with pytest.raises(ValueError, match="version conflict"):
        await service.reject_task(
            ApprovalDecisionCommand(
                tenant_id="tenant-1",
                task_id=created.task_id,
                actor_id="manager-1",
                expected_version=2,
                idempotency_key="idem-reject-task",
            )
        )
