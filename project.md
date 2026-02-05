# Upwork Processing - Project Conventions

**Last Updated:** 2026-02-04
**Purpose:** Project conventions for Upflow-lite job processing system

---

## Project Overview

This is a backend processing node that evaluates and ranks Upwork jobs against AI Systems Engineer criteria. It communicates via Telegram bot and uses Cerebras GLM 4.7 for intelligent job scoring.

**Core Philosophy:**
- Agent-driven, no UI
- Terminal-first testing
- Async processing within rate limits
- Manual criteria updates (no database schema migrations for criteria)

---

## Development Workflow

### Phase 1: Terminal Testing (Current)
- CLI-based interaction
- Manual file path inputs
- Direct output to console

### Phase 2: Streamlined Interaction (Future)
- TBD based on Phase 1 learnings
- Possibly simplified commands / shortcuts

### Phase 3: Telegram Integration (Future)
- clawdbot integration for reports
- Async job submission and result delivery

---

## File Organization

```
upwork-processing/
├── features/
│   ├── job-processing/           # Feature: Main job pipeline
│   │   ├── services/
│   │   │   ├── ingestion.py      # Parse Apify CSV files
│   │   │   ├── evaluation.py     # Score jobs against criteria
│   │   │   ├── ranking.py        # Sort and rank jobs
│   │   │   └── reporting.py      # Generate markdown reports
│   │   ├── models/
│   │   │   ├── job.py            # Job data models
│   │   │   └── criteria.py       # Criteria models
│   │   └── tests/
│   │       └── test_job_processing.py
│   └── telegram-integration/     # Feature: Telegram bot integration
│       ├── services/
│       ├── models/
│       └── tests/
├── core/
│   ├── config/
│   │   ├── settings.py           # App settings (pydantic-settings)
│   │   └── criteria.py           # Hardcoded criteria (manual updates)
│   ├── logging.py                # Logging configuration
│   ├── cerebras_client.py        # Cerebras SDK wrapper
│   └── types.py                  # Shared type definitions
├── shared/
│   └── utils.py                  # Shared helper functions
├── tests/
│   ├── conftest.py               # Pytest configuration
│   └── test_integration.py       # Integration tests
├── main.py                       # CLI entry point (terminal mode)
├── requirements.txt              # Production dependencies
└── pyproject.toml                # Dev dependencies & tool configs
```

---

## Git Workflow

### Branch Naming
- Use `main` as primary branch (not `master`)
- Feature branches: `job-processing/feature-name`
- Bugfixes: `job-processing/fix-description`
- Refactors: `job-processing/refactor-description`

### Commit Messages
Follow conventional commits:
- `feat(job-processing): add CSV ingestion service`
- `fix(evaluation): correct criteria weight calculation`
- `refactor(ranking): simplify scoring algorithm`

### PR Workflow
1. Create feature branch from `main`
2. Implement feature in isolated feature directory
3. Add tests (test-first preferred)
4. Run linting + type checking
5. Open PR with description
6. Review before merge

---

## Coding Conventions

### Python Style Guide
- Follow PEP 8 with 100 character line length
- Use type hints for all function signatures
- Use pyproject.toml for tool configuration (black, ruff, mypy)

### File Size Limit
- Maximum 500 lines per file
- Split large files into smaller modules
- Each module should have a single responsibility

### Type Safety
- **NEVER suppress type errors**:
  - No `# type: ignore` without explicit justification in comment
  - No `typing.cast()` unless absolutely necessary
  - If type checking fails, fix the types, don't suppress

### Error Handling
- Always catch specific exceptions
- Never use bare `except:` clauses
- Log all errors with context
- Use custom exception classes for business logic errors

### Async/Await
- Use `asyncio` for concurrent job processing
- Respect Cerebras rate limits (max 5 concurrent workers by default)
- Use `asyncpg` for database operations
- All database access must be async

### Database Operations
- Use SQLAlchemy async ORM
- Always use async sessions
- Use context managers for sessions:
  ```python
  async with AsyncSession(engine) as session:
      result = await session.execute(stmt)
  ```

---

## Testing Conventions

### Test Organization
- Unit tests in `features/*/tests/` (next to implementation)
- Integration tests in `tests/` root
- Fixtures in `tests/conftest.py`

