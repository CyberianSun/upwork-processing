"""
Mock opencode_functions for testing purposes.

This module simulates OpenCode's delegate_task function to enable local testing
without requiring the actual OpenCode agent environment.
"""

import json
import logging
from typing import Optional, Dict, Any
import uuid

logger = logging.getLogger(__name__)


async def delegate_task(
    category: str,
    load_skills: list,
    description: str,
    prompt: str,
    run_in_background: bool = False,
    session_id: Optional[str] = None,
    subagent_type: Optional[str] = None,
    command: Optional[str] = None
) -> str:
    """Mock delegate_task function for testing.

    Args:
        category: Task category
        load_skills: List of skills to load
        description: Task description
        prompt: Task prompt
        run_in_background: Whether to run in background
        session_id: Existing session ID to continue
        subagent_type: Agent type to delegate to
        command: Command that triggered the task

    Returns:
        Session ID (or task_id if background=True)
    """
    # Generate a fake session ID
    fake_session_id = f"test_session_{uuid.uuid4().hex[:12]}"

    logger.info(f"MOCK delegate_task called:")
    logger.info(f"  Category: {category}")
    logger.info(f"  Description: {description}")
    logger.info(f"  Skills: {load_skills}")
    logger.info(f"  Session ID: {session_id or '[NEW]'}")
    logger.info(f"  Background: {run_in_background}")

    # Return mock response based on step
    if "intent" in description.lower() or "clarification" in description.lower():
        logger.info(f"  Mock response: intent clarification complete")
    elif "prp" in description.lower() or "initial" in description.lower():
        logger.info(f"  Mock response: PRP created with INITIAL.md and PLAN.md")
    elif "planning" in description.lower():
        logger.info(f"  Mock response: Implementation plan created, N Beads tasks ready")
    elif "execution" in description.lower() or "swarm" in description.lower():
        logger.info(f"  Mock response: Execution tasks delegated to swarm")
    elif "validation" in description.lower():
        logger.info(f"  Mock response: Validation complete, compliance verified")
    elif "git" in description.lower():
        logger.info(f"  Mock response: Git operations complete")

    return fake_session_id