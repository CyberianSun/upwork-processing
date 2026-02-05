# Job Evaluation Criteria - Recommendations

**Last Updated:** 2026-02-04
**Purpose:** Compare old (upflow) vs. new (devpersona-based) criteria
**Objective:** Recommendations for updating job evaluation criteria

---

## Executive Summary

**Recommendation:** Migrate from old upflow criteria to new devpersona-based criteria

**Rationale:**
- Old criteria were general and generic
- New criteria are specifically tailored for AI Systems Engineer profile
- New criteria emphasize deep technical expertise in NLP, AI agents, and infrastructure
- Better alignment with current career focus and market positioning

---

## Criteria Comparison

| Action | Old Criterion | New Criterion | Change Type | Rationale |
|--------|---------------|---------------|-------------|-----------|
| **REMOVE** | "Relevance to AI Agents & NLP" | - | REMOVED | Too generic, replaced by more specific criteria |
| **REMOVE** | "Relevance to Machine Learning Infrastructure" | - | REMOVED | Too generic, replaced by more specific criteria |
| **REMOVE** | "Relevance to Prompt Engineering" | - | REMOVED | Too generic, replaced by more specific criteria |
| **REMOVE** | "Relevance to RAG Systems" | - | REMOVED | Too generic, replaced by more specific criteria |
| **REMOVE** | "Relevance to LLM Integration" | - | REMOVED | Too generic, replaced by more specific criteria |
| **ADD** | - | "Deep AI & NLP Expertise" | ADD | Comprehensive technical depth requirement |
| **ADD** | - | "LLM System Architecture & Integration" | ADD | End-to-end system design capability |
| **ADD** | - | "Advanced RAG & Agent Orchestration" | ADD | Complex agent workflow specialization |
| **ADD** | - | "ML Infrastructure & MLOps" | ADD | Production-grade AI systems |
| **ADD** | - | "Technical Leadership & Communication" | ADD | Leadership and collaboration skills |

---

## Detailed Changes

### REMOVED CRITERIA

#### 1. Relevance to AI Agents & NLP
**Old Definition:** "How relevant is this job to AI agents, NLP, and natural language processing?"

**Why Removed:**
- Too generic - doesn't specify depth of knowledge required
- Covered in new criteria with more specificity
- "Relevance" is subjective - need concrete technical indicators

**Coverage in New Criteria:**
- Merged into "Deep AI & NLP Expertise" with specific technical requirements
- Hugging Face, LangChain, LlamaIndex mentioned explicitly

---

#### 2. Relevance to Machine Learning Infrastructure
**Old Definition:** "How relevant is this job to building ML infrastructure, MLOps, and scalable ML systems?"

**Why Removed:**
- Too generic - doesn't distinguish between junior ML ops and senior ML infrastructure
- ML is only part of AI systems - missing LLM-specific infrastructure needs
- Covered in new criteria with more LLM-specific focus

**Coverage in New Criteria:**
- Replaced by "ML Infrastructure & MLOps" with clear technical stack:
  - Docker containers
  - CI/CD pipelines
  - Docker Compose
  - Traefik reverse proxy

---

#### 3. Relevance to Prompt Engineering
**Old Definition:** "How relevant is this job to prompt engineering, prompt optimization, and prompt management?"

**Why Removed:**
- Too narrow - prompt engineering is only one aspect of LLM systems
- User's profile emphasizes "systems engineering beyond simple prompt engineering"
- Prompt engineering alone doesn't indicate senior AI systems role

**Coverage in New Criteria:**
- Prompt engineering is a factor within "Deep AI & NLP Expertise"
- But not a standalone criterion - it's a subset of broader skills

---

#### 4. Relevance to RAG Systems
**Old Definition:** "How relevant is this job to building RAG (Retrieval-Augmented Generation) systems?"

**Why Removed:**
- Too narrow - RAG is one pattern among many in AI systems
- Doesn't capture agent orchestration, workflow design, or production considerations
- Covered in new criteria with broader agent system scope

**Coverage in New Criteria:**
- Merged into "Advanced RAG & Agent Orchestration" with:
  - Vector databases (pinecone, qdrant, chromadb)
  - Agent frameworks (LangChain, AutoGPT, CAMEL)
  - Production considerations

---

#### 5. Relevance to LLM Integration
**Old Definition:** "How relevant is this job to integrating LLMs into applications and systems?"

