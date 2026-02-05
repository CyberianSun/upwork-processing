from typing import Optional

from ..models.job import Job
from ..models.evaluation import JobEvaluation
from ..schemas.evaluation import (
    JobEvaluationRequest,
    JobEvaluationResponse,
)
from core.cerebras import CerebrasClient
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession


class JobEvaluator:
    """Evaluates Upwork jobs against AI Systems Engineer criteria using Cerebras GLM 4.7."""

    def __init__(self, cerebras_client: CerebrasClient):
        """Initialize evaluator with Cerebras client."""
        self.client = cerebras_client
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are an expert job evaluator for an AI Systems Engineer.
You evaluate Upwork jobs against the following profile:

EXPERTISE AREAS:
1. AI Agent Architecture & Design (Expert): agent, autonomous, multi-agent, LangChain, crewAI
2. RAG Systems (Advanced): RAG, retrieval, vector database, embeddings, semantic search
3. Local AI Infrastructure (Expert): local LLM, ollama, LM Studio, self-hosted, on-premises, privacy
4. Backend Systems (Expert): FastAPI, Python, PostgreSQL, pgvector, REST API, async
5. Frontend Development (Advanced): React, TypeScript, Next.js, UI, web app
6. DevOps & Infrastructure (Expert): Docker, deployment, CI/CD
7. Voice & Real-Time AI (Advanced): voice, audio, Speech-to-Text, text-to-speech, WebRTC, Deepgram
8. Testing & Code Quality (Intermediate-Advanced): testing, pytest, TDD, code quality, CI

EVALUATION CRITERIA (score 0-10 for each):
1. Budget Adequacy (25%): 10 if ≥$500 and matches scope, 0 if <$500 or mismatches wildly
2. Client Reliability (15%): Evaluate using:
   - Payment verification (verified=bonus)
   - Client rating (4.5+=bonus, 4.0-4.5=ok, <4.0=penalty)
   - Hire rate (>20%=bonus, 10-20%=ok, <10%=penalty)
   - Total paid amount (>1000=bonus, 0=penalty)
3. Requirements Clarity (20%): 10 if specific/actionable, 7 if clear but vague, 3 if ambiguous, 0 if nonsensical
4. AI Technical Fit (30%): 10 if matches 3+ expertise areas, 7 if matches 2, 3 if matches 1, 0 if no match
5. Competition & Freshness (10%): Evaluate using:
   - Applicant count (<5=bonus, 5-15=neutral, >20=penalty)
   - Job age (<24h=bonus, <72h=neutral, >1w=penalty)

SCORE TO JSON FIELD MAPPING:
- score_budget maps to "score_budget"
- score_client maps to "score_client"
- score_clarity maps to "score_clarity"
- score_tech_fit maps to "score_tech_fit"
- Competition score maps to "score_timeline" (JSON output field name)

TOTAL SCORE = weighted sum (budget*2.5 + client*1.5 + clarity*2.0 + tech_fit*3.0 + competition*1.0)

PRIORITY CLASSIFICATION:
- High: score_total ≥ 80
- Medium: 50 ≤ score_total < 80
- Low: score_total < 50

EXPERTISE MATCH FORMAT:
Match expertise only when job description explicitly mentions related keywords or concepts.

