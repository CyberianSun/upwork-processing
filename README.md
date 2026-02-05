# Upwork Job Processing

AI-powered job evaluation system for Upwork opportunities. Analyzes jobs using Cerebras GLM 4.7 and ranks them by fit score.

## Quick Start

### Docker (Recommended)

```bash
# Build and run
docker-compose up -d

# Ingest and evaluate jobs
docker-compose exec app python cli.py jobs_dataset_upwork_2026-02-05_04-09-24-623.json
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Cerebras API key

# Run migrations
alembic upgrade head

# Ingest jobs
python cli.py jobs_dataset_upwork_2026-02-05_04-09-24-623.json

# Run API
uvicorn main:app --reload
```

## API Endpoints

- `GET /jobs/ranked` - Ranked AI-related jobs
- `GET /jobs/stats` - Evaluation statistics
- `GET /docs` - Interactive API documentation

## Tech Stack

Python 3.11+ | FastAPI | PostgreSQL 16 + pgvector | SQLAlchemy 2.0 | Cerebras GLM 4.7

## Architecture

Vertical Slice Architecture (SeedFW). All business logic in `features/job_processing/`.

```
features/job_processing/
├── models/        # SQLAlchemy ORM
├── schemas/       # Pydantic validation
├── services/      # Business logic (evaluator, ingestion)
└── routes/        # API endpoints
```