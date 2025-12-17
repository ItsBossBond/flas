"""initial schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-12-02 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Users Table
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('balance', sa.Float(), default=0.0),
        sa.Column('google_id', sa.String(length=255), nullable=True, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        # Referral columns
        sa.Column('referral_code', sa.String(length=10), nullable=True, unique=True),
        sa.Column('referrer_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('referral_balance', sa.Float(), default=0.0)
    )

    # 2. Products Table (replaces flash_offers)
    op.create_table('products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(length=20), nullable=True),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('daily_limit_text', sa.String(length=100), nullable=True),
        sa.Column('validity_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True)
    )

    # 3. Wallets Table
    op.create_table('wallets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('symbol', sa.String(length=10), nullable=True),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('qr_image', sa.String(length=100), nullable=True),
        sa.Column('folder', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True)
    )

    # 4. Purchases Table
    op.create_table('purchases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('item_name', sa.String(length=200), nullable=True),
        sa.Column('amount_paid', sa.Float(), nullable=True),
        sa.Column('coin', sa.String(length=20), nullable=True),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), default='Pending'),
        sa.Column('access_code', sa.String(length=100), nullable=True),
        sa.Column('receiving_address', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

    # 5. Deposits Table
    op.create_table('deposits',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('tx_id', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), default='pending'),
        sa.Column('tx_network', sa.String(length=20), nullable=True),
        sa.Column('to_address', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('confirmations', sa.Integer(), default=0),
        sa.Column('required_confs', sa.Integer(), default=1),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True)
    )

    # 6. Deposit Addresses Table
    op.create_table('deposit_addresses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('network', sa.String(length=20), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=False, unique=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )

def downgrade():
    op.drop_table('deposit_addresses')
    op.drop_table('deposits')
    op.drop_table('purchases')
    op.drop_table('wallets')
    op.drop_table('products')
    op.drop_table('users')