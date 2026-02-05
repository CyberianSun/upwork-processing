from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    ts_publish = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)

    fixed_budget_amount = Column(Numeric(10, 2), nullable=True)
    fixed_duration_weeks = Column(Numeric(5, 1), nullable=True)

    hourly_min = Column(Numeric(10, 2), nullable=True)
    hourly_max = Column(Numeric(10, 2), nullable=True)

    source = Column(String, nullable=False, default="apify")
    scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    evaluation = relationship(
        "JobEvaluation", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )