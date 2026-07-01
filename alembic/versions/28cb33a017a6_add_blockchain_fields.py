"""add_blockchain_fields

Revision ID: 28cb33a017a6
Revises: 188fc65a4c02
Create Date: 2026-07-01 17:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28cb33a017a6'
down_revision: Union[str, None] = '188fc65a4c02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. credit_batches
    op.add_column('credit_batches', sa.Column('blockchain_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    op.add_column('credit_batches', sa.Column('blockchain_tx_hash', sa.String(length=255), nullable=True))
    op.add_column('credit_batches', sa.Column('block_number', sa.Integer(), nullable=True))
    op.add_column('credit_batches', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('credit_batches', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('credit_batches', sa.Column('blockchain_error', sa.Text(), nullable=True))

    # 2. transactions
    op.add_column('transactions', sa.Column('blockchain_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    op.add_column('transactions', sa.Column('block_number', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('transactions', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('transactions', sa.Column('blockchain_error', sa.Text(), nullable=True))

    # 3. retirements
    op.add_column('retirements', sa.Column('blockchain_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    op.add_column('retirements', sa.Column('block_number', sa.Integer(), nullable=True))
    op.add_column('retirements', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('retirements', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('retirements', sa.Column('blockchain_error', sa.Text(), nullable=True))

    # 4. audit_logs
    op.add_column('audit_logs', sa.Column('blockchain_status', sa.String(length=50), nullable=False, server_default='PENDING'))
    op.add_column('audit_logs', sa.Column('blockchain_tx_hash', sa.String(length=255), nullable=True))
    op.add_column('audit_logs', sa.Column('block_number', sa.Integer(), nullable=True))
    op.add_column('audit_logs', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('audit_logs', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('audit_logs', sa.Column('blockchain_error', sa.Text(), nullable=True))


def downgrade() -> None:
    # 4. audit_logs
    op.drop_column('audit_logs', 'blockchain_error')
    op.drop_column('audit_logs', 'retry_count')
    op.drop_column('audit_logs', 'confirmed_at')
    op.drop_column('audit_logs', 'block_number')
    op.drop_column('audit_logs', 'blockchain_tx_hash')
    op.drop_column('audit_logs', 'blockchain_status')

    # 3. retirements
    op.drop_column('retirements', 'blockchain_error')
    op.drop_column('retirements', 'retry_count')
    op.drop_column('retirements', 'confirmed_at')
    op.drop_column('retirements', 'block_number')
    op.drop_column('retirements', 'blockchain_status')

    # 2. transactions
    op.drop_column('transactions', 'blockchain_error')
    op.drop_column('transactions', 'retry_count')
    op.drop_column('transactions', 'confirmed_at')
    op.drop_column('transactions', 'block_number')
    op.drop_column('transactions', 'blockchain_status')

    # 1. credit_batches
    op.drop_column('credit_batches', 'blockchain_error')
    op.drop_column('credit_batches', 'retry_count')
    op.drop_column('credit_batches', 'confirmed_at')
    op.drop_column('credit_batches', 'block_number')
    op.drop_column('credit_batches', 'blockchain_tx_hash')
    op.drop_column('credit_batches', 'blockchain_status')
