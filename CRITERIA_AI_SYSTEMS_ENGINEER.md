# AI Systems Engineer - Job Evaluation Criteria

**Purpose**: Evaluate Upwork jobs against AI Systems Engineer expertise areas
**Based on**: `AI_SYSTEMS_ENGINEER_PROFILE.md` + 100-job market analysis
**Date**: 2026-02-05

---

## Overview

This criteria file replaces upflow's data-scraping focused "Technical Feasibility" with AI Systems Engineering focus. It maintains upflow's 5-criteria framework (0-20 points each, max 100 total) but adjusts scoring to target production-grade AI infrastructure roles.

---

## Five Criteria Framework

| Criterion | Weight | Description | Status |
|-----------|--------|-------------|--------|
| **1. Budget** | 0-20 | Project budget vs. minimum threshold | Keep as-is |
| **2. Client Verification** | 0-20 | Payment verification, rating, history | Use defaults (Apify limitation) |
| **3. Requirements Clarity** | 0-20 | Description quality, detail level | Keep as-is |
| **4. AI Technical Fit** | 0-20 | **NEW**: AI Systems Engineering relevance | Replace Technical Feasibility |
| **5. Timeline** | 0-20 | Project timeline expectations | Keep as-is |

---

## Criterion Design Decisions

### Why Fix Client Verification?
**Problem**: Apify doesn't provide payment verification, client rating, or feedback count.

**Solution**: Use default values for missing data:
- `payment_verified` = False (0 points for this sub-criterion)
- `client_rating` = 4.0 (neutral middle value, 4 points)
- `client_feedback_count` = 5 (minimal history, 0 points)

**Impact**: Client verification will almost always score 4/20 points, making other criteria more influential.

---

### Why Replace Technical Feasibility?
**Problem**: upflow's "Technical Feasibility" checks for web scraping skills and penalizes complexity—misaligned with AI Systems Engineer role.

**Original upflow criteria** (lines 290-331 in `parse_upwork_tasks_v2.py`):
- Data extraction skills (scraping, mining) - 0-10 points
- Technical complexity penalty (payment processing, DocuSign, etc.) - 0-10 points

**Solution**: Replace with "AI Technical Fit" checking for:
- AI/LLM core skills (agents, APIs, multi-step reasoning)
- RAG & vector systems (databases, semantic search)
- AI integration & automation (APIs, workflows)
- Local AI & infrastructure (self-hosted, Docker, deployment)
- Voice & multimodal AI (STT/TTS, WebRTC, voice agents)
- Backend & frontend AI (FastAPI, React, full-stack)

---

## Detailed Criteria Scoring

### Criterion 1: Budget (0-20 points)

**Note**: Minimum acceptable budget is $500. Jobs below $500 score 0 points.

| Score Range | Budget Amount | Quality Rating |
|-------------|---------------|----------------|
| 20 | ≥ $2,000 | Excellent - Well above minimum threshold |
| 16 | ≥ $1,000 | Very good - High priority range |
| 12 | ≥ $750 | Good - Medium priority range |
| 8 | ≥ $500 | Acceptable - Meets minimum threshold |
| 0 | < $500 | Too low - Below minimum threshold |

**Implementation**:
```python
if budget >= 2000: score = 20
elif budget >= 1000: score = 16
elif budget >= 750: score = 12
elif budget >= 500: score = 8
else: score = 0  # Below $500 = 0 points
```

---

### Criterion 2: Client Verification (0-20 points)

| Sub-Criterion | Points | Criteria | Notes |
|---------------|--------|----------|-------|
| Payment Verified | 0-8 | Payment method verified by Upwork | Default: False (0 points, Apify limitation) |
| Client Rating | 0-8 | ≥ 4.8 (8), ≥ 4.5 (6), ≥ 4.0 (4), ≥ 3.5 (2) | Default: 4.0 (4 points, neutral) |
| Feedback Count | 0-4 | ≥ 20 reviews (4), ≥ 5 reviews (2), < 5 reviews (0) | Default: 5 (2 points, minimal history) |

**With Defaults (Apify data)**: 4 points (payment not verified + neutral rating + minimal history)

**Implementation**:
```python
score = 0
if payment_verified: score += 8  # Default: False → 0 points
if client_rating >= 4.8: score += 8
elif client_rating >= 4.5: score += 6
elif client_rating >= 4.0: score += 4  # Default: 4.0 → 4 points
elif client_rating >= 3.5: score += 2

if client_feedback_count >= 20: score += 4
elif client_feedback_count >= 5: score += 2  # Default: 5 → 2 points
```

