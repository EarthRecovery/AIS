"""world style_guide (per-sandbox reference writing style)

Revision ID: a1b2c3d4e5f6
Revises: 4e1c4e8e9a45
Create Date: 2026-06-23 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4e1c4e8e9a45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('ais_worlds', sa.Column('style_guide', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('ais_worlds', 'style_guide')
