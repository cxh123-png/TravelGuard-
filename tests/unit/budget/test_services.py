"""Budget service tests."""

import asyncio
from decimal import Decimal

import pytest

from src.application.budget.schemas import CheckBudgetAvailabilityCommand, ReleaseBudgetCommand, ReserveBudgetCommand
from src.application.budget.services import BudgetReadTool, BudgetService
from src.domain.budget.tools import BudgetAvailabilityCheck


class FakeBudgetRepository:
    def __init__(self, account: object) -> None:
        self.account = account
        self.ledgers_by_key: dict[str, object] = {}

    async def add_account(self, model: object) -> object:
        self.account = model
        return model

    async def get_account_by_id(self, tenant_id: str, account_id: str) -> object | None:
        if self.account.tenant_id == tenant_id and self.account.id == account_id:
            return self.account
        return None

    async def get_account_for_update(self, tenant_id: str, account_id: str) -> object | None:
        return await self.get_account_by_id(tenant_id, account_id)

    async def get_ledger_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> object | None:
        ledger = self.ledgers_by_key.get(idempotency_key)
        if ledger is not None and ledger.tenant_id == tenant_id:
            return ledger
        return None

    async def add_ledger(self, model: object) -> object:
        self.ledgers_by_key[model.idempotency_key] = model
        return model

    async def update_account(self, model: object) -> object:
        self.account = model
        return model


class AccountModel:
    id = "budget-1"
    tenant_id = "tenant-1"
    budget_center_id = "dept-1"
    currency = "CNY"
    allocated_amount = Decimal("1000.00")
    reserved_amount = Decimal("0.00")
    spent_amount = Decimal("0.00")
    version = 1
    created_at = None
    updated_at = None


def test_reserve_budget_is_idempotent() -> None:
    asyncio.run(_test_reserve_budget_is_idempotent())


async def _test_reserve_budget_is_idempotent() -> None:
    repo = FakeBudgetRepository(AccountModel())
    service = BudgetService(repo)
    command = ReserveBudgetCommand(
        tenant_id="tenant-1",
        account_id="budget-1",
        business_id="travel-1",
        amount="300",
        idempotency_key="idem-reserve-1",
    )

    first = await service.reserve_budget(command)
    second = await service.reserve_budget(command)

    assert first.duplicated is False
    assert second.duplicated is True
    assert repo.account.reserved_amount == Decimal("300.00")
    assert len(repo.ledgers_by_key) == 1


def test_second_reserve_fails_when_available_budget_is_not_enough() -> None:
    asyncio.run(_test_second_reserve_fails_when_available_budget_is_not_enough())


async def _test_second_reserve_fails_when_available_budget_is_not_enough() -> None:
    repo = FakeBudgetRepository(AccountModel())
    service = BudgetService(repo)

    await service.reserve_budget(
        ReserveBudgetCommand(
            tenant_id="tenant-1",
            account_id="budget-1",
            business_id="travel-1",
            amount="800",
            idempotency_key="idem-reserve-1",
        )
    )

    with pytest.raises(ValueError, match="Insufficient budget"):
        await service.reserve_budget(
            ReserveBudgetCommand(
                tenant_id="tenant-1",
                account_id="budget-1",
                business_id="travel-2",
                amount="300",
                idempotency_key="idem-reserve-2",
            )
        )


def test_release_budget_is_idempotent() -> None:
    asyncio.run(_test_release_budget_is_idempotent())


async def _test_release_budget_is_idempotent() -> None:
    repo = FakeBudgetRepository(AccountModel())
    service = BudgetService(repo)

    await service.reserve_budget(
        ReserveBudgetCommand(
            tenant_id="tenant-1",
            account_id="budget-1",
            business_id="travel-1",
            amount="300",
            idempotency_key="idem-reserve-1",
        )
    )
    command = ReleaseBudgetCommand(
        tenant_id="tenant-1",
        account_id="budget-1",
        business_id="travel-1",
        amount="300",
        idempotency_key="idem-release-1",
    )

    first = await service.release_budget(command)
    second = await service.release_budget(command)

    assert first.duplicated is False
    assert second.duplicated is True
    assert repo.account.reserved_amount == Decimal("0.00")
    assert len(repo.ledgers_by_key) == 2


def test_read_tool_checks_availability_without_writing_ledger() -> None:
    asyncio.run(_test_read_tool_checks_availability_without_writing_ledger())


async def _test_read_tool_checks_availability_without_writing_ledger() -> None:
    repo = FakeBudgetRepository(AccountModel())
    service = BudgetService(repo)
    tool = BudgetReadTool(service)

    result = await tool.check_availability(
        BudgetAvailabilityCheck(
            tenant_id="tenant-1",
            account_id="budget-1",
            amount="900",
        )
    )

    assert result.is_available is True
    assert result.available_amount == "1000.00"
    assert repo.ledgers_by_key == {}


def test_check_availability_returns_false_for_insufficient_amount() -> None:
    asyncio.run(_test_check_availability_returns_false_for_insufficient_amount())


async def _test_check_availability_returns_false_for_insufficient_amount() -> None:
    repo = FakeBudgetRepository(AccountModel())
    service = BudgetService(repo)

    result = await service.check_availability(
        CheckBudgetAvailabilityCommand(
            tenant_id="tenant-1",
            account_id="budget-1",
            amount="1200",
        )
    )

    assert result.is_available is False