---

### Criterion 3: Requirements Clarity (0-20 points)

| Sub-Criterion | Points | Criteria |
|---------------|--------|----------|
| Description Length | 0-10 | ≥ 1000 chars (10), ≥ 500 (8), ≥ 300 (6), ≥ 200 (4), < 200 (0) |
| Quality Indicators | 0-10 | Contains 4+ of: requirements, deliverables, timeline, specifications, format |

**Implementation**:
```python
score = 0
if len(description) >= 1000: score += 10
elif len(description) >= 500: score += 8
elif len(description) >= 300: score += 6
elif len(description) >= 200: score += 4

quality_indicators = ["requirements", "deliverables", "timeline", "specifications", "format"]
quality_count = sum(1 for i in quality_indicators if i in description.lower())
if quality_count >= 4: score += 10
elif quality_count >= 2: score += 6
elif quality_count >= 1: score += 2
```

---

### Criterion 4: AI Technical Fit (0-20 points) - NEW

**Purpose**: Evaluate job relevance to AI Systems Engineer expertise areas. Unlike upflow's data-scraping focus, this checks for AI infrastructure skills: agents, RAG, local deployment, integration, voice, and full-stack AI.

| Sub-Criterion | Max Points | Evaluation Criteria |
|---------------|------------|---------------------|
| **4A. AI/LLM Core Skills** | 7 | AI agents, LLM APIs, multi-agent systems, autonomous reasoning |
| **4B. RAG & Vector Systems** | 5 | Vector databases, semantic search, knowledge bases, document intelligence |
| **4C. AI Integration & Automation** | 4 | API integration with AI, workflow automation, webhooks |
| **4D. Local AI & Infrastructure** | 2 | Self-hosted AI, Docker, deployment, production infrastructure |
| **4E. Voice & Multimodal AI** | 1 | STT/TTS, WebRTC, voice agents, multimodal AI (bonus points for emerging tech) |
| **4F. Backend & Frontend AI** | 1 | FastAPI, async Python, React, full-stack AI (contextual fit) |

---

#### 4A. AI/LLM Core Skills (0-7 points)

**Keywords to check** (from expertise areas + job analysis):
- **Core terms**: `ai agent`, `agent`, `ai`, `llm`, `language模型`, `gpt`, `claude`, `openai`, `anthropic`
- **Agent patterns**: `multi-agent`, `autonomous agent`, `agentic workflow`, `agent architecture`, `conversational agent`, `ai assistant`, `intelligent agent`, `multi-step reasoning`, `agent orchestration`, `tool calling`, `function calling`, `state management`
- **Agent systems**: `langchain`, `langgraph`, `crewai`, `autogpt`, `babyagi`, `camel`, `pydantic ai`

**Scoring**:
```python
ai_llm_keywords = [
    # Core terms (weight: 2 each)
    "ai agent", "multi-agent", "autonomous agent", "agentic workflow",
    # High-value patterns (weight: 3 each)
    "agent architecture", "agent orchestration", "multi-step reasoning",
    "tool calling", "function calling", "state management", "langchain", "langgraph",
    # General terms (weight: 1 each)
    "ai", "agent", "llm", "gpt", "claude", "openai", "anthropic",
    "conversational agent", "ai assistant", "intelligent agent"
]

# Calculate weighted score (capped at 7 points)
# Core terms: 2 points, High-value: 3 points, General: 1 point
score = min(7, weighted_keyword_match_count)
```

| Score | Criteria |
|-------|----------|
| 7 | 3+ high-value or 2 core + 2 general AI/LLM terms |
| 6 | 2 high-value or 1 core + 3 general terms |
| 5 | 1 high-value or 2+ core terms |
| 4 | 1 core + 1-2 general terms |
| 3 | 2-3 general AI/LLM terms |
| 2 | 1 general AI/LLM term |
| 0 | No AI/LLM keywords |

---

#### 4B. RAG & Vector Systems (0-5 points)

**Keywords to check**:
- **Core RAG**: `rag`, `rag system`, `retrieval augmented generation`, `retrieval augmented`
- **Vector/database**: `vector database`, `vector search`, `pgvector`, `pinecone`, `qdrant`, `chromadb`, `faiss`, `milvus`, `weaviate`
- **Search/knowledge**: `semantic search`, `knowledge base`, `knowledge graph`, `neo4j`, `elastic search`, `elasticsearch`
- **Document processing**: `document intelligence`, `document retrieval`, `document processing`, `pdf processing`, `chunking`, `embedding`, `embeddings`, `docling`, `text embedding`

