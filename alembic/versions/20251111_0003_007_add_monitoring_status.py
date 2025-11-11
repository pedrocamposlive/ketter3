"""Add MONITORING status to TransferStatus enum

Revision ID: 007_add_monitoring_status
Revises: 006_week6_continuous_watch
Create Date: 2025-11-11 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add MONITORING to the enum type
    # First, we need to alter the existing enum
    op.execute("ALTER TYPE transferstatus ADD VALUE 'monitoring'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily
    # So we'll just leave it (it won't hurt)
    pass
