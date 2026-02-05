from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PGArray
from sqlalchemy.orm import relationship

from core.database import Base


class JobEvaluation(Base):
    __tablename__ = "job_evaluations"

    job_id = Column(
        String, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )

    is_ai_related = Column(Integer, nullable=False)
    filter_reason = Column(Text, nullable=True)

    tech_stack = Column(JSONB, nullable=False, default=list)
    project_type = Column(String, nullable=False)
    complexity = Column(String, nullable=False)
    matched_expertise_ids = Column(PGArray(SmallInteger), nullable=False, default=list)

    score_budget = Column(SmallInteger, nullable=False)
    score_client = Column(SmallInteger, nullable=False)
    score_clarity = Column(SmallInteger, nullable=False)
    score_tech_fit = Column(SmallInteger, nullable=False)
    score_timeline = Column(SmallInteger, nullable=False)
    score_total = Column(SmallInteger, nullable=False)

    reason_budget = Column(Text, nullable=False)
    reason_client = Column(Text, nullable=False)
    reason_clarity = Column(Text, nullable=False)
    reason_tech_fit = Column(Text, nullable=False)
    reason_timeline = Column(Text, nullable=False)

    priority = Column(String, nullable=False)
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="evaluation")