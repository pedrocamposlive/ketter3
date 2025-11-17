"""add folder support for ZIP Smart

Revision ID: 002_add_folder_support
Revises: 20251104_2210_001_initial_schema
Create Date: 2025-11-05 14:15:00

Week 5: ZIP Smart + Watch Folder Intelligence
Adds support for folder transfers with ZIP Smart Engine

Changes:
- is_folder_transfer: Track if transfer is folder (not single file)
- original_folder_path: Store original folder path
- zip_file_path: Store temp ZIP file path
- file_count: Number of files in folder
- unzip_completed: Track if unzip completed at destination
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add folder support columns to transfers table
    """
    # Add new columns for ZIP Smart functionality
    op.add_column('transfers', sa.Column('is_folder_transfer', sa.Integer(), server_default='0', nullable=False))
    op.add_column('transfers', sa.Column('original_folder_path', sa.String(length=4096), nullable=True))
    op.add_column('transfers', sa.Column('zip_file_path', sa.String(length=4096), nullable=True))
    op.add_column('transfers', sa.Column('file_count', sa.Integer(), nullable=True))
    op.add_column('transfers', sa.Column('unzip_completed', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    """
    Remove folder support columns from transfers table
    """
    op.drop_column('transfers', 'unzip_completed')
    op.drop_column('transfers', 'file_count')
    op.drop_column('transfers', 'zip_file_path')
    op.drop_column('transfers', 'original_folder_path')
    op.drop_column('transfers', 'is_folder_transfer')
