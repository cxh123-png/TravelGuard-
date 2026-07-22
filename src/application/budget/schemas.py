"""Budget application command and result schemas."""

from pydantic import BaseModel, Field


class CreateBudgetAccountCommand(BaseModel):
    tenant_id: str
    budget_center_id: str
    allocated_amount: str
    currency: str = "CNY"


class CheckBudgetAvailabilityCommand(BaseModel):
    tenant_id: str
    account_id: str
    amount: str
    currency: str = "CNY"


class ReserveBudgetCommand(BaseModel):
    tenant_id: str
    account_id: str
    business_type: str = Field(default="TRAVEL_REQUEST")
    business_id: str
    amount: str
    currency: str = "CNY"
    idempotency_key: str


class ReleaseBudgetCommand(BaseModel):
    tenant_id: str
    account_id: str
    business_type: str = Field(default="TRAVEL_REQUEST")
    business_id: str
    amount: str
    currency: str = "CNY"
    idempotency_key: str


class BudgetAccountResult(BaseModel):
    account_id: str
    tenant_id: str
    budget_center_id: str
    allocated_amount: str
    reserved_amount: str
    spent_amount: str
    available_amount: str
    currency: str
    version: int


class BudgetAvailabilityResult(BaseModel):
    account_id: str
    tenant_id: str
    requested_amount: str
    available_amount: str
    currency: str
    is_available: bool


class BudgetOperationResult(BaseModel):
    ledger_id: str
    account_id: str
    tenant_id: str
    entry_type: str
    amount: str
    available_amount: str
    reserved_amount: str
    currency: str
    duplicated: bool = False
