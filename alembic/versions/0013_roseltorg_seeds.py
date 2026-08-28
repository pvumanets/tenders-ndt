"""040: seed Росэлторг CORP named searches (queue gated by credentials).

Revision ID: 0013_roseltorg_seeds
Revises: 0012_supply_exclude_all
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.worker.platform_ids import PLATFORM_ROSELTORG
from app.worker.search_seeds import search_seed_rows

revision: str = "0013_roseltorg_seeds"
down_revision: Union[str, Sequence[str], None] = "0012_supply_exclude_all"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = [
        row
        for row in search_seed_rows(roseltorg_in_queue=False)
        if row["platform_id"] == PLATFORM_ROSELTORG
    ]
    for row in rows:
        conn.execute(
            sa.text("DELETE FROM searches WHERE id = :id OR name = :name"),
            {"id": row["id"], "name": row["name"]},
        )
        conn.execute(
            sa.text(
                "INSERT INTO searches "
                "(id, name, platform_id, queries, exclude, limit_n, in_queue, sort_order) "
                "VALUES (:id, :name, :platform_id, CAST(:queries AS jsonb), "
                "CAST(:exclude AS jsonb), :limit_n, :in_queue, :sort_order)"
            ),
            {
                "id": row["id"],
                "name": row["name"],
                "platform_id": row["platform_id"],
                "queries": json.dumps(row["queries"], ensure_ascii=False),
                "exclude": json.dumps(row.get("exclude") or [], ensure_ascii=False),
                "limit_n": row["limit_n"],
                "in_queue": bool(row["in_queue"]),
                "sort_order": row["sort_order"],
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for row in search_seed_rows(roseltorg_in_queue=False):
        if row["platform_id"] != PLATFORM_ROSELTORG:
            continue
        conn.execute(
            sa.text("DELETE FROM searches WHERE id = :id"),
            {"id": row["id"]},
        )
