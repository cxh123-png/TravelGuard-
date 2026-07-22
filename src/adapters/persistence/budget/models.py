"""Budget SQLAlchemy models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class BudgetAccountModel(Base):
    """Budget account table."""

    __tablename__ = "budget_accounts"
    __table_args__ = (UniqueConstraint("tenant_id", "budget_center_id", "currency", name="uq_budget_account_scope"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    budget_center_id: Mapped[str] = mapped_column(String(64), index=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    reserved_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ledger_entries: Mapped[list["BudgetLedgerEntryModel"]] = relationship(back_populates="account")
    __mapper_args__ = {"version_id_col": version}


class BudgetLedgerEntryModel(Base):
    """Append-only budget ledger entry table."""

    __tablename__ = "budget_ledger_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_budget_ledger_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("budget_accounts.id"), index=True)
    entry_type: Mapped[str] = mapped_column(String(32), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    business_type: Mapped[str] = mapped_column(String(64), index=True)
    business_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)
    before_available_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    after_available_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    account: Mapped[BudgetAccountModel] = relationship(back_populates="ledger_entries")
