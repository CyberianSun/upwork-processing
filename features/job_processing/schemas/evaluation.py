from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ExpertiseMatch(BaseModel):
    expertise_id: int = Field(..., ge=1, le=8)
    match_reason: str = Field(...)


class ScoreBreakdown(BaseModel):
    score: int = Field(..., ge=0, le=10)
    reasoning: str = Field(...)


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


class JobEvaluationResponse(BaseModel):
    is_ai_related: bool = Field(...)
    filter_reason: Optional[str] = Field(None)

    tech_stack: List[str] = Field(default_factory=list)
    project_type: str = Field(...)
    complexity: str = Field(...)
    matched_expertise: List[ExpertiseMatch] = Field(default_factory=list)

    scores: Dict[str, ScoreBreakdown] = Field(...)

    score_total: int = Field(..., ge=0, le=100)
    priority: str = Field(...)


class JobEvaluationListResponse(BaseModel):
    job_id: str
    title: str
    url: str
    budget: Optional[float]
    duration_weeks: Optional[float]
    score_total: int
    priority: str
    project_type: str
    tech_stack: List[str]
    matched_expertise_ids: List[int]
    reasoning_summary: str