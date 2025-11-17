"""Initial schema: transfers, checksums, audit_logs

Revision ID: 001
Revises:
Create Date: 2025-11-04 22:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Cria schema inicial do Ketter 3.0

    Tabelas:
    - transfers: Transferências de arquivos
    - checksums: Checksums SHA-256 triplos
    - audit_logs: Logs de auditoria
    """

    # Create transfers table
    op.create_table(
        'transfers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_path', sa.String(length=4096), nullable=False),
        sa.Column('destination_path', sa.String(length=4096), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_name', sa.String(length=512), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'VALIDATING', 'COPYING', 'VERIFYING',
            'COMPLETED', 'FAILED', 'CANCELLED',
            name='transferstatus'
        ), nullable=False),
        sa.Column('bytes_transferred', sa.BigInteger(), server_default='0'),
        sa.Column('progress_percent', sa.Integer(), server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for transfers
    op.create_index('idx_transfer_created_at', 'transfers', ['created_at'])
    op.create_index('idx_transfer_status_created', 'transfers', ['status', 'created_at'])
    op.create_index(op.f('ix_transfers_id'), 'transfers', ['id'], unique=False)
    op.create_index(op.f('ix_transfers_status'), 'transfers', ['status'], unique=False)

    # Create checksums table
    op.create_table(
        'checksums',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('checksum_type', sa.Enum(
            'SOURCE', 'DESTINATION', 'FINAL',
            name='checksumtype'
        ), nullable=False),
        sa.Column('checksum_value', sa.String(length=64), nullable=False),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('calculation_duration_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for checksums
    op.create_index('idx_checksum_transfer_type', 'checksums', ['transfer_id', 'checksum_type'])
    op.create_index(op.f('ix_checksums_id'), 'checksums', ['id'], unique=False)
    op.create_index(op.f('ix_checksums_transfer_id'), 'checksums', ['transfer_id'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Enum(
            'TRANSFER_CREATED', 'TRANSFER_STARTED', 'TRANSFER_PROGRESS',
            'CHECKSUM_CALCULATED', 'CHECKSUM_VERIFIED',
            'TRANSFER_COMPLETED', 'TRANSFER_FAILED', 'TRANSFER_CANCELLED',
            'ERROR',
            name='auditeventtype'
        ), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('event_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['transfer_id'], ['transfers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for audit_logs
    op.create_index('idx_audit_event_created', 'audit_logs', ['event_type', 'created_at'])
    op.create_index('idx_audit_transfer_created', 'audit_logs', ['transfer_id', 'created_at'])
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_transfer_id'), 'audit_logs', ['transfer_id'], unique=False)


def downgrade() -> None:
    """
    Remove todas as tabelas do schema inicial
    """
    # Drop indexes first
    op.drop_index(op.f('ix_audit_logs_transfer_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index('idx_audit_transfer_created', table_name='audit_logs')
    op.drop_index('idx_audit_event_created', table_name='audit_logs')

    # Drop audit_logs table
    op.drop_table('audit_logs')

    # Drop checksums indexes
    op.drop_index(op.f('ix_checksums_transfer_id'), table_name='checksums')
    op.drop_index(op.f('ix_checksums_id'), table_name='checksums')
    op.drop_index('idx_checksum_transfer_type', table_name='checksums')

    # Drop checksums table
    op.drop_table('checksums')

    # Drop transfers indexes
    op.drop_index(op.f('ix_transfers_status'), table_name='transfers')
    op.drop_index(op.f('ix_transfers_id'), table_name='transfers')
    op.drop_index('idx_transfer_status_created', table_name='transfers')
    op.drop_index('idx_transfer_created_at', table_name='transfers')

    # Drop transfers table
    op.drop_table('transfers')

    # Drop enums
    sa.Enum(name='auditeventtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='checksumtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='transferstatus').drop(op.get_bind(), checkfirst=True)
