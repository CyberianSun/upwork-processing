<!-- OpenSpec Change Proposal: Job Processing Feature -->
<!-- Project: upwork-processing -->
<!-- Date: 2026-02-05 -->

# OpenSpec Change Proposal

## Feature Name

`job-processing` - Upwork Job AI Evaluation System

## Priority

High (MVP feature for core business value)

## Summary

Add AI-powered job evaluation capability to automatically assess Upwork opportunities against the AI Systems Engineer profile. System ingests Apify job data, uses Cerebras GLM 4.7 to extract structured data and score 5 evaluation criteria, stores results in PostgreSQL, and provides ranked job suggestions with reasoning.

## Motivation

Currently, job evaluation is manual and time-consuming. AI automation will:
- Process 1000+ jobs/day automatically
- Identify viable opportunities (≥$500) matching expertise profile
- Provide consistent, transparent scoring with reasoning
- Store structured data for analysis and filtering

## Technical Approach

- Single-pass AI evaluation (one request per job)
- Pydantic-structured AI output (validated on response)
- Async architecture with rate limiting (2 req/s, 2 concurrent)
- PostgreSQL storage for jobs and evaluations
- Programmatic ranking by `score_total`

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.104+ | Web framework |
| SQLAlchemy | 2.0+ | Async ORM |
| Alembic | 1.13+ | Migrations |
| PostgreSQL | 16+ | Database |
| pgvector | 0.5+ | Vector extension (future use) |
| Cerebras GLM 4.7 SDK | Latest | AI evaluation |
| Pydantic | 2.5+ | Data validation |
| asyncpg | 0.29+ | Async PostgreSQL driver |

## Success Criteria

1. Ingest Apify JSON files and transform schema
2. Evaluate jobs with AI (single-pass, structured output)
3. Store evaluations in PostgreSQL
4. Rank jobs programmatically by score
5. Output ranked list with reasoning

---

# Implementation Tasks

## Phase 1: Infrastructure and Setup

### Task 1.1: Project Structure (SeedFW VSA)

**Time**: 15 minutes | **Priority**: High

Create directory structure following SeedFW Vertical Slice Architecture:

```
home/mishka/Documents/projects/upwork-processing/
├── .git/
├── .gitignore
├── pyproject.toml
├── README.md
├── docker-compose.yml
├── features/
│   ├── __init__.py
│   └── job_processing/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── job.py (ORM models)
│       │   └── evaluation.py (ORM models)
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── job.py (Pydantic schemas)
│       │   └── evaluation.py (Pydantic schemas)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── ingestion.py (Apify JSON ingestion)
│       │   └── evaluator.py (AI evaluation service)
│       └── routes/
│           ├── __init__.py
│           └── endpoints.py (FastAPI routes)
├── core/
│   ├── __init__.py
│   ├── config.py (Settings, pydantic-settings)
│   ├── database.py (Async SQLAlchemy engine)
│   └── cerebras.py (Cerebras GLM 4.7 client)
├── migrations/
│   └── versions/
├── tests/
│   ├── __init__.py
│   └── features/
│       └── test_job_processing.py
└── main.py (FastAPI app entry point)
```

### Task 1.2: Dependencies and Configuration

**Time**: 10 minutes | **Priority**: High

Create `pyproject.toml` with all dependencies:

```toml
[project]
name = "upwork-processing"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.23",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.25.2",
    "orjson>=3.9.10",
    "structlog>=23.2.0",
    "python-dotenv>=1.0.0",
]

[tool.black]
line-length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Create `.env.example`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/upwork_processing

# Cerebras GLM 4.7
CEREBRAS_API_KEY=your_api_key_here
CEREBRAS_MODEL=glm-4.7

# Rate Limiting
RATE_LIMIT_REQUESTS=2
RATE_LIMIT_CONCURRENT=2
API_TIMEOUT=30

# Evaluation
FILTER_BUDGET_MIN=500
CHECKPOINT_INTERVAL=10

# Logging
LOG_LEVEL=INFO
```

### Task 1.3: Database Setup

**Time**: 30 minutes | **Priority**: High

Create `core/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(
    settings.database_url,
    echo=settings.log_level == "DEBUG",
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

Create initial migration (Alembic init):
```bash
alembic init migrations
```

### Task 1.4: Cerebras Client

**Time**: 20 minutes | **Priority**: High

Create `core/cerebras.py`:

```python
import httpx
import asyncio
from typing import Any, TypeVar
from pydantic import BaseModel

