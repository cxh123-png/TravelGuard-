"""Budget application services."""

from decimal import Decimal
from typing import Any, Protocol
from uuid import uuid4

from src.application.budget.schemas import (
    BudgetAccountResult,
    BudgetAvailabilityResult,
    BudgetOperationResult,
    CheckBudgetAvailabilityCommand,
    CreateBudgetAccountCommand,
    ReleaseBudgetCommand,
    ReserveBudgetCommand,
)
from src.domain.budget.entities import BudgetAccount, BudgetLedgerType
from src.domain.budget.tools import BudgetAvailability, BudgetAvailabilityCheck
from src.domain.budget.value_objects import Money


class BudgetRepositoryProtocol(Protocol):
    async def add_account(self, model: Any) -> Any: ...
    async def get_account_by_id(self, tenant_id: str, account_id: str) -> Any | None: ...
    async def get_account_for_update(self, tenant_id: str, account_id: str) -> Any | None: ...
    async def get_ledger_by_idempotency_key(self, tenant_id: str, idempotency_key: str) -> Any | None: ...
    async def add_ledger(self, model: Any) -> Any: ...
    async def update_account(self, model: Any) -> Any: ...


class BudgetService:
    """Deterministic budget service for availability, reserve, and release."""

    def __init__(self, budget_repo: BudgetRepositoryProtocol) -> None:
        self.budget_repo = budget_repo

    async def create_account(self, command: CreateBudgetAccountCommand) -> BudgetAccountResult:
        from src.adapters.persistence.budget.models import BudgetAccountModel

        account_id = str(uuid4())
        allocated = Money.from_value(command.allocated_amount, command.currency)
        model = BudgetAccountModel(
            id=account_id,
            tenant_id=command.tenant_id,
            budget_center_id=command.budget_center_id,
            currency=command.currency,
            allocated_amount=allocated.amount,
            reserved_amount=Decimal("0.00"),
            spent_amount=Decimal("0.00"),
            version=1,
        )
        await self.budget_repo.add_account(model)
        return _account_result_from_model(model)

    async def check_availability(self, command: CheckBudgetAvailabilityCommand) -> BudgetAvailabilityResult:
        account_model = await self.budget_repo.get_account_by_id(command.tenant_id, command.account_id)
        if account_model is None:
            raise ValueError("Budget account not found")
        account = _model_to_account(account_model)
        requested = Money.from_value(command.amount, command.currency)
        return BudgetAvailabilityResult(
            account_id=account.id,
            tenant_id=account.tenant_id,
            requested_amount=requested.to_string(),
            available_amount=account.available_amount().to_string(),
            currency=account.currency,
            is_available=account.can_reserve(requested),
        )

    async def reserve_budget(self, command: ReserveBudgetCommand) -> BudgetOperationResult:
        amount = Money.from_value(command.amount, command.currency)
        existing = await self.budget_repo.get_ledger_by_idempotency_key(command.tenant_id, command.idempotency_key)
        if existing is not None:
            _assert_existing_ledger_matches(existing, BudgetLedgerType.RESERVE, command, amount)
            account_model = await self.budget_repo.get_account_by_id(command.tenant_id, command.account_id)
            if account_model is None:
                raise ValueError("Budget account not found")
            return _operation_result_from_existing(existing, _model_to_account(account_model), duplicated=True)

        account_model = await self.budget_repo.get_account_for_update(command.tenant_id, command.account_id)
        if account_model is None:
            raise ValueError("Budget account not found")
        account = _model_to_account(account_model)
        before, after = account.reserve(amount)
        _sync_account_to_model(account, account_model)
        ledger_model = _build_ledger_model(command, BudgetLedgerType.RESERVE, amount, before, after)
        await self.budget_repo.add_ledger(ledger_model)
        await self.budget_repo.update_account(account_model)
        return _operation_result_from_existing(ledger_model, account, duplicated=False)

    async def release_budget(self, command: ReleaseBudgetCommand) -> BudgetOperationResult:
        amount = Money.from_value(command.amount, command.currency)
        existing = await self.budget_repo.get_ledger_by_idempotency_key(command.tenant_id, command.idempotency_key)
        if existing is not None:
            _assert_existing_ledger_matches(existing, BudgetLedgerType.RELEASE, command, amount)
            account_model = await self.budget_repo.get_account_by_id(command.tenant_id, command.account_id)
            if account_model is None:
                raise ValueError("Budget account not found")
            return _operation_result_from_existing(existing, _model_to_account(account_model), duplicated=True)

        account_model = await self.budget_repo.get_account_for_update(command.tenant_id, command.account_id)
        if account_model is None:
            raise ValueError("Budget account not found")
        account = _model_to_account(account_model)
        before, after = account.release(amount)
        _sync_account_to_model(account, account_model)
        ledger_model = _build_ledger_model(command, BudgetLedgerType.RELEASE, amount, before, after)
        await self.budget_repo.add_ledger(ledger_model)
        await self.budget_repo.update_account(account_model)
        return _operation_result_from_existing(ledger_model, account, duplicated=False)


