# Handoff Context

## 1. Current Work

**Overall Goal**: Build an AI-powered job evaluation and ranking system for Upwork jobs. The app processes Apify CSV files, evaluates jobs against AI Systems Engineer criteria using Cerebras GLM 4.7, stores results in PostgreSQL, and displays ranked results in terminal.

**Current Phase**: Design phase complete. All documentation, architecture, tech stacks, and configuration decisions finalized.

**Most Recent Actions**:
- Consolidated keywords from multiple files into single `KEYWORDS.md`
- Created `POSTGRESQL_ACTUAL_STATUS.md` documenting actual PostgreSQL instance (pgvector needs manual installation)
- Created `CEREBRAS_RATE_LIMITS.md` documenting GLM 4.7 rate limits (2 req/s, 120M tokens/day bottleneck)
- Created `MY_ACTUAL_TECH_STACK.md` and `TECH_STACK_COMPARISON.md` with verified experience (100% market coverage)
- Created `UPWORK_PROFILE.md` - human-sounding profile based on verified tech stack
- Removed duplicate keyword files (`APIFY_KEYWORDS.md`, `KEYWORD_STRATEGY_UPDATED.md`, `MARKET_DEMAND_STACK.md`)

**Status**: Awaiting user to provide fresh Apify CSV file to begin implementation.

---

## 2. Key Technical Concepts

### Application Architecture
- **Architecture**: Vertical Slice (SeedFW)
  - Entry point: `main.py` (CLI)
  - Core logic: `features/job_processing/`
  - Database: Async PostgreSQL with asyncpg
  - LLM: Cerebras GLM 4.7 SDK

- **Processing Flow** (Simplified - NO enricher for MVP):
  ```
  Apify CSV → Load → Evaluate (LLM) → Store → Rank → Display
                      ↓                ↓
                Cerebras GLM 4.7  PostgreSQL DB
  ```

- **Cerebras Rate Limits**:
  - Max: 120 requests/min = 2 req/s
  - Workers: 2 concurrent with 0.5s delay between requests
  - Bottleneck: 120M tokens/day = ~48,000 jobs/day @ 2.5k tokens/job
  - Semaphore: `asyncio.Semaphore(2)`

### Tech Stack

**App Stack** (what we use to build):
- Python 3.11+, FastAPI, PostgreSQL (pgvector), Docker
- Cerebras GLM 4.7, AsyncIO (async processing)
- Pydantic v2, SQLAlchemy 2.0, Alembic (migrations)
- Black, Ruff, MyPy (code quality)

**Market Stack** (what clients request - for comparison)
- AI Agents (LangChain, LangGraph) - 77-92% demand
- Voice AI (Deepgram, ElevenLabs, Twilio, Telnyx, WebRTC) - 42% demand
- RAG (pgvector, Pinecone, Qdrant, Milvus) - 18% demand
- Integration (REST/GraphQL, webhooks) - 35-49% demand

### Database Configuration

**Local PostgreSQL** (recommended):
- Service: `postgresql@16-main` (running, 20h uptime)
- Database: `upwork_processing` (created)
- User: `postgres` (superuser)
- Connection: `postgresql+asyncpg://postgres@localhost:5432/upwork_processing`
- pgvector: NOT installed - needs manual compilation

**pgvector Installation** (required before first run):
```bash
sudo apt install postgresql-server-dev-16 build-essential git
cd /tmp && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && cd pgvector
make && sudo make install
sudo -u postgres psql -d upwork_processing -c "CREATE EXTENSION vector;"
```

### Coding Conventions (SeedFW)
- Vertical Slice Architecture - business logic in `features/`
- Files under 500 lines
- Type hints (strict)
- No `# type: ignore` or `cast()` without justification
- Async-first (asyncio)
- 100 char line length (Black)
- `pytest` with async support for tests

### Criteria & Scoring

