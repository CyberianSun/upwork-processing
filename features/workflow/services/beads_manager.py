import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from subprocess import run, PIPE

logger = logging.getLogger(__name__)


class BeadsManager:
    """Service for managing Beads CLI operations.

    Provides async wrapper around Beads commands for task tracking
    in autonomous development workflows.
    """

    def __init__(self, base_projects_path: str = "projects"):
        """Initialize Beads manager.

        Args:
            base_projects_path: Base directory for project workspaces
        """
        self.base_projects_path = Path(base_projects_path)
        self.beads_bin = os.environ.get("BEADS_BIN", "/usr/local/bin/bd")

        # Ensure base projects directory exists
        self.base_projects_path.mkdir(parents=True, exist_ok=True)

    async def initialize(self, job_id: str) -> Dict[str, Any]:
        """Initialize Beads for a new job workspace.

        Creates workspace directory and runs 'bd init'.

        Args:
            job_id: Job identifier (used as workspace name)

        Returns:
            Dict with workspace path and initialization status
        """
        workspace_path = self.base_projects_path / job_id

        try:
            # Create workspace directory
            workspace_path.mkdir(parents=True, exist_ok=True)

            # Run 'bd init' - Beads should handle initialization
            # Note: Beads automatically initializes in current directory
            result = run(
                [self.beads_bin, "init"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"bd init returned non-zero: {result.stderr}")

            # Check if Beads database was created
            beads_db = workspace_path / "task_db.db"
            if beads_db.exists():
                logger.info(f"Beads initialized successfully at {workspace_path}")
                return {
                    "success": True,
                    "workspace_path": str(workspace_path),
                    "beads_db": str(beads_db),
                    "message": "Beads workspace initialized"
                }
            else:
                logger.warning(f"Beads DB not found at {beads_db}, but init completed")
                return {
                    "success": True,
                    "workspace_path": str(workspace_path),
                    "message": "Workspace created (Beads may initialize on first use)"
                }

        except Exception as e:
            logger.error(f"Failed to initialize Beads workspace: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to initialize workspace"
            }

    async def create_task(
        self,
        job_id: str,
        title: str,
        task_type: str,
        deps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new Beads task.

        Args:
            job_id: Job identifier
            title: Task title
            task_type: Task type (feature, bug, refactor, etc.)
            deps: List of task dependencies (task IDs)

        Returns:
            Dict with task creation result
        """
        workspace_path = self.base_projects_path / job_id

        if not workspace_path.exists():
            return {
                "success": False,
                "error": "Workspace does not exist",
                "message": f"Workspace {job_id} not initialized"
            }

        try:
            # Build bd create command
            cmd = [self.beads_bin, "create", title]

            # Add task type
            if task_type:
                cmd.extend(["--type", task_type])

            # Add dependencies
            if deps:
                for dep in deps:
                    cmd.extend(["--deps", dep])

            result = run(
                cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Parse output to get task ID
                task_id = None
                if result.stdout:
                    # Beads typically outputs task ID on success
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        # Try to extract ID from output
                        task_id = lines[0].strip()

                logger.info(f"Task created: {title} -> {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "title": title,
                    "message": "Task created successfully",
                    "output": result.stdout
                }
            else:
                logger.error(f"Failed to create task: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "message": "Failed to create task"
                }

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error creating task"
            }

    async def get_ready_tasks(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get ready (dependency-satisfied) tasks.

        Args:
            job_id: Job identifier
            limit: Maximum number of tasks to return

        Returns:
            List of ready tasks
        """
        workspace_path = self.base_projects_path / job_id

        try:
            result = run(
                [self.beads_bin, "ready", "--output", "json", "--limit", str(limit)],
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                tasks = json.loads(result.stdout)
                return tasks if isinstance(tasks, list) else []
            else:
                logger.warning(f"Failed to get ready tasks: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"Error getting ready tasks: {e}")
            return []

    async def update_task_status(
        self,
        job_id: str,
        task_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update task status.

        Args:
            job_id: Job identifier
            task_id: Task identifier
            status: New status (in-progress, done, etc.)

        Returns:
            Dict with update result
        """
        workspace_path = self.base_projects_path / job_id

        try:
            result = run(
                [self.beads_bin, "update", task_id, "--status", status],
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            success = result.returncode == 0
            if success:
                logger.info(f"Task {task_id} updated to {status}")
            else:
                logger.error(f"Failed to update task: {result.stderr}")

            return {
                "success": success,
                "task_id": task_id,
                "status": status,
                "message": "Task updated" if success else "Failed to update task",
                "output": result.stdout if success else None,
                "error": result.stderr if not success else None
            }

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error updating task"
            }

    async def close_task(
        self,
        job_id: str,
        task_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Close a task (mark as completed/obsolete).

        Args:
            job_id: Job identifier
            task_id: Task identifier
            reason: Reason for closing

        Returns:
            Dict with close result
        """
        workspace_path = self.base_projects_path / job_id

        try:
            cmd = [self.beads_bin, "close", task_id]
            if reason:
                cmd.extend(["--reason", reason])

            result = run(
                cmd,
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            success = result.returncode == 0
            if success:
                logger.info(f"Task {task_id} closed")
            else:
                logger.error(f"Failed to close task: {result.stderr}")

            return {
                "success": success,
                "task_id": task_id,
                "message": "Task closed" if success else "Failed to close task",
                "output": result.stdout if success else None,
                "error": result.stderr if not success else None
            }

        except Exception as e:
            logger.error(f"Error closing task: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error closing task"
            }

    async def get_all_tasks(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a job.

        Args:
            job_id: Job identifier

        Returns:
            List of all tasks
        """
        workspace_path = self.base_projects_path / job_id

        try:
            # Use 'bd show' or similar to get all tasks
            # Note: Beads command may vary, adjust based on actual CLI
            result = run(
                [self.beads_bin, "show", "--output", "json"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout:
                tasks = json.loads(result.stdout)
                return tasks if isinstance(tasks, list) else []
            else:
                logger.warning(f"Failed to get tasks: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    async def sync(self, job_id: str) -> Dict[str, Any]:
        """Sync Beads database.

        Args:
            job_id: Job identifier

        Returns:
            Dict with sync result
        """
        workspace_path = self.base_projects_path / job_id

        try:
            result = run(
                [self.beads_bin, "sync"],
                cwd=str(workspace_path),
                capture_output=True,
                text=True
            )

            success = result.returncode == 0
            if success:
                logger.info(f"Beads synced for job {job_id}")

            return {
                "success": success,
                "message": "Beads synced" if success else "Failed to sync",
                "output": result.stdout if success else None,
                "error": result.stderr if not success else None
            }

        except Exception as e:
            logger.error(f"Error syncing Beads: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error syncing Beads"
            }

    def get_workspace_path(self, job_id: str) -> str:
        """Get workspace path for a job.

        Args:
            job_id: Job identifier

        Returns:
            Absolute path to workspace
        """
        return str(self.base_projects_path / job_id)