**Scoring**:
```python
rag_keywords = {
    "core": ["rag", "rag system", "retrieval augmented generation", "retrieval augmented"],
    "vector_db": ["vector database", "vector search", "pgvector", "pinecone", "qdrant", "chromadb", "faiss", "milvus", "weaviate"],
    "search_kb": ["semantic search", "knowledge base", "knowledge graph", "neo4j", "elasticsearch"],
    "docs": ["document intelligence", "document retrieval", "document processing", "pdf processing", "chunking", "embedding", "embeddings", "docling"]
}

# Weighted: core (2), vector_db (1), search_kb (1), docs (1)
score = min(5, weighted_keyword_match_count)
```

| Score | Criteria |
|-------|----------|
| 5 | 1+ "rag" + 2 vector/doc terms |
| 4 | 1+ "rag" + 1 vector/doc term |
| 3 | 2+ vector/doc terms (no "rag") |
| 2 | 1 vector/doc term |
| 1 | 1+ search/knowledge term |
| 0 | No RAG/vector keywords |

---

#### 4C. AI Integration & Automation (0-4 points)

**Keywords to check**:
- **Integration**: `api integration`, `webhook integration`, `ai integration`, `third-party integration`, `system integration`, `service integration`
- **Automation**: `workflow automation`, `business automation`, `web automation`, `automation`
- **API keywords**: `rest api`, `graphql`, `api`, `webhook`, `api endpoint`, `api call`

**Scoring**:
```python
integration_keywords = {
    "high_value": ["workflow automation", "business automation"],  # 2 points each
    "medium_value": ["api integration", "webhook integration", "ai integration", "third-party integration"],  # 1 point each
    "general": ["api", "webhook", "automation"],  # 0.5 points each
}

score = min(4, weighted_keyword_match_count)
```

| Score | Criteria |
|-------|----------|
| 4 | 2+ high-value automation terms OR 1 high-value + 2 integration terms |
| 3 | 1 high-value + 1 integration term |
| 2 | 1 high-value OR 2+ integration terms |
| 1 | 1 integration term OR 2+ general automation terms |
| 0 | No integration/automation keywords |

---

#### 4D. Local AI & Infrastructure (0-2 points)

**Keywords to check**:
- **Hosting**: `self-hosted`, `self hosted`, `local llm`, `local ai`, `on-premise`, `on-premise deployment`, `on-premises`
- **Deployment**: `deployment`, `production`, `production-ready`, `production ai`, `ai deployment`, `docker`, `docker compose`, `kubernetes`, `k8s`
- **Infrastructure**: `ai infrastructure`, `infrastructure`, `scaling`, `cost optimization`, `latency optimization`
- **Tools**: `ollama`, `vllm`, `litellm`, `cerebras`, `model serving`, `inference`

**Scoring**:
```python
local_ai_keywords = {
    "hosting": ["self-hosted", "self hosted", "local llm", "local ai", "on-premise", "on premise"],  # 1 point each
    "deployment": ["docker", "docker compose", "kubernetes", "k8s", "deployment", "production ai"],  # 0.5 points each
}

score = min(2, weighted_keyword_match_count)
```

| Score | Criteria |
|-------|----------|
| 2 | 1+ hosting term OR 2+ deployment terms |
| 1 | 1 deployment term |
| 0 | No local AI/infrastructure keywords |

---

#### 4E. Voice & Multimodal AI (0-1 point)

**Keywords to check**:
- **Voice**: `ai voice agent`, `voice ai`, `voice agent`, `text-to-speech`, `tts`, `speech-to-text`, `stt`, `voice chatbot`, `voice assistant`
- **Tools**: `twilio`, `elevenlabs`, `bland ai`, `synthflow`, `voiceflow`, `deepgram`, `play.ht`, `daily.co`, `webrtc`, `pipecat`
- **Multimodal**: `multimodal`, `audio processing`, `speech recognition`, `speech synthesis`

**Scoring**:
```python
voice_keywords = [
    "ai voice agent", "voice ai", "voice agent", "text-to-speech", "tts",
    "speech-to-text", "stt", "twilio", "elevenlabs", "bland ai", "synthflow",
    "deepgram", "webrtc", "daily.co", "pipecat", "multimodal ai", "voice chatbot", "voice assistant"
]

score = 1 if any(keyword in text.lower() for keyword in voice_keywords) else 0
```

