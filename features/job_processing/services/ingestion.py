import orjson
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..models.job import Job
from ..utils.url_parser import extract_urls, calculate_job_age
from .evaluator import JobEvaluator
from sqlalchemy.ext.asyncio import AsyncSession


class JobIngestionService:
    def __init__(self, evaluator: JobEvaluator):
        self.evaluator = evaluator

    async def ingest_apify_json(
        self,
        file_path: Path,
        db: AsyncSession,
        checkpoint_interval: int = 10,
    ) -> Dict[str, int]:
        with open(file_path, "rb") as f:
            content = f.read()
            data = orjson.loads(content)

        results = {
            "total_jobs": 0,
            "ingested": 0,
            "evaluated": 0,
            "ai_related": 0,
            "not_ai_related": 0,
            "errors": 0,
        }

        results["total_jobs"] = len(data)

        for idx, job_data in enumerate(data):
            try:
                job = self._parse_job_data(job_data)

                existing = await db.get(Job, job.id)
                if existing:
                    # Update job metadata even if already ingested
                    existing.job_age_hours = job.job_age_hours
                    existing.job_age_string = job.job_age_string
                    existing.applicant_count = job.applicant_count
                    existing.interviewing_count = job.interviewing_count
                    existing.invite_only = job.invite_only
                    existing.client_payment_verified = job.client_payment_verified
                    existing.client_rating = job.client_rating
                    existing.client_jobs_posted = job.client_jobs_posted
                    existing.client_hire_rate = job.client_hire_rate
                    existing.client_total_paid = job.client_total_paid
                    existing.client_hires = job.client_hires
                    existing.client_reviews = job.client_reviews
                    existing.experience_level = job.experience_level
                    existing.project_length = job.project_length
                    existing.proposal_required = job.proposal_required
                    existing.client_response_time = job.client_response_time
                    existing.description_urls = job.description_urls
                    existing.updated_at = datetime.utcnow()
                    await db.commit()
                    results["ingested"] += 1
                else:
                    db.add(job)
                    await db.commit()
                    await db.refresh(job)
                    results["ingested"] += 1

                from ..models.evaluation import JobEvaluation
                from sqlalchemy import select
                existing_eval = await db.execute(
                    select(JobEvaluation).where(JobEvaluation.job_id == job.id)
                )
                existing_record = existing_eval.scalar_one_or_none()

                if existing_record:
                    print(f"  → Already evaluated, skipping")
                    results["evaluated"] += 1
                    if existing_record.is_ai_related:
                        results["ai_related"] += 1
                    else:
                        results["not_ai_related"] += 1
                else:
                    print(f"Evaluating job {idx + 1}: {job.title[:50]}...")
                    try:
                        evaluation = await self.evaluator.evaluate_job(job, db)

                        if evaluation:
                            results["evaluated"] += 1
                            if evaluation.is_ai_related:
                                results["ai_related"] += 1
                            else:
                                results["not_ai_related"] += 1

                            print(f"  → Score: {evaluation.score_total}/100, Priority: {evaluation.priority}")
                    except Exception as eval_error:
                        import httpx
                        if isinstance(eval_error, httpx.HTTPStatusError) and eval_error.response.status_code == 502:
                            print(f"  → API unavailable (502), will retry in next run")
                        else:
                            raise

                if (idx + 1) % checkpoint_interval == 0:
                    print(f"Checkpoint: {idx + 1}/{len(data)} jobs processed")

            except Exception as e:
                results["errors"] += 1
                import traceback
                traceback.print_exc()
                await db.rollback()

        return results

    def _parse_job_data(self, job_data: Dict[str, Any]) -> Job:
        budget_amount = None
        duration_weeks = None

        if "fixed" in job_data and job_data["fixed"]:
            fixed = job_data["fixed"]
            if "budget" in fixed and fixed["budget"]:
                budget_amount = float(fixed["budget"]["amount"])
            if "duration" in fixed and fixed["duration"]:
                duration_rid = fixed["duration"].get("rid")
                duration_weeks = self._map_duration_rid_to_weeks(duration_rid)

        ts_publish = self._parse_timestamp(job_data.get("ts_publish"))
        scraped_at = self._parse_timestamp(job_data.get("scraped_at"))

        # Calculate job age
        description = job_data.get("description", "")
        job_age_hours, job_age_str = calculate_job_age(ts_publish) if ts_publish else (0, "")

        # Extract URLs from description
        urls = extract_urls(description)

        # Get client data (default to 0/None if not available)
        client_data = job_data.get("client_info", {})
        client_secondary = job_data.get("client_secondary_info", {})

        return Job(
            id=job_data["id"],
            title=job_data["title"],
            ts_publish=ts_publish,
            description=description,
            type=job_data.get("type", "FIXED"),
            url=job_data["url"],
            fixed_budget_amount=budget_amount,
            fixed_duration_weeks=duration_weeks,
            job_age_hours=job_age_hours,
            job_age_string=job_age_str,
            applicant_count=job_data.get("applicant_count", 0),
            interviewing_count=job_data.get("interviewing_count", 0),
            invite_only=job_data.get("invite_only", False),
            client_payment_verified=job_data.get("payment_verified", False),
            client_rating=job_data.get("client_rating"),
            client_jobs_posted=job_data.get("client_jobs_posted", 0),
            client_hire_rate=job_data.get("client_hire_rate"),
            client_total_paid=job_data.get("client_total_paid"),
            client_hires=job_data.get("client_hires", 0),
            client_reviews=job_data.get("client_reviews", 0),
            experience_level=job_data.get("experience_level"),
            project_length=job_data.get("project_length"),
            proposal_required=job_data.get("proposal_required", False),
            client_response_time=job_data.get("client_response_time"),
            description_urls=urls,
            source="apify",
            scraped_at=scraped_at,
        )

    def _map_duration_rid_to_weeks(self, rid: int | None) -> float | None:
        if rid is None:
            return None

        mapping = {
            1: 52.0,
            2: 18.0,
            3: 9.0,
            4: 3.0,
        }

        return mapping.get(rid)

    def _parse_timestamp(self, ts: str | None) -> datetime | None:
        if ts is None:
            return None

        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        except (ValueError, AttributeError):
            return None