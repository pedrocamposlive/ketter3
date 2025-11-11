"""Week 6: Add continuous watch mode fields and parent_transfer_id

Revision ID: 006_week6_continuous_watch
Revises: 005_operation_mode
Create Date: 2025-11-11 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to transfers table for Week 6 continuous watch mode
    op.add_column('transfers', sa.Column('is_continuous_watch', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('transfers', sa.Column('watched_files_processed', sa.JSON(), nullable=True))
    op.add_column('transfers', sa.Column('last_watch_check_at', sa.DateTime(), nullable=True))
    op.add_column('transfers', sa.Column('continuous_files_transferred', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('transfers', sa.Column('parent_transfer_id', sa.Integer(), nullable=True))

    # Add foreign key constraint for parent_transfer_id
    op.create_foreign_key(
        'fk_transfers_parent_transfer_id',
        'transfers',
        'transfers',
        ['parent_transfer_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for querying child transfers
    op.create_index('idx_transfers_parent_transfer_id', 'transfers', ['parent_transfer_id'])


def downgrade() -> None:
    # Drop index and foreign key
    op.drop_index('idx_transfers_parent_transfer_id', table_name='transfers')
    op.drop_constraint('fk_transfers_parent_transfer_id', 'transfers', type_='foreignkey')

    # Drop new columns
    op.drop_column('transfers', 'parent_transfer_id')
    op.drop_column('transfers', 'continuous_files_transferred')
    op.drop_column('transfers', 'last_watch_check_at')
    op.drop_column('transfers', 'watched_files_processed')
    op.drop_column('transfers', 'is_continuous_watch')
