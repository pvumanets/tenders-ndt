"""071/072: operator_settings singleton + lot_state.bitrix_sent_at stub.

Revision ID: 0022_operator_settings_bitrix
Revises: 0021_sibur_srm_platform
Create Date: 2026-09-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_operator_settings_bitrix"
down_revision: Union[str, Sequence[str], None] = "0021_sibur_srm_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operator_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "l1_min_price_rub",
            sa.Integer(),
            nullable=False,
            server_default="100000",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        sa.text("INSERT INTO operator_settings (id, l1_min_price_rub) VALUES (1, 100000)")
    )
    op.add_column(
        "lot_state",
        sa.Column("bitrix_sent_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lot_state", "bitrix_sent_at")
    op.drop_table("operator_settings")
