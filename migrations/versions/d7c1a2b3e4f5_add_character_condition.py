"""add character condition (narrative status phrase injected by Keeper)

Revision ID: d7c1a2b3e4f5
Revises: c4d5e6f70811
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7c1a2b3e4f5"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f70811"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ais_characters",
        sa.Column("condition", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ais_characters", "condition")
