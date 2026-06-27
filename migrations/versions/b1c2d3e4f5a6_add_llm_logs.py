"""add ais_llm_logs (per-call LLM prompt/response logging, admin only)

Revision ID: b1c2d3e4f5a6
Revises: a9f0c1d2e3b4
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a9f0c1d2e3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ais_llm_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("agent", sa.String(length=40), nullable=True),
        sa.Column("model", sa.String(length=60), nullable=True),
        sa.Column("prompt", mysql.LONGTEXT(), nullable=True),
        sa.Column("response", mysql.LONGTEXT(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ais_llm_logs_created_at", "ais_llm_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ais_llm_logs_created_at", table_name="ais_llm_logs")
    op.drop_table("ais_llm_logs")
