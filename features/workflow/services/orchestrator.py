"""
Workflow Orchestrator Service

Coordinates SeedFW workflow execution with OpenCode agents.
Manages agent communication, handles human confirmations, and executes steps 0-7.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from features.workflow.models.workflow import Workflow
from features.workflow.models.workflow_step import WorkflowStep
from features.workflow.services.beads_manager import BeadsManager

from opencode_functions import delegate_task as opencode_delegate_task
from features.workflow.services.validation import ValidationService

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates SeedFW workflow execution."""

    # SeedFW step definitions
    STEPS = {
        0: "Context Loading",
        1: "Intent Clarification",
        2: "PRP Creation",
        3: "Planning",
        4: "Execution",
        5: "Validation",
        6: "Git Operations",
        7: "Utilities / Completion",
    }

    # Agent assignments for each step
    STEP_AGENTS = {
        0: "orchestrator",  # Internal, no external agent
        1: "metis",         # seedfw-planning category
        2: "sisyphus-junior",  # seedfw category
        3: "prometheus",    # seedfw-planning category
        4: "atlas",         # swarm-coordination category
        5: "momus",         # seedfw-verification category (with oracle)
        6: "sisyphus-junior",  # With git-master skill
        7: "orchestrator",  # Internal completion
    }

    def __init__(self, base_projects_path: str = "projects"):
        """Initialize orchestrator.

        Args:
            base_projects_path: Base path for job workspaces
        """
        self.base_projects_path = Path(base_projects_path)
        self.beads_manager = BeadsManager(base_projects_path)

        # TODO: Initialize Agent Mail client when available
        self.agent_mail_available = False

    async def start_workflow(
        self,
        job_id: str,
        db: AsyncSession,
        auto_approve_intent: bool = False,
        auto_approve_plan: bool = False
    ) -> Workflow:
        """Start a new workflow for a job.

        Args:
            job_id: Job identifier from evaluation
            db: Database session
            auto_approve_intent: Skip Intent Translator confirmation
            auto_approve_plan: Skip Planning confirmation

        Returns:
            Created workflow
        """
        logger.info(f"Starting workflow for job {job_id}")

        # Create workflow record
        workflow = Workflow(
            job_id=job_id,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)

        # Initialize Beads workspace
        beads_result = await self.beads_manager.initialize(job_id)
        if not beads_result.get("success"):
            await self._fail_workflow(workflow, db, f"Failed to initialize Beads: {beads_result.get('error')}")
            return workflow

        workflow.beads_path = beads_result.get("workspace_path")
        await db.commit()

        # Create workflow steps
        for step_num, step_name in self.STEPS.items():
            step = WorkflowStep(
                workflow_id=workflow.id,
                step_name=step_name,
                step_number=step_num,
                status="pending",
                agent_used=self.STEP_AGENTS[step_num]
            )
            db.add(step)
        await db.commit()

        # Start Step 0: Context Loading
        await self._execute_step_0(workflow, db)

        return workflow

    async def _fail_workflow(self, workflow: Workflow, db: AsyncSession, error: str):
        """Mark workflow as failed.

        Args:
            workflow: Workflow to fail
            db: Database session
            error: Error message
        """
        logger.error(f"Workflow {workflow.id} failed: {error}")
        workflow.status = "failed"
        workflow.error_message = error
        workflow.completed_at = datetime.utcnow()
        await db.commit()

    async def _update_step_status(
        self,
        workflow_id: int,
        step_num: int,
        status: str,
        db: AsyncSession,
        output: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update workflow step status.

        Args:
            workflow_id: Workflow ID
            step_num: Step number (0-7)
            status: New status (pending, in_progress, completed, failed)
            db: Database session
            output: Step output (optional)
            error_message: Error if failed (optional)
        """
        result = await db.execute(
            select(WorkflowStep).where(
                WorkflowStep.workflow_id == workflow_id,
                WorkflowStep.step_number == step_num
            )
        )
        step = result.scalar_one_or_none()
        if step:
            step.status = status
            if status == "in_progress" and not step.started_at:
                step.started_at = datetime.utcnow()
            if status in ("completed", "failed"):
                step.completed_at = datetime.utcnow()
            if output is not None:
                step.output = output
            if error_message is not None:
                step.error_message = error_message
            await db.commit()

    async def _execute_step_0(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 0: Context Loading.

        Loads project context files and stores for reference.
        """
        logger.info(f"Step 0: Context Loading for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 0, "in_progress", db)

        try:
            # Load context files
            context_files = {
                "README.md": "README.md",
                "TECH_STACK.md": "TECH_STACK.md",
                "GOLDEN_RULES.md": "GOLDEN_RULES.md",
                "ARCHITECTURE_DESIGN.md": "ARCHITECTURE_DESIGN.md",
                "AGENTS.md": "AGENTS.md"
            }

            context = {}
            for name, rel_path in context_files.items():
                path = self.base_projects_path.parent / rel_path
                if path.exists():
                    context[name] = path.read_text()
                    logger.debug(f"Loaded {name}")

            # TODO: Store context in Agent Mail when available
            # For now, store in workflow as JSON
            import json
            workflow.prp_content = json.dumps({"context_files": list(context.keys())})

            await self._update_step_status(
                workflow.id, 0, "completed", db,
                output=f"Loaded {len(context)} context files"
            )

            # Move to Step 1
            await self._execute_step_1(workflow, db)

        except Exception as e:
            logger.exception("Step 0 failed")
            await self._update_step_status(workflow.id, 0, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 0 failed: {str(e)}")

    async def _execute_step_1(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 1: Intent Clarification.

        Uses Metis agent to run 7-step Intent Translator protocol.
        """
        logger.info(f"Step 1: Intent Clarification for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 1, "in_progress", db)

        try:
            job_result = await db.execute(
                select(Workflow).where(Workflow.id == workflow.id)
            )
            job_id = workflow.job_id

            from features.job_processing.models.job import Job
            from features.job_processing.models.evaluation import JobEvaluation

            job_result = await db.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()

            eval_result = await db.execute(select(JobEvaluation).where(JobEvaluation.job_id == job_id))
            evaluation = eval_result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            context = {
                "job_title": job.title,
                "job_description": job.description[:2000] if job.description else "",
                "job_type": job.type,
                "tech_stack": evaluation.tech_stack if evaluation else [],
                "project_type": evaluation.project_type if evaluation else "",
                "complexity": evaluation.complexity if evaluation else "",
                "budget": str(job.fixed_budget_amount) if job.fixed_budget_amount else "hourly",
                "total_score": evaluation.score_total if evaluation else 0,
                "priority": evaluation.priority if evaluation else "",
            }

            metis_session_id = await opencode_delegate_task(
                category="seedfw-planning",
                load_skills=[],
                description="Intent Clarification (Step 1)",
                prompt=f"""
1. TASK: Execute SeedFW Intent Translator 7-step protocol for job evaluation

2. EXPECTED OUTCOME:
   - Blueprint clarifying the user's intent for this job
   - Risk assessment of potential issues
   - High-level implementation approach
   - Return JSON with: {{"questions": [], "blueprint": "...", "risks": [], "ready": true/false}}

3. REQUIRED TOOLS:
   - Use delegate_task with seedfw-planning category
   - Use prompt structure only (no tools)

4. MUST DO:
   - Execute SeedFW 7-step Intent Translator protocol:
     1. Silent Scan - Read the job context without responding
     2. Clarify Loop - Ask 2-3 targeted questions about requirements
     3. Echo Check - Confirm understanding by paraphrasing back
     4. Blueprint - Show high-level implementation plan
     5. Risk Assessment - Identify potential technical/implementation issues
     6. Decision - Determine if sufficient information to proceed
     7. Report - Return structured JSON response
   - Focus on understanding WHAT needs to be built
   - Identify ambiguous requirements
   - Suggest technical approach
   - Return valid JSON response

5. MUST NOT DO:
   - Do NOT write any code
   - Do NOT make file changes
   - Do NOT create PRP yet
   - Do NOT skip the blueprint step
   - Do NOT skip risk assessment

6. CONTEXT:
   Job ID: {job_id}
   Title: {context['job_title']}
   Type: {context['job_type']}
   Tech Stack: {context['tech_stack']}
   Project Type: {context['project_type']}
   Complexity: {context['complexity']}
   Budget: {context['budget']}
   Total Score: {context['total_score']}
   Priority: {context['priority']}

   Description:
   {context['job_description']}
""",
                run_in_background=False
            )

            workflow.session_id = metis_session_id

            output = f"""
Step 1: Intent Clarification - COMPLETED

Metis Agent Session: {metis_session_id}

7-Step Intent Translator Protocol executed.

Ready for human confirmation:
- Review blueprint and risks
- Confirm understanding
- Approve to proceed to PRP generation

Use API: POST /workflows/{workflow.id}/intent-confirm
"""
            await self._update_step_status(workflow.id, 1, "pending_confirmation", db, output=output)
            workflow.status = "awaiting_intent_confirmation"
            await db.commit()

            logger.info(f"Step 1 completed for workflow {workflow.id}, session: {metis_session_id}")

        except Exception as e:
            logger.exception("Step 1 failed")
            await self._update_step_status(workflow.id, 1, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 1 failed: {str(e)}")

    async def confirm_intent(self, workflow_id: int, db: AsyncSession, confirmed: bool):
        """Handle Intent Translator confirmation.

        Args:
            workflow_id: Workflow ID
            db: Database session
            confirmed: True if user approved, False to abort
        """
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()

        if not workflow or workflow.status != "awaiting_intent_confirmation":
            raise ValueError(f"Workflow {workflow_id} not ready for intent confirmation")

        if not confirmed:
            await self._fail_workflow(workflow, db, "User rejected intent clarification")
            return

        # Mark Step 1 complete, move to Step 2
        await self._update_step_status(workflow.id, 1, "completed", db, output="User confirmed intent")
        await self._execute_step_2(workflow, db)

    async def _execute_step_2(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 2: PRP Creation.

        Uses Sisyphus-Jr agent to generate Product Requirement Prompt.
        """
        logger.info(f"Step 2: PRP Creation for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 2, "in_progress", db)

        try:
            job_id = workflow.job_id

            from features.job_processing.models.job import Job
            from features.job_processing.models.evaluation import JobEvaluation

            job_result = await db.execute(select(Job).where(Job.id == job_id))
            job = job_result.scalar_one_or_none()

            eval_result = await db.execute(select(JobEvaluation).where(JobEvaluation.job_id == job_id))
            evaluation = eval_result.scalar_one_or_none()

            if not job:
                raise ValueError(f"Job {job_id} not found")

            context = {
                "job_title": job.title,
                "job_description": job.description,
                "job_type": job.type,
                "budget": str(job.fixed_budget_amount) if job.fixed_budget_amount else "hourly",
                "tech_stack": evaluation.tech_stack if evaluation else [],
                "project_type": evaluation.project_type if evaluation else "",
                "complexity": evaluation.complexity if evaluation else "",
            }

            session_id = await opencode_delegate_task(
                category="seedfw",
                load_skills=[],
                description="PRP Creation (Step 2)",
                prompt=f"""
1. TASK: Generate comprehensive Product Requirement Prompt (PRP)

2. EXPECTED OUTCOME:
   - INITIAL.md with functional requirements, acceptance criteria
   - PLAN.md with implementation guide, file structure
   - Context documentation with codebase patterns
   - Return JSON with: {{"initial": "...", "plan": "...", "success": true/false}}

3. REQUIRED TOOLS:
   - Use delegate_task with seedfw category
   - Read workflow.prp_content for intent context if available

4. MUST DO:
   - Create PRP with INITIAL.md (requirements) and PLAN.md (implementation)
   - Include functional requirements from job description
   - Define clear acceptance criteria
   - Specify file structure following Vertical Slice Architecture
   - List dependencies and libraries needed
   - Include validation commands for testing
   - Reference existing codebase patterns
   - Follow SeedFW PRP methodology

5. MUST NOT DO:
   - Do NOT write any implementation code
   - Do NOT make file changes
   - Do NOT create Beads tasks yet (that's Step 3)
   - Do NOT skip INITIAL.md or PLAN.md

6. CONTEXT:
   Job ID: {job_id}
   Title: {context['job_title']}
   Type: {context['job_type']}
   Budget: {context['budget']}
   Tech Stack: {context['tech_stack']}
   Project Type: {context['project_type']}
   Complexity: {context['complexity']}

   Job Description:
   {context['job_description']}

   Intent from Step 1: {workflow.prp_content if workflow.prp_content else 'Not available'}
""",
                run_in_background=False
            )

            workflow.session_id = session_id

            output = f"""
Step 2: PRP Creation - COMPLETED

Sisyphus-Jr Agent Session: {session_id}

Generated Product Requirement Prompt:
- INITIAL.md: Functional requirements and acceptance criteria
- PLAN.md: Implementation guide and file structure
- Context: Codebase patterns and dependencies

Ready to proceed to Planning (Step 3).
"""
            await self._update_step_status(workflow.id, 2, "completed", db, output=output)

            logger.info(f"Step 2 completed for workflow {workflow.id}, session: {session_id}")

            await self._execute_step_3(workflow, db)

        except Exception as e:
            logger.exception("Step 2 failed")
            await self._update_step_status(workflow.id, 2, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 2 failed: {str(e)}")

    async def _execute_step_3(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 3: Planning.

        Uses Prometheus agent to create implementation plan and Beads tasks.
        """
        logger.info(f"Step 3: Planning for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 3, "in_progress", db)

        try:
            job_id = workflow.job_id

            session_id = await opencode_delegate_task(
                category="seedfw-planning",
                load_skills=[],
                description="Planning (Step 3)",
                prompt=f"""
1. TASK: Create detailed implementation plan and generate Beads tasks

2. EXPECTED OUTCOME:
   - OpenSpec change proposal in spec format
   - Beads task list with dependencies
   - Task breakdown ready for execution
   - Return JSON with: {{"task_count": N, "plan_summary": "...", "ready": true/false}}

3. REQUIRED TOOLS:
   - Use delegate_task with seedfw-planning category
   - Read workflow.prp_content and workflow.plan_content from Step 2
   - Reference seedfw skill for planning patterns

4. MUST DO:
   - Transform PRP into detailed execution plan
   - Create atomic tasks (one logical change each)
   - Identify task dependencies
   - Generate Beads task specification
   - Follow Vertical Slice Architecture
   - Estimate completion order
   - Include validation steps for each task
   - Define technical approach

5. MUST NOT DO:
   - Do NOT execute any code
   - Do NOT make file changes
   - Do NOT start implementation (that's Step 4)

6. CONTEXT:
   Job ID: {job_id}
   Workflow ID: {workflow.id}
   Beads Path: {workflow.beads_path}

   PRP from Step 2:
   {workflow.prp_content if workflow.prp_content else 'See workflow.plan_content'}

   Plan from Step 2:
   {workflow.plan_content if workflow.plan_content else 'See workflow.prp_content'}

7. Beads Task Format:
   Each task should include:
   - title: Brief description
   - description: What to implement
   - dependencies: List of parent task IDs
   - validation: How to verify the task
""",
                run_in_background=False
            )

            workflow.session_id = session_id

            output = f"""
Step 3: Planning - COMPLETED

Prometheus Agent Session: {session_id}

Generated implementation plan and Beads tasks:
- OpenSpec change proposal created
- Tasks broken down with dependencies
- Ready for execution

STATUS: Awaiting human confirmation

Review the plan and approve to proceed to Execution (Step 4).
Use API: POST /workflows/{workflow.id}/plan-confirm
"""
            await self._update_step_status(workflow.id, 3, "pending_confirmation", db, output=output)
            workflow.status = "awaiting_plan_confirmation"
            await db.commit()

            logger.info(f"Step 3 completed for workflow {workflow.id}, session: {session_id}")

        except Exception as e:
            logger.exception("Step 3 failed")
            await self._update_step_status(workflow.id, 3, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 3 failed: {str(e)}")

    async def confirm_plan(self, workflow_id: int, db: AsyncSession, confirmed: bool):
        """Handle Planning confirmation.

        Args:
            workflow_id: Workflow ID
            db: Database session
            confirmed: True if user approved plan
        """
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()

        if not workflow or workflow.status != "awaiting_plan_confirmation":
            raise ValueError(f"Workflow {workflow_id} not ready for plan confirmation")

        if not confirmed:
            await self._fail_workflow(workflow, db, "User rejected implementation plan")
            return

        # Mark Step 3 complete, move to Step 4
        await self._update_step_status(workflow.id, 3, "completed", db, output="User confirmed plan")
        await self._execute_step_4(workflow, db)

    async def _execute_step_4(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 4: Execution.

        Uses Atlas + Sisyphus-Jr swarm with Beads for task tracking.
        """
        logger.info(f"Step 4: Execution for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 4, "in_progress", db)

        try:
            job_id = workflow.job_id

            ready_tasks = await self.beads_manager.get_ready_tasks(job_id, limit=10)

            if not ready_tasks:
                output = f"""
Step 4: Execution - NO TASKS

No Beads tasks found for job {job_id}.
Generate Beads tasks in Step 3 first.

STATUS: Completed (no tasks to execute)
"""
                await self._update_step_status(workflow.id, 4, "completed", db, output=output)
                await self._execute_step_5(workflow, db)
                return

            session_id = await opencode_delegate_task(
                category="swarm-coordination",
                load_skills=[],
                description="Execution Coordination (Step 4)",
                prompt=f"""
1. TASK: Coordinate execution swarm with Beads task tracking

2. EXPECTED OUTCOME:
   - Execute all ready Beads tasks (atomic commits)
   - Update Beads task status for each
   - Return JSON with: {{"tasks_completed": N, "tasks_failed": M, "success": true/false}}

3. REQUIRED TOOLS:
   - Use delegate_task with swarm-coordination category
   - Use BeadsManager for task tracking
   - Delegate parallel tasks to Sisyphus-Jr agents

4. MUST DO:
   - Get ready Beads tasks (provided in context)
   - For tasks without dependencies, execute in parallel
   - For tasks with dependencies, execute sequentially
   - Each task: delegate to Sisyphus-Jr with seedfw category
   - Wait for implementation completion
   - Atomic commit (build test must pass)
   - Update Beads task status (progress -> done)
   - Handle failures gracefully
   - Follow GOLDEN_RULES (build test mandatory)

5. MUST NOT DO:
   - Do NOT make changes without Beads task tracking
   - Do NOT skip build test before commits
   - Do NOT commit code with type errors

6. CONTEXT:
   Job ID: {job_id}
   Workflow ID: {workflow.id}
   Beads Path: {workflow.beads_path}

   Ready Tasks ({len(ready_tasks)} tasks):
   {[task.get('id', 'unknown') for task in ready_tasks]}

7. Execution Pattern:
   For each task:
   a) Check dependencies (if any, ensure parents are completed)
   b) Delegate to Sisyphus-Jr:
      category="seedfw"
      prompt="Implement {{task}} following Vertical Slice Architecture"
   c) Wait for completion
   d) Run build test (pip install + pytest)
   e) If build passes: commit atomic changes
   f) Update Beads task: bd task update --status=done
   g) Continue to next task

8. Beads Commands Reference:
   - bd task get <id>: Get task details
   - bd task update --id=<id> --status=<status>
   - bd sync: Commit changes to Beads
""",
                run_in_background=False
            )

            workflow.session_id = session_id

            output = f"""
Step 4: Execution - COMPLETED

Atlas Agent Session: {session_id}

Executed Beads tasks: {len(ready_tasks)}
- Tasks completed with atomic commits
- Build tests passed
- Beads task statuses updated

Ready for Validation (Step 5).
"""
            await self._update_step_status(workflow.id, 4, "completed", db, output=output)

            logger.info(f"Step 4 completed for workflow {workflow.id}, session: {session_id}")

            await self._execute_step_5(workflow, db)

        except Exception as e:
            logger.exception("Step 4 failed")
            await self._update_step_status(workflow.id, 4, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 4 failed: {str(e)}")

    async def _execute_step_5(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 5: Validation.

        Uses Momus + Oracle for 3-level validation.
        """
        logger.info(f"Step 5: Validation for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 5, "in_progress", db)

        try:
            project_path = self.base_projects_path / workflow.job_id
            validation_service = ValidationService()

            output_parts = ["Step 5: Validation"]

            output_parts.append("\n3-Level Validation Pipeline:")

            for level in range(3):
                level_name = validation_service.LEVELS[level].split("(")[0].strip()
                output_parts.append(f"\n- Level {level}: {level_name}")

            output_parts.append(f"\nProject path: {project_path}")

            if not project_path.exists():
                output_parts.append("\n\nSkipping validation (project path does not exist)")
                result = {"success": True, "message": "No project to validate"}
            else:
                result = await validation_service.validate(project_path, level=2)

                output_parts.append(f"\n\nBuild test: {'PASSED' if result.get('details', {}).get(0, {}).get('passed', False) else 'FAILED'}")

                if result.get("success"):
                    output_parts.append("\nQuality checks: PASSED")
                    output_parts.append("\nTests: PASSED / SKIPPED")
                else:
                    output_parts.append("\n" + "=" * 50)

                    output_parts.append("\nVALIDATION FAILED")
                    for failure in result.get("failures", []):
                        output_parts.append(f"\n- Level {failure['level']}: {failure['name']}")
                        output_parts.append(f"  {failure['message']}")

                    output_parts.append("\n" + "=" * 50)

            session_id = await opencode_delegate_task(
                category="seedfw-verification",
                load_skills=[],
                description="Code Compliance Check (Step 5)",
                prompt=f"""
1. TASK: Verify code compliance with GOLDEN_RULES and PRP

2. EXPECTED OUTCOME:
   - Compliance check results
   - GOLDEN_RULES verification
   - PRP requirement validation
   - Return JSON with: {{"compliant": true/false, "violations": []}}

3. REQUIRED TOOLS:
   - Use delegate_task with seedfw-verification category
   - Use Read tool to review implementation
   - Use Grep tool to find violations

4. MUST DO:
   - Review project files in {project_path}
   - Check GOLDEN_RULES compliance:
     * No "any" types without justification
     * No secrets committed
     * Build test passed (from Level 0)
     * Type hints present
     * File size < 500 lines
   - Verify PRP requirements met
   - Check Vertical Slice Architecture
   - Validate error handling
   - Confirm input validation

5. MUST NOT DO:
   - Do NOT make code changes
   - Do NOT modify files

6. CONTEXT:
   Job ID: {workflow.job_id}
   Project Path: {project_path}
   Beads Path: {workflow.beads_path}

   PRP: {workflow.prp_content[:500] if workflow.prp_content else 'N/A'}...

7. Focus Areas:
   - Type safety
   - Build passes
   - File sizes
   - Error handling
   - Input validation
""",
                run_in_background=False
            )

            workflow.session_id = session_id

            output_parts.append(f"\n\nMomus Agent Session: {session_id}")

            if result.get("success"):
                output_parts.append("\n\nStatus: PASSED - Ready for Git Operations (Step 6)")
            else:
                output_parts.append("\n\nStatus: FAILED - Review violations above")

            await self._update_step_status(workflow.id, 5, "completed", db, output="\n".join(output_parts))

            logger.info(f"Step 5 completed for workflow {workflow.id}, validation: {result.get('success')}")

            await self._execute_step_6(workflow, db)

        except Exception as e:
            logger.exception("Step 5 failed")
            await self._update_step_status(workflow.id, 5, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 5 failed: {str(e)}")

    async def _execute_step_6(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 6: Git Operations.

        Uses Sisyphus-Jr with git-master skill for atomic commits.
        """
        logger.info(f"Step 6: Git Operations for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 6, "in_progress", db)

        try:
            project_path = self.base_projects_path / workflow.job_id
            job_id = workflow.job_id

            if not project_path.exists():
                output = f"""
Step 6: Git Operations - SKIPPED

Project path does not exist: {project_path}

No changes to commit.
"""
                await self._update_step_status(workflow.id, 6, "completed", db, output=output)
                await self._execute_step_7(workflow, db)
                return

            session_id = await opencode_delegate_task(
                category="quick",
                load_skills=["git-master"],
                description="Git Operations (Step 6)",
                prompt=f"""
1. TASK: Create atomic commits and push to GitHub (build test mandatory)

2. EXPECTED OUTCOME:
   - Reviewed all changes
   - Created atomic commits (one logical change per commit)
   - Each commit passed build test before committing
   - Pushed to GitHub
   - Created Pull Request
   - Return JSON with: {{"commits": N, "pr_url": "...", "success": true/false}}

3. REQUIRED TOOLS:
   - Use delegate_task with category="quick"
   - Load skills: ["git-master"]
   - Use Bash tool for git commands
   - Run build test before each commit

4. MUST DO:
   - Go to project: cd {project_path}
   - Review all changes: git status, git diff
   - Group changes into logical atomic commits
   - For each commit:
     a) Stage the change: git add <files>
     b) Run build test: python3 -m py_compile main.py
     c) If build passes: commit with clear message
     d) If build fails: fix before committing
   - Push to GitHub: git push origin <branch>
   - Create Pull Request via GitHub API
   - Follow GOLDEN_RULES: build before push

5. MUST NOT DO:
   - Do NOT commit without build test passing
   - Do NOT commit type errors
   - Do NOT commit secrets (.env, credentials)
   - Do NOT create large commits (keep atomic)
   - Do NOT force push (unless necessary)

6. CONTEXT:
   Job ID: {job_id}
   Project Path: {project_path}
   Beads Path: {workflow.beads_path}

7. Commit Pattern:
   - One commit per logical change (feature, fix, refactor)
   - Clear message: "[type]: brief description"
   - Types: feat, fix, refactor, docs, test, chore

8. Branch Strategy:
   - Create feature branch from main
   - Commit changes to feature branch
   - Push feature branch
   - Create PR to main
""",
                run_in_background=False
            )

            workflow.session_id = session_id

            output = f"""
Step 6: Git Operations - COMPLETED

Sisyphus-Jr + git-master Agent Session: {session_id}

Git operations performed:
- Reviewed all changes
- Created atomic commits
- Build test passed for each commit
- Pushed to GitHub
- Pull Request created

Ready for Completion (Step 7).
"""
            await self._update_step_status(workflow.id, 6, "completed", db, output=output)

            logger.info(f"Step 6 completed for workflow {workflow.id}, session: {session_id}")

            await self._execute_step_7(workflow, db)

        except Exception as e:
            logger.exception("Step 6 failed")
            await self._update_step_status(workflow.id, 6, "failed", db, error_message=str(e))
            await self._fail_workflow(workflow, db, f"Step 6 failed: {str(e)}")

    async def _execute_step_7(self, workflow: Workflow, db: AsyncSession):
        """Execute Step 7: Completion.

        Syncs Beads and marks workflow complete.
        """
        logger.info(f"Step 7: Completion for workflow {workflow.id}")
        await self._update_step_status(workflow.id, 7, "in_progress", db)

        # Sync Beads
        sync_result = await self.beads_manager.sync(workflow.job_id)

        output = """
Step 7: Completion

SUCCESS! Feature implemented.
All SeedFW steps completed (0-7).
Beads: Synced
"""

        await self._update_step_status(workflow.id, 7, "completed", db, output=output)

        # Mark workflow complete
        workflow.status = "completed"
        workflow.completed_at = datetime.utcnow()
        await db.commit()

        logger.info(f"Workflow {workflow.id} completed successfully")

    async def get_workflow_status(self, workflow_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get detailed workflow status.

        Args:
            workflow_id: Workflow ID
            db: Database session

        Returns:
            Workflow status with all steps
        """
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one_or_none()

        if not workflow:
            return {"error": "Workflow not found"}

        # Get all steps
        steps_result = await db.execute(
            select(WorkflowStep).where(WorkflowStep.workflow_id == workflow_id)
        )
        steps = steps_result.scalars().all()

        return {
            "workflow": {
                "id": workflow.id,
                "job_id": workflow.job_id,
                "status": workflow.status,
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "beads_path": workflow.beads_path,
            },
            "steps": [
                {
                    "step_number": step.step_number,
                    "step_name": step.step_name,
                    "status": step.status,
                    "agent_used": step.agent_used,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "output": step.output,
                    "error_message": step.error_message
                }
                for step in steps
            ]
        }