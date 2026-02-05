"""add client metrics competition data and urls

Revision ID: b722c11953c4
Revises: 20250205_040924_initial
Create Date: 2026-02-05 01:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'b722c11953c4'
down_revision = '20250205_040924_initial'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('jobs') as batch_op:
        # Job age metrics
        batch_op.add_column(sa.Column('job_age_hours', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('job_age_string', sa.String(), nullable=False, server_default=''))

        # Competition metrics
        batch_op.add_column(sa.Column('applicant_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('interviewing_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('invite_only', sa.Boolean(), nullable=False, server_default='false'))

        # Client quality signals
        batch_op.add_column(sa.Column('client_payment_verified', sa.Boolean(), nullable=False, server_default='false'))
        batch_op.add_column(sa.Column('client_rating', sa.Numeric(3, 2), nullable=True))
        batch_op.add_column(sa.Column('client_jobs_posted', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('client_hire_rate', sa.Numeric(5, 2), nullable=True))
        batch_op.add_column(sa.Column('client_total_paid', sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column('client_hires', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('client_reviews', sa.Integer(), nullable=False, server_default='0'))

        # Job specifics
        batch_op.add_column(sa.Column('experience_level', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('project_length', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('proposal_required', sa.Boolean(), nullable=False, server_default='false'))

        # Client engagement
        batch_op.add_column(sa.Column('client_response_time', sa.String(), nullable=True))

        # URLs in description
        batch_op.add_column(sa.Column('description_urls', postgresql.JSONB(), nullable=False, server_default='[]'))


def downgrade():
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('description_urls')
        batch_op.drop_column('client_response_time')
        batch_op.drop_column('proposal_required')
        batch_op.drop_column('project_length')
        batch_op.drop_column('experience_level')
        batch_op.drop_column('client_reviews')
        batch_op.drop_column('client_hires')
        batch_op.drop_column('client_total_paid')
        batch_op.drop_column('client_hire_rate')
        batch_op.drop_column('client_jobs_posted')
        batch_op.drop_column('client_rating')
        batch_op.drop_column('client_payment_verified')
        batch_op.drop_column('invite_only')
        batch_op.drop_column('interviewing_count')
        batch_op.drop_column('applicant_count')
        batch_op.drop_column('job_age_string')
        batch_op.drop_column('job_age_hours')