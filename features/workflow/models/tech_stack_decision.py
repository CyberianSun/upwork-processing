from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class TechStackDecision(Base):
    """Tech stack decision made during workflow.

    Tracks technology choices and their justifications.
    """
    __tablename__ = "tech_stack_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)

    # Decision details
    requirement = Column(String(500), nullable=False)  # What requirement are we solving?
    our_choice = Column(String(200), nullable=True)  # What did we choose?
    reason = Column(Text, nullable=True)  # Why did we choose this?

    # Confirmation status
    user_confirmed = Column(Boolean, nullable=False, default=True)

    # Category for organization: language, framework, database, deployment, etc.
    category = Column(String(50), nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="tech_decisions")

    def __repr__(self):
        return f"<TechStackDecision(id={self.id}, requirement='{self.requirement}', our_choice='{self.our_choice}')>"