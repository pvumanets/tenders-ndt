"""056: lot_state.l1_mailed_at for auto L1 mail idempotency.

Revision ID: 0017_l1_mailed_at
Revises: 0016_schedule_pipeline
Create Date: 2026-08-31

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_l1_mailed_at"
down_revision: Union[str, Sequence[str], None] = "0016_schedule_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lot_state",
        sa.Column("l1_mailed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lot_state", "l1_mailed_at")
