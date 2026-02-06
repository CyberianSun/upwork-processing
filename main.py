import asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.database import AsyncSessionLocal
from features.job_processing.routes.endpoints import router as job_router
from features.workflow.routes.endpoints import router as workflow_router

app = FastAPI(title="Upwork Job Processing API")

app.include_router(job_router)
app.include_router(workflow_router)


async def check_db_connection(max_retries: int = 30, retry_interval: float = 2.0):
    """Wait for database connection with retries."""
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
                return
        except Exception:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_interval)
    raise RuntimeError("Database connection failed after retries")


@app.on_event("startup")
async def startup():
    await check_db_connection()


@app.on_event("shutdown")
async def shutdown():
    pass


@app.get("/")
async def root():
    return {"message": "Upwork Job Processing API"}