**Why Removed:**
- Too generic - "LLM integration" could mean simple API calls or complex orchestration
- Doesn't distinguish between wrapper jobs and systems engineering jobs
- Covered in new criteria with specific integration patterns

**Coverage in New Criteria:**
- Replaced by "LLM System Architecture & Integration" with:
  - Fine-tuning and prompt optimization
  - LLM caching and performance optimization
  - Enterprise integration patterns

---

### ADDED CRITERIA

#### 1. Deep AI & NLP Expertise (NEW)
**Definition:** "Demonstrated expertise in cutting-edge AI and NLP technologies, with hands-on experience building production systems."

**Weight:** 0.25

**Technical Indicators (Scoring Factors):**

| Factor                     | Description                                                                 | Score |
|----------------------------|-----------------------------------------------------------------------------|-------|
| Hugging Face Stack         | Transformers, datasets, tokenizers, PEFT, adapters                      | 0-100 |
| LLM Frameworks            | LangChain, LlamaIndex, Haystack, Semantic Kernel                         | 0-100 |
| Vector Databases          | RAPTOR, LlamaIndex, pinecone, qdrant, chromadb                             | 0-100 |
| Prompt Engineering        | System messages, few-shot, chain-of-thought, temperature, top_p          | 0-100 |
| LLM APIs                  | OpenAI, Anthropic, Cohere, Mistral, local LLMs (llama.cpp)               | 0-100 |

**Why Added:**
- Comprehensive technical depth requirement
- Specific technologies and frameworks mentioned
- Objective indicators (not subjective "relevance")
- High weight - this is the core expertise area

**Examples of High-Scoring Jobs:**
- "Senior AI Engineer - Build production RAG system with LangChain and Pinecone"
- "LLM Systems Architect - Design and implement enterprise NLP infrastructure"
- "NLP Team Lead - Build scalable AI systems using Hugging Face and vector databases"

**Examples of Low-Scoring Jobs:**
- "Junior NLP Researcher - Fine-tune BERT model (no production focus)"
- "ML Engineer - Traditional ML, no LLM or NLP focus"
- "Data Scientist - General ML, no specific AI systems experience"

---

#### 2. LLM System Architecture & Integration (NEW)
**Definition:** "End-to-end design and implementation of LLM-powered systems, including integration patterns, performance optimization, and enterprise architecture."

**Weight:** 0.20

**Technical Indicators (Scoring Factors):**

| Factor                     | Description                                                                 | Score |
|----------------------------|-----------------------------------------------------------------------------|-------|
| Fine-tuning & Prompt Opt   | LoRA, P-tuning, QLoRA, prompt engineering, system prompts                  | 0-100 |
| LLM Caching & Performance  | Semantic caching, token caching, memoization, query decomposition           | 0-100 |
| Enterprise Integration     | Message queues, caching layer, service mesh, microservices                    | 0-100 |
| LLM Orchestration          | Multi-LLM routing, fallback strategies, cost optimization                   | 0-100 |
| Deployment & Scaling       | K8s, Lambda, batch processing, streaming, monitoring                         | 0-100 |

**Why Added:**
- Emphasizes systems engineering perspective (not just ML)
- Production deployment and scalability concerns
- Enterprise integration patterns
- Differentiates from "LLM integration" wrapper jobs

**Examples of High-Scoring Jobs:**
- "LLM Platform Engineer - Build enterprise LLM infrastructure with caching and monitoring"
- "AI Systems Architect - Design multi-LLM orchestration with fallback strategies"
- "Senior Platform Engineer - Deploy and scale production LLM systems on K8s"

**Examples of Low-Scoring Jobs:**
- "LLM Application Developer - Build simple chatbot with OpenAI API (no architecture)"
- "Backend Engineer - Add LLM feature to existing app (basic API wrapper)"
- "Full Stack Developer - Integrate ChatGPT into web app (minimal LLM expertise)"

---

#### 3. Advanced RAG & Agent Orchestration (NEW)
**Definition:** "Building production RAG systems and intelligent AI agents with advanced orchestration, multi-step reasoning, and complex workflow design."

**Weight:** 0.20

**Technical Indicators (Scoring Factors):**

