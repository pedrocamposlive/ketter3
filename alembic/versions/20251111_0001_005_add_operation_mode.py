"""Add operation mode (COPY vs MOVE) support

Revision ID: 005_operation_mode
Revises: 004_continuous_watch
Create Date: 2025-11-11 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add operation_mode column to transfers table
    # 'copy' = keep originals at source
    # 'move' = delete originals after checksum verification
    op.add_column('transfers', sa.Column('operation_mode', sa.String(10), nullable=False, server_default='copy'))


def downgrade() -> None:
    # Drop operation_mode column from transfers table
    op.drop_column('transfers', 'operation_mode')
