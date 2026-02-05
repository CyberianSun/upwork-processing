# Upwork Processing App - Architecture & Data Flow

**Purpose**: Process Upwork jobs from Apify CSV files using Cerebras GLM 4.7 for AI evaluation and ranking

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            UPWORK PROCESSING APPLICATON                            │
│                           (Agent-Driven, No UI, Terminal-First)                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Information Flow Diagram

```
┌──────────────────┐                                                   
│                  │                                                   
│   You (User)     │                                                   
│                  │                                                   
└────────┬─────────┘                                                   
         │                                                             
         │ (1) Provides Apify file path                                 
         ▼                                                             
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     CLI ENTRYPOINT (main.py)                        │  │
│  │                    - Parse command line args                        │  │
│  │                    - Validate file path                            │  │
│  │                    - Trigger processing pipeline                    │  │
│  └──────────────────────────┬───────────────────────────────────────────┘  │
│                             │                                              │
│                             │ (2) Start processing pipeline                │
│                             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                 JOB PROCESSING PIPELINE                              │  │
│  │                  (features/job_processing/)                          │  │
│  └──────────────────────────┬───────────────────────────────────────────┘  │
│                             │                                              │
│         ┌───────────────────┼───────────────────┐                         │
│         │                   │                   │                         │
│         │                   │                   │                         │
│         ▼                   ▼                   ▼                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                     │
│  │  Apify File  │  │   Criteria   │  │  Keywords    │                     │
│  │   Loader     │  │   (CRITERIA) │  │ Strategy     │                     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                     │
│         │                 │                 │                             │
│         │ (3) Load jobs   │ (4) Load        │ (5) Load keywords           │
│         │                 │ scoring rules   │ & frequency data            │
│         │  ┌─────────────┐│                 │                             │
│         │  │ JSON/CSV    ││                 │                             │
│         │  │ Parser      ││                 │                             │
│         │  └─────────────┘│                 │                             │
│         │                 │                 │                             │
│         └─────────────────┼─────────────────┘                             │
│                           │                                              │
│                           │ (6) Enrich jobs with metadata                │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    JOB EVALUATION ENGINE                             │  │
│  │                 (Async, Concurrent Processing)                       │  │
│  │                                                                      │  │
│  │   ┌────────────────────────────────────────────────────────────┐    │  │
│  │   │              SEMAPHORE-RATE-LIMITED POOL                   │    │  │
│  │   │              (Max N concurrent evaluations)                 │    │  │
│  │   │                                                              │    │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │    │  │
│  │   │  │  Worker 1   │  │  Worker 2   │  │  Worker N   │         │    │  │
│  │   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │    │  │
│  │   │         │                 │                 │               │    │  │
│  │   │         ▼                 ▼                 ▼               │    │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │    │  │
│  │   │  │   LLM       │  │   LLM       │  │   LLM       │         │    │  │
│  │   │  │  Evaluation │  │  Evaluation │  │  Evaluation │         │    │  │
│  │   │  │  (Cerebras) │  │  (Cerebras) │  │  (Cerebras) │         │    │  │
│  │   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │    │  │
│  │   │         │                 │                 │               │    │  │
│  │   │         └─────────────────┼─────────────────┘               │    │  │
│  │   │                           │                                │    │  │
│  │   └───────────────────────────┼────────────────────────────────┘    │  │
│  │                               │                                       │
│  │                               │ (7) Evaluate against 5 criteria       │
│  │                               │     - Budget                          │
│  │                               │     - Client Verification             │
│  │                               │     - Requirements Clarity           │
│  │                               │     - AI Technical Fit (NEW)          │
│  │                               │     - Timeline                        │
│  │                               │                                       │
│  └───────────────────────────────┼───────────────────────────────────────┘  │
│                                  │                                           │
│                                  ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      SCORING & RANKING                               │  │
│  │                 - Calculate total score (0-100)                      │  │
│  │                 - Assign priority (High/Medium/Low/Very Low)         │  │
│  │                 - Set go/no-go decision                              │  │
│  │                 - Generate score breakdown per criterion             │  │
│  └──────────────────────────┬───────────────────────────────────────────┘  │
│                             │                                              │
│                             │ (8) Store evaluation results                │
│                             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    POSTGRESQL DATABASE                               │  │
│  │                    (upwork database on VPS)                           │  │
│  │                                                                      │  │
│  │   Tables:                                                            │  │
│  │   - jobs          (job metadata from Apify)                         │  │
│  │   - evaluations   (LLM scoring results)                             │  │
│  │   - tech_trends   (tracked technology usage)                        │  │
│  │   - keyword_stats (keyword frequency analysis)                       │  │
│  │   - market_pulse  (aggregate metrics & insights)                    │  │
│  └──────────────────────────┬───────────────────────────────────────────┘  │
│                             │                                              │
│                             │ (9) Query ranked results                     │
│                             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    RESULT FORMATTER                                  │  │
│  │                 - Sort by score (descending)                         │  │
│  │                 - Format output (JSON/Markdown/ASCII table)          │  │
│  │                 - Include: job ID, score, priority, URL, breakdown   │  │
│  └──────────────────────────┬───────────────────────────────────────────┘  │
│                             │                                              │
│                             │ (10) Display results                         │
│                             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    OUTPUT TO CONSOLE                                 │  │
│  │                 - Ranked jobs list                                   │  │
│  │                 - Score breakdowns                                   │  │
│  │                 - Recommendations                                    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│                             │ (Optional: Send to Telegram bot)              │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────┐                              │
│  │        TELEGRAM BOT (clawdbot)              │                              │
│  │        - Send ranked results               │                              │
│  │        - Allow interactive filtering       │                              │
│  │        - Notify new job opportunities       │                              │
│  └─────────────────────────────────────────────┘                              │
└───────────────────────────────────────────────────────────────────────────────┘
         │
         │ (11) You review ranked jobs
         │      and select which to work on
         ▼
   ┌──────────┐
   │ Decision │
   │: Apply   │
   │: Skip    │
   │: Later   │
   └──────────┘
```

