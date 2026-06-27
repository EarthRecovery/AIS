"""add scene_message kind (say/do/think channels)

Revision ID: e8b2c3d4f561
Revises: d7c1a2b3e4f5
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8b2c3d4f561"
down_revision: Union[str, Sequence[str], None] = "d7c1a2b3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ais_scene_messages",
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="say"),
    )


def downgrade() -> None:
    op.drop_column("ais_scene_messages", "kind")