from core.config import settings

T = TypeVar("T", bound=BaseModel)

class CerebrasClient:
    def __init__(self):
        self.api_key = settings.cerebras_api_key
        self.model = settings.cerebras_model
        self.base_url = "https://api.cerebras.ai/v1"
        self._client: httpx.AsyncClient | None = None

        # Rate limiting
        self._semaphore = asyncio.Semaphore(settings.rate_limit_concurrent)
        self._request_lock = asyncio.Lock()
        self._last_request_time = 0
        self._min_request_interval = 1.0 / settings.rate_limit_requests

    async def _client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=settings.api_timeout,
            )
        return self._client

    async def _rate_limit(self):
        async with self._request_lock:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
            self._last_request_time = asyncio.get_event_loop().time()

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        response_model: type[T],
    ) -> T:
        async with self._semaphore:
            await self._rate_limit()

            client = await self._client()
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,  # Low temperature for consistent scoring
                },
            )

            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            return response_model.model_validate_json(content)

    async def close(self):
        if self._client:
            await self._client.aclose()
```

---

## Phase 2: Data Models and Schemas

### Task 2.1: Database Models

**Time**: 20 minutes | **Priority**: High

Create `features/job_processing/models/job.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # Apify job ID
    title = Column(String, nullable=False)
    ts_publish = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # "FIXED" or "HOURLY"
    url = Column(String, unique=True, nullable=False)

    # Fixed budget fields
    fixed_budget_amount = Column(Numeric(10, 2), nullable=True)
    fixed_duration_weeks = Column(Numeric(5, 1), nullable=True)

    # Hourly fields
    hourly_min = Column(Numeric(10, 2), nullable=True)
    hourly_max = Column(Numeric(10, 2), nullable=True)

    # Metadata
    source = Column(String, nullable=False, default="apify")
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Create `features/job_processing/models/evaluation.py`:

```python
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PGArray
from sqlalchemy.orm import relationship

from core.database import Base

class JobEvaluation(Base):
    __tablename__ = "job_evaluations"

    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)

    # Filter
    is_ai_related = Column(Integer, nullable=False)  # 0 or 1 (boolean)
    filter_reason = Column(Text, nullable=True)

    # Extracted
    tech_stack = Column(JSONB, nullable=False, default=list)
    project_type = Column(String, nullable=False)
    complexity = Column(String, nullable=False)
    matched_expertise_ids = Column(PGArray(SmallInteger), nullable=False, default=list)

    # Scores (0-10)
    score_budget = Column(SmallInteger, nullable=False)
    score_client = Column(SmallInteger, nullable=False)
    score_clarity = Column(SmallInteger, nullable=False)
    score_tech_fit = Column(SmallInteger, nullable=False)
    score_timeline = Column(SmallInteger, nullable=False)
    score_total = Column(SmallInteger, nullable=False)  # 0-100

    # Reasoning
    reason_budget = Column(Text, nullable=False)
    reason_client = Column(Text, nullable=False)
    reason_clarity = Column(Text, nullable=False)
    reason_tech_fit = Column(Text, nullable=False)
    reason_timeline = Column(Text, nullable=False)

    # Computed
    priority = Column(String, nullable=False)
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="evaluation")

# Add relationship to Job
Job.evaluation = relationship("JobEvaluation", back_populates="job", uselist=False, cascade="all, delete-orphan")
```

Create `features/job_processing/models/expertise.py`:

```python
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY as PGArray

from core.database import Base

class ExpertiseArea(Base):
    __tablename__ = "expertise_areas"

    id = Column(SmallInteger, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    level = Column(String, nullable=False)
    keywords = Column(PGArray(String), nullable=False, default=list)
```

### Task 2.2: Pydantic Schemas

**Time**: 20 minutes | **Priority**: High

Create `features/job_processing/schemas/evaluation.py`:

```python
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExpertiseMatch(BaseModel):
    """Matched expertise areas with reasoning"""
    expertise_id: int = Field(..., ge=1, le=8, description="Expertise area ID 1-8")
    match_reason: str = Field(..., description="Why this expertise matches")

class ScoreBreakdown(BaseModel):
    """Individual criterion scores with reasoning"""
    score: int = Field(..., ge=0, le=10, description="Score 0-10")
    reasoning: str = Field(..., description="AI reasoning for this score")

class JobEvaluationRequest(BaseModel):
    """Input to AI evaluation"""
    job_id: str
    title: str
    description: str
    type: str
    url: str
    fixed_budget_amount: Optional[float] = None
    fixed_duration_weeks: Optional[float] = None
    hourly_min: Optional[float] = None
    hourly_max: Optional[float] = None

class JobEvaluationResponse(BaseModel):
    """Complete AI evaluation output (validated from Cerebras)"""
    is_ai_related: bool = Field(..., description="Is this job related to AI/LLM systems?")
    filter_reason: Optional[str] = Field(None, description="Reason if not AI-related")

    # Extracted structured data
    tech_stack: List[str] = Field(default_factory=list, description="Technologies mentioned")
    project_type: str = Field(..., description="Project type: AI Agent, RAG System, Voice AI, or Other")
    complexity: str = Field(..., description="Complexity: Low, Medium, High")
    matched_expertise: List[ExpertiseMatch] = Field(default_factory=list, description="Matched expertise areas")

    # Scores (0-10) and reasoning
    scores: Dict[str, ScoreBreakdown] = Field(
        ...,
        description="Scores for: budget, client, clarity, tech_fit, timeline"
    )

    # Computed
    score_total: int = Field(..., ge=0, le=100, description="Total score 0-100 (weighted)")
    priority: str = Field(..., description="Priority: High, Medium, Low")

class JobEvaluationListResponse(BaseModel):
    """Ranked list of evaluated jobs"""
    job_id: str
    title: str
    url: str
    budget: Optional[float]
    duration_weeks: Optional[float]
    score_total: int
    priority: str
    project_type: str
    tech_stack: List[str]
    matched_expertise_ids: List[int]
    reasoning_summary: str
```

---

## Phase 3: Core Services

### Task 3.1: AI Evaluation Service

**Time**: 45 minutes | **Priority**: High

Create `features/job_processing/services/evaluator.py`:

```python
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
            fixed_budget_amount=float(job.fixed_budget_amount) if job.fixed_budget_amount else None,
            fixed_duration_weeks=float(job.fixed_duration_weeks) if job.fixed_duration_weeks else None,
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
                # Mark as not AI-related, don't store detailed evaluation
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
                    matched_expertise_ids=[m.expertise_id for m in response.matched_expertise],
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
            budget_info = f"Budget: ${request.fixed_budget_amount}, Duration: {request.fixed_duration_weeks} weeks"
        else:
            budget_info = f"Hourly Rate: ${request.hourly_min} - ${request.hourly_max}/hr"

        return f"""Evaluate this Upwork job:

Title: {request.title}
Type: {request.type}
{budget_info}

Description:
{request.description}

URL: {request.url}

Provide a detailed evaluation as JSON."""
```

### Task 3.2: Ingestion Service

**Time**: 30 minutes | **Priority**: High

Create `features/job_processing/services/ingestion.py`:

```python
import orjson
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models.job import Job
from .evaluator import JobEvaluator
from core.cerebras import CerebrasClient

class JobIngestionService:
    def __init__(self, evaluator: JobEvaluator):
        self.evaluator = evaluator

    async def ingest_apify_json(
        self,
        file_path: Path,
        db: AsyncSession,
        checkpoint_interval: int = 10,
    ) -> Dict[str, int]:
        """Ingest Apify JSON file and evaluate jobs"""
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
                # Parse and transform job data
                job = self._parse_job_data(job_data)

                # Check if job already exists (by ID)
                existing = await db.get(Job, job.id)
                if existing:
                    results["ingested"] += 1
                else:
                    db.add(job)
                    await db.commit()
                    await db.refresh(job)
                    results["ingested"] += 1

                # Evaluate
                evaluation = await self.evaluator.evaluate_job(job, db)

                if evaluation:
                    results["evaluated"] += 1
                    if evaluation.is_ai_related:
                        results["ai_related"] += 1
                    else:
                        results["not_ai_related"] += 1

                # Checkpoint
                if (idx + 1) % checkpoint_interval == 0:
                    print(f"Processed {idx + 1}/{len(data)} jobs")

            except Exception as e:
                results["errors"] += 1
                print(f"Error processing job {idx}: {e}")
                await db.rollback()

        return results

    def _parse_job_data(self, job_data: Dict[str, Any]) -> Job:
        """Parse Apify job data into ORM model"""
        # Extract budget
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
        """Map Apify duration rid to weeks"""
        if rid is None:
            return None

        mapping = {
            1: 52.0,  # More than 6 months
            2: 18.0,  # 3 to 6 months
            3: 9.0,   # 1 to 3 months
            4: 3.0,   # Less than 1 month
        }

        return mapping.get(rid)
```

