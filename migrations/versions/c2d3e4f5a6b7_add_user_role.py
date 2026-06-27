"""add user role (user/admin); seed yuxiang-lin as admin

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ais_users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )
    # 既有管理员账号置为 admin
    op.execute("UPDATE ais_users SET role='admin' WHERE email='yuxiang-lin@outlook.com'")


def downgrade() -> None:
    op.drop_column("ais_users", "role")
