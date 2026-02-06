"""add workflow tables for autonomous development

Revision ID: add_workflow_tables_20260206
Revises: b722c11953c4
Create Date: 2026-02-06 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_workflow_tables_20260206'
down_revision = 'b722c11953c4'
branch_labels = None
depends_on = None


def upgrade():
    # Main workflow table
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('beads_path', sa.String(500), nullable=True),
        sa.Column('prd_path', sa.String(500), nullable=True),
        sa.Column('github_repo_url', sa.String(500), nullable=True),
        sa.Column('prp_content', sa.Text(), nullable=True),
        sa.Column('plan_content', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], name='fk_workflow_job_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', name='uq_workflow_job_id')
    )
    op.create_index('idx_workflows_status', 'workflows', ['status'])
    op.create_index('idx_workflows_job_id', 'workflows', ['job_id'])

    # Workflow steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('step_name', sa.String(100), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('agent_used', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE', name='fk_step_workflow_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'step_number', name='uq_step_workflow_number')
    )
    op.create_index('idx_workflow_steps_workflow_id', 'workflow_steps', ['workflow_id'])
    op.create_index('idx_workflow_steps_step_number', 'workflow_steps', ['step_number'])

    # Tech stack decisions table
    op.create_table(
        'tech_stack_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('requirement', sa.String(500), nullable=False),
        sa.Column('our_choice', sa.String(200), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('user_confirmed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('category', sa.String(50), nullable=True),  # language, framework, database, etc.
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE', name='fk_decision_workflow_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tech_decisions_workflow_id', 'tech_stack_decisions', ['workflow_id'])
    op.create_index('idx_tech_decisions_category', 'tech_stack_decisions', ['category'])


def downgrade():
    # Drop in reverse order due to foreign keys
    op.drop_index('idx_tech_decisions_category', table_name='tech_stack_decisions')
    op.drop_index('idx_tech_decisions_workflow_id', table_name='tech_stack_decisions')
    op.drop_table('tech_stack_decisions')

    op.drop_index('idx_workflow_steps_step_number', table_name='workflow_steps')
    op.drop_index('idx_workflow_steps_workflow_id', table_name='workflow_steps')
    op.drop_table('workflow_steps')

    op.drop_index('idx_workflows_job_id', table_name='workflows')
    op.drop_index('idx_workflows_status', table_name='workflows')
    op.drop_table('workflows')