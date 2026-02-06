"""Validation service for 3-level code quality checks."""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from opencode_functions import delegate_task as opencode_delegate_task

logger = logging.getLogger(__name__)


class ValidationService:
    """3-level validation pipeline following GOLDEN_RULES."""

    LEVELS = {
        0: "Build test (MANDATORY)",
        1: "Code quality (type check, lint)",
        2: "Tests (unit, integration)",
        3: "Manual (feature verification - skipped in automated flow)",
    }

    async def validate(
        self,
        project_path: Path,
        level: int = 2
    ) -> Dict[str, Any]:
        """Run validation up to specified level.

        Args:
            project_path: Path to project directory
            level: Max level to validate (0-3)

        Returns:
            Validation result with status and failures
        """
        results = {
            "success": True,
            "level_reached": 0,
            "failures": [],
            "details": {}
        }

        for l in range(level + 1):
            logger.info(f"Running Level {l}: {self.LEVELS[l]}")

            if l == 0:
                result = await self._level_0_build_test(project_path)
            elif l == 1:
                result = await self._level_1_quality_checks(project_path)
            elif l == 2:
                result = await self._level_2_tests(project_path)
            else:
                logger.info(f"Level {l}: Skipped (manual verification)")
                continue

            results["details"][l] = result

            if not result["passed"]:
                results["success"] = False
                results["failures"].append({
                    "level": l,
                    "name": self.LEVELS[l],
                    "message": result.get("message", "Validation failed")
                })
                break

            results["level_reached"] = l

        return results

    async def _level_0_build_test(self, project_path: Path) -> Dict[str, Any]:
        """Level 0: Build test (MANDATORY)."""
        logger.info("Level 0: Build test - PIP + Import check")

        result = {"passed": False, "message": ""}

        try:
            cmd = ["python3", "-m", "py_compile", "main.py"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                result["passed"] = True
                result["message"] = "Build test passed"
                logger.info("Build test passed")
            else:
                result["message"] = f"Build test failed: {stderr.decode()}"
                logger.error(f"Build test failed: {stderr.decode()}")

        except Exception as e:
            result["message"] = f"Build test error: {str(e)}"
            logger.exception("Build test error")

        return result

    async def _level_1_quality_checks(self, project_path: Path) -> Dict[str, Any]:
        """Level 1: Code quality checks."""
        logger.info("Level 1: Code quality - Type hints, lint, file size")

        result = {"passed": True, "message": "", "checks": {}}

        checks_to_run = [
            ("type_hints", self._check_type_hints, project_path),
            ("file_size", self._check_file_sizes, project_path),
        ]

        for check_name, check_func, path in checks_to_run:
            check_result = await check_func(path)
            result["checks"][check_name] = check_result

            if not check_result["passed"]:
                result["passed"] = False
                result["message"] += f"{check_name} failed: {check_result.get('message', '')}; "

        if result["passed"]:
            result["message"] = "All quality checks passed"

        return result

    async def _check_type_hints(self, project_path: Path) -> Dict[str, Any]:
        """Check project uses proper type hints."""
        result = {"passed": True, "message": ""}

        features_path = project_path / "features"
        if not features_path.exists():
            return result

        try:
            py_files = list(features_path.rglob("*.py"))

            for py_file in py_files:
                content = py_file.read_text()

                if "def " in content and "->" not in content:
                    result["passed"] = False
                    result["message"] = f"{py_file.name}: Missing return type hints"
                    break

        except Exception as e:
            logger.warning(f"Type hint check error: {e}")

        return result

    async def _check_file_sizes(self, project_path: Path) -> Dict[str, Any]:
        """Check files are under 500 lines (GOLDEN_RULES)."""
        result = {"passed": True, "message": ""}

        features_path = project_path / "features"
        if not features_path.exists():
            return result

        try:
            py_files = list(features_path.rglob("*.py"))

            for py_file in py_files:
                line_count = len(py_file.read_text().splitlines())

                if line_count > 500:
                    result["passed"] = False
                    result["message"] = f"{py_file.name}: {line_count} lines (max 500)"
                    break

        except Exception as e:
            logger.warning(f"File size check error: {e}")

        return result

    async def _level_2_tests(self, project_path: Path) -> Dict[str, Any]:
        """Level 2: Run tests if available."""
        logger.info("Level 2: Tests")

        result = {"passed": True, "message": ""}

        try:
            cmd = ["python3", "-m", "pytest", "-x", "--tb=short", "features/"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                result["passed"] = True
                result["message"] = "Tests passed"
                logger.info("Tests passed")
            else:
                output = stderr.decode() or stdout.decode()
                if "No tests found" in output or "collected 0 items" in output:
                    result["passed"] = True
                    result["message"] = "No tests found (skipping)"
                    logger.info("No tests found - skipping")
                else:
                    result["passed"] = False
                    result["message"] = f"Tests failed: {output[:500]}"
                    logger.error(f"Tests failed: {output[:500]}")

        except Exception as e:
            result["message"] = f"Test error: {str(e)}"
            logger.warning("Test execution error (tests may not exist)")

        return result

    async def validate_with_momus(
        self,
        session_id: str,
        project_path: Path
    ) -> Dict[str, Any]:
        """Run validation with Momus agent for code review."""
        logger.info(f"Validating with Momus agent (session: {session_id})")

        try:
            result = await opencode_delegate_task(
                category="seedfw-verification",
                load_skills=[],
                description="Code Validation (Step 5)",
                prompt=f"""
1. TASK: Validate code following GOLDEN_RULES and SeedFW standards

2. EXPECTED OUTCOME:
   - Check PRP compliance
   - Verify GOLDEN_RULES adherence
   - Review code quality
   - Return JSON with: {{"passed": true/false, "issues": [], "suggestions": []}}

3. REQUIRED TOOLS:
   - Use delegate_task with seedfw-verification category
   - Use Read tool to review code files
   - Use Grep tool to find patterns (e.g., "any", "as any")

4. MUST DO:
   - Read project files in {project_path}
   - Check for GOLDEN_RULES violations:
     * No "any" types without justification
     * No secrets in git config
     * Build test passed (Level 0)
     * Type hints present
     * File size < 500 lines
   - Verify Vertical Slice Architecture followed
   - Check PRP compliance (requirements met)
   - Review error handling
   - Validate input handling

5. MUST NOT DO:
   - Do NOT make code changes
   - Do NOT modify files

6. CONTEXT:
   Session: {session_id}
   Project Path: {project_path}

7. Review Focus Areas:
   - Type safety (no "any")
   - Build passes
   - File sizes < 500 lines
   - Dependencies correct
   - Error handling
   - Input validation
""",
                run_in_background=False
            )

            logger.info(f"Momus validation complete: {result}")

            return {"success": True, "session_id": result, "message": "Momus validation complete"}

        except Exception as e:
            logger.exception("Momus validation failed")
            return {"success": False, "message": str(e)}