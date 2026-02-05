import asyncio
import typer
from pathlib import Path

from core.database import AsyncSessionLocal, init_db
from core.config import settings
from core.cerebras import CerebrasClient
from features.job_processing.services.evaluator import JobEvaluator
from features.job_processing.services.ingestion import JobIngestionService


async def ingest(file_path: Path):
    await init_db()

    async with AsyncSessionLocal() as db:
        cerebras_client = CerebrasClient()
        evaluator = JobEvaluator(cerebras_client)
        ingestion_service = JobIngestionService(evaluator)

        try:
            results = await ingestion_service.ingest_apify_json(
                file_path,
                db,
                checkpoint_interval=settings.checkpoint_interval,
            )

            print("\n=== Ingestion Complete ===")
            print(f"Total jobs: {results['total_jobs']}")
            print(f"Ingested: {results['ingested']}")
            print(f"Evaluated: {results['evaluated']}")
            print(f"AI-related: {results['ai_related']}")
            print(f"Not AI-related: {results['not_ai_related']}")
            print(f"Errors: {results['errors']}")

        finally:
            await cerebras_client.close()


if __name__ == "__main__":
    import sys

    def _main(file_path: Path):
        asyncio.run(ingest(file_path))

    typer.run(_main)