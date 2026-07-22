"""Approval domain entities."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ApprovalTaskStatus(StrEnum):
    """Approval task lifecycle."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalActionType(StrEnum):
    """Append-only approval action type."""

    CREATED = "CREATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class ApprovalTask:
    """Single-step approval task."""

    id: str
    tenant_id: str
    business_type: str
    business_id: str
    applicant_id: str
    approver_role: str
    created_by: str
    status: ApprovalTaskStatus = ApprovalTaskStatus.PENDING
    budget_account_id: str | None = None
    reserved_amount: str | None = None
    currency: str = "CNY"
    expires_at: datetime | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def approve(self, expected_version: int) -> None:
        self._assert_expected_version(expected_version)
        self._assert_pending()
        self.status = ApprovalTaskStatus.APPROVED
        self.version += 1

    def reject(self, expected_version: int) -> None:
        self._assert_expected_version(expected_version)
        self._assert_pending()
        self.status = ApprovalTaskStatus.REJECTED
        self.version += 1

    def expire(self, expected_version: int) -> None:
        self._assert_expected_version(expected_version)
        self._assert_pending()
        self.status = ApprovalTaskStatus.EXPIRED
        self.version += 1

    def has_budget_reservation(self) -> bool:
        return bool(self.budget_account_id and self.reserved_amount)

    def _assert_pending(self) -> None:
        if self.status != ApprovalTaskStatus.PENDING:
            raise ValueError(f"Approval task is not pending: {self.status.value}")

    def _assert_expected_version(self, expected_version: int) -> None:
        if self.version != expected_version:
            raise ValueError("Approval task version conflict")


@dataclass(frozen=True)
class ApprovalAction:
    """Immutable approval action fact."""

    id: str
    tenant_id: str
    task_id: str
    action_type: ApprovalActionType
    actor_id: str
    idempotency_key: str
    comment: str = ""
    created_at: datetime | None = None
