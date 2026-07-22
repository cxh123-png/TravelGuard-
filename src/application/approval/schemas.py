"""Approval application command and result schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateApprovalTaskCommand(BaseModel):
    tenant_id: str
    business_type: str = Field(default="TRAVEL_REQUEST")
    business_id: str
    applicant_id: str
    approver_role: str
    created_by: str
    idempotency_key: str
    budget_account_id: str | None = None
    reserved_amount: str | None = None
    currency: str = "CNY"
    expires_at: datetime | None = None


class ApprovalDecisionCommand(BaseModel):
    tenant_id: str
    task_id: str
    actor_id: str
    expected_version: int
    idempotency_key: str
    comment: str = ""


class ApprovalTaskResult(BaseModel):
    task_id: str
    tenant_id: str
    business_type: str
    business_id: str
    applicant_id: str
    approver_role: str
    status: str
    version: int
    budget_account_id: str | None = None
    reserved_amount: str | None = None
    currency: str = "CNY"
    duplicated: bool = False
    budget_release_ledger_id: str | None = None
