"""migrate agents data from json to database

Revision ID: migrate_agents_data
Revises: create_agents_table
Create Date: 2024-03-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json
import os
from datetime import datetime
from uuid import UUID

# revision identifiers, used by Alembic.
revision = 'migrate_agents_data'
down_revision = 'create_agents_table'
branch_labels = None
depends_on = None

def upgrade():
    # Get connection and transaction
    connection = op.get_bind()
    
    # Load agents from JSON file
    json_file = os.path.join(os.path.dirname(__file__), 'agents.json')
    with open(json_file, 'r') as f:
        agents_data = json.load(f)

    # Insert each agent into the database
    for agent in agents_data:
        # Convert string dates to datetime objects if they exist
        created_at = datetime.fromisoformat(agent.get('created_at', datetime.utcnow().isoformat()))
        updated_at = datetime.fromisoformat(agent.get('updated_at', datetime.utcnow().isoformat()))
        
        # Get features as HTML string directly from the JSON
        features = ""
        if agent.get('capabilities') and len(agent['capabilities']) > 0:
            capability = agent['capabilities'][0]
            if capability.get('parameters', {}).get('features'):
                features = capability['parameters']['features']
        id_alias = agent['capabilities'][0]['name']

        # Convert other dict/list values to JSON strings
        agent['language_support'] = json.dumps(agent['language_support'])
        agent['tags'] = json.dumps(agent['tags'])
            
        # Insert the agent
        connection.execute(
            sa.text("""
                INSERT INTO agents (
                    id, name, title, description, version, image_url, features,
                    status, pricing_model, price, display_order, created_at, updated_at,
                    provider, language_support, tags, demo_url, prod_url
                ) VALUES (
                    :id, :name, :title, :description, :version, :image_url, :features,
                    :status, :pricing_model, :price, :display_order, :created_at, :updated_at,
                    :provider, :language_support, :tags, :demo_url, :prod_url
                )
            """),
            {
                'id': agent['id'],
                'name': id_alias,
                'title': agent['name'],
                'description': agent['description'],
                'version': agent['version'],
                'image_url': agent.get('image_url'),
                'features': features,
                'status': agent.get('status', 'active'),
                'pricing_model': agent['pricing_model'],
                'price': agent.get('price'),
                'display_order': agent.get('display_order', 0),
                'created_at': created_at,
                'updated_at': updated_at,
                'provider': agent['provider'],
                'language_support': agent['language_support'],
                'tags': agent['tags'],
                'demo_url': agent.get('demo_url'),
                'prod_url': agent.get('prod_url')
            }
        )

def downgrade():
    # Get connection
    connection = op.get_bind()
    
    # Delete all agents from the database
    connection.execute(sa.text("DELETE FROM agents")) 