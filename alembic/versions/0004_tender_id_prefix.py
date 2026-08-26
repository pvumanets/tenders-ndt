"""Widen tender_id and prefix existing rostender rows (024).

Revision ID: 0004_tender_id_prefix
Revises: 0003_searches
Create Date: 2026-08-26

"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_tender_id_prefix"
down_revision: Union[str, Sequence[str], None] = "0003_searches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TENDER_ID_LEN = 128


def _docs_root() -> Path:
    raw = os.environ.get("SCOUT_DOCS_DIR", "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else Path.cwd() / path
    return Path.cwd() / "data" / "docs"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fk_lot_state = next(
        (
            fk["name"]
            for fk in inspector.get_foreign_keys("lot_state")
            if fk.get("constrained_columns") == ["tender_id"]
        ),
        "lot_state_tender_id_fkey",
    )
    fk_documents = next(
        (
            fk["name"]
            for fk in inspector.get_foreign_keys("documents")
            if fk.get("constrained_columns") == ["tender_id"]
        ),
        "documents_tender_id_fkey",
    )
    op.drop_constraint(fk_lot_state, "lot_state", type_="foreignkey")
    op.drop_constraint(fk_documents, "documents", type_="foreignkey")

    op.alter_column(
        "lots",
        "tender_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=_TENDER_ID_LEN),
        existing_nullable=False,
    )
    op.alter_column(
        "lot_state",
        "tender_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=_TENDER_ID_LEN),
        existing_nullable=False,
    )
    op.alter_column(
        "documents",
        "tender_id",
        existing_type=sa.String(length=64),
        type_=sa.String(length=_TENDER_ID_LEN),
        existing_nullable=False,
    )

    op.execute(
        sa.text(
            """
            UPDATE lots
            SET tender_id = 'rostender:' || tender_id
            WHERE tender_id ~ '^[0-9]+$'
              AND (source_platform_id IS NULL OR source_platform_id = 'rostender')
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE lot_state AS ls
            SET tender_id = 'rostender:' || ls.tender_id
            WHERE ls.tender_id ~ '^[0-9]+$'
              AND EXISTS (
                SELECT 1 FROM lots AS l
                WHERE l.tender_id = 'rostender:' || ls.tender_id
              )
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE documents AS d
            SET
              tender_id = 'rostender:' || d.tender_id,
              volume_path = CASE
                WHEN position('/' in d.volume_path) > 0
                  THEN 'rostender__' || split_part(d.volume_path, '/', 1)
                       || '/' || substring(d.volume_path from position('/' in d.volume_path) + 1)
                ELSE 'rostender__' || d.volume_path
              END
            WHERE d.tender_id ~ '^[0-9]+$'
              AND EXISTS (
                SELECT 1 FROM lots AS l
                WHERE l.tender_id = 'rostender:' || d.tender_id
              )
            """
        )
    )

    op.create_foreign_key(
        fk_lot_state,
        "lot_state",
        "lots",
        ["tender_id"],
        ["tender_id"],
    )
    op.create_foreign_key(
        fk_documents,
        "documents",
        "lots",
        ["tender_id"],
        ["tender_id"],
    )

    try:
        from app.worker.platform_ids import rename_legacy_docs_dirs

        rename_legacy_docs_dirs(_docs_root())
    except Exception:  # noqa: BLE001 — volume may be absent in CI
        pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fk_lot_state = next(
        (
            fk["name"]
            for fk in inspector.get_foreign_keys("lot_state")
            if fk.get("constrained_columns") == ["tender_id"]
        ),
        "lot_state_tender_id_fkey",
    )
    fk_documents = next(
        (
            fk["name"]
            for fk in inspector.get_foreign_keys("documents")
            if fk.get("constrained_columns") == ["tender_id"]
        ),
        "documents_tender_id_fkey",
    )
    op.drop_constraint(fk_lot_state, "lot_state", type_="foreignkey")
    op.drop_constraint(fk_documents, "documents", type_="foreignkey")

    op.execute(
        sa.text(
            """
            UPDATE documents
            SET
              tender_id = substring(tender_id from length('rostender:') + 1),
              volume_path = CASE
                WHEN volume_path LIKE 'rostender__%'
                  THEN substring(volume_path from length('rostender__') + 1)
                ELSE volume_path
              END
            WHERE tender_id LIKE 'rostender:%'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE lot_state
            SET tender_id = substring(tender_id from length('rostender:') + 1)
            WHERE tender_id LIKE 'rostender:%'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE lots
            SET tender_id = substring(tender_id from length('rostender:') + 1)
            WHERE tender_id LIKE 'rostender:%'
            """
        )
    )

    op.alter_column(
        "documents",
        "tender_id",
        existing_type=sa.String(length=_TENDER_ID_LEN),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.alter_column(
        "lot_state",
        "tender_id",
        existing_type=sa.String(length=_TENDER_ID_LEN),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.alter_column(
        "lots",
        "tender_id",
        existing_type=sa.String(length=_TENDER_ID_LEN),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.create_foreign_key(
        fk_lot_state,
        "lot_state",
        "lots",
        ["tender_id"],
        ["tender_id"],
    )
    op.create_foreign_key(
        fk_documents,
        "documents",
        "lots",
        ["tender_id"],
        ["tender_id"],
    )
