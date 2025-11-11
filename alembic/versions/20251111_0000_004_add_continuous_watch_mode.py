"""Add continuous watch mode support

Revision ID: 004_continuous_watch
Revises: 20251105_1430_003
Create Date: 2025-11-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to transfers table for continuous watch mode
    op.add_column('transfers', sa.Column('watch_continuous', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('transfers', sa.Column('watch_job_id', sa.String(100), nullable=True))
    op.add_column('transfers', sa.Column('last_files_processed', sa.Text(), nullable=True))
    op.add_column('transfers', sa.Column('watch_cycle_count', sa.Integer(), nullable=False, server_default='0'))

    # Create watch_files table
    op.create_table(
        'watch_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(512), nullable=False),
        sa.Column('file_path', sa.String(4096), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('transfer_job_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('source_checksum', sa.String(64), nullable=True),
        sa.Column('destination_checksum', sa.String(64), nullable=True),
        sa.Column('checksum_match', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('transfer_started_at', sa.DateTime(), nullable=True),
        sa.Column('transfer_completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for watch_files
    op.create_index('idx_watch_file_transfer_detected', 'watch_files', ['transfer_id', 'detected_at'])
    op.create_index('idx_watch_file_status_transfer', 'watch_files', ['status', 'transfer_id'])
    op.create_index('ix_watch_files_transfer_id', 'watch_files', ['transfer_id'])
    op.create_index('ix_watch_files_status', 'watch_files', ['status'])
    op.create_index('ix_watch_files_detected_at', 'watch_files', ['detected_at'])


def downgrade() -> None:
    # Drop watch_files table and indexes
    op.drop_index('ix_watch_files_detected_at', table_name='watch_files')
    op.drop_index('ix_watch_files_status', table_name='watch_files')
    op.drop_index('ix_watch_files_transfer_id', table_name='watch_files')
    op.drop_index('idx_watch_file_status_transfer', table_name='watch_files')
    op.drop_index('idx_watch_file_transfer_detected', table_name='watch_files')
    op.drop_table('watch_files')

    # Drop new columns from transfers table
    op.drop_column('transfers', 'watch_cycle_count')
    op.drop_column('transfers', 'last_files_processed')
    op.drop_column('transfers', 'watch_job_id')
    op.drop_column('transfers', 'watch_continuous')
