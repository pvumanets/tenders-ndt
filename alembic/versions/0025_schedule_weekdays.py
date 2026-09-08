"""schedule_settings.weekdays — MSK weekday mask for auto-run.

Revision ID: 0025_schedule_weekdays
Revises: 0024_tier_teach_prompt
Create Date: 2026-09-08
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025_schedule_weekdays"
down_revision: Union[str, Sequence[str], None] = "0024_tier_teach_prompt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schedule_settings",
        sa.Column(
            "weekdays",
            sa.String(length=32),
            nullable=False,
            server_default="0,1,2,3,4,5,6",
        ),
    )


def downgrade() -> None:
    op.drop_column("schedule_settings", "weekdays")
