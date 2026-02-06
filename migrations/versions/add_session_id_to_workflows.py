"""add session_id column to workflows

Revision ID: add_session_id_to_workflows
Revises: add_workflow_tables_20260206
Create Date: 2026-02-06 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_session_id_to_workflows'
down_revision = 'add_workflow_tables_20260206'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'workflows',
        sa.Column('session_id', sa.String(100), nullable=True)
    )
    op.create_index('idx_workflows_session_id', 'workflows', ['session_id'])


def downgrade():
    op.drop_index('idx_workflows_session_id', table_name='workflows')
    op.drop_column('workflows', 'session_id')