**5 Criteria** (0-20 points each, max 100):
1. Budget (0-20) - Min $500, below scores 0 points
2. Client Verification (0-20) - Use defaults: payment_verified=False, client_rating=4.0, feedback_count=5
3. Requirements Clarity (0-20) - Description length + quality indicators
4. AI Technical Fit (0-20) - NEW: AI Systems Engineering focus
   - 4A. AI/LLM Core Skills (0-7) - Agents, APIs, multi-step reasoning
   - 4B. RAG & Vector Systems (0-5) - Vector DBs, semantic search
   - 4C. AI Integration & Automation (0-4) - APIs, webhooks, automation
   - 4D. Local AI & Infrastructure (0-2) - Self-hosted, Docker, deployment
   - 4E. Voice & Multimodal AI (0-1) - STT/TTS, WebRTC, voice agents
   - 4F. Backend & Frontend AI (0-1) - FastAPI, React, full-stack
5. Timeline (0-20) - Default: 10, Urgent: 4, Reasonable: 16

**Priority Classification**:
- ≥70: High (go)
- ≥50: Medium (go)
- ≥40: Low (no-go)
- <40: Very Low (no-go)

### Constraints & Requirements

**User-confirmed**:
- Minimum budget: $500 (below scores 0 points)
- Removed n8n, Make.com, Zapier, Bubble.io - NOT interested in these
- Enricher NOT needed for MVP - keyword extraction happens inline via LLM
- Run in Docker container (later deploy to VPS via Coolify)
- Use existing local PostgreSQL (create `upwork_processing` DB)
- NEVER act without user approval - always ask YES/NO before building

**User's Verified Experience** (for Upwork profile/keyword matching):
- Voice AI: Deepgram, ElevenLabs, Telnyx, Twilio, Pipecat, WebRTC, Daily.co (SolarVox proof)
- Vector DBs: pgvector, Pinecone, Qdrant, Milvus, FAISS
- Graph: Neo4j, Cypher, Knowledge Graphs, GraphQL
- Backend: FastAPI, Python, REST/GraphQL, asyncio
- Frontend: React, Next.js, TypeScript

---

## 3. Relevant Files and Code

### Design Documents

- `project.md`: SeedFW conventions - Vertical slice, <500 lines, no type suppression
- `TECH_STACK.md`: App technology choices - Python, FastAPI, PostgreSQL, Cerebras GLM 4.7
- `MY_ACTUAL_TECH_STACK.md`: Complete verified tech profile (200+ technologies)
- `KEYWORDS.md`: Single consolidated keyword reference (200+ keywords)
  - Market frequency analysis
  - Master list by category (AI, Voice, RAG, Integration, Backend, Frontend, DB, etc.)
  - Usage strategy for Upwork profile, proposals, bids
  - Service-based keyword allocation
  - Portfolio optimization tips

### Architecture & Configuration

- `ARCHITECTURE.md`: Information flow diagram, components, database schema
  - Tables: jobs, evaluations, tech_trends, keyword_stats, market_pulse
  - Simplified architecture (no enricher for MVP)

- `CONFIGURATION_SUMMARY.md`: All 10 configuration decisions confirmed
  1. Output: Markdown terminal display
  2. Result persistence: Keep all evaluations
  3. Keyword updates: Auto-every-run, confirm before applying
  4. Market pulse: Daily
  5. Scoring validation: TBD
  6. Telegram bot: Phase 2 (terminal-first)
  7. Rate limiting: Cerebras GLM 4.7 limits
  8. Budget cutoff: Min $500 (below = 0 points)
  9. Tech trend alerts: None (accumulate only)
  10. Skill gaps: Auto-mark as "learn priority"

