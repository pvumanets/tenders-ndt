"""0021: platform_settings row for sibur-srm (disabled until cookie sync / operator).

Revision ID: 0021_sibur_srm_platform
Revises: 0020_oilb2bcs_platform
Create Date: 2026-09-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_sibur_srm_platform"
down_revision: Union[str, Sequence[str], None] = "0020_oilb2bcs_platform"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM platform_settings WHERE platform_id = :pid LIMIT 1"
        ),
        {"pid": "sibur-srm"},
    ).first()
    if exists is None:
        conn.execute(
            sa.text(
                "INSERT INTO platform_settings (platform_id, enabled) "
                "VALUES (:platform_id, :enabled)"
            ),
            {"platform_id": "sibur-srm", "enabled": False},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM platform_settings WHERE platform_id = :pid"),
        {"pid": "sibur-srm"},
    )
