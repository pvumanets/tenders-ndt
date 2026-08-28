"""037: supply minus (поставка/закупка/прибор) on all search packages.

Revision ID: 0012_supply_exclude_all
Revises: 0011_search_exclude
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_supply_exclude_all"
down_revision: Union[str, Sequence[str], None] = "0011_search_exclude"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SUPPLY = ["поставка", "закупка", "прибор"]


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, exclude FROM searches")).fetchall()
    for row_id, exclude in rows:
        current = list(exclude or [])
        merged = list(current)
        for phrase in _SUPPLY:
            if phrase not in merged:
                merged.append(phrase)
        conn.execute(
            sa.text("UPDATE searches SET exclude = CAST(:e AS jsonb) WHERE id = :id"),
            {"id": row_id, "e": json.dumps(merged, ensure_ascii=False)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, exclude FROM searches")).fetchall()
    for row_id, exclude in rows:
        current = [x for x in (exclude or []) if x not in _SUPPLY]
        conn.execute(
            sa.text("UPDATE searches SET exclude = CAST(:e AS jsonb) WHERE id = :id"),
            {"id": row_id, "e": json.dumps(current, ensure_ascii=False)},
        )