| Factor                     | Description                                                                 | Score |
|----------------------------|-----------------------------------------------------------------------------|-------|
| RAG Systems                | Vector DB integration, hybrid search, semantic chunking, retrieval         | 0-100 |
| Agent Frameworks           | LangChain, AutoGPT, CAMEL, LangGraph, crewAI, custom frameworks            | 0-100 |
| Multi-Agent Orchestration  | Agent swarms, role-based agents, collaborative agents, tool calling         | 0-100 |
| Tool Integration           | Function calling, API integration, code interpreter, web browsing           | 0-100 |
| Production Considerations  | Performance, latency, cost optimization, error handling, monitoring         | 0-100 |

**Why Added:**
- Specialized expertise in RAG and agent systems
- Not just simple RAG - emphasizes advanced orchestration
- Production concerns (performance, cost, monitoring)
- Specific agent frameworks mentioned

**Examples of High-Scoring Jobs:**
- "AI Agent Engineer - Build multi-agent system with LangChain and tool integration"
- "RAG System Architect - Design production RAG with hybrid search and monitoring"
- "Senior AI Engineer - Build intelligent agents with advanced orchestration"

**Examples of Low-Scoring Jobs:**
- "NLP Engineer - Build simple vector search (no agents, no production focus)"
- "Machine Learning Engineer - Classical ML tasks (no RAG or agents)"
- "Research Scientist - Agent research (no production implementation)"

---

#### 4. ML Infrastructure & MLOps (NEW)
**Definition:** "Building production-grade ML infrastructure, CI/CD pipelines, and scalable ML systems with proper monitoring and deployment."

**Weight:** 0.20

**Technical Indicators (Scoring Factors):**

| Factor                     | Description                                                                 | Score |
|----------------------------|-----------------------------------------------------------------------------|-------|
| Docker & Containers       | Docker, Docker Compose, multi-container apps, networking                    | 0-100 |
| CI/CD Pipelines           | GitHub Actions, GitLab CI, custom pipelines, automated testing             | 0-100 |
| Deployment & Monitoring   | K8s, Coolify, Traefik, health checks, logging, metrics                     | 0-100 |
| MLOps Practices            | Model versioning, experiment tracking, feature stores, reproducibility     | 0-100 |
| Cloud Infrastructure      | AWS, GCP, Azure, serverless, managed services, cost optimization           | 0-100 |

**Why Added:**
- Specific infrastructure stack (Docker, Coolify, Traefik)
- CI/CD and automation emphasis
- Production concerns (monitoring, logging)
- MLOps best practices (not just ML ops)

**Examples of High-Scoring Jobs:**
- "MLOps Engineer - Build CI/CD pipelines for LLM deployment"
- "DevOps Engineer - Deploy and monitor production ML systems with Docker and K8s"
- "ML Platform Engineer - Build scalable infrastructure for AI workloads"

**Examples of Low-Scoring Jobs:**
- "Data Scientist - Build ML models (no infrastructure focus)"
- "ML Engineer - Model training only (no CI/CD, no production)"
- "Backend Developer - Generic DevOps (no ML/AI specific experience)"

---

#### 5. Technical Leadership & Communication (NEW)
**Definition:** "Ability to lead technical teams, communicate complex technical concepts, and drive AI initiatives in production environments."

**Weight:** 0.15

**Non-Technical Indicators (Scoring Factors):**

| Factor                     | Description                                                                 | Score |
|----------------------------|-----------------------------------------------------------------------------|-------|
| Leadership Experience      | Team lead, tech lead, architect roles, mentoring                            | 0-100 |
| Technical Communication    | Documentation, tech blog, conference talks, clear explanations             | 0-100 |
| Systems Thinking           | Architecture design, tradeoffs, scalability, production concerns          | 0-100 |
| Collaboration              | Cross-functional work, stakeholder management, product thinking            | 0-100 |
| Problem Solving            | Debugging production issues, incident response, root cause analysis        | 0-100 |

**Why Added:**
- Technical leadership is critical for senior AI Systems Engineer roles
- Differentiates from individual contributor roles
- Emphasizes communication and collaboration
- Production problem-solving is valued

**Examples of High-Scoring Jobs:**
- "AI Team Lead - Lead team of 5 engineers building production AI systems"
- "Principal AI Engineer - Architect enterprise AI platform, lead technical strategy"
- "AI Engineering Manager - Bridge business and technical teams on AI initiatives"

