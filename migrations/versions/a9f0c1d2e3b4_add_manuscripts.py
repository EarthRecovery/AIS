"""add ais_manuscripts (writing-layer chapter prose)

Revision ID: a9f0c1d2e3b4
Revises: e8b2c3d4f561
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a9f0c1d2e3b4"
down_revision: Union[str, Sequence[str], None] = "e8b2c3d4f561"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ais_manuscripts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("world_id", sa.Integer(), nullable=False, index=True),
        sa.Column("chapter_label", sa.String(length=60), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("world_id", "chapter_label", name="uq_manuscript_world_chapter"),
    )


def downgrade() -> None:
    op.drop_table("ais_manuscripts")