---

## Phase 4: API and CLI

### Task 4.1: FastAPI Routes

**Time**: 20 minutes | **Priority**: High

Create `features/job_processing/routes/endpoints.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from .models.job import Job
from .models.evaluation import JobEvaluation
from .schemas.evaluation import JobEvaluationListResponse
from .services.evaluator import JobEvaluator
from .services.ingestion import JobIngestionService

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("/ranked")
async def get_ranked_jobs(
    limit: int = 50,
    min_score: int = 50,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[JobEvaluationListResponse]:
    """Get ranked jobs by fit score"""
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
            duration_weeks=float(job.fixed_duration_weeks) if job.fixed_duration_weeks else None,
            score_total=evaluation.score_total,
            priority=evaluation.priority,
            project_type=evaluation.project_type,
            tech_stack=evaluation.tech_stack,
            matched_expertise_ids=evaluation.matched_expertise_ids,
            reasoning_summary=self._summarize_reasoning(evaluation),
        )
        for job, evaluation in jobs
    ]

@router.get("/stats")
async def get_evaluation_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """Get evaluation statistics"""
    total_jobs = await db.scalar(select(func.count(Job.id)))
    ai_related = await db.scalar(
        select(func.count(JobEvaluation.job_id))
        .where(JobEvaluation.is_ai_related == 1)
    )
    high_priority = await db.scalar(
        select(func.count(JobEvaluation.job_id))
        .where(JobEvaluation.is_ai_related == 1)
        .where(JobEvaluation.priority == "High")
    )

    return {
        "total_jobs": total_jobs or 0,
        "ai_related_jobs": ai_related or 0,
        "high_priority_jobs": high_priority or 0,
        "ai_related_percentage": (ai_related / total_jobs * 100) if total_jobs else 0,
    }

def _summarize_reasoning(evaluation: JobEvaluation) -> str:
    return f"""Budget: {evaluation.reason_budget}
Tech Fit: {evaluation.reason_tech_fit}
Clarity: {evaluation.reason_clarity}
"""
```

Create `main.py`:

```python
from fastapi import FastAPI
from core.database import init_db
from features.job_processing.routes.endpoints import router as job_router
import structlog

logger = structlog.get_logger()

app = FastAPI(title="Upwork Job Processing API")

app.include_router(job_router)

@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Application stopped")

@app.get("/")
async def root():
    return {"message": "Upwork Job Processing API"}
```

### Task 4.2: CLI Tool

**Time**: 20 minutes | **Priority**: High

Create `cli.py`:

```python
import typer
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal, init_db
from core.config import settings
from core.cerebras import CerebrasClient
from features.job_processing.services.evaluator import JobEvaluator
from features.job_processing.services.ingestion import JobIngestionService

app = typer.Typer(name="upwork-processing")

@app.command()
async def ingest(
    file_path: Path = typer.Argument(..., help="Apify JSON file path"),
):
    """Ingest and evaluate jobs from Apify JSON file"""
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
            await cerebars_client.close()

if __name__ == "__main__":
    app()
```

---

## Phase 5: Database and Migrations

### Task 5.1: Create Initial Migration

**Time**: 15 minutes | **Priority**: High