| Score | Criteria |
|-------|----------|
| 1 | Any voice/multimodal keyword |
| 0 | No voice/multimodal keywords |

*Note: User has proven experience via SolarVox project (Deepgram STT/TTS + Daily.co WebRTC + OpenAI Pipecat pipeline)*

---

#### 4F. Backend & Frontend AI (0-1 point)

**Keywords to check**:
- **Backend**: `fastapi`, `python`, `async python`, `backend`, `api development`, `rest api`
- **Frontend**: `react`, `next.js`, `typescript`, `vue`, `frontend`, `full-stack`, `full stack`, `fullstack`

**Scoring** (only award if NOT already covered by other sub-criteria):
```python
backend_frontend_keywords = [
    "fastapi", "python", "async python", "backend", "api development",
    "react", "next.js", "typescript", "frontend", "full-stack", "fullstack"
]

# Only award this point if job shows full-stack intent (both backend + frontend)
has_backend = any(kw in text.lower() for kw in ["fastapi", "python", "backend", "api"])
has_frontend = any(kw in text.lower() for kw in ["react", "next.js", "typescript", "frontend"])

score = 1 if (has_backend and has_frontend) else 0
```

| Score | Criteria |
|-------|----------|
| 1 | Both backend AND frontend keywords (full-stack intent) |
| 0 | Single layer OR no keywords |

---

### Criterion 5: Timeline (0-20 points)

| Score | Criteria | Notes |
|-------|----------|-------|
| 16 | Reasonable timeline indicated | Keywords: "2 weeks", "two weeks", "14 days", "reasonable timeline" |
| 10 | No explicit timeline information | Default: neutral middle score |
| 4 | Urgent/rush timeline | Keywords: "urgent", "asap", "immediately", "rush", "quick turnaround" |

**Implementation**:
```python
score = 10  # Default: neutral

rush_indicators = ["urgent", "asap", "immediately", "rush", "quick turnaround"]
if any(indicator in description.lower() for indicator in rush_indicators):
    score = 4

reasonable_indicators = ["2 weeks", "two weeks", "14 days", "reasonable timeline"]
if any(indicator in description.lower() for indicator in reasonable_indicators):
    score = 16
```

---

## Overall Scoring & Fit Score

### Total Score (0-100)
```python
total_score = (
    budget_score +
    client_verification_score +
    requirements_clarity_score +
    ai_technical_fit_score +
    timeline_score
)
```

### Priority Classification

| Total Score | Priority | Go Decision | Summary |
|-------------|----------|-------------|---------|
| ≥ 70 | High | ✅ Yes | Excellent match. Meets most criteria. Recommended. |
| ≥ 50 | Medium | ✅ Yes | Good match. Meets key criteria. Worth considering. |
| ≥ 40 | Low | ❌ No | Marginal match. Some criteria met but significant drawbacks. |
| < 40 | Very Low | ❌ No | Poor match. Fails most criteria. Not recommended. |

---

## Implementation Notes

### Data Source Compatibility

| Data Field | Source | Availability | Notes |
|------------|--------|--------------|-------|
| Budget | Apify (`fixed.budget.amount`) | ✅ Yes | Use fixed price or hourly equivalent |
| Payment Verified | Not in Apify | ❌ No | Use default: False |
| Client Rating | Not in Apify | ❌ No | Use default: 4.0 |
| Feedback Count | Not in Apify | ❌ No | Use default: 5 |
| Description | Apify (`description`) | ✅ Yes | Full text available |
| Skills | Apify (`skills`) | ✅ Yes | Optional: Enhance title/description matching |

### Keyword Matching Strategy

1. **Case-insensitive matching**: Convert all text to lowercase before matching
2. **Weighted scoring**: Different keywords have different point values
3. **Per-category caps**: Each sub-criterion has a maximum score
4. **Evidence extraction**: Extract relevant excerpts for explanation

---

## Simplified Architecture (No Enricher for MVP)

### Original Architecture (from ARCHITECTURE.md)

```
Apify File → Load → Enrich → Evaluate (LLM) → Store → Rank → Display
                          ↓                     ↓
                    Keyword extraction    PostgreSQL DB
                    (no AI)               (all data)
```

### MVP Architecture (Simplified - No Enricher)

```
Apify File → Load → Evaluate (LLM) → Store → Rank → Display
                     ↓                ↓
                Cerebras GLM 4.7  PostgreSQL DB
                (scoring)         (all data)
```

**Change**: Enricher removed for MVP. Keyword extraction and analysis happens inline in the evaluator via LLM scoring.

