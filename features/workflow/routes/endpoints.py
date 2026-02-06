from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

from core.database import get_db
from features.workflow.models.workflow import Workflow
from features.workflow.models.workflow_step import WorkflowStep
from features.workflow.models.tech_stack_decision import TechStackDecision
from features.workflow.services.beads_manager import BeadsManager
from features.workflow.services.orchestrator import WorkflowOrchestrator
from features.workflow.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowWithDetailsResponse,
    WorkflowStepCreate,
    WorkflowStepResponse,
    TechStackDecisionCreate,
    TechStackDecisionResponse
)

router = APIRouter(prefix="/workflows", tags=["workflows"])
beads_manager = BeadsManager(base_projects_path="projects")
orchestrator = WorkflowOrchestrator(base_projects_path="projects")


class ConfirmationRequest(BaseModel):
    confirmed: bool


class OrchestratedWorkflowStart(BaseModel):
    auto_approve_intent: bool = False
    auto_approve_plan: bool = False


@router.post("/jobs/{job_id}/start", response_model=WorkflowResponse)
async def start_workflow(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """Start a new workflow for a job.

    Initializes Beads workspace and creates workflow record.
    """
    # Check if workflow already exists
    existing = await db.execute(
        select(Workflow).where(Workflow.job_id == job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Workflow already exists for job {job_id}")

    # Initialize Beads workspace
    init_result = await beads_manager.initialize(job_id)
    if not init_result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize Beads workspace: {init_result.get('error')}"
        )

    # Create workflow record
    workflow = Workflow(
        job_id=job_id,
        status="pending",
        beads_path=init_result.get("workspace_path")
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.get("/{workflow_id}", response_model=WorkflowWithDetailsResponse)
async def get_workflow(
    workflow_id: int,
    include_details: bool = True,
    db: AsyncSession = Depends(get_db)
) -> WorkflowWithDetailsResponse:
    """Get workflow by ID with optional details."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    steps = []
    tech_decisions = []

    if include_details:
        # Get workflow steps
        steps_result = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
        )
        steps = steps_result.scalars().all()

        # Get tech stack decisions
        decisions_result = await db.execute(
            select(TechStackDecision).where(TechStackDecision.workflow_id == workflow_id)
        )
        tech_decisions = decisions_result.scalars().all()

    return WorkflowWithDetailsResponse(
        **workflow.__dict__,
        steps=steps,
        tech_decisions=tech_decisions
    )


@router.get("/jobs/{job_id}", response_model=WorkflowWithDetailsResponse)
async def get_workflow_by_job_id(
    job_id: str,
    include_details: bool = True,
    db: AsyncSession = Depends(get_db)
) -> WorkflowWithDetailsResponse:
    """Get workflow by job ID."""
    result = await db.execute(
        select(Workflow).where(Workflow.job_id == job_id)
    )
    workflow = result.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    steps = []
    tech_decisions = []

    if include_details:
        # Get workflow steps
        steps_result = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == workflow.id)
        )
        steps = steps_result.scalars().all()

        # Get tech stack decisions
        decisions_result = await db.execute(
            select(TechStackDecision).where(TechStackDecision.workflow_id == workflow.id)
        )
        tech_decisions = decisions_result.scalars().all()

    return WorkflowWithDetailsResponse(
        **workflow.__dict__,
        steps=steps,
        tech_decisions=tech_decisions
    )


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> List[WorkflowResponse]:
    """List workflows with optional status filtering."""
    query = select(Workflow).order_by(Workflow.created_at.desc())

    if status:
        query = query.where(Workflow.status == status)

    query = query.limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    update_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """Update workflow status and metadata."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Update only provided fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(workflow, field, value)

    await db.commit()
    await db.refresh(workflow)

    return workflow


@router.post("/{workflow_id}/steps", response_model=WorkflowStepResponse)
async def create_workflow_step(
    workflow_id: int,
    step_data: WorkflowStepCreate,
    db: AsyncSession = Depends(get_db)
) -> WorkflowStepResponse:
    """Create a workflow step."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    step = WorkflowStep(
        workflow_id=workflow_id,
        step_name=step_data.step_name,
        step_number=step_data.step_number,
        status="pending"
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)

    return step


@router.put("/{workflow_id}/steps/{step_id}", response_model=WorkflowStepResponse)
async def update_workflow_step(
    workflow_id: int,
    step_id: int,
    status: str | None = None,
    output: str | None = None,
    error_message: str | None = None,
    agent_used: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> WorkflowStepResponse:
    """Update workflow step status and output."""
    step = await db.get(WorkflowStep, step_id)
    if not step or step.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Workflow step not found")

    if status:
        step.status = status
    if output is not None:
        step.output = output
    if error_message is not None:
        step.error_message = error_message
    if agent_used:
        step.agent_used = agent_used

    await db.commit()
    await db.refresh(step)

    return step


@router.post("/{workflow_id}/decisions", response_model=TechStackDecisionResponse)
async def create_tech_decision(
    workflow_id: int,
    decision_data: TechStackDecisionCreate,
    db: AsyncSession = Depends(get_db)
) -> TechStackDecisionResponse:
    """Create a tech stack decision."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    decision = TechStackDecision(
        workflow_id=workflow_id,
        requirement=decision_data.requirement,
        our_choice=decision_data.our_choice,
        reason=decision_data.reason,
        category=decision_data.category,
        user_confirmed=decision_data.user_confirmed
    )
    db.add(decision)
    await db.commit()
    await db.refresh(decision)

    return decision


@router.post("/{workflow_id}/beads/tasks", status_code=201)
async def create_beads_task(
    workflow_id: int,
    job_id: str,
    title: str,
    task_type: str = "feature",
    deps: List[str] = [],
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a Beads task for the workflow."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    result = await beads_manager.create_task(
        job_id=job_id,
        title=title,
        task_type=task_type,
        deps=deps
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Beads task: {result.get('error')}"
        )

    return result


@router.get("/{workflow_id}/beads/tasks/ready")
async def get_ready_beads_tasks(
    workflow_id: int,
    job_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get ready (dependency-satisfied) Beads tasks."""
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    tasks = await beads_manager.get_ready_tasks(job_id=job_id, limit=limit)
    return tasks


# Orchestrator endpoints
@router.post("/v2/jobs/{job_id}/start", response_model=WorkflowResponse)
async def start_orchestrated_workflow(
    job_id: str,
    config: OrchestratedWorkflowStart,
    db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    """Start a workflow using the Orchestrator.

    This executes the full SeedFW workflow automatically with human-in-the-loop confirmations.
    """
    existing = await db.execute(
        select(Workflow).where(Workflow.job_id == job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Workflow already exists for job {job_id}")

    workflow = await orchestrator.start_workflow(
        job_id=job_id,
        db=db,
        auto_approve_intent=config.auto_approve_intent,
        auto_approve_plan=config.auto_approve_plan
    )

    return workflow


@router.post("/{workflow_id}/intent-confirm")
async def confirm_intent(
    workflow_id: int,
    confirmation: ConfirmationRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Confirm Intent Translator (Step 1) blueprint."""

    await orchestrator.confirm_intent(workflow_id, db, confirmation.confirmed)

    return {"status": "confirmed" if confirmation.confirmed else "rejected"}


@router.post("/{workflow_id}/plan-confirm")
async def confirm_plan(
    workflow_id: int,
    confirmation: ConfirmationRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Confirm Planning (Step 3) implementation plan."""

    await orchestrator.confirm_plan(workflow_id, db, confirmation.confirmed)

    return {"status": "confirmed" if confirmation.confirmed else "rejected"}


@router.get("/{workflow_id}/orchestrator-status")
async def get_orchestrator_status(
    workflow_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get detailed workflow status from Orchestrator."""

    status = await orchestrator.get_workflow_status(workflow_id, db)

    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])

    return status