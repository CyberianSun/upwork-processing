from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PGArray
from sqlalchemy.orm import relationship

from core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    # Basic job info
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    ts_publish = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)

    # Budget & duration
    fixed_budget_amount = Column(Numeric(10, 2), nullable=True)
    fixed_duration_weeks = Column(Numeric(5, 1), nullable=True)
    hourly_min = Column(Numeric(10, 2), nullable=True)
    hourly_max = Column(Numeric(10, 2), nullable=True)

    # Job age (calculated at ingest time)
    job_age_hours = Column(Integer, nullable=False, default=0)
    job_age_string = Column(String, nullable=False, default="")

    # Competition metrics
    applicant_count = Column(Integer, nullable=False, default=0)
    interviewing_count = Column(Integer, nullable=False, default=0)
    invite_only = Column(Boolean, nullable=False, default=False)

    # Client quality signals
    client_payment_verified = Column(Boolean, nullable=False, default=False)
    client_rating = Column(Numeric(3, 2), nullable=True)  # 0.00 - 5.00
    client_jobs_posted = Column(Integer, nullable=False, default=0)
    client_hire_rate = Column(Numeric(5, 2), nullable=True)  # Percentage
    client_total_paid = Column(Numeric(10, 2), nullable=True)
    client_hires = Column(Integer, nullable=False, default=0)
    client_reviews = Column(Integer, nullable=False, default=0)

    # Job specifics
    experience_level = Column(String, nullable=True)  # Entry, Intermediate, Expert
    project_length = Column(String, nullable=True)  # Less than 1 mo, 1-3 mo, etc.
    proposal_required = Column(Boolean, nullable=False, default=False)

    # Client engagement quality
    client_response_time = Column(String, nullable=True)  # e.g., "within a few hours"

    # URLs found in description
    description_urls = Column(JSONB, nullable=False, default=list)

    # Metadata
    source = Column(String, nullable=False, default="apify")
    scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    evaluation = relationship(
        "JobEvaluation", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )