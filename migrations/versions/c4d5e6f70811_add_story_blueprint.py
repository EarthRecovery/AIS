"""add story_blueprint (STORY layer S1: blueprint + ending goal)

Revision ID: c4d5e6f70811
Revises: a1b2c3d4e5f6
Create Date: 2026-06-23 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f70811'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'ais_story_blueprints',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('world_id', sa.Integer(), nullable=False),
        sa.Column('premise', sa.Text(), nullable=True),
        sa.Column('central_conflict', sa.Text(), nullable=True),
        sa.Column('theme', sa.Text(), nullable=True),
        sa.Column('intended_endings', sa.JSON(), nullable=True),
        sa.Column('dramatic_phase', sa.String(length=20), nullable=False, server_default='setup'),
        sa.Column('tension_target', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('last_plan', sa.JSON(), nullable=True),
        sa.Column('ending_verdict', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('world_id', name='uq_story_blueprints_world_id'),
    )
    op.create_index('ix_ais_story_blueprints_world_id', 'ais_story_blueprints', ['world_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_ais_story_blueprints_world_id', table_name='ais_story_blueprints')
    op.drop_table('ais_story_blueprints')
