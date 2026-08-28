"""033: drop UK/RK from abbreviation search seeds; add UZK.

Revision ID: 0008_no_uk_rk_keywords
Revises: 0007_search_coverage
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0008_no_uk_rk_keywords"
down_revision: Union[str, Sequence[str], None] = "0007_search_coverage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RT_C = UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a3")
_TP_ABBR = UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000b2")

_RT_QUERIES = ["НК", "УЗК", "ВИК", "ПВК"]
_TP_QUERIES = ["ВИК", "ПВК", "УЗК", "НК"]


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
        {"id": _RT_C, "q": json.dumps(_RT_QUERIES, ensure_ascii=False)},
    )
    conn.execute(
        sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
        {"id": _TP_ABBR, "q": json.dumps(_TP_QUERIES, ensure_ascii=False)},
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
        {"id": _RT_C, "q": json.dumps(["НК", "УК", "ВИК", "ПВК", "РК"], ensure_ascii=False)},
    )
    conn.execute(
        sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
        {"id": _TP_ABBR, "q": json.dumps(["ВИК", "ПВК", "УК", "РК", "НК"], ensure_ascii=False)},
    )