**Examples of Low-Scoring Jobs:**
- "AI Engineer - Individual contributor role (no leadership)"
- "ML Researcher - Academic focus, no production experience"
- "Junior AI Developer - Entry-level, learning and growing)"

---

## Implementation Recommendation

### Proposed Weights

| Criterion                              | Weight | Rationale                                                                 |
|----------------------------------------|--------|---------------------------------------------------------------------------|
| Deep AI & NLP Expertise               | 0.25   | Core technical competency - primary differentiator                        |
| LLM System Architecture & Integration | 0.20   | Systems engineering perspective - production focus                        |
| Advanced RAG & Agent Orchestration    | 0.20   | Specialized expertise in advanced patterns                                |
| ML Infrastructure & MLOps             | 0.20   | Production infrastructure and DevOps skills                               |
| Technical Leadership & Communication  | 0.15   | Differentiates senior roles from individual contributors                  |
| **Total**                             | **1.00** | -                                                                         |

### Why These Weights?

1. **Deep AI & NLP (0.25)**: Highest weight - this is the core expertise area that sets you apart from general ML engineers
2. **LLM Architecture & MLOps (0.20 each)**: Equal weight - systems engineering and production infrastructure are equally important for scalable AI systems
3. **RAG & Agents (0.20)**: Equal weight - advanced patterns that demonstrate senior-level AI systems work
4. **Leadership (0.15)**: Lower weight - important but secondary to technical depth

---

## Migration Path

### Step 1: Update Criteria File
Edit `core/config/criteria.py` to implement new criteria structure:

```python
from pydantic import BaseModel
from typing import List, Dict

class ScoringFactor(BaseModel):
    name: str
    description: str
    max_score: int = 100

class Criterion(BaseModel):
    name: str
    description: str
    weight: float
    scoring_factors: List[ScoringFactor]

CRITERIA = [
    Criterion(
        name="Deep AI & NLP Expertise",
        description="Demonstrated expertise in cutting-edge AI and NLP technologies...",
        weight=0.25,
        scoring_factors=[
            ScoringFactor("Hugging Face Stack", "..."),
            ScoringFactor("LLM Frameworks", "..."),
            # ...
        ]
    ),
    # Add other 4 criteria
]
```

### Step 2: Update Evaluation Logic
Modify `services/evaluation.py` to score against new criteria:
- Each criterion has multiple scoring factors
- Score is weighted average of factors (or max factor, TBD)
- Final score is weighted sum of criterion scores

### Step 3: Test with Sample Jobs
Run evaluation on sample job postings to verify:
- High-scoring jobs (AI architect, ML platform engineer) score 80+
- Low-scoring jobs (junior ML dev, general backend) score <50
- Weighted sum makes sense

### Step 4: Refine Factors
Adjust scoring factors based on test results:
- Remove factors that are always zero
- Split factors that are too broad
- Add missing factors

---

## Next Steps

1. **User Approval**: Confirm you agree with this criteria migration
2. **Implementation**: Update `core/config/criteria.py` with new structure
3. **Testing**: Provide sample job postings for testing
4. **Refinement**: Adjust based on test results

---

## Appendices

### A. Removed Criteria Details

Full text of all 5 old criteria for reference (see RESEARCH_ANALYSIS.md for complete details).

### B. Technical Indicators Reference

Detailed breakdown of all scoring factors across 5 new criteria (see above tables).

### C. Weight Calculation Example

Example scoring calculation for a "Senior AI Architect" job:

```
Deep AI & NLP: 85/100 × 0.25 = 21.25
LLM Architecture: 90/100 × 0.20 = 18.00
RAG & Agents: 75/100 × 0.20 = 15.00
ML Infrastructure: 70/100 × 0.20 = 14.00
Leadership: 80/100 × 0.15 = 12.00
----------------------------------------
Total Score: 80.25/100
```

### D. Comparison with devpersona Profile

Alignment check: All 5 new criteria directly map to devpersona sections:
- Deep AI & NLP → "Core Technical Expertise"
- LLM Architecture & Integration → "Systems Engineering Beyond Simple Prompt Engineering"
- RAG & Agents → "Core Technical Expertise" (agent frameworks)
- ML Infrastructure → "Production Deployment & Monitoring"
- Leadership → "Technical Leadership" (implied by senior roles)

**Conclusion: Near-perfect alignment with devpersona profile.**