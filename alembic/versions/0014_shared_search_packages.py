"""041: shared A–E search packages on all platforms (Rostender lexicon).

Revision ID: 0014_shared_search_packages
Revises: 0013_roseltorg_seeds
Create Date: 2026-08-29

"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.worker.search_seeds import search_seed_rows

revision: str = "0014_shared_search_packages"
down_revision: Union[str, Sequence[str], None] = "0013_roseltorg_seeds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upsert all seed rows (RT/TP/RE A–E) by stable UUID; do not touch non-seed searches."""
    conn = op.get_bind()
    # Gate flags false in migration: queue sync at API boot sets TP/RE from credentials.
    rows = search_seed_rows(tender_pro_in_queue=False, roseltorg_in_queue=False)
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
    """Remove only packages introduced as A on TP/RE; leave aligned B–E as-is."""
    conn = op.get_bind()
    for row in search_seed_rows(tender_pro_in_queue=False, roseltorg_in_queue=False):
        if row["name"].endswith("— услуги НК") and row["platform_id"] in (
            "tender-pro",
            "roseltorg",
        ):
            conn.execute(
                sa.text("DELETE FROM searches WHERE id = :id"),
                {"id": row["id"]},
            )
