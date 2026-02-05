from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional, Dict, Any


class ExpertiseMatch(BaseModel):
    expertise_id: int = Field(..., ge=1, le=8)
    match_reason: str = Field(...)


class JobEvaluationRequest(BaseModel):
    job_id: str
    title: str
    description: str
    type: str
    url: str
    fixed_budget_amount: Optional[float] = None
    fixed_duration_weeks: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None

    # Competition metrics
    applicant_count: int = 0
    interviewing_count: int = 0
    invite_only: bool = False

    # Client quality signals
    client_payment_verified: bool = False
    client_rating: Optional[float] = None
    client_jobs_posted: int = 0
    client_hire_rate: Optional[float] = None
    client_total_paid: Optional[float] = None
    client_hires: int = 0
    client_reviews: int = 0

    # Job specifics
    experience_level: Optional[str] = None
    project_length: Optional[str] = None

    # Job age
    job_age_hours: int = 0
    job_age_string: str = ""

    # URLs in description
    description_urls: List[str] = Field(default_factory=list)


class JobEvaluationResponse(BaseModel):
    is_ai_related: bool = Field(...)
    filter_reason: Optional[str] = None

    tech_stack: str | List[str] = ""
    project_type: Optional[str] = None
    complexity: Optional[str] = None
    matched_expertise: List[ExpertiseMatch] = Field(default_factory=list)

    score_budget: Optional[int] = None
    reason_budget: Optional[str] = None

    score_client: Optional[int] = None
    reason_client: Optional[str] = None

    score_clarity: Optional[int] = None
    reason_clarity: Optional[str] = None

    score_tech_fit: Optional[int] = None
    reason_tech_fit: Optional[str] = None

    score_timeline: Optional[int] = None
    reason_timeline: Optional[str] = None

    score_total: Optional[float] = None
    priority: Optional[str] = None

    @computed_field
    @property
    def computed_score_total(self) -> float:
        if self.score_total is not None:
            return self.score_total
        if all(x is not None for x in [self.score_budget, self.score_client, self.score_clarity, self.score_tech_fit, self.score_timeline]):
            return (self.score_budget * 0.25 + self.score_client * 0.15 +
                    self.score_clarity * 0.20 + self.score_tech_fit * 0.30 + self.score_timeline * 0.10) * 100 / 10
        return 0.0


class JobEvaluationListResponse(BaseModel):
    job_id: str
    title: str
    description: str
    url: str
    budget: Optional[float]
    duration_weeks: Optional[float]
    score_total: int
    priority: str
    project_type: str
    tech_stack: List[str]
    matched_expertise_ids: List[int]
    reasoning_summary: str

    # Competition metrics
    applicant_count: int = 0
    interviewing_count: int = 0
    invite_only: bool = False

    # Client quality signals
    client_payment_verified: bool = False
    client_rating: Optional[float] = None
    client_jobs_posted: int = 0
    client_hire_rate: Optional[float] = None
    client_total_paid: Optional[float] = None
    client_hires: int = 0
    client_reviews: int = 0

    # Job specifics
    experience_level: Optional[str] = None
    project_length: Optional[str] = None
    client_response_time: Optional[str] = None

    # Job age
    job_age_hours: int = 0
    job_age_string: str = ""

    # URLs in description
    description_urls: List[str] = Field(default_factory=list)