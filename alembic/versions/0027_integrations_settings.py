"""111: operator_settings integrations (Provod key + Bitrix routing).

Revision ID: 0027_integrations_settings
Revises: 0026_lot_docs_status
Create Date: 2026-09-11

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027_integrations_settings"
down_revision: Union[str, Sequence[str], None] = "0026_lot_docs_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("operator_settings", sa.Column("provod_api_key", sa.Text(), nullable=True))
    op.add_column("operator_settings", sa.Column("bitrix_webhook_url", sa.Text(), nullable=True))
    op.add_column(
        "operator_settings", sa.Column("bitrix_assigned_by_id", sa.Text(), nullable=True)
    )
    op.add_column(
        "operator_settings", sa.Column("bitrix_lead_source_id", sa.Text(), nullable=True)
    )
    op.add_column(
        "operator_settings", sa.Column("bitrix_chat_dialog_id", sa.Text(), nullable=True)
    )
    op.add_column(
        "operator_settings", sa.Column("bitrix_ops_dialog_id", sa.Text(), nullable=True)
    )
    op.add_column(
        "operator_settings", sa.Column("bitrix_send_chat", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "operator_settings", sa.Column("bitrix_auto_l1_enabled", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "operator_settings",
        sa.Column("bitrix_ops_alerts_enabled", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("operator_settings", "bitrix_ops_alerts_enabled")
    op.drop_column("operator_settings", "bitrix_auto_l1_enabled")
    op.drop_column("operator_settings", "bitrix_send_chat")
    op.drop_column("operator_settings", "bitrix_ops_dialog_id")
    op.drop_column("operator_settings", "bitrix_chat_dialog_id")
    op.drop_column("operator_settings", "bitrix_lead_source_id")
    op.drop_column("operator_settings", "bitrix_assigned_by_id")
    op.drop_column("operator_settings", "bitrix_webhook_url")
    op.drop_column("operator_settings", "provod_api_key")
