"""add role table

Revision ID: f2d8a2d6f3b1
Revises: e57127c33335
Create Date: 2025-02-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2d8a2d6f3b1"
down_revision: Union[str, Sequence[str], None] = "e57127c33335"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ais_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("settings", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ais_roles")
