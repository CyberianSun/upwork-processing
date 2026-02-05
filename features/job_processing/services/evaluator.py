from .models.job import Job
from .models.evaluation import JobEvaluation
from .schemas.evaluation import (
    JobEvaluationRequest,
    JobEvaluationResponse,
    ScoreBreakdown,
)
from core.cerebras import CerebrasClient
from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession


class JobEvaluator:
    def __init__(self, cerebras_client: CerebrasClient):
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
2. Client Reliability (15%): 10 if verified/hires>10%, 7 if some activity, 3 if new/unknown, 0 if suspicious
3. Requirements Clarity (20%): 10 if specific/actionable, 7 if clear but vague, 3 if ambiguous, 0 if nonsensical
4. AI Technical Fit (30%): 10 if matches 3+ expertise areas, 7 if matches 2, 3 if matches 1, 0 if no match
5. Timeline Realism (10%): 10 if realistic, 7 if slightly tight, 3 if unrealistic, 0 if impossible

TOTAL SCORE = weighted sum (budget*2.5 + client*1.5 + clarity*2.0 + tech_fit*3.0 + timeline*1.0)

PRIORITY CLASSIFICATION:
- High: score_total ≥ 80
- Medium: 50 ≤ score_total < 80
- Low: score_total < 50

EXPERTISE MATCH FORMAT:
Match expertise only when job description explicitly mentions related keywords or concepts.

OUTPUT RULES:
- Return valid JSON matching the provided schema
- is_ai_related=false → set filter_reason, skip other fields
- is_ai_related=true → fill all fields
- Provide clear, concise reasoning for each score"""

    async def evaluate_job(
        self,
        job: Job,
        db: AsyncSession,
    ) -> Optional[JobEvaluation]:
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
                    filter_reason=response.filter_reason,
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
                evaluation = JobEvaluation(
                    job_id=job.id,
                    is_ai_related=1,
                    filter_reason=None,
                    tech_stack=response.tech_stack,
                    project_type=response.project_type,
                    complexity=response.complexity,
                    matched_expertise_ids=[
                        m.expertise_id for m in response.matched_expertise
                    ],
                    score_budget=response.scores["budget"].score,
                    score_client=response.scores["client"].score,
                    score_clarity=response.scores["clarity"].score,
                    score_tech_fit=response.scores["tech_fit"].score,
                    score_timeline=response.scores["timeline"].score,
                    score_total=response.score_total,
                    reason_budget=response.scores["budget"].reasoning,
                    reason_client=response.scores["client"].reasoning,
                    reason_clarity=response.scores["clarity"].reasoning,
                    reason_tech_fit=response.scores["tech_fit"].reasoning,
                    reason_timeline=response.scores["timeline"].reasoning,
                    priority=response.priority,
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

        return f"""Evaluate this Upwork job:

Title: {request.title}
Type: {request.type}
{budget_info}

Description:
{request.description}

URL: {request.url}

Provide a detailed evaluation as JSON."""