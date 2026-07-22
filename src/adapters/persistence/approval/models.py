"""Approval SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class ApprovalTaskModel(Base):
    """Single-step approval task table."""

    __tablename__ = "approval_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    business_type: Mapped[str] = mapped_column(String(64), index=True)
    business_id: Mapped[str] = mapped_column(String(64), index=True)
    applicant_id: Mapped[str] = mapped_column(String(64), index=True)
    approver_role: Mapped[str] = mapped_column(String(64), index=True)
    created_by: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True)
    budget_account_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reserved_amount: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    actions: Mapped[list["ApprovalActionModel"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    __mapper_args__ = {"version_id_col": version}


class ApprovalActionModel(Base):
    """Append-only approval action table."""

    __tablename__ = "approval_actions"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_approval_action_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("approval_tasks.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(32), index=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    comment: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[ApprovalTaskModel] = relationship(back_populates="actions")
