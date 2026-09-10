"""lot_state.docs_status + docs_external_url (094 zip-after-AI).

Revision ID: 0026_lot_docs_status
Revises: 0025_schedule_weekdays
Create Date: 2026-09-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026_lot_docs_status"
down_revision: Union[str, Sequence[str], None] = "0025_schedule_weekdays"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "lot_state",
        sa.Column("docs_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "lot_state",
        sa.Column("docs_external_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lot_state", "docs_external_url")
    op.drop_column("lot_state", "docs_status")
