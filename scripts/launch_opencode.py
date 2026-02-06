#!/usr/bin/env python3
"""
OpenCode Workflow Launcher

Prepare workflow context and launch OpenCode with pre-configured SEEDFW environment.
This script bridges the database/workflow system with OpenCode's agent capabilities.

Usage:
    python scripts/launch_opencode.py <job_id>

Example:
    python scripts/launch_opencode.py 2017343680036874996
"""

import asyncio
import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from core.database import get_db
from features.workflow.models.workflow import Workflow
from features.workflow.models.workflow_step import WorkflowStep
from features.job_processing.models.job import Job


class OpenCodeLauncher:
    """Prepare and launch OpenCode for workflow execution."""

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

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.workflow: Optional[Workflow] = None
        self.job: Optional[Job] = None
        self.workspace_path: Optional[Path] = None

    async def prepare_workflow_context(self):
        """Load workflow and job data from database."""
        print(f"Loading workflow context for job {self.job_id}...")

        async for db in get_db():
            job_result = await db.execute(
                select(Job).where(Job.job_id == self.job_id)
            )
            self.job = job_result.scalar_one_or_none()

            if not self.job:
                print(f"❌ Job {self.job_id} not found in database")
                return False

            workflow_result = await db.execute(
                select(Workflow).where(Workflow.job_id == self.job_id)
            )
            self.workflow = workflow_result.scalar_one_or_none()

            if not self.workflow:
                print(f"❌ No workflow found for job {self.job_id}")
                print(f"   Create one via API first:")
                print(f"   curl -X POST http://localhost:8001/workflows/v2/jobs/{self.job_id}/start \\")
                print(f"     -H 'Content-Type: application/json' \\")
                print(f"     -d '{{\"auto_approve_intent\": false, \"auto_approve_plan\": false}}'")
                return False

            self.workspace_path = Path(self.workflow.beads_path) if self.workflow.beads_path else None

            if not self.workspace_path or not self.workspace_path.exists():
                print(f"❌ Workspace not found: {self.workspace_path}")
                return False

            steps_result = await db.execute(
                select(WorkflowStep)
                .where(WorkflowStep.workflow_id == self.workflow.id)
                .order_by(WorkflowStep.step_number)
            )
            self.steps = steps_result.scalars().all()

            return True

    def display_context(self):
        """Display workflow context to user."""
        print("\n" + "="*80)
        print("WORKFLOW CONTEXT")
        print("="*80)
        print(f"Job ID: {self.job_id}")
        print(f"Title: {self.job.title}")
        print(f"Workflow ID: {self.workflow.id}")
        print(f"Status: {self.workflow.status}")
        print(f"Workspace: {self.workspace_path}")
        print(f"Session ID: {self.workflow.session_id or 'Not set'}")
        print()

        print("WORKFLOW STEPS:")
        print("-" * 80)
        for step in self.steps:
            status_icon = "✓" if step.status == "completed" else ("○" if step.status == "pending" else "!")
            print(f"  [{status_icon}] Step {step.step_number}: {step.step_name}")
            print(f"      Status: {step.status}")
            print(f"      Agent: {step.agent_name or 'N/A'}")
            if step.error_message:
                print(f"      Error: {step.error_message}")
            print()

        print("="*80)
        print()

    def create_initial_context_file(self):
        """Create initial context file for OpenCode agents."""
        if not self.workspace_path:
            return None

        context_file = self.workspace_path / ".workflow_context.json"

        context = {
            "job_id": self.job_id,
            "workflow_id": self.workflow.id,
            "job_title": self.job.title,
            "job_description": self.job.description,
            "skills_required": self.job.skills_required or [],
            "budget": str(self.job.budget) if self.job.budget else None,
            "client_info": {
                "payment_verified": self.job.payment_verification,
                "rating": self.job.client_rating,
                "jobs_posted": self.job.jobs_posted,
                "hire_rate": float(self.job.hire_rate) if self.job.hire_rate else None,
            },
            "workflow_steps": [
                {
                    "number": step.step_number,
                    "name": step.step_name,
                    "status": step.status,
                    "agent": step.agent_name,
                }
                for step in self.steps
            ],
            "beads_workspace": str(self.workspace_path),
        }

        with open(context_file, 'w') as f:
            json.dump(context, f, indent=2)

        print(f"✓ Created context file: {context_file}")
        return context_file

    def get_next_step(self) -> tuple[int, str]:
        """Find the next pending step to execute."""
        for step in self.steps:
            if step.status in ["pending", "pending_confirmation"]:
                return step.step_number, step.step_name
        return None, None

    def launch_opencode(self):
        """Launch OpenCode TUI in workspace directory."""
        if not self.workspace_path:
            print("❌ No workspace available")
            return

        next_step_number, next_step_name = self.get_next_step()

        print("\n" + "="*80)
        print("LAUNCHING OPENCODE")
        print("="*80)
        print(f"Workspace: {self.workspace_path}")
        print(f"Next Step: Step {next_step_number} - {next_step_name}" if next_step_number else "All steps completed")
        print()

        initial_prompt = self._prepare_step_prompt(next_step_number)

        print("\nRecommended OpenCode commands:")
        print("-" * 80)
        self._print_step_commands(next_step_number)
        print("-" * 80)
        print()

        os.chdir(self.workspace_path)

        if initial_prompt:
            cmd = ["/home/mishka/.opencode/bin/opencode", "run", initial_prompt]
        else:
            cmd = ["/home/mishka/.opencode/bin/opencode"]

        print(f"Launching OpenCode in: {self.workspace_path}")
        print("Press Ctrl+C to exit OpenCode")
        print()

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"\nOpenCode exited with code {e.returncode}")
        except KeyboardInterrupt:
            print("\nInterrupted by user")

    def _prepare_step_prompt(self, step_number: Optional[int]) -> str:
        """Prepare initial prompt for the given step."""
        if step_number is None:
            return None

        step_prompts = {
            0: "/prime-context-seedfw Load workflow context from .workflow_context.json",
            1: "/intent-translator Use .workflow_context.json to clarify requirements",
            2: "/prp-core-create Generate PRP based on intent and context",
            3: "/create-plan Create implementation plan",
            4: "/start-work Execute plan using Sisyphus-Jr agents",
            5: "/verify-prp Verify implementation against PRP and Golden Rules",
            6: Commit and create PR if ready",
            7: Finalize and archive workflow",
        }

        return step_prompts.get(step_number, "")

        step_name = self.STEPS.get(step_number, f"Step {step_number}")

        prompts = {
            0: f"You are in Step 0: Context Loading. Load the workflow context from .workflow_context.json and understand the job requirements.",
            1: f"Use /intent-translator to clarify requirements for: {self.job.title}",
            2: f"Use /prp-core-create to generate Product Requirement Prompts",
            3: f"Use /create-plan to create the implementation plan",
            4: f"Use /start-work to begin execution with coding swarm",
            5: f"Use /verify-prp to validate the implementation",
            6: f"Commit changes and create pull request",
            7: f"Finalize workflow and archive results",
        }

        return prompts.get(step_number, f"Execute Step {step_number}: {step_name}")

    def _print_step_commands(self, step_number: Optional[int]):
        """Print recommended commands for each step."""
        if step_number is None:
            print("All steps completed. Review results:")
            print("  cat INITIAL.md")
            print("  cat PLAN.md")
            print("  git log")
            return

        print(f"\nFor Step {step_number} ({self.STEPS.get(step_number)}):")
        print()

        if step_number == 0:
            print("1. Context Loading:")
            print("   Read .workflow_context.json")
            print("   Review job requirements and skills")
            print()

        elif step_number == 1:
            print("2. Intent Clarification:")
            print("   /intent-translator")
            print("   Clarify ambiguous requirements")
            print("   Confirm technical approach with user")
            print()

        elif step_number == 2:
            print("3. PRP Creation:")
            print("   /prp-core-create")
            print("   Document functional requirements")
            print("   Define success criteria")
            print()

        elif step_number == 3:
            print("4. Planning:")
            print("   /create-plan")
            print("   Break down into atomic tasks")
            print("   Select tech stack components")
            print()

        elif step_number == 4:
            print("5. Execution:")
            print("   /start-work")
            print("   Assign tasks to specialist agents")
            print("   Track progress via Beads (/usr/local/bin/bd)")
            print()

        elif step_number == 5:
            print("6. Validation:")
            print("   /verify-prp")
            print("   Check against Golden Rules")
            print("   Verify all requirements met")
            print()

        elif step_number == 6:
            print("7. Git Operations:")
            print("   git add .")
            print("   git commit -m 'feat: [description]'")
            print("   git push")
            print("   gh pr create ...")
            print()

        elif step_number == 7:
            print("8. Completion:")
            print("   Review all deliverables")
            print("   Archive workflow")
            print("   Mark as complete in database")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/launch_opencode.py <job_id>")
        print()
        print("Example:")
        print("  python scripts/launch_opencode.py 2017343680036874996")
        sys.exit(1)

    job_id = sys.argv[1]

    launcher = OpenCodeLauncher(job_id)

    # Load workflow context
    success = await launcher.prepare_workflow_context()
    if not success:
        sys.exit(1)

    # Display context
    launcher.display_context()

    # Create context file for OpenCode
    launcher.create_initial_context_file()

    # Show next step and launch OpenCode
    print("Ready to launch OpenCode with workflow context.\n")
    launcher.launch_opencode()


if __name__ == "__main__":
    asyncio.run(main())