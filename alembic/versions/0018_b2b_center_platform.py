"""0018: platform_settings row for b2b-center (disabled until cookie sync / operator).

Revision ID: 0018_b2b_center_platform
Revises: 0017_l1_mailed_at
Create Date: 2026-08-31

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_b2b_center_platform"
down_revision: Union[str, Sequence[str], None] = "0017_l1_mailed_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM platform_settings WHERE platform_id = :pid LIMIT 1"
        ),
        {"pid": "b2b-center"},
    ).first()
    if exists is None:
        conn.execute(
            sa.text(
                "INSERT INTO platform_settings (platform_id, enabled) "
                "VALUES (:platform_id, :enabled)"
            ),
            {"platform_id": "b2b-center", "enabled": False},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM platform_settings WHERE platform_id = :pid"),
        {"pid": "b2b-center"},
    )
