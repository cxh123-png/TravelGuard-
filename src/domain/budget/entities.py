"""Budget domain entities."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.domain.budget.value_objects import Money


class BudgetLedgerType(StrEnum):
    """Append-only budget ledger entry type."""

    ALLOCATE = "ALLOCATE"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    SETTLE = "SETTLE"
    ADJUST = "ADJUST"


@dataclass
class BudgetAccount:
    """Budget account with reserved and spent balances."""

    id: str
    tenant_id: str
    budget_center_id: str
    currency: str = "CNY"
    allocated_amount: Money | None = None
    reserved_amount: Money | None = None
    spent_amount: Money | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        self.allocated_amount = self.allocated_amount or Money.from_value("0", self.currency)
        self.reserved_amount = self.reserved_amount or Money.from_value("0", self.currency)
        self.spent_amount = self.spent_amount or Money.from_value("0", self.currency)
        self._ensure_currency(self.allocated_amount)
        self._ensure_currency(self.reserved_amount)
        self._ensure_currency(self.spent_amount)

    def available_amount(self) -> Money:
        reserved = self.reserved_amount or Money.from_value("0", self.currency)
        spent = self.spent_amount or Money.from_value("0", self.currency)
        allocated = self.allocated_amount or Money.from_value("0", self.currency)
        return allocated.subtract(reserved).subtract(spent)

    def can_reserve(self, amount: Money) -> bool:
        self._ensure_currency(amount)
        amount.require_positive()
        return self.available_amount().amount >= amount.amount

    def reserve(self, amount: Money) -> tuple[Money, Money]:
        self._ensure_currency(amount)
        amount.require_positive()
        before = self.available_amount()
        if before.amount < amount.amount:
            raise ValueError("Insufficient budget available")
        current_reserved = self.reserved_amount or Money.from_value("0", self.currency)
        self.reserved_amount = current_reserved.add(amount)
        self.version += 1
        return before, self.available_amount()

    def release(self, amount: Money) -> tuple[Money, Money]:
        self._ensure_currency(amount)
        amount.require_positive()
        current_reserved = self.reserved_amount or Money.from_value("0", self.currency)
        if current_reserved.amount < amount.amount:
            raise ValueError("Release amount exceeds reserved budget")
        before = self.available_amount()
        self.reserved_amount = current_reserved.subtract(amount)
        self.version += 1
        return before, self.available_amount()

    def _ensure_currency(self, money: Money) -> None:
        if money.currency != self.currency:
            raise ValueError("Budget account currency mismatch")


@dataclass(frozen=True)
class BudgetLedgerEntry:
    """Immutable budget ledger fact."""

    id: str
    tenant_id: str
    account_id: str
    entry_type: BudgetLedgerType
    amount: Money
    business_type: str
    business_id: str
    idempotency_key: str
    before_available_amount: Money
    after_available_amount: Money
    created_at: datetime | None = None
