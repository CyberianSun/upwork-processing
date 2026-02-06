from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.orm import relationship

from core.database import Base


class Workflow(Base):
    """Workflow model for autonomous development process.

    Tracks the complete workflow from job evaluation to code implementation.
    """
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, unique=True)

    # Workflow status: pending, intent_translation, prp_created, planning,
    # coding_started, coding_completed, completed, failed
    status = Column(String(50), nullable=False, default="pending")

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Paths to artifacts
    beads_path = Column(String(500), nullable=True)  # Path to Beads workspace
    prd_path = Column(String(500), nullable=True)   # Path to PRD document
    github_repo_url = Column(String(500), nullable=True)  # GitHub repo URL

    # Generated content
    prp_content = Column(Text, nullable=True)  # Product Requirement Prompt
    plan_content = Column(Text, nullable=True)  # Implementation plan
    error_message = Column(Text, nullable=True)  # Error if failed
    session_id = Column(String(100), nullable=True)

    # Relationships
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_number"
    )
    tech_decisions = relationship(
        "TechStackDecision",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Workflow(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"