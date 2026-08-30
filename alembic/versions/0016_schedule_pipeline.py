"""054: schedule_settings singleton; runs.pipeline; lot_state.ai_trigger.

Revision ID: 0016_schedule_pipeline
Revises: 0015_search_groups
Create Date: 2026-08-30

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_schedule_pipeline"
down_revision: Union[str, Sequence[str], None] = "0015_search_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedule_settings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("time_msk", sa.String(length=5), nullable=False, server_default="07:00"),
        sa.Column("last_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_skip_reason", sa.Text(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO schedule_settings (id, enabled, time_msk) "
            "VALUES (1, true, '07:00')"
        )
    )
    op.add_column(
        "runs",
        sa.Column("pipeline", sa.String(length=16), nullable=True),
    )
    op.execute(sa.text("UPDATE runs SET pipeline = 'manual' WHERE pipeline IS NULL"))
    op.alter_column(
        "runs",
        "pipeline",
        existing_type=sa.String(length=16),
        nullable=False,
        server_default="manual",
    )
    op.add_column(
        "lot_state",
        sa.Column("ai_trigger", sa.String(length=16), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lot_state", "ai_trigger")
    op.drop_column("runs", "pipeline")
    op.drop_table("schedule_settings")