### Test Naming
- Use descriptive names: `test_should_reject_jobs_without_description`
- Use `pytest.mark.asyncio` for async tests
- Use `@pytest.fixture` for shared test data

### Test Coverage
- Aim for 80%+ code coverage
- Use `pytest-cov` to generate reports
- Critical paths must have tests

---

## Criteria Management

### Current Approach
- **Hardcoded in `main/core/config/criteria.py`**
- Manual updates only (no database schema for criteria)

### Updating Criteria
1. Edit `core/config/criteria.py` directly
2. Criteria structure:
   ```python
   criteria = [
       CriteriaItem(
           name="AI Systems Experience",
           description="..."
           weight=0.25,
           factors=[...]
       ),
       ...
   ]
   ```
3. No migration needed (just Python file edit)
4. Test with updated criteria before deploy

### Future Migration (if needed)
- If criteria become complex, move to database
- This is NOT currently planned

---

## Schema Derivation

### First Run
- Parse Apify CSV files to detect schema
- Compare with upwork-scraping schema
- Store derived schema as Pydantic models
- Reuse schema for subsequent runs

### Schema Changes
- If Apify format changes, re-derive schema
- Update Pydantic models accordingly
- Tests will catch breaking changes

---

## Environment Setup

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"  # Install dev dependencies

# Set environment variables
export CEREBRAS_API_KEY=your_key
export DATABASE_URL=postgresql+asyncpg://...

# Run tests
pytest features/

# Run linter
ruff check .

# Type check
mypy .

# Format code
black .
```

### Docker Testing
```bash
docker build -t upwork-processing .
docker run -it --env-file .env upwork-processing python main.py --help
```

---

## Deployment

### Coolify Deployment
1. Build Docker image
2. Push to registry
3. Deploy via Coolify using Docker Compose
4. Configure environment variables in Coolify
5. PostgreSQL via Coolify's Supabase

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Type checking clean (`mypy`)
- [ ] Linting clean (`ruff check`)
- [ ] Code formatted (`black --check`)
- [ ] Environment variables documented
- [ ] Migration scripts ready (if needed)

---

## Logging

### Log Levels
- `DEBUG`: Detailed trace information
- `INFO`: Normal operations (start/finish, job counts)
- `WARNING`: Non-critical issues (missing fields, minor failures)
- `ERROR`: Errors that don't stop processing (job evaluation errors)
- `CRITICAL`: Errors that stop the service (API failures, DB down)

### Log Format
```
[2026-02-04 10:30:00] INFO job_processing.ingestion: Ingested 50 jobs from apify_jobs.csv
[2026-02-04 10:30:01] ERROR job_processing.evaluation: Job #123: Missing description field
```

---

## Rate Limiting

### Cerebras API
- Default: 5 concurrent async workers
- Configurable via `ASYNC_MAX_WORKERS` env var
- Never exceed provider rate limits

### Database
- Use connection pooling via SQLAlchemy
- Close connections after use
- Don't hold transactions long unnecessarily

---

## Communication Channels

### During Development
- Terminal output for testing
- Logs for debugging
- GitHub Issues for tracking

### Production (Future)
- Telegram bot for user interaction
- Slack/Discord for alerts (optional)

---

## Documentation

### What to Document
- README.md: Quick start, usage examples
- TECH_STACK.md: Technology stack and versions
- FEATURES.md: Feature descriptions (if complex)
- API docs: Auto-generated by FastAPI (if API surface grows)

### What NOT to Document
- Inline comments are sufficient for obvious logic
- Don't document self-explanatory code

---

## Quality Standards

### Code Quality
- [ ] All type hints present (no `Any` unless justified)
- [ ] All functions have docstrings
- [ ] No type errors (`mypy` clean)
- [ ] No lint errors (`ruff check` clean)
- [ ] Proper error handling
- [ ] Logs at appropriate levels

### Test Quality
- [ ] Unit tests for business logic
- [ ] Integration tests for workflows
- [ ] Tests are deterministic
- [ ] Tests are fast (sub-second where possible)

---

## Known Limitations

1. **Manual criteria updates**: No UI for criteria management
2. **Terminal-first**: No API surface planned (may add later)
3. **Single user**: Designed for personal use
4. **No migration system**: Criteria updated via Python file

---

## Future Enhancements (Not Planned Yet)

- Web UI for criteria management
- API endpoints for job submission
- Historical job tracking
- Analytics dashboard
- Automated job recommendations