OUTPUT RULES:
- Return valid JSON matching the exact field names: is_ai_related, tech_stack, project_type, complexity, matched_expertise (array with expertise_id and match_reason), score_budget, reason_budget, score_client, reason_client, score_clarity, reason_clarity, score_tech_fit, reason_tech_fit, score_timeline, reason_timeline, score_total, priority
- is_ai_related=false → set filter_reason, other fields can be omitted
- is_ai_related=true → fill all fields
- complexity must be: Low, Medium, or High
- priority must be: High, Medium, or High
- expertise_id must be 1-8 corresponding to expertise area
- Provide clear, concise reasoning for each score"""

    async def evaluate_job(
        self,
        job: Job,
        db: AsyncSession,
    ) -> Optional[JobEvaluation]:
        """Evaluate a job using AI and store results in database.

        Args:
            job: Job to evaluate
            db: Database session

        Returns:
            JobEvaluation if stored, None if job already evaluated
        """
        request = JobEvaluationRequest(
            job_id=job.id,
            title=job.title,
            description=job.description,
            type=job.type,
            url=job.url,
            fixed_budget_amount=float(job.fixed_budget_amount)
            if job.fixed_budget_amount
            else None,
            fixed_duration_weeks=float(job.fixed_duration_weeks)
            if job.fixed_duration_weeks
            else None,
            hourly_min=float(job.hourly_min) if job.hourly_min else None,
            hourly_max=float(job.hourly_max) if job.hourly_max else None,
            # Competition metrics
            applicant_count=job.applicant_count or 0,
            interviewing_count=job.interviewing_count or 0,
            invite_only=job.invite_only or False,
            # Client quality
            client_payment_verified=job.client_payment_verified or False,
            client_rating=float(job.client_rating) if job.client_rating else None,
            client_jobs_posted=job.client_jobs_posted or 0,
            client_hire_rate=float(job.client_hire_rate) if job.client_hire_rate else None,
            client_total_paid=float(job.client_total_paid) if job.client_total_paid else None,
            client_hires=job.client_hires or 0,
            client_reviews=job.client_reviews or 0,
            # Job specifics
            experience_level=job.experience_level,
            project_length=job.project_length,
            # Job age
            job_age_hours=job.job_age_hours or 0,
            job_age_string=job.job_age_string or "",
            # URLs
            description_urls=job.description_urls or [],
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._build_user_prompt(request)},
        ]

        try:
            response = await self.client.chat_completion(
                messages=messages,
                response_model=JobEvaluationResponse,
            )

            if not response.is_ai_related:
                evaluation = JobEvaluation(
                    job_id=job.id,
                    is_ai_related=0,
                    filter_reason=response.filter_reason or "Not AI-related",
                    tech_stack=[],
                    project_type="",
                    complexity="",
                    matched_expertise_ids=[],
                    score_budget=0,
                    score_client=0,
                    score_clarity=0,
                    score_tech_fit=0,
                    score_timeline=0,
                    score_total=0,
                    reason_budget="",
                    reason_client="",
                    reason_clarity="",
                    reason_tech_fit="",
                    reason_timeline="",
                    priority="Low",
                )
            else:
                tech_stack_list = []
                if isinstance(response.tech_stack, str):
                    tech_stack_list = [t.strip() for t in response.tech_stack.split(",")]
                else:
                    tech_stack_list = response.tech_stack or []

                score_total = int(response.computed_score_total) if response.computed_score_total else 0

                evaluation = JobEvaluation(
                    job_id=job.id,
                    is_ai_related=1,
                    filter_reason=None,
                    tech_stack=tech_stack_list,
                    project_type=response.project_type or "",
                    complexity=response.complexity or "",
                    matched_expertise_ids=[
                        m.expertise_id for m in (response.matched_expertise or [])
                    ],
                    score_budget=response.score_budget or 0,
                    score_client=response.score_client or 0,
                    score_clarity=response.score_clarity or 0,
                    score_tech_fit=response.score_tech_fit or 0,
                    score_timeline=response.score_timeline or 0,
                    score_total=score_total,
                    reason_budget=response.reason_budget or "",
                    reason_client=response.reason_client or "",
                    reason_clarity=response.reason_clarity or "",
                    reason_tech_fit=response.reason_tech_fit or "",
                    reason_timeline=response.reason_timeline or "",
                    priority=response.priority or "Medium",
                )

            db.add(evaluation)
            await db.commit()

            return evaluation

        except Exception as e:
            await db.rollback()
            raise

    def _build_user_prompt(self, request: JobEvaluationRequest) -> str:
        budget_info = ""
        if request.type == "FIXED":
            budget_info = (
                f"Budget: ${request.fixed_budget_amount}, "
                f"Duration: {request.fixed_duration_weeks} weeks"
            )
        else:
            budget_info = (
                f"Hourly Rate: ${request.hourly_min} - ${request.hourly_max}/hr"
            )

        client_info = []
        if request.client_payment_verified:
            client_info.append("Payment Verified: Yes")
        if request.client_rating:
            client_info.append(f"Client Rating: {request.client_rating}/5.0")
        if request.client_hire_rate:
            client_info.append(f"Hire Rate: {request.client_hire_rate}%")
        if request.client_total_paid:
            client_info.append(f"Total Paid: ${request.client_total_paid:,.0f}")
        if request.client_jobs_posted:
            client_info.append(f"Jobs Posted: {request.client_jobs_posted}")

        competition_info = []
        competition_info.append(f"Applicants: {request.applicant_count}")
        competition_info.append(f"Interviewing: {request.interviewing_count}")
        if request.invite_only:
            competition_info.append("Invite Only: Yes")
        competition_info.append(f"Posted: {request.job_age_string}")

        urls_section = ""
        if request.description_urls:
            urls_section = f"\nURLs in Description ({len(request.description_urls)}):\n" + \
                           "\n".join(f"  - {url}" for url in request.description_urls[:5])
            if len(request.description_urls) > 5:
                urls_section += f"\n  ... and {len(request.description_urls) - 5} more"

        return f"""Evaluate this Upwork job:

Title: {request.title}
Type: {request.type}
{budget_info}

{', '.join(client_info) if client_info else 'Client Info: Not available'}

Competition:
{', '.join(competition_info)}

Description:
{request.description}
{urls_section}

URL: {request.url}

Provide a detailed evaluation as JSON."""