- `CRITERIA_AI_SYSTEMS_ENGINEER.md`: Scoring criteria
  - Replaced "Technical Feasibility" (data-scraping) with "AI Technical Fit"
  - Budget min $500 scoring
  - Default client verification values
  - Voice_ai sub-criterion includes: Twilio, ElevenLabs, Telnyx, Deepgram, WebRTC, Pipecat, Play.ai, Play.ht
  - Simplified architecture (no enricher for MVP)
  - Test cases included (high-score agent, voice agent, low-score scraping)

- `CEREBRAS_RATE_LIMITS.md`: GLM 4.7 rate limits
  - Requests: 120/min = 2 req/s
  - Tokens: 1.5M/min, 120M/hour, 120M/day (bottleneck)
  - Workers: 2 concurrent, 0.5s delay
  - Semaphore configuration: `asyncio.Semaphore(2)`

- `TECHNOLOGY_REFERENCE.md`: Explains FAISS, Milvus, CAMEL, BabyAGI, Enricher, Evaluator

- `POSTGRESQL_ACTUAL_STATUS.md`: Real PostgreSQL status
  - Service running: `postgresql@16-main` (localhost:5432)
  - Database created: `upwork_processing`
  - pgvector: NOT installed - manual compilation steps provided
  - Connection string: `postgresql+asyncpg://postgres@localhost:5432/upwork_processing`

- `TECH_STACK_COMPARISON.md`: Updated comparison with 100% market coverage
  - Verified Voice AI experience (SolarVox) - NOT a gap
  - Multi-vector DB expertise (6+ technologies)
  - Neo4j + GraphQL competitive edge
  - Bid strategy based on keyword matching

- `UPWORK_PROFILE.md`: Human-sounding Upwork profile
  - Title: "AI Systems Engineer - Voice Agents, RAG Systems, Full-Stack AI"
  - Services: AI Agent Architecture, Voice AI, RAG Systems, Full-Stack AI, Advanced Retrieval (Neo4j + Vector)
  - Portfolio: SolarVox voice agent (deepgram, daily.co, pipecat, webrtc)
  - Skills list: 15 recommended Upwork tags

---

## 4. Problem Solving

### Resolved Issues

**1. Two tech stacks confusion**
- User clarified: Two stacks = (1) what we use to build app vs (2) what market wants
- Created separate documents: `TECH_STACK.md` (app) vs `MARKET_DEMAND_STACK.md` → `KEYWORDS.md` (market)

**2. Voice AI gap assumption**
- Initially assumed no voice AI experience
- User corrected: Has full voice AI stack experience
- Created `MY_ACTUAL_TECH_STACK.md` documenting proof: SolarVox project (Deepgram STT/TTS, Daily.co WebRTC, Pipecat, OpenAI)
- Updated all references to show 100% voice AI coverage

**3. PostgreSQL assumptions**
- Initially suggested default credentials
- User requested actual verification
- Checked system: Found `postgresql@16-main` running, created `upwork_processing` DB
- Discovered pgvector NOT installed - documented manual installation steps

**4. Consolidating duplicate keyword files**
- Had: `KEYWORD_STRATEGY_UPDATED.md`, `MARKET_DEMAND_STACK.md`, `APIFY_KEYWORDS.md`
- User requested single keyword file
- Consolidated into `KEYWORDS.md` (200+ keywords)
- Removed duplicate files

---

### Ongoing Items

**1. pgvector Installation** (Before implementation)
- Status: NOT installed on local PostgreSQL
- Steps documented in `POSTGRESQL_ACTUAL_STATUS.md`
- User has NOT installed yet - to be done when implementing
- Fallback: Use Docker with `pgvector/pgvector:pg16` image if manual install fails

**2. Apify File** (Prerequisite for implementation)
- User: "will supply in a bit, after we are done with the rest"
- Design phase complete - now can accept file
- File format: CSV with job data
- To be provided by user

---

## 5. Pending Tasks and Next Steps

### Pending Task 1: Complete Implementation

**User's context request** (from session): "Continue if you have next steps" (implied after design completion)

