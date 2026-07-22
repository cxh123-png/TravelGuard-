"""政策数据库 ORM 模型。"""

from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class PolicyModel(Base):
    """政策数据库模型。"""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    target_org_ids: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    versions: Mapped[list["PolicyVersionModel"]] = relationship(
        back_populates="policy", cascade="all, delete-orphan"
    )


class PolicyVersionModel(Base):
    """政策版本数据库模型。"""

    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int]
    effective_date: Mapped[datetime] = mapped_column(Date)
    expiry_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    policy: Mapped[PolicyModel] = relationship(back_populates="versions")
    rules: Mapped[list["PolicyRuleModel"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class PolicyRuleModel(Base):
    """规则数据库模型。"""

    __tablename__ = "policy_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[str] = mapped_column(
        ForeignKey("policy_versions.id", ondelete="CASCADE"), index=True
    )
    rule_type: Mapped[str] = mapped_column(String(64))
    limit_value: Mapped[str] = mapped_column(String(64))
    is_exception_allowed: Mapped[bool] = mapped_column(default=False)
    condition_json: Mapped[str] = mapped_column(String(1024), default="")
    exception_approver_roles: Mapped[str] = mapped_column(String(512), default="")

    version: Mapped[PolicyVersionModel] = relationship(back_populates="rules")
