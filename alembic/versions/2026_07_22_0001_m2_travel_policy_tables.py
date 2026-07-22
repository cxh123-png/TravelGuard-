"""M2: 差旅申请与政策规则表。

Revision ID: 2026_07_22_0001
Revises: None
Create Date: 2026-07-22 10:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2026_07_22_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "travel_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), index=True),
        sa.Column("user_id", sa.String(36), index=True),
        sa.Column("status", sa.String(32), default="DRAFT"),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("version", sa.Integer, default=1),
    )

    op.create_table(
        "travel_itineraries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_id", sa.String(36), sa.ForeignKey("travel_requests.id", ondelete="CASCADE"), index=True),
        sa.Column("city", sa.String(64)),
        sa.Column("check_in", sa.Date),
        sa.Column("check_out", sa.Date),
        sa.Column("estimated_hotel_amount", sa.Numeric(18, 2)),
        sa.Column("estimated_transport_amount", sa.Numeric(18, 2)),
        sa.Column("purpose", sa.String(256), default=""),
    )

    op.create_table(
        "policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), index=True),
        sa.Column("name", sa.String(128)),
        sa.Column("status", sa.String(32), default="DRAFT"),
        sa.Column("target_org_ids", sa.String(512), default=""),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "policy_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("policy_id", sa.String(36), sa.ForeignKey("policies.id", ondelete="CASCADE"), index=True),
        sa.Column("version_number", sa.Integer),
        sa.Column("effective_date", sa.Date),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, default=sa.func.now()),
    )

    op.create_table(
        "policy_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("policy_versions.id", ondelete="CASCADE"), index=True),
        sa.Column("rule_type", sa.String(64)),
        sa.Column("limit_value", sa.String(64)),
        sa.Column("is_exception_allowed", sa.Boolean, default=False),
        sa.Column("condition_json", sa.String(1024), default=""),
        sa.Column("exception_approver_roles", sa.String(512), default=""),
    )


def downgrade() -> None:
    op.drop_table("policy_rules")
    op.drop_table("policy_versions")
    op.drop_table("policies")
    op.drop_table("travel_itineraries")
    op.drop_table("travel_requests")
