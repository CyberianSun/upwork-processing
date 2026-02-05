import orjson
from pathlib import Path
from typing import Dict, Any

from features.job_processing.models.job import Job
from features.job_processing.services.evaluator import JobEvaluator
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
            data = orjson.load(f)

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
                    results["ingested"] += 1
                else:
                    db.add(job)
                    await db.commit()
                    await db.refresh(job)
                    results["ingested"] += 1

                evaluation = await self.evaluator.evaluate_job(job, db)

                if evaluation:
                    results["evaluated"] += 1
                    if evaluation.is_ai_related:
                        results["ai_related"] += 1
                    else:
                        results["not_ai_related"] += 1

                if (idx + 1) % checkpoint_interval == 0:
                    print(f"Processed {idx + 1}/{len(data)} jobs")

            except Exception as e:
                results["errors"] += 1
                print(f"Error processing job {idx}: {e}")
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

        return Job(
            id=job_data["id"],
            title=job_data["title"],
            ts_publish=job_data["ts_publish"],
            description=job_data["description"],
            type=job_data.get("type", "FIXED"),
            url=job_data["url"],
            fixed_budget_amount=budget_amount,
            fixed_duration_weeks=duration_weeks,
            source="apify",
            scraped_at=job_data.get("scraped_at"),
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