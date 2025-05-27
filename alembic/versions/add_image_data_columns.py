"""add image data columns

Revision ID: add_image_data_columns
Revises: migrate_agents_data
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
revision = 'add_image_data_columns'
down_revision = 'migrate_agents_data'
branch_labels = None
depends_on = None

def upgrade():
    # Add image_data column to agents table
    op.add_column('agents', sa.Column('image_data', postgresql.BYTEA, nullable=True), schema=DB_SCHEMA)

def downgrade():
    # Remove the image_data column
    op.drop_column('agents', 'image_data', schema=DB_SCHEMA) 