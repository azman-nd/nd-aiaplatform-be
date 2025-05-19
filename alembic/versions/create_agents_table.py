"""create agents table

Revision ID: create_agents_table
Revises: 
Create Date: 2024-03-14 12:00:00.000000

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
revision = 'create_agents_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create agents table with status and pricing_model enums
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('image_url', sa.String, nullable=True),
        sa.Column('features', sa.Text, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('pricing_model', sa.String(20), nullable=False),
        sa.Column('price', sa.Float, nullable=True),
        sa.Column('display_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('language_support', postgresql.JSON, nullable=False, server_default='["en"]'),
        sa.Column('tags', postgresql.JSON, nullable=False, server_default='[]'),
        sa.Column('demo_url', sa.String, nullable=True),
        sa.Column('prod_url', sa.String, nullable=True),
        schema=DB_SCHEMA
    )

def downgrade():
    op.drop_table('agents', schema=DB_SCHEMA) 