from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class WorkflowStep(Base):
    """Individual workflow step representation.

    Tracks each step of the SEEDFW workflow (0-7) with status and output.
    """
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)

    # Step identification
    step_name = Column(String(100), nullable=False)  # e.g., "intent_translation", "prp_creation"
    step_number = Column(Integer, nullable=False)  # 0-7 for SEEDFW steps

    # Step status: pending, in_progress, completed, failed, skipped
    status = Column(String(50), nullable=False, default="pending")

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Output and errors
    output = Column(Text, nullable=True)  # Generated output from this step
    error_message = Column(Text, nullable=True)  # Error if failed

    # Agent that executed this step
    agent_used = Column(String(50), nullable=True)  # e.g., "metis", "sisyphus-junior"

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")

    # Unique constraint on workflow + step_number
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<WorkflowStep(id={self.id}, workflow_id={self.workflow_id}, step_name='{self.step_name}', status='{self.status}')>"