---

## Detailed Component Architecture

### 1. CLI Entry Point (`main.py`)

```
┌─────────────────────────────────────────────────────────┐
│                    main.py                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   Arguments:                                            │
│   - --apify-file: Path to Apify CSV/JSON file          │
│   - --workers: Number of concurrent workers (default: 5)│
│   - --output: Output format (json/markdown/ascii)      │
│   - --send-telegram: Send results to bot (optional)    │
│                                                         │
│   Validation:                                           │
│   ✅ File exists                                        │
│   ✅ File format valid (CSV/JSON)                       │
│   ✅ Database connection established                    │
│   ✅ Cerebras API key available                         │
│                                                         │
│   Actions:                                              │
│   1. Load configuration                                 │
│   2. Initialize database connection                     │
│   3. Kick off job processing pipeline                   │
│   4. Display progress tracking                          │
│   5. Output final results                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 2. Job Processing Pipeline (`features/job_processing/`)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    features/job_processing/                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  loader.py      │  │  evaluator.py   │  │  ranker.py      │      │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤      │
│  │ • Load Apify    │  │ • Call Cerebras │  │ • Calculate     │      │
│  │   file          │  │   GLM 4.7      │  │   total scores  │      │
│  │ • Parse JSON    │  │ • Score each    │  │ • Sort by score │      │
│  │ • Normalize     │  │   criterion     │  │ • Assign       │      │
│  │   schema        │  │ • Store results │  │   priorities    │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │  enricher.py    │  │  store.py       │  │  formatter.py   │      │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤      │
│  │ • Add metadata  │  │ • Insert jobs   │  │ • JSON output   │      │
│  │ • Extract       │  │ • Insert evals  │  │ • Markdown      │      │
│  │   keywords      │  │ • Update trends │  │   tables        │      │
│  │ • Compute stats │  │   tables        │  │ • ASCII tables  │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 3. LLM Evaluation Engine (Cerebras GLM 4.7)

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LLM Evaluation Engine                             │
│                                                                      │
│  Input per Job:                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Job Title:     {title}                                     │     │
│  │ Job URL:       {url}                                       │     │
│  │ Budget:        ${amount} (from fixed.budget.amount)        │     │
│  │ Description:   {description}                               │     │
│  │ Skills:        {skills} (array of strings)                 │     │
│  │ Type:          {type} (fixed/hourly)                       │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ System Prompt:                                               │     │
│  │ "You are an AI Systems Engineer evaluating Upwork jobs.    │     │
│  │ Score the job on 5 criteria (0-20 points each, max 100):   │     │
│  │                                                              │     │
│  │ 1. Budget: Score $ amount:                                  │     │
│  │    - ≥$2000 = 20, ≥$1000 = 16, ≥$750 = 12,                  │     │
│  │      ≥$500 = 8, ≥$200 = 4, <$200 = 0                        │     │
│  │                                                              │     │
│  │ 2. Client Verification (use defaults if missing):           │     │
│  │    - Payment verified = 8 pts, Not verified = 0            │     │
│  │    - Rating ≥4.8 = 8,≥4.5=6,≥4.0=4,≥3.5=2 (default 4.0)    │     │
│  │    - Feedback ≥20 = 4,≥5=2,<5=0 (default 5)                 │     │
│  │                                                              │     │
│  │ 3. Requirements Clarity:                                    │     │
│  │    - Length ≥1000char=10,≥500=8,≥300=6,≥200=4,<200=0      │     │
│  │    - Has 4+ quality indicators = 10, 2-3 = 6, 1 = 2, 0 = 0 │     │
│  │      (requirements, deliverables, timeline, specs, format)  │     │
│  │                                                              │     │
│  │ 4. AI Technical Fit (NEW - check for AI Systems Engineering):│   │
│  │    a) AI/LLM Core Skills (max 7): Ai agents, LLM APIs,     │     │
│  │       autonomous agents, LangChain, LangGraph, etc.        │     │
│  │    b) RAG & Vector Systems (max 5): RAG, vector databases, │     │
│  │       semantic search, knowledge bases, embeddings         │     │
│  │    c) AI Integration & Automation (max 4): API integration, │     │
│  │       business automation, workflow automation             │     │
│  │    d) Local AI & Infrastructure (max 2): self-hosted AI,   │     │
│  │       Docker, deployment, production infrastructure        │     │
│  │    e) Voice & Multimodal AI (max 1): Twilio, voice agents, │     │
│  │       STT/TTS                                              │     │
│  │    f) Backend & Frontend AI (max 1): FastAPI, React,       │     │
│  │       full-stack AI                                        │     │
│  │                                                              │     │
│  │ 5. Timeline:                                                │     │
│  │    - Reasonable timeline = 16, No timeline = 10,           │     │
│  │      Urgent/rush = 4                                       │     │
│  │                                                              │     │
│  │ Return JSON with:                                            │     │
│  │ {                                                            │     │
│  │   'budget_score': 0-20,                                      │     │
│  │   'budget_explanation': '...',                              │     │
│  │   'client_verification_score': 0-20,                         │     │
│  │   'client_verification_explanation': '...',                 │     │
│  │   'requirements_clarity_score': 0-20,                       │     │
│  │   'requirements_clarity_explanation': '...',                │     │
│  │   'ai_technical_fit_score': 0-20,                           │     │
│  │   'ai_technical_fit_explanation': '...',                    │     │
│  │   'ai_technical_fit_breakdown': {                           │     │
│  │     'ai_llm_core': 0-7,                                     │     │
│  │     'rag_vector': 0-5,                                      │     │
│  │     'ai_integration_automation': 0-4,                      │     │
│  │     'local_ai_infrastructure': 0-2,                         │     │
│  │     'voice_multimodal': 0-1,                                │     │
│  │     'backend_frontend_ai': 0-1                              │     │
│  │   },                                                        │     │
│  │   'timeline_score': 0-20,                                   │     │
│  │   'timeline_explanation': '...',                            │     │
│  │   'total_score': 0-100,                                     │     │
│  │   'priority': 'High'/'Medium'/'Low'/'Very Low',            │     │
│  │   'go_decision': true/false,                                │     │
│  │   'summary': '...'                                          │     │
│  │ }"                                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Output: Structured JSON evaluation per job                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 4. Database Schema

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Schema                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ jobs                                                             │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ • id              UUID   PRIMARY KEY                           │ │
│  │ • title           TEXT                                          │ │
│  │ • url             TEXT   UNIQUE                                │ │
│  │ • description     TEXTBLOB                                      │ │
│  │ • budget_amount   DECIMAL                                       │ │
│  │ • budget_type     ENUM('fixed','hourly')                       │ │
│  │ • hour_min        DECIMAL                                       │ │
│  │ • hour_max        DECIMAL                                       │ │
│  │ • skills          JSONB[]                                       │ │
│  │ • type            ENUM('fixed','hourly')                       │ │
│  │ • ts_publish      TIMESTAMP                                     │ │
│  │ • ts_imported     TIMESTAMP  DEFAULT NOW()                     │ │
│  │ • raw_data        JSONB      (original Apify data)             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ evaluations                                                      │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ • id                  UUID   PRIMARY KEY                       │ │
│  │ • job_id              UUID   FOREIGN KEY (jobs.id)            │ │
│  │ • budget_score        SMALLINT (0-20)                          │ │
│  │ • client_verification_score SMALLINT (0-20)                    │ │
│  │ • requirements_clarity_score SMALLINT (0-20)                   │ │
│  │ • ai_technical_fit_score SMALLINT (0-20)                       │ │
│  │ • timeline_score      SMALLINT (0-20)                          │ │
│  │ • total_score         SMALLINT (0-100)                         │ │
│  │ • priority            VARCHAR(20)                              │ │
│  │ • go_decision         BOOLEAN                                  │ │
│  │ • score_breakdown     JSONB   (detailed scores per sub-crit.)  │ │
│  │ • summary             TEXT                                    │ │
│  │ • ts_evaluated        TIMESTAMP DEFAULT NOW()                  │ │
│  │ • llm_model           VARCHAR(50) DEFAULT 'cerebras-glm-4.7'   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ tech_trends                                                      │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ • id                  UUID   PRIMARY KEY                       │ │
│  │ • technology          VARCHAR(100) UNIQUE                      │ │
│  │ • category            VARCHAR(50)                               │ │
│  │ • job_count           INTEGER                                  │ │
│  │ • last_seen           TIMESTAMP                                 │ │
│  │ • trend_score         DECIMAL (computed: recent frequency)    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ keyword_stats                                                    │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ • id                  UUID   PRIMARY KEY                       │ │
│  │ • keyword             VARCHAR(100) UNIQUE                      │ │
│  │ • category            VARCHAR(50)                              │ │
│  │ • frequency           INTEGER                                  │ │
│  │ • jobs_mentioned      INTEGER                                  │ │
│  │ • last_updated        TIMESTAMP DEFAULT NOW()                  │ │
│  │ • trend_change        DECIMAL (delta vs previous period)       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ market_pulse                                                     │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │ • id                  UUID   PRIMARY KEY                       │ │
│  │ • period_start        TIMESTAMP                                 │ │
│  │ • period_end          TIMESTAMP                                 │
│  │ • total_jobs_analyzed INTEGER                                  │ │
│  │ • avg_budget          DECIMAL                                   │ │
│  │ • avg_score           DECIMAL                                   │
│  │ • top_technologies    JSONB                                     │ │
│  │ • emerging_keywords   JSONB                                     │
│  │ • declining_keywords  JSONB                                     │
│  │ • insights            JSONB                                     │
│  │ • ts_generated        TIMESTAMP DEFAULT NOW()                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Points We Track & Update

### 1. **Criteria** (`CRITERIA_AI_SYSTEMS_ENGINEER.md`)
**Purpose**: Defines how jobs are scored
**Updated by**: Manual review (initial) → periodic refinement based on results
**Data points**:
- Budget thresholds ($2000, $1000, $750, $500, $200)
- Client verification scoring rules
- Requirements clarity indicators
- AI Technical Fit keywords (6 sub-criteria with 100+ keywords)
- Timeline scoring rules
- Overall priority thresholds (≥70 High, ≥50 Medium, ≥40 Low)

**Update triggers**:
- You provide new keyword list from fresh Apify file
- Market analysis shows emerging technologies
- Scoring accuracy needs adjustment

---

### 2. **Keywords & Tech Stack** (`KEYWORD_STRATEGY_UPDATED.md`)
**Purpose**: Capture market demand for technologies
**Updated by**: Agent analyzing Apify files → keyword frequency tracking
**Data points**:
| Category | Keywords | Frequency | Trend |
|----------|----------|-----------|-------|
| AI/LLM Core | ai agent, agent, llm, etc. | Count per period | Rising/Stable/Falling |
| RAG & Vector | rag, vector database, etc. | Count per period | Rising/Stable/Falling |
| Voice AI | twilio, elevenlabs, etc. | Count per period | Rising/Stable/Falling |
| Backend | fastapi, python, etc. | Count per period | Rising/Stable/Falling |
| Frontend | react, next.js, etc. | Count per period | Rising/Stable/Falling |
| Integration | api, webhook, business automation, workflow automation | Count per period | Rising/Stable/Falling |

**Update triggers**:
- Every Apify file processing run
- New keywords detected in job descriptions
- Frequency changes indicate market shift

---

### 3. **Tech Stack Comparison** (`TECH_STACK_COMPARISON.md` - TO BE CREATED)
**Purpose**: Track gap between market demand and your expertise
**Updated by**: Agent analyzing keywords + job data
**Data points**:
| Your Stack | Market Demand | Status | Gap Analysis |
|------------|---------------|--------|--------------|
| Python | 14% | ✅ In market | Match |
| FastAPI | 3% | ✅ In market | Match |
| React | 11% | ✅ In market | Match |
| PostgreSQL | 3% | ✅ In market | Match |
| Milvus | Emerging | ⚠️ New demand | Review (optional: if client requests) |
| CAMEL | Niche | ⚠️ Multi-agent framework | Review (optional: if client requests) |
| FAISS | Niche | ⚠️ Vector search library | Already covered by vector DB knowledge |
| BabyAGI | Niche | ⚠️ Experimental | Concept knowledge only |

**Update triggers**:
- Fresh Apify file analysis
- New technologies appear in top keywords
- Existing skills need validation

---

### 4. **Market Pulse** (Database table `market_pulse`)
**Purpose**: Aggregate insights about job market trends
**Updated by**: Agent after each evaluation batch
**Data points**:
- Total jobs analyzed per period
- Average budget across all jobs
- Average score (selectivity of market)
- Top 10 technologies by frequency
- Emerging keywords (new or rising)
- Declining keywords (falling demand)
- AI-generated insights (e.g., "Voice AI +15% this month")

**Update triggers**:
- After each Apify file processing run
- Weekly/periodic aggregation queries
- On-demand analysis request

---

### 5. **Tech Trends** (Database table `tech_trends`)
**Purpose**: Track individual technology popularity over time
**Updated by**: Agent extracting keywords from job descriptions
**Data points**:
| Technology | Category | Job Count (last 30d) | Job Count (last 90d) | Trend Score | Last Seen |
|------------|----------|---------------------|---------------------|-------------|------------|
| ai agent | AI/LLM Core | 45 | 120 | 0.375 | 2026-02-05 |
| rag | RAG | 8 | 30 | 0.267 | 2026-02-05 |
| voice ai | Voice | 12 | 25 | 0.480 | 2026-02-05 |
| twilio | Voice | 14 | 40 | 0.350 | 2026-02-05 |

**Trend Score Formula**: `(recent_count / historical_count)`

**Update triggers**:
- Every job evaluation (extract keywords)
- Daily batch jobs to recalculate trend scores

---

### 6. **Keyword Stats** (Database table `keyword_stats`)
**Purpose**: Track keyword frequency at granular level
**Updated by**: Agent analyzing job text
**Data points**:
| Keyword | Category | Frequency | Jobs Mentioned | Last Updated | Trend Change |
|---------|----------|-----------|----------------|--------------|--------------|
| ai agent | AI/LLM Core | 92 | 92 | 2026-02-05 | +5% |
| rag | RAG | 18 | 18 | 2026-02-05 | +2% |
| twilio | Voice | 14 | 14 | 2026-02-05 | +8% |

**Trend Change**: Percentage change vs previous period

**Update triggers**:
- Every job evaluation (keyword extraction)
- Weekly aggregation (compute trend changes)

---

### 7. **Budget Trends** (Derived from `jobs` table)
**Purpose**: Track compensation patterns
**Updated by**: Queries on job data
**Data points**:
- Average budget by job type (fixed/hourly)
- Budget distribution (percentiles: 25th, 50th, 75th)
- Budget vs. score correlation
- Budget trends over time

**Update triggers**:
- After Apify file processing runs
- Weekly analysis queries

---

### 8. **Quality Signals** (Derived from `evaluations` table)
**Purpose**: Understand job posting quality
**Updated by**: Queries on evaluation data
**Data points**:
- Average requirements clarity score
- Percentage of jobs with go_decision=true
- Top-scoring job categories
- Common dealbreakers (what causes low scores)

**Update triggers**:
- After evaluation batches
- Periodic analysis

---

## Missing Data Points (What Else Might We Need?)

| Category | Data Point | Description | Importance |
|----------|------------|-------------|------------|
| **Proposal Success** | applied_jobs | Jobs you actually applied to | Track conversion rate |
| **Proposal Success** | proposal_response | Whether client responded | Track engagement quality |
| **Proposal Success** | won_jobs | Jobs you won | Track actual ROI |
| **Proposal Success** | client_feedback_rated | Client rating on completed jobs | Validate scoring accuracy |
| **Skill Validation** | skill_learning_log | New skills learned | Track growth areas |
| **Skill Validation** | job_complexity_rating | Your perceived difficulty | Compare to AI score |
| **Market Timing** | seasonality_patterns | Monthly volume variations | Optimize applying timing |
| **Competition** | applicant_count | Number of freelancers applied | Gauge competition |
| **Competition** | avg_client_hire_rate | % of jobs client actually hires | Validate budget signals |
| **Personal Fit** | domain_alignment | Your past project relevance | Pre-filter by domain |

---

## Data Flow Summary

```
┌───────────┐
│   INPUT   │ Apify CSV/JSON file (fresh job data)
└─────┬─────┘
      │
      ▼
