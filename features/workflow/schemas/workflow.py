from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WorkflowBase(BaseModel):
    """Base schema for Workflow."""
    job_id: str = Field(..., min_length=1, description="Job identifier")


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""
    pass


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    status: Optional[str] = None
    beads_path: Optional[str] = None
    prd_path: Optional[str] = None
    github_repo_url: Optional[str] = None
    prp_content: Optional[str] = None
    plan_content: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response."""
    id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    beads_path: Optional[str]
    prd_path: Optional[str]
    github_repo_url: Optional[str]
    prp_content: Optional[str]
    plan_content: Optional[str]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class WorkflowStepBase(BaseModel):
    """Base schema for WorkflowStep."""
    step_name: str = Field(..., min_length=1)
    step_number: int = Field(..., ge=0, le=7)  # SEEDFW steps 0-7


class WorkflowStepCreate(WorkflowStepBase):
    """Schema for creating a workflow step."""
    workflow_id: int


class WorkflowStepResponse(WorkflowStepBase):
    """Schema for workflow step response."""
    id: int
    workflow_id: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    output: Optional[str]
    error_message: Optional[str]
    agent_used: Optional[str]

    class Config:
        from_attributes = True


class TechStackDecisionBase(BaseModel):
    """Base schema for TechStackDecision."""
    requirement: str = Field(..., min_length=1, max_length=500)
    our_choice: Optional[str] = Field(None, max_length=200)
    reason: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)


class TechStackDecisionCreate(TechStackDecisionBase):
    """Schema for creating a tech stack decision."""
    workflow_id: int
    user_confirmed: bool = True


class TechStackDecisionResponse(TechStackDecisionBase):
    """Schema for tech stack decision response."""
    id: int
    workflow_id: int
    user_confirmed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowWithDetailsResponse(WorkflowResponse):
    """Workflow response including steps and decisions."""
    steps: List[WorkflowStepResponse] = []
    tech_decisions: List[TechStackDecisionResponse] = []