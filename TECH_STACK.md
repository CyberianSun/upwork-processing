# Upwork Processing - Technology Stack

**Last Updated:** 2026-02-04
**Purpose:** Upflow Lite - Simplified job evaluation and ranking system
**Reference:** Custom tech stack for backend processing node with LLM integration

---

## Core Stack

| Category    | Technology                     | Version       | Purpose                                                        |
|-------------|--------------------------------|---------------|----------------------------------------------------------------|
| Language    | Python                         | 3.11+         | Primary language for all processing logic                      |
| API         | FastAPI                        | Latest        | Fast async API for service endpoints                           |
| Models      | Pydantic                       | v2.0+         | Data validation and type safety                                |
| Database    | PostgreSQL                     | 14+           | Persistent data storage (self-hosted via Coolify/Supabase)    |
| LLM         | Cerebras SDK                   | GLM 4.7       | Fast inference for job evaluation and ranking                  |
| Async       | asyncio + aiohttp              | Built-in      | Respects rate limits for concurrent operations                |
| Testing     | pytest + pytest-asyncio        | Latest        | Industry-standard test framework with async support            |
| Code Quality| black + ruff + mypy            | Latest        | Modern Python tooling for formatting, linting, type checking  |
| Container   | Docker                         | Latest        | Local testing + Coolify deployment                             |
| Deployment  | Coolify                        | -             | Deployed via Docker Compose                                    |
| Logging     | logging                        | Built-in      | 12-factor compliant structured logging                        |

---

## Libraries & Dependencies

### Core Framework
```
fastapi>=0.104.0         # Modern FastAPI with async support
uvicorn[standard]>=0.24.0 # ASGI server with auto-reload
pydantic>=2.4.0          # v2 for modern type safety
pydantic-settings>=2.1.0 # Settings management
```

### Database
```
sqlalchemy>=2.0.23       # SQL toolkit and ORM
asyncpg>=0.29.0          # Async PostgreSQL driver
alembic>=1.13.0          # Database migrations
```

### LLM Integration
```
cerebras-cloud-sdk       # Cerebras SDK for GLM 4.7
openai>=1.3.0            # OpenAI-compatible client (optional compatibility)
```

### Data Processing
```
pandas>=2.1.0            # CSV parsing and data manipulation
numpy>=1.26.0            # Numerical operations
```

### Async & HTTP
```
aiohttp>=3.9.0           # Async HTTP client
asyncio>=3.4.3           # Built-in (import, not install)
```

### Utilities
```
python-dotenv>=1.0.0     # Environment variable management
```

### Development Tools (dev dependencies)
```
pytest>=7.4.3            # Test framework
pytest-asyncio>=0.21.1   # Async test support
pytest-cov>=4.1.0        # Test coverage
black>=23.11.0           # Code formatter
ruff>=0.1.8              # Fast linter
mypy>=1.7.0              # Type checker
pre-commit>=3.6.0        # Git hooks (optional)
```

---

## Development Tools Configuration

### Black (Code Formatter)
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

### Ruff (Linter)
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
```

### MyPy (Type Checker)
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### Pytest (Testing)
```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["features"]
```

---

## Architecture Constraints (SeedFW)

- **Vertical Slice Architecture** - Organize by feature (business logic in features/)
- **Files under 500 lines** - AI comprehension and maintainability
- **No manual package.json equivalents** - Use pip/requirements.txt or poetry
- **Type hints** - Strict typing where possible
- **Error handling** - Proper try-catch blocks with logging
- **No type suppression** - Never use `# type: ignore` or `cast()` without justification

---

## Data Formats

| Purpose   | Format  | Source/Destination                      |
|-----------|---------|-----------------------------------------|
| Input     | CSV     | Apify scraped job data                  |
| Output    | Markdown| Job reports (formatted for Telegram)    |
| Internal  | JSON    | Config files, API responses (optional)  |
| Storage   | SQL     | PostgreSQL database                     |

---

## Deployment Architecture

### Local Development
```
Terminal testing
    ↑
Docker container (for local testing)
```

### Production (Coolify)
```
Telegram Bot (clawdbot)
    ↑ HTTP API
Upwork Processing Service (FastAPI)
    ↑ Async processing
PostgreSQL Database (Coolify's Supabase)
    ↑ Rate-limited calls
Cerebras GLM 4.7 API
```

---

## Environment Variables

Required environment variables:

```bash
# Cerebras API
CEREBRAS_API_KEY=your_api_key_here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/upwork_processing

# Telegram (optional, for integration)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Service Config
LOG_LEVEL=INFO
ASYNC_MAX_WORKERS=5  # Cerebras rate limit sync
```

---

## Notes

- Criteria will be hardcoded in Python file (manual updates)
- Schema will be derived on first run with Apify files
- Initial testing via terminal, later streamlined interaction
- Async processing within Cerebras rate limits