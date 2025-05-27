"""create user agent purchases table

Revision ID: create_user_agent_purchases
Revises: add_image_data_columns
Create Date: 2024-03-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get schema from environment
DB_SCHEMA = os.getenv('DB_SCHEMA', 'aiaplatform')

# revision identifiers, used by Alembic.
revision = 'create_user_agent_purchases'
down_revision = 'add_image_data_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Create user_agent_purchases table
    op.create_table(
        'user_agent_purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purchase_modality', sa.String(50), nullable=False),
        sa.Column('purchase_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ownership_status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        schema=DB_SCHEMA
    )

    # Create indexes
    op.create_index(
        'idx_user_agent_purchases_user_id',
        'user_agent_purchases',
        ['user_id'],
        schema=DB_SCHEMA
    )
    op.create_index(
        'idx_user_agent_purchases_agent_id',
        'user_agent_purchases',
        ['agent_id'],
        schema=DB_SCHEMA
    )
    op.create_index(
        'idx_user_agent_purchases_ownership_status',
        'user_agent_purchases',
        ['ownership_status'],
        schema=DB_SCHEMA
    )

def downgrade():
    op.drop_table('user_agent_purchases', schema=DB_SCHEMA) 