Create `migrations/versions/001_initial_schema.py`:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("ts_publish", sa.DateTime(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), unique=True, nullable=False),
        sa.Column("fixed_budget_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("fixed_duration_weeks", sa.Numeric(5, 1), nullable=True),
        sa.Column("hourly_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("hourly_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default="apify"),
        sa.Column("scraped_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Evaluations table
    op.create_table(
        "job_evaluations",
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_ai_related", sa.Integer(), nullable=False),
        sa.Column("filter_reason", sa.Text(), nullable=True),
        sa.Column("tech_stack", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("project_type", sa.String(), nullable=False),
        sa.Column("complexity", sa.String(), nullable=False),
        sa.Column("matched_expertise_ids", postgresql.ARRAY(sa.SmallInteger()), nullable=False, server_default="[]"),
        sa.Column("score_budget", sa.SmallInteger(), nullable=False),
        sa.Column("score_client", sa.SmallInteger(), nullable=False),
        sa.Column("score_clarity", sa.SmallInteger(), nullable=False),
        sa.Column("score_tech_fit", sa.SmallInteger(), nullable=False),
        sa.Column("score_timeline", sa.SmallInteger(), nullable=False),
        sa.Column("score_total", sa.SmallInteger(), nullable=False),
        sa.Column("reason_budget", sa.Text(), nullable=False),
        sa.Column("reason_client", sa.Text(), nullable=False),
        sa.Column("reason_clarity", sa.Text(), nullable=False),
        sa.Column("reason_tech_fit", sa.Text(), nullable=False),
        sa.Column("reason_timeline", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Expertise areas table
    op.create_table(
        "expertise_areas",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=False, server_default="[]"),
    )

    # Seed expertise areas
    op.execute("""
        INSERT INTO expertise_areas (id, name, level, keywords) VALUES
        (1, 'AI Agent Architecture & Design', 'Expert', ARRAY['agent', 'autonomous', 'multi-agent', 'LangChain', 'crewAI']),
        (2, 'RAG Systems', 'Advanced', ARRAY['RAG', 'retrieval', 'vector database', 'embeddings', 'semantic search']),
        (3, 'Local AI Infrastructure', 'Expert', ARRAY['local LLM', 'ollama', 'LM Studio', 'self-hosted', 'on-premises', 'privacy']),
        (4, 'Backend Systems', 'Expert', ARRAY['FastAPI', 'Python', 'PostgreSQL', 'pgvector', 'REST API', 'async']),
        (5, 'Frontend Development', 'Advanced', ARRAY['React', 'TypeScript', 'Next.js', 'UI', 'web app']),
        (6, 'DevOps & Infrastructure', 'Expert', ARRAY['Docker', 'deployment', 'CI/CD']),
        (7, 'Voice & Real-Time AI', 'Advanced', ARRAY['voice', 'audio', 'Speech-to-Text', 'text-to-speech', 'WebRTC', 'Deepgram']),
        (8, 'Testing & Code Quality', 'Intermediate-Advanced', ARRAY['testing', 'pytest', 'TDD', 'code quality', 'CI'])
    """)

    # Indexes
    op.create_index("idx_job_evaluations_score_total", "job_evaluations", ["score_total"])
    op.create_index("idx_job_evaluations_priority", "job_evaluations", ["priority"])

def downgrade():
    op.drop_table("expertise_areas")
    op.drop_table("job_evaluations")
    op.drop_table("jobs")
```

---

## Phase 6: Testing

### Task 6.1: Core Tests

**Time**: 30 minutes | **Priority**: Medium

Create `tests/features/test_job_processing.py`:

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import init_db
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient):
    response = await client.get("/jobs/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "ai_related_jobs" in data

@pytest.mark.asyncio
async def test_ranked_jobs_empty(client: AsyncClient):
    response = await client.get("/jobs/ranked")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Summary

| Phase | Tasks | Est. Time | Priority |
|-------|-------|-----------|----------|
| 1. Infrastructure | 1.1-1.4 | 75 min | High |
| 2. Data Models | 2.1-2.2 | 40 min | High |
| 3. Core Services | 3.1-3.2 | 75 min | High |
| 4. API & CLI | 4.1-4.2 | 40 min | High |
| 5. Database | 5.1 | 15 min | High |
| 6. Testing | 6.1 | 30 min | Medium |

**Total Estimated Time**: ~4.5 hours

---

# Spec Delta

## What Changes

| Scope | Change |
|-------|--------|
| **Database Schema** | New tables: `jobs`, `job_evaluations`, `expertise_areas` |

## Database Schema

### Table: jobs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | String | PK | Apify job ID |
| title | String | NOT NULL | Job title |
| ts_publish | DateTime | NOT NULL | Publish timestamp |
| description | Text | NOT NULL | Job description |
| type | String | NOT NULL | "FIXED" or "HOURLY" |
| url | String | UNIQUE, NOT NULL | Job URL |
| fixed_budget_amount | Numeric(10,2) | NULL | Fixed budget amount |
| fixed_duration_weeks | Numeric(5,1) | NULL | Duration in weeks |
| hourly_min | Numeric(10,2) | NULL | Hourly min rate |
| hourly_max | Numeric(10,2) | NULL | Hourly max rate |
| source | String | NOT NULL, default="apify" | Job source |
| scraped_at | DateTime | NULL | Scraped timestamp |
| created_at | DateTime | NOT NULL, default=NOW() | Created timestamp |
| updated_at | DateTime | NOT NULL, default=NOW() | Updated timestamp |

### Table: job_evaluations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| job_id | String | PK, FK→jobs.id | Job ID |
| is_ai_related | Integer | NOT NULL (0 or 1) | AI-related flag |
| filter_reason | Text | NULL | Filter reason if not AI |
| tech_stack | JSONB | NOT NULL | Extracted tech stack |
| project_type | String | NOT NULL | Project type |
| complexity | String | NOT NULL | Complexity level |
| matched_expertise_ids | SMALLINT[] | NOT NULL | Matched expertise IDs |
| score_budget | SmallInt | NOT NULL (0-10) | Budget score |
| score_client | SmallInt | NOT NULL (0-10) | Client score |
| score_clarity | SmallInt | NOT NULL (0-10) | Clarity score |
| score_tech_fit | SmallInt | NOT NULL (0-10) | Tech fit score |
| score_timeline | SmallInt | NOT NULL (0-10) | Timeline score |
| score_total | SmallInt | NOT NULL (0-100) | Total score |
| reason_budget | Text | NOT NULL | Budget reasoning |
| reason_client | Text | NOT NULL | Client reasoning |
| reason_clarity | Text | NOT NULL | Clarity reasoning |
| reason_tech_fit | Text | NOT NULL | Tech fit reasoning |
| reason_timeline | Text | NOT NULL | Timeline reasoning |
| priority | String | NOT NULL | Priority class |
| evaluated_at | DateTime | NOT NULL, default=NOW() | Evaluation timestamp |

### Table: expertise_areas

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SmallInt | PK | Expertise ID (1-8) |
| name | String | UNIQUE, NOT NULL | Expertise name |
| level | String | NOT NULL | Expertise level |
| keywords | String[] | NOT NULL | Matching keywords |

## API Contracts

### GET /jobs/ranked

Returns ranked AI-related jobs by fit score.

**Query Parameters**:
- `limit`: int (default 50) - Max results
- `min_score`: int (default 50) - Minimum score filter
- `priority`: str (optional) - Filter by priority (High/Medium/Low)

**Response**: `JobEvaluationListResponse[]`

```typescript
{
  job_id: string,
  title: string,
  url: string,
  budget: number | null,
  duration_weeks: number | null,
  score_total: number,
  priority: "High" | "Medium" | "Low",
  project_type: string,
  tech_stack: string[],
  matched_expertise_ids: number[],
  reasoning_summary: string
}
```

### GET /jobs/stats

Returns evaluation statistics.

**Response**:
```typescript
{
  total_jobs: number,
  ai_related_jobs: number,
  high_priority_jobs: number,
  ai_related_percentage: number
}
```

### POST /jobs/ingest (Future, not in MVP)

Ingest jobs from file or URL. (CLI handles this in MVP)

---

# Configuration

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes | None | PostgreSQL connection URL |
| CEREBRAS_API_KEY | Yes | None | Cerebras API key |
| CEREBRAS_MODEL | No | "glm-4.7" | Model name |
| RATE_LIMIT_REQUESTS | No | 2 | API requests per second |
| RATE_LIMIT_CONCURRENT | No | 2 | Concurrent API requests |
| API_TIMEOUT | No | 30 | AI request timeout (seconds) |
| FILTER_BUDGET_MIN | No | 500 | Minimum budget threshold |
| CHECKPOINT_INTERVAL | No | 10 | Checkpoint every N jobs |
| LOG_LEVEL | No | "INFO" | Logging level |

---

# Deployment Notes

## Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/upwork_processing
      - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=upwork_processing
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_extensions.sql:/docker-entrypoint-initdb.d/init_extensions.sql

volumes:
  postgres_data:
```

Initialize pgvector:
```sql
-- init_extensions.sql
CREATE EXTENSION IF NOT EXISTS "vector";
```

---

# Next Steps After Implementation

1. Run migrations: `alembic upgrade head`
2. Test with sample data: `python cli.py ingest jobs_dataset_upwork_2026-02-05_04-09-24-623.json`
3. Review API: Access `http://localhost:8000/docs`
4. Validate results: Check `/jobs/ranked` and `/jobs/stats`

---

**End of Implementation Plan**