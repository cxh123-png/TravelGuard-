"""M3: budget and approval tables.

Revision ID: 2026_07_22_0002
Revises: 2026_07_22_0001
Create Date: 2026-07-22 12:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_07_22_0002"
down_revision: Union[str, None] = "2026_07_22_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budget_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("budget_center_id", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("allocated_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("reserved_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("spent_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "budget_center_id", "currency", name="uq_budget_account_scope"),
    )
    op.create_index("ix_budget_accounts_tenant_id", "budget_accounts", ["tenant_id"])
    op.create_index("ix_budget_accounts_budget_center_id", "budget_accounts", ["budget_center_id"])

    op.create_table(
        "budget_ledger_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("budget_accounts.id"), nullable=False),
        sa.Column("entry_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("business_type", sa.String(64), nullable=False),
        sa.Column("business_id", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("before_available_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("after_available_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_budget_ledger_idempotency"),
    )
    op.create_index("ix_budget_ledger_entries_tenant_id", "budget_ledger_entries", ["tenant_id"])
    op.create_index("ix_budget_ledger_entries_account_id", "budget_ledger_entries", ["account_id"])
    op.create_index("ix_budget_ledger_entries_entry_type", "budget_ledger_entries", ["entry_type"])
    op.create_index("ix_budget_ledger_entries_business_type", "budget_ledger_entries", ["business_type"])
    op.create_index("ix_budget_ledger_entries_business_id", "budget_ledger_entries", ["business_id"])
    op.create_index("ix_budget_ledger_entries_idempotency_key", "budget_ledger_entries", ["idempotency_key"])

    op.create_table(
        "approval_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("business_type", sa.String(64), nullable=False),
        sa.Column("business_id", sa.String(64), nullable=False),
        sa.Column("applicant_id", sa.String(64), nullable=False),
        sa.Column("approver_role", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("budget_account_id", sa.String(36), nullable=True),
        sa.Column("reserved_amount", sa.String(64), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="CNY"),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_approval_tasks_tenant_id", "approval_tasks", ["tenant_id"])
    op.create_index("ix_approval_tasks_business_type", "approval_tasks", ["business_type"])
    op.create_index("ix_approval_tasks_business_id", "approval_tasks", ["business_id"])
    op.create_index("ix_approval_tasks_applicant_id", "approval_tasks", ["applicant_id"])
    op.create_index("ix_approval_tasks_approver_role", "approval_tasks", ["approver_role"])
    op.create_index("ix_approval_tasks_status", "approval_tasks", ["status"])

    op.create_table(
        "approval_actions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("approval_tasks.id"), nullable=False),
        sa.Column("action_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("comment", sa.String(512), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_approval_action_idempotency"),
    )
    op.create_index("ix_approval_actions_tenant_id", "approval_actions", ["tenant_id"])
    op.create_index("ix_approval_actions_task_id", "approval_actions", ["task_id"])
    op.create_index("ix_approval_actions_action_type", "approval_actions", ["action_type"])
    op.create_index("ix_approval_actions_actor_id", "approval_actions", ["actor_id"])
    op.create_index("ix_approval_actions_idempotency_key", "approval_actions", ["idempotency_key"])


def downgrade() -> None:
    op.drop_index("ix_approval_actions_idempotency_key", table_name="approval_actions")
    op.drop_index("ix_approval_actions_actor_id", table_name="approval_actions")
    op.drop_index("ix_approval_actions_action_type", table_name="approval_actions")
    op.drop_index("ix_approval_actions_task_id", table_name="approval_actions")
    op.drop_index("ix_approval_actions_tenant_id", table_name="approval_actions")
    op.drop_table("approval_actions")

    op.drop_index("ix_approval_tasks_status", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_approver_role", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_applicant_id", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_business_id", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_business_type", table_name="approval_tasks")
    op.drop_index("ix_approval_tasks_tenant_id", table_name="approval_tasks")
    op.drop_table("approval_tasks")

    op.drop_index("ix_budget_ledger_entries_idempotency_key", table_name="budget_ledger_entries")
    op.drop_index("ix_budget_ledger_entries_business_id", table_name="budget_ledger_entries")
    op.drop_index("ix_budget_ledger_entries_business_type", table_name="budget_ledger_entries")
    op.drop_index("ix_budget_ledger_entries_entry_type", table_name="budget_ledger_entries")
    op.drop_index("ix_budget_ledger_entries_account_id", table_name="budget_ledger_entries")
    op.drop_index("ix_budget_ledger_entries_tenant_id", table_name="budget_ledger_entries")
    op.drop_table("budget_ledger_entries")

    op.drop_index("ix_budget_accounts_budget_center_id", table_name="budget_accounts")
    op.drop_index("ix_budget_accounts_tenant_id", table_name="budget_accounts")
    op.drop_table("budget_accounts")