**Next Steps** (when Apify file provided):
1. Initialize project structure (SeedFW vertical slice layout)
   - Create `main.py` CLI entry point
   - Create `features/job_processing/` directory structure
   - Set up `pyproject.toml` (dependencies, Black/Ruff/MyPy config)
   - Create `.env` template (Cerebras API key, DATABASE_URL)

2. Set up PostgreSQL database
   - Install pgvector extension (manual compilation)
   - Run Alembic migrations for schema (from ARCHITECTURE.md)
   - Test connection

3. Implement job loader
   - Parse Apify CSV files
   - Extract relevant fields (title, description, budget, skills)

4. Implement evaluator (Cerebras GLM 4.7)
   - Call GLM 4.7 with job data + criteria
   - Rate-limited: 2 workers, 0.5s delay, semaphore
   - Parse scores from LLM response
   - Store in PostgreSQL

5. Output ranked results
   - Display in Markdown format (terminal)
   - Sort by total score (descending)
   - Show priority classification

6. Run in Docker
   - Create `Dockerfile`
   - Create `docker-compose.yml` (include PostgreSQL optional)
   - Test container

**User decision needed**: Apify CSV file location/path

---

### Pending Task 2: pgvector Installation

**From user**: "we need to connect I guess, or create a new? idk, also I want the app to run a docker container"

**Next Steps**:
1. Install pgvector (manual compilation):
   ```bash
   sudo apt install postgresql-server-dev-16 build-essential git
   cd /tmp && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && cd pgvector
   make && sudo make install
   sudo -u postgres psql -d upwork_processing -c "CREATE EXTENSION vector;"
   ```

2. Verify installation:
   ```bash
   sudo -u postgres psql -d upwork_processing -c "\dx vector"
   ```

3. If fails: Use Docker fallback with `pgvector/pgvector:pg16`

**User decision needed**: Manual install preferred or Docker fallback?

---

### Pending Task 3: Docker Deployment Setup

**From user**: "later on the app will be deployed on my vps, via coolify via containers"

**Next Steps** (after local implementation):
1. Create `Dockerfile` for application
2. Create `docker-compose.yml` (app + optional PostgreSQL)
3. Configure environment variables for Coolify
4. Test local Docker container
5. Prepare for VPS deployment (later phase)

**Not immediate**: This is for later deployment phase. Local implementation first.

---

## 6. Files to Load

**Critical files for implementation** (load in this order):
- `project.md` - SeedFW conventions and patterns
- `TECH_STACK.md` - App technology choices
- `ARCHITECTURE.md` - Data flow and database schema
- `CRITERIA_AI_SYSTEMS_ENGINEER.md` - Scoring criteria (use for LLM prompt)
- `CEREBRAS_RATE_LIMITS.md` - Rate limiting configuration (use for semaphore setup)
- `POSTGRESQL_ACTUAL_STATUS.md` - Database connection details
- `KEYWORDS.md` - Reference for keyword matching (if implementing enricher later)

**Optional reference files**:
- `MY_ACTUAL_TECH_STACK.md` - User's expertise (for Upwork profile - not needed for implementation)
- `UPWORK_PROFILE.md` - Upwork portfolio content (not needed for implementation)
- `CONFIGURATION_SUMMARY.md` - Configuration decisions (referenced, but implementation follows CRITERIA and ARCHITECTURE)

---

## Additional Notes

- **Enricher**: User explicitly said "enricher is not necessary at this stage - leave it for later" - keyword extraction happens inline during LLM evaluation
- **Always ask user**: User said "NEVER act without user approval - always ask YES/NO before building"
- **Two tech stacks**: Remember the distinction - `TECH_STACK.md` is for building app, `KEYWORDS.md` is for market demand comparison
- **SolarVox proof**: User has production voice agent experience (documented in `MY_ACTUAL_TECH_STACK.md`)

---

**Handoff Date**: 2026-02-05
**Status**: Design complete, awaiting Apify file to begin implementation