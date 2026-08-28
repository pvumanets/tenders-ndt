"""P11/030: replace legacy search seeds with A–E + Tender.Pro packages.

Revision ID: 0007_search_coverage
Revises: 0006_ai_review
Create Date: 2026-08-27

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.worker.search_seeds import LEGACY_SEARCH_IDS, search_seed_rows

revision: str = "0007_search_coverage"
down_revision: Union[str, Sequence[str], None] = "0006_ai_review"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    searches = sa.table(
        "searches",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("platform_id", sa.String()),
        sa.column("queries", postgresql.JSONB()),
        sa.column("limit_n", sa.Integer()),
        sa.column("in_queue", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    conn = op.get_bind()
    # Drop legacy single-query seeds (FK on runs.search_id is ON DELETE SET NULL).
    for legacy_id in LEGACY_SEARCH_IDS:
        conn.execute(sa.text("DELETE FROM searches WHERE id = :id"), {"id": legacy_id})
    # Also drop by old names if IDs already changed
    conn.execute(
        sa.text(
            "DELETE FROM searches WHERE name IN "
            "('РосТендер НК', 'Tender.Pro НК')"
        )
    )
    rows = search_seed_rows(tender_pro_in_queue=False)
    for row in rows:
        conn.execute(
            sa.text("DELETE FROM searches WHERE id = :id OR name = :name"),
            {"id": row["id"], "name": row["name"]},
        )
    # exclude column arrives in 0011 — strip so historical upgrade stays valid
    op.bulk_insert(
        searches,
        [{k: v for k, v in row.items() if k != "exclude"} for row in rows],
    )


def downgrade() -> None:
    conn = op.get_bind()
    for row in search_seed_rows(tender_pro_in_queue=False):
        conn.execute(
            sa.text("DELETE FROM searches WHERE id = :id"),
            {"id": row["id"]},
        )
    searches = sa.table(
        "searches",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("platform_id", sa.String()),
        sa.column("queries", postgresql.JSONB()),
        sa.column("limit_n", sa.Integer()),
        sa.column("in_queue", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
    )
    from uuid import UUID

    op.bulk_insert(
        searches,
        [
            {
                "id": UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000001"),
                "name": "РосТендер НК",
                "platform_id": "rostender",
                "queries": ["неразрушающий"],
                "limit_n": 1000,
                "in_queue": True,
                "sort_order": 0,
            },
            {
                "id": UUID("aaaaaaaa-bbbb-4ccc-8ddd-000000000002"),
                "name": "Tender.Pro НК",
                "platform_id": "tender-pro",
                "queries": ["ВИК", "ПВК", "УЗК", "РК"],
                "limit_n": 1000,
                "in_queue": False,
                "sort_order": 1,
            },
        ],
    )
