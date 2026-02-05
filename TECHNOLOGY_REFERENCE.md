# Technology Quick Reference

**Purpose**: Brief explanations of keywords mentioned in the app

---

## Vector Databases & Search

### FAISS (Facebook AI Similarity Search)
**What it is**: Open-source library by Meta for efficient similarity search and clustering of dense vectors.

**Who uses it**: Companies building large-scale RAG systems with millions of vectors. Works well when you need custom indexing strategies and are comfortable running your own vector search layer.

**Relevance to you**: If a client wants a custom RAG solution with specific performance requirements, they might mention FAISS. You can implement RAG using pgvector instead, but should know what FAISS is when mentioned.

**Your stack alternative**: PostgreSQL + pgvector (simpler, integrated with database)

---

### Milvus
**What it is**: Open-source vector database (40k+ GitHub stars) for storing, indexing, and managing massive embedding vectors. Has a managed version (Zilliz Cloud).

**Who uses it**: Enterprise companies with large-scale AI applications needing high-performance vector search. Supports data-in/data-out (can handle embeddings directly in v2.6+).

**Relevance to you**: Alternative to Pinecone/Qdrant/Weaviate. If a client has existing Milvus infrastructure, they might request skills with it.

**Your stack alternative**: PostgreSQL + pgvector, or you can learn Milvus if client needs it.

---

## Multi-Agent Frameworks

### CAMEL
**What it is**: "Communicative Agents for Mind Exploration" - an open-source framework (15.9k stars) for building multi-agent systems. Provides primitives for creating agents, societies (groups of agents with roles), memory, RAG pipelines, and synthetic data generation.

**Who uses it**: Researchers and developers building sophisticated multi-agent systems with role-playing between agents (e.g., Planner + Researcher + Writer agents collaborating).

**Relevance to you**: You work on agent architecture. If a client wants a multi-agent system, they might mention CAMEL or ask about frameworks.

**Your stack alternative**: You typically build agents using LangChain + custom Python patterns, but CAMEL is another option to be aware of.

---

### BabyAGI
**What it is**: Experimental autonomous agent framework (22k stars) for task management. It creates, prioritizes, and executes tasks iteratively to work toward a goal.

**Who uses it**: Proof-of-concept autonomous systems, experimental AI workflows.

**Relevance to you**: More of a conceptual reference. If clients mention "BabyAGI-style agents", they want autonomous task execution without human hand-holding.

**Your stack alternative**: You build custom agent orchestration using Pydantic AI or LangChain's agent patterns.

---

## Processing Layer Components

### Enricher (`features/job_processing/enricher.py`)
**Purpose**: Add metadata and analysis to raw job data before LLM evaluation.

**What it does**:
1. **Extract keywords**: Scan job title + description for all tracked keywords (AI agents, RAG, voice, etc.)
2. **Compute technology tags**: Identify technologies mentioned (FastAPI, React, PostgreSQL, Twilio, etc.)
3. **Add metadata fields**:
   - `extracted_keywords`: Array of keywords found
   - `tech_tags`: High-level technology categories
   - `estimated_complexity`: Simple heuristic (based on description length + keyword density)
   - `domain_signals`: Industry indicators (healthcare, fintech, SaaS, etc.)
4. **Flag potential issues**: Very short descriptions, missing budget, urgent timeline

**Why it exists**: LLM evaluation is expensive. Pre-filtering with keyword extraction lets you:
- Track keyword frequency for market trends
- Quickly filter out completely irrelevant jobs (no AI keywords)
- Provide context to LLM for faster scoring

**Input**: Raw job from Apify (title, description, skills, budget)
**Output**: Enriched job with metadata + keyword matches

---

### Evaluator (`features/job_processing/evaluator.py`)
**Purpose**: Call Cerebras GLM 4.7 LLM to score jobs against the 5 criteria.

**What it does**:
1. **Build LLM prompt**: Combine job data + criteria rules into a prompt
2. **Rate-limited async calls**: Use semaphore to limit concurrent requests (prevents API overload)
3. **Parse LLM response**: Extract JSON scores from Cerebras output
4. **Validate scores**: Ensure scores are 0-20, total is 0-100, format is correct
5. **Store results**: Write evaluation to database (`evaluations` table)

**Rate limiting behavior**:
- Uses `asyncio.Semaphore(N)` where N = max concurrent requests
- Waits for available slot before sending request
- Respects Cerebras API rate limits (your $200/month plan)

**Error handling**:
- Retry failed requests (exponential backoff)
- Log malformed LLM responses
- Store partial results if possible

**Input**: Enriched job data
**Output**: Structured JSON evaluation:
```json
{
  "budget_score": 16,
  "client_verification_score": 4,
  "requirements_clarity_score": 12,
  "ai_technical_fit_score": 14,
  "timeline_score": 10,
  "total_score": 56,
  "priority": "Medium",
  "go_decision": true,
  "summary": "Good match. Meets key criteria.",
  "ai_technical_fit_breakdown": {
    "ai_llm_core": 5,
    "rag_vector": 3,
    "integration_automation": 3,
    "local_ai_infrastructure": 2,
    "voice_multimodal": 1,
    "backend_frontend_ai": 0
  }
}
```

---

## Visual Summary

```
                        Raw Apify Job
                              │
                              ▼
         ┌──────────────────────────────────────┐
         │             ENRICHER                 │
         │  • Extract keywords                 │
         │  • Identify technologies             │
         │  • Add metadata                      │
         │  • Enrich data structure             │
         └──────────────────┬───────────────────┘
                              │
                              ▼
                      Enriched Job
                              │
                              ▼
         ┌──────────────────────────────────────┐
         │            EVALUATOR                 │
         │  • Build LLM prompt                  │
         │  • Rate-limited API calls            │
         │  • Parse Cerebras response           │
         │  • Validate scores                   │
         │  • Store to database                 │
         └──────────────────┬───────────────────┘
                              │
                              ▼
                       Ranked Job
                              │
                              ▼
                    Display to user
```

---

## Key Differences

| Component | Input | Primary Function | Output |
|-----------|-------|------------------|--------|
| **Enricher** | Raw job data | Keyword extraction, metadata extraction | Enriched job (with keywords, tech tags) |
| **Evaluator** | Enriched job data | LLM scoring against criteria | Evaluation results (scores, priority, breakdown) |

**Enricher** = Fast, deterministic keyword/tech extraction (no AI)
**Evaluator** = Slower, AI-powered scoring (uses Cerebras GLM 4.7)

---

**Document Created**: 2026-02-05
**Purpose**: Quick reference for technologies and processing components