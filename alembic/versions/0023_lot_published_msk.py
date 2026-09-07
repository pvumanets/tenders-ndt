"""091: lots.published_msk — ETP publication date (nullable text).

Revision ID: 0023_lot_published_msk
Revises: 0022_operator_settings_bitrix
Create Date: 2026-09-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_lot_published_msk"
down_revision: Union[str, Sequence[str], None] = "0022_operator_settings_bitrix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("lots", sa.Column("published_msk", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("lots", "published_msk")
