"""092: tier_teach_events + operator_settings.ai_system_prompt.

Revision ID: 0024_tier_teach_prompt
Revises: 0023_lot_published_msk
Create Date: 2026-09-08

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_tier_teach_prompt"
down_revision: Union[str, Sequence[str], None] = "0023_lot_published_msk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "operator_settings",
        sa.Column("ai_system_prompt", sa.Text(), nullable=True),
    )
    op.create_table(
        "tier_teach_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("from_bucket", sa.String(length=16), nullable=False),
        sa.Column("to_bucket", sa.String(length=16), nullable=False),
        sa.Column("drop_tier_correct", sa.Boolean(), nullable=False),
        sa.Column("reason_ru", sa.Text(), nullable=False),
        sa.Column("rules_tier", sa.String(length=8), nullable=True),
        sa.Column("ai_tier", sa.String(length=8), nullable=True),
        sa.Column("manual_tier_before", sa.String(length=8), nullable=True),
        sa.Column("effective_tier_before", sa.String(length=8), nullable=True),
        sa.Column("deadline_expired_before", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ai_reviewed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["tender_id"], ["lots.tender_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_tier_teach_events_created_at", "tier_teach_events", ["created_at"])
    op.create_index("ix_tier_teach_events_tender_id", "tier_teach_events", ["tender_id"])


def downgrade() -> None:
    op.drop_index("ix_tier_teach_events_tender_id", table_name="tier_teach_events")
    op.drop_index("ix_tier_teach_events_created_at", table_name="tier_teach_events")
    op.drop_table("tier_teach_events")
    op.drop_column("operator_settings", "ai_system_prompt")