┌───────────────────────────────────────────────────────────┐
│                PROCESSING LAYER (App)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Loader  │→│Enricher │→│Evaluator│→│  Store  │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│                                                   ▼        │
│                                          ┌────────────┐    │
│                                          │ PostgreSQL │    │
│                                          └────────────┘    │
└───────────────────────────────────────────────────────────┘
      │
      ▼
┌───────────┐
│  OUTPUT   │ Ranked jobs + score breakdowns + market insights
└───────────┘
      │
      ▼
┌───────────┐
│  ACTION   │ Your decision: apply / skip / research gap
└───────────┘
```

---

## Decisions Made (Configuration Set)

| Question | Decision | Notes |
|----------|----------|-------|
| **Output Format** | ✅ Markdown | Terminal display |
| **Result Persistence** | ✅ Keep all evaluations | Need complete data for analysis |
| **Keyword Update Frequency** | ✅ Auto on every run | Confirm changes before applying |
| **Market Pulse Period** | ✅ Daily | Stats can be added later |
| **Scoring Validation** | ⏸️ TBD | "IDK" - will decide later |
| **Telegram Bot Integration** | ✅ Later (Phase 2) | Terminal-first approach |
| **Rate Limiting** | ✅ Cerebras GLM 4.7 limits | Based on $200/month code plan |
| **Budget Cutoff** | ✅ Min $500 | Jobs below $500 score 0 points |
| **Tech Trend Alert** | ✅ No alerts | Just accumulate data for retrieval |
| **Skill Gap Tracking** | ✅ Auto-mark | Automatically flag missing tech as "learn priority" |

---

## What's Left to Decide (Open Questions)

| Question | Status |
|----------|--------|
| **Scoring Validation** | ⏸️ TBD - Will decide later (human review, sample, none) |

---

**Document Created**: 2026-02-05
**Purpose**: Architecture reference for Upwork Processing App development