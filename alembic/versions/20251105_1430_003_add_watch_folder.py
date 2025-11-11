"""add watch folder intelligence

Revision ID: 003_add_watch_folder
Revises: 002_add_folder_support
Create Date: 2025-11-05 14:30:00

Week 5: Watch Folder Intelligence
Adds support for monitoring folders until stable (settle time detection)

Changes:
- watch_mode_enabled: Track if watch mode is enabled
- settle_time_seconds: Configurable settle time (default 30s)
- watch_started_at: When watch monitoring began
- watch_triggered_at: When folder became stable and transfer started
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add watch folder columns to transfers table
    """
    # Add new columns for Watch Folder functionality
    op.add_column('transfers', sa.Column('watch_mode_enabled', sa.Integer(), server_default='0', nullable=False))
    op.add_column('transfers', sa.Column('settle_time_seconds', sa.Integer(), server_default='30', nullable=False))
    op.add_column('transfers', sa.Column('watch_started_at', sa.DateTime(), nullable=True))
    op.add_column('transfers', sa.Column('watch_triggered_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """
    Remove watch folder columns from transfers table
    """
    op.drop_column('transfers', 'watch_triggered_at')
    op.drop_column('transfers', 'watch_started_at')
    op.drop_column('transfers', 'settle_time_seconds')
    op.drop_column('transfers', 'watch_mode_enabled')
