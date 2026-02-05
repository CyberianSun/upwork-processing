# Upwork Job Processing

AI-powered job evaluation system for Upwork opportunities.

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run migrations:
```bash
alembic upgrade head
```

## Usage

### Ingest Jobs

```bash
python cli.py ingest jobs_dataset_upwork_2026-02-05_04-09-24-623.json
```

### Run API

```bash
uvicorn main:app --reload
```

### API Endpoints

- `GET /jobs/ranked` - Get ranked AI-related jobs
- `GET /jobs/stats` - Get evaluation statistics

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL 16 + pgvector
- SQLAlchemy 2.0 (async)
- Cerebras GLM 4.7
- Alembic