class BudgetReadTool:
    """Read-only adapter for Rule Gate and Agent modules."""

    def __init__(self, budget_service: BudgetService) -> None:
        self.budget_service = budget_service

    async def check_availability(self, check: BudgetAvailabilityCheck) -> BudgetAvailability:
        result = await self.budget_service.check_availability(
            CheckBudgetAvailabilityCommand(
                tenant_id=check.tenant_id,
                account_id=check.account_id,
                amount=check.amount,
                currency=check.currency,
            )
        )
        return BudgetAvailability(
            tenant_id=result.tenant_id,
            account_id=result.account_id,
            requested_amount=result.requested_amount,
            available_amount=result.available_amount,
            currency=result.currency,
            is_available=result.is_available,
        )


def _build_ledger_model(
    command: ReserveBudgetCommand | ReleaseBudgetCommand,
    entry_type: BudgetLedgerType,
    amount: Money,
    before: Money,
    after: Money,
) -> Any:
    from src.adapters.persistence.budget.models import BudgetLedgerEntryModel

    return BudgetLedgerEntryModel(
        id=str(uuid4()),
        tenant_id=command.tenant_id,
        account_id=command.account_id,
        entry_type=entry_type.value,
        amount=amount.amount,
        currency=amount.currency,
        business_type=command.business_type,
        business_id=command.business_id,
        idempotency_key=command.idempotency_key,
        before_available_amount=before.amount,
        after_available_amount=after.amount,
    )


def _model_to_account(model: Any) -> BudgetAccount:
    currency = str(getattr(model, "currency", "CNY"))
    return BudgetAccount(
        id=str(getattr(model, "id", "")),
        tenant_id=str(getattr(model, "tenant_id", "")),
        budget_center_id=str(getattr(model, "budget_center_id", "")),
        currency=currency,
        allocated_amount=Money.from_value(getattr(model, "allocated_amount", "0"), currency),
        reserved_amount=Money.from_value(getattr(model, "reserved_amount", "0"), currency),
        spent_amount=Money.from_value(getattr(model, "spent_amount", "0"), currency),
        version=int(getattr(model, "version", 1) or 1),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def _sync_account_to_model(account: BudgetAccount, model: Any) -> None:
    model.allocated_amount = (account.allocated_amount or Money.from_value("0", account.currency)).amount
    model.reserved_amount = (account.reserved_amount or Money.from_value("0", account.currency)).amount
    model.spent_amount = (account.spent_amount or Money.from_value("0", account.currency)).amount
    model.version = account.version


def _account_result_from_model(model: Any) -> BudgetAccountResult:
    account = _model_to_account(model)
    allocated = account.allocated_amount or Money.from_value("0", account.currency)
    reserved = account.reserved_amount or Money.from_value("0", account.currency)
    spent = account.spent_amount or Money.from_value("0", account.currency)
    return BudgetAccountResult(
        account_id=account.id,
        tenant_id=account.tenant_id,
        budget_center_id=account.budget_center_id,
        allocated_amount=allocated.to_string(),
        reserved_amount=reserved.to_string(),
        spent_amount=spent.to_string(),
        available_amount=account.available_amount().to_string(),
        currency=account.currency,
        version=account.version,
    )


def _operation_result_from_existing(model: Any, account: BudgetAccount, *, duplicated: bool) -> BudgetOperationResult:
    amount = Money.from_value(getattr(model, "amount", "0"), str(getattr(model, "currency", account.currency)))
    reserved = account.reserved_amount or Money.from_value("0", account.currency)
    return BudgetOperationResult(
        ledger_id=str(getattr(model, "id", "")),
        account_id=str(getattr(model, "account_id", account.id)),
        tenant_id=str(getattr(model, "tenant_id", account.tenant_id)),
        entry_type=str(getattr(model, "entry_type", "")),
        amount=amount.to_string(),
        available_amount=account.available_amount().to_string(),
        reserved_amount=reserved.to_string(),
        currency=amount.currency,
        duplicated=duplicated,
    )


def _assert_existing_ledger_matches(
    model: Any,
    expected_type: BudgetLedgerType,
    command: ReserveBudgetCommand | ReleaseBudgetCommand,
    amount: Money,
) -> None:
    if str(getattr(model, "entry_type", "")) != expected_type.value:
        raise ValueError("Idempotency key already used for another budget operation")
    if str(getattr(model, "account_id", "")) != command.account_id:
        raise ValueError("Idempotency key already used for another budget account")
    if str(getattr(model, "business_type", "")) != command.business_type:
        raise ValueError("Idempotency key already used for another business type")
    if str(getattr(model, "business_id", "")) != command.business_id:
        raise ValueError("Idempotency key already used for another business id")
    if Money.from_value(getattr(model, "amount", "0"), str(getattr(model, "currency", amount.currency))) != amount:
        raise ValueError("Idempotency key already used for another budget amount")
