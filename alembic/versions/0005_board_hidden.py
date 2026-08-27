"""Add lot_state.board_hidden for P8 archive (027).

Revision ID: 0005_board_hidden
Revises: 0004_tender_id_prefix
Create Date: 2026-08-27

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_board_hidden"
down_revision: Union[str, Sequence[str], None] = "0004_tender_id_prefix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lot_state",
        sa.Column(
            "board_hidden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "lot_state",
        sa.Column("board_hidden_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lot_state", "board_hidden_at")
    op.drop_column("lot_state", "board_hidden")