**Rationale**:
- Simplifies initial implementation
- LLM can extract keywords and score in one pass
- Enricher can be added later if needed for performance optimization

---

## Comparison to upflow Original

| Aspect | upflow Original | AI Systems Engineer (This File) |
|--------|-----------------|----------------------------------|
| **Budget** | Same thresholds | ✅ Same |
| **Client Verification** | Same logic | ✅ Same (but using defaults) |
| **Requirements Clarity** | Same indicators | ✅ Same |
| **Technical Focus** | Data scraping (scraping, mining) | ❌ Replaced with AI Systems (agents, RAG, integration) |
| **Technical Complexity** | Penalty for complexity (DocuSign, payment processing) | ❌ Removed - complexity is not negative for AI engineer |
| **Timeline** | Same logic | ✅ Same |
| **Total Score** | 0-100 | ✅ Same |

---

## Testing & Validation

### Test Cases

#### Case 1: High-Score Job (AI Agent + RAG + Full-Stack)
**Job Title**: "Build AI Agent for Document Search with RAG and React Dashboard"
**Budget**: $2,500
**Description**: "Need autonomous AI agent that can query our knowledge base using vector search (pgvector). The agent should use LangChain for orchestration and support multi-step reasoning with tool calling. Must integrate with our existing FastAPI backend and React dashboard UI."

**Expected Scores**:
- Budget: 20 ($2,500 ≥ $2,000)
- Client Verification: 4 (defaults)
- Requirements Clarity: 12 (good length, multiple quality indicators)
- AI Technical Fit:
  - AI/LLM: 7 (ai agent, autonomous agent, langchain, multi-step reasoning, tool calling)
  - RAG: 5 (vector search, knowledge base, pgvector)
  - Integration: 2 (integrate with backend)
  - Local AI: 0
  - Voice: 0
  - Backend/Frontend: 1 (fastapi + react)
  - **Subtotal**: 15
- Timeline: 10 (no explicit timeline)
- **Total**: 61 (Medium priority, go decision)

---

#### Case 2: High-Score Voice AI Job
**Job Title**: "Build Voice Agent using Twilio and Deepgram"
**Budget**: $3,000
**Description**: "Need AI voice agent for customer support. Must use Twilio for phone calls, Deepgram Nova-2 for STT/TTS, and OpenAI GPT-4o for conversations. Real-time streaming via WebRTC or Pipecat. Use tool calling for CRM integration."

**Expected Scores**:
- Budget: 20 ($3,000 ≥ $2,000)
- Client Verification: 4 (defaults)
- Requirements Clarity: 10 (adequate length)
- AI Technical Fit:
  - AI/LLM: 5 (voice agent, ai agent, tool calling)
  - RAG: 0
  - Integration: 2 (api integration)
  - Local AI: 0
  - Voice: 1 (twilio, deepgram, stt, tts, webrtc, pipecat)
  - Backend/Frontend: 0
  - **Subtotal**: 8
- Timeline: 4 (if urgent) or 10 (no timeline)
- **Total**: 46-52 (Low-Medium priority)

**Note**: Voice AI is a strength (proven via SolarVox project).

---

#### Case 3: Low-Score Job (Generic Web Scraping)
**Job Title**: "Scrape Product Data from E-commerce Sites"
**Budget**: $150
**Description**: "I need to scrape product prices from 10 websites daily. Data should be stored in a CSV file."

**Expected Scores**:
- Budget: 0 ($150 < $500)
- Client Verification: 4 (defaults)
- Requirements Clarity: 4 (minimal description)
- AI Technical Fit:
  - AI/LLM: 0 (no AI keywords)
  - RAG: 0
  - Integration: 1 (scrape implies some automation)
  - Local AI: 0
  - Voice: 0
  - Backend/Frontend: 0
  - **Subtotal**: 1
- Timeline: 10 (no explicit timeline)
- **Total**: 19 (Very Low priority, no-go)

---

## Next Steps

1. **Implement scoring logic** in job processing pipeline
2. **Validate with real jobs** from Apify CSV files
3. **Adjust weights** based on actual job relevance (tune over time)
4. **Consider LLM-based evaluation** for nuanced cases (Cerebras GLM 4.7)

---

**Document Created**: 2026-02-05
**Purpose**: Replace upflow's data-scraping criteria with AI Systems Engineering focus
**Total Criteria**: 5 (Budget, Client Verification, Requirements Clarity, AI Technical Fit, Timeline)
**Max Score**: 100 points
**Architecture**: Simplified (no enricher for MVP)