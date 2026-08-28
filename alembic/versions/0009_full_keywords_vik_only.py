"""034: Rostender seeds — full phrases only; VIK as sole abbreviation.

Revision ID: 0009_full_keywords_vik_only
Revises: 0008_no_uk_rk_keywords
Create Date: 2026-08-28

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op

revision: str = "0009_full_keywords_vik_only"
down_revision: Union[str, Sequence[str], None] = "0008_no_uk_rk_keywords"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_RT = {
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a1"): [
        "неразрушающий контроль",
        "дефектоскопия",
    ],
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a2"): [
        "ультразвуковой контроль",
        "визуально-измерительный контроль",
        "капиллярный контроль",
        "радиографический контроль",
        "гаммаграфический контроль",
        "толщинометрия ультразвуковая",
    ],
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a3"): ["ВИК"],
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4"): [
        "принимающий контроль",
        "приёмочный контроль",
        "входной контроль",
        "строительный контроль",
    ],
    UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a5"): [
        "контроль сварных соединений",
        "сварных соединений",
    ],
}


def upgrade() -> None:
    conn = op.get_bind()
    for sid, queries in _RT.items():
        conn.execute(
            sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
            {"id": sid, "q": json.dumps(queries, ensure_ascii=False)},
        )


def downgrade() -> None:
    conn = op.get_bind()
    prev = {
        UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a1"): [
            "неразрушающий контроль",
            "нераз.",
            "дефектоскопия",
            "дефект.",
        ],
        UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a2"): [
            "ультразвуковой контроль",
            "ультр.",
            "визуально-измерительный",
            "визуал.",
            "капиллярный",
            "капиляр.",
            "радиографический",
            "радиогр.",
            "гаммаграфический",
            "гамма.",
            "толщинометрия ультразвуковая",
        ],
        UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a3"): ["НК", "УЗК", "ВИК", "ПВК"],
        UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a4"): [
            "принимающий контроль",
            "прин.",
            "приёмочный контроль",
            "входной контроль",
            "строительный контроль",
        ],
        UUID("aaaaaaaa-bbbb-4ccc-8ddd-0000000000a5"): [
            "контроль сварн",
            "сварных соединений",
            "диагностирование",
            "техническое диагностирование",
        ],
    }
    for sid, queries in prev.items():
        conn.execute(
            sa.text("UPDATE searches SET queries = CAST(:q AS jsonb) WHERE id = :id"),
            {"id": sid, "q": json.dumps(queries, ensure_ascii=False)},
        )
