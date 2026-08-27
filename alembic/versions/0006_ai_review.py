"""P10/029: AI review fields on lot_state.

Revision ID: 0006_ai_review
Revises: 0005_board_hidden
Create Date: 2026-08-27

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_ai_review"
down_revision: Union[str, Sequence[str], None] = "0005_board_hidden"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lot_state", sa.Column("rules_tier", sa.String(length=8), nullable=True))
    op.add_column(
        "lot_state",
        sa.Column("ai_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("lot_state", sa.Column("ai_tier", sa.String(length=8), nullable=True))
    op.add_column("lot_state", sa.Column("ai_reason_ru", sa.Text(), nullable=True))
    op.add_column("lot_state", sa.Column("ai_error", sa.Text(), nullable=True))
    op.add_column(
        "lot_state",
        sa.Column("ai_wrong_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("lot_state", sa.Column("ai_wrong_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("lot_state", "ai_wrong_note")
    op.drop_column("lot_state", "ai_wrong_at")
    op.drop_column("lot_state", "ai_error")
    op.drop_column("lot_state", "ai_reason_ru")
    op.drop_column("lot_state", "ai_tier")
    op.drop_column("lot_state", "ai_reviewed_at")
    op.drop_column("lot_state", "rules_tier")
