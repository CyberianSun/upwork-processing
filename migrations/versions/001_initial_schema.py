
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("ts_publish", sa.DateTime(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), unique=True, nullable=False),
        sa.Column("fixed_budget_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("fixed_duration_weeks", sa.Numeric(5, 1), nullable=True),
        sa.Column("hourly_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("hourly_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="apify"),
        sa.Column("scraped_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "job_evaluations",
        sa.Column(
            "job_id",
            sa.String(),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("is_ai_related", sa.Integer(), nullable=False),
        sa.Column("filter_reason", sa.Text(), nullable=True),
        sa.Column(
            "tech_stack", postgresql.JSONB(), nullable=False, server_default="[]"
        ),
        sa.Column("project_type", sa.String(), nullable=False),
        sa.Column("complexity", sa.String(), nullable=False),
        sa.Column(
            "matched_expertise_ids",
            postgresql.ARRAY(sa.SmallInteger()),
            nullable=False,
            server_default=text("'{}'"),
        ),
        sa.Column("score_budget", sa.SmallInteger(), nullable=False),
        sa.Column("score_client", sa.SmallInteger(), nullable=False),
        sa.Column("score_clarity", sa.SmallInteger(), nullable=False),
        sa.Column("score_tech_fit", sa.SmallInteger(), nullable=False),
        sa.Column("score_timeline", sa.SmallInteger(), nullable=False),
        sa.Column("score_total", sa.SmallInteger(), nullable=False),
        sa.Column("reason_budget", sa.Text(), nullable=False),
        sa.Column("reason_client", sa.Text(), nullable=False),
        sa.Column("reason_clarity", sa.Text(), nullable=False),
        sa.Column("reason_tech_fit", sa.Text(), nullable=False),
        sa.Column("reason_timeline", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "expertise_areas",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column(
            "keywords", postgresql.ARRAY(sa.String()), nullable=False, server_default=text("'{}'")
        ),
    )

    op.execute(
        """
        INSERT INTO expertise_areas (id, name, level, keywords) VALUES
        (1, 'AI Agent Architecture & Design', 'Expert', ARRAY['agent', 'autonomous', 'multi-agent', 'LangChain', 'crewAI']),
        (2, 'RAG Systems', 'Advanced', ARRAY['RAG', 'retrieval', 'vector database', 'embeddings', 'semantic search']),
        (3, 'Local AI Infrastructure', 'Expert', ARRAY['local LLM', 'ollama', 'LM Studio', 'self-hosted', 'on-premises', 'privacy']),
        (4, 'Backend Systems', 'Expert', ARRAY['FastAPI', 'Python', 'PostgreSQL', 'pgvector', 'REST API', 'async']),
        (5, 'Frontend Development', 'Advanced', ARRAY['React', 'TypeScript', 'Next.js', 'UI', 'web app']),
        (6, 'DevOps & Infrastructure', 'Expert', ARRAY['Docker', 'deployment', 'CI/CD']),
        (7, 'Voice & Real-Time AI', 'Advanced', ARRAY['voice', 'audio', 'Speech-to-Text', 'text-to-speech', 'WebRTC', 'Deepgram']),
        (8, 'Testing & Code Quality', 'Intermediate-Advanced', ARRAY['testing', 'pytest', 'TDD', 'code quality', 'CI'])
    """
    )

    op.create_index(
        "idx_job_evaluations_score_total", "job_evaluations", ["score_total"]
    )
    op.create_index("idx_job_evaluations_priority", "job_evaluations", ["priority"])


def downgrade():
    op.drop_index("idx_job_evaluations_priority", table_name="job_evaluations")
    op.drop_index("idx_job_evaluations_score_total", table_name="job_evaluations")
    op.drop_table("expertise_areas")
    op.drop_table("job_evaluations")
    op.drop_table("jobs")