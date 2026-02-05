from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from features.job_processing.models.job import Job
from features.job_processing.models.evaluation import JobEvaluation
from features.job_processing.schemas.evaluation import JobEvaluationListResponse
from features.job_processing.utils.url_parser import calculate_job_age

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/ranked")
async def get_ranked_jobs(
    limit: int = 50,
    min_score: int = 50,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[JobEvaluationListResponse]:
    query = (
        select(Job, JobEvaluation)
        .join(JobEvaluation, Job.id == JobEvaluation.job_id)
        .where(JobEvaluation.is_ai_related == 1)
        .where(JobEvaluation.score_total >= min_score)
    )

    if priority:
        query = query.where(JobEvaluation.priority == priority)

    query = query.order_by(JobEvaluation.score_total.desc()).limit(limit)

    result = await db.execute(query)
    jobs = result.all()

    return [
        JobEvaluationListResponse(
            job_id=job.id,
            title=job.title,
            url=job.url,
            budget=float(job.fixed_budget_amount) if job.fixed_budget_amount else None,
            duration_weeks=float(job.fixed_duration_weeks)
            if job.fixed_duration_weeks
            else None,
            score_total=evaluation.score_total,
            priority=evaluation.priority,
            project_type=evaluation.project_type,
            tech_stack=evaluation.tech_stack,
            matched_expertise_ids=evaluation.matched_expertise_ids,
            reasoning_summary=_summarize_reasoning(evaluation),
            applicant_count=job.applicant_count,
            interviewing_count=job.interviewing_count,
            invite_only=job.invite_only,
            client_payment_verified=job.client_payment_verified,
            client_rating=job.client_rating,
            client_jobs_posted=job.client_jobs_posted,
            client_hire_rate=job.client_hire_rate,
            client_total_paid=job.client_total_paid,
            client_hires=job.client_hires,
            client_reviews=job.client_reviews,
            experience_level=job.experience_level,
            project_length=job.project_length,
            client_response_time=job.client_response_time,
            job_age_hours=calculate_job_age(job.ts_publish)[0],
            job_age_string=calculate_job_age(job.ts_publish)[1],
            description_urls=job.description_urls or [],
        )
        for job, evaluation in jobs
    ]


@router.get("/stats")
async def get_evaluation_stats(db: AsyncSession = Depends(get_db)) -> dict:
    total_jobs = await db.scalar(select(func.count(Job.id)))
    ai_related = await db.scalar(
        select(func.count(JobEvaluation.job_id)).where(
            JobEvaluation.is_ai_related == 1
        )
    )
    high_priority = await db.scalar(
        select(func.count(JobEvaluation.job_id)).where(
            JobEvaluation.is_ai_related == 1
        ).where(JobEvaluation.priority == "High")
    )
    jobs_with_urls = await db.scalar(
        select(func.count(Job.id)).where(func.jsonb_array_length(Job.description_urls) > 0)
    )

    return {
        "total_jobs": total_jobs or 0,
        "ai_related_jobs": ai_related or 0,
        "high_priority_jobs": high_priority or 0,
        "ai_related_percentage": (ai_related / total_jobs * 100) if total_jobs else 0,
        "jobs_with_urls": jobs_with_urls or 0,
    }


def _summarize_reasoning(evaluation: JobEvaluation) -> str:
    return f"""Budget: {evaluation.reason_budget}
Tech Fit: {evaluation.reason_tech_fit}
Clarity: {evaluation.reason_clarity}"""