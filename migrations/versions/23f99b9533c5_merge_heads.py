"""merge heads

Revision ID: 23f99b9533c5
Revises: 6a4fd1a1a2bb, f2d8a2d6f3b1
Create Date: 2026-01-07 06:40:24.187916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23f99b9533c5'
down_revision: Union[str, Sequence[str], None] = ('6a4fd1a1a2bb', 'f2d8a2d6f3b1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
