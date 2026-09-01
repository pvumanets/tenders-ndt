"""0019: platform_settings row for rts-rosatom (disabled until cookie sync / operator).

Revision ID: 0019_rts_rosatom_platform
Revises: 0018_b2b_center_platform
Create Date: 2026-09-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_rts_rosatom_platform"
down_revision: Union[str, Sequence[str], None] = "0018_b2b_center_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM platform_settings WHERE platform_id = :pid LIMIT 1"
        ),
        {"pid": "rts-rosatom"},
    ).first()
    if exists is None:
        conn.execute(
            sa.text(
                "INSERT INTO platform_settings (platform_id, enabled) "
                "VALUES (:platform_id, :enabled)"
            ),
            {"platform_id": "rts-rosatom", "enabled": False},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM platform_settings WHERE platform_id = :pid"),
        {"pid": "rts-rosatom"},
    )
