"""Read-only budget tool contract for Rule Gate and Agent modules."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetAvailabilityCheck:
    tenant_id: str
    account_id: str
    amount: str
    currency: str = "CNY"


@dataclass(frozen=True)
class BudgetAvailability:
    tenant_id: str
    account_id: str
    requested_amount: str
    available_amount: str
    currency: str
    is_available: bool
