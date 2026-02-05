# Configuration Summary

**Status**: All design decisions made. Ready for implementation.

---

## Final Decisions

| # | Category | Decision | Details |
|---|----------|----------|---------|
| 1 | Output Format | ✅ Markdown | Display results in terminal using Markdown tables |
| 2 | Result Persistence | ✅ Keep all | Store every evaluation in database (no deletion) |
| 3 | Keyword Updates | ✅ Auto-every-run | Update stats automatically, but **confirm changes before applying** |
| 4 | Market Pulse | ✅ Daily | Daily aggregation of stats (can add more later) |
| 5 | Scoring Validation | ⏸️ TBD | Will decide later (human review of top 10, random 5%, or none) |
| 6 | Telegram Bot | ✅ Phase 2 | Build after terminal version works |
| 7 | Rate Limiting | ✅ Cerebras limits | Respect GLM 4.7 API rates ($200/month code plan) |
| 8 | Budget Cutoff | ✅ Min $500 | Below $500 scores 0 points (filters out low-value work) |
| 9 | Tech Trend Alerts | ✅ None | Just track data, no alerts |
| 10 | Skill Gaps | ✅ Auto-mark | Automatically flag missing tech as "learn priority" |

---

## Removed Keywords

| Category | Keywords | Reason |
|----------|----------|--------|
| Automation | n8n | Not interested |
| Automation | Make.com | Not interested |
| Automation | Zapier | Not interested |
| No-Code | Bubble.io | Not interested |

---

## Budget Scoring (Updated)

| Score | Budget Range | Note |
|-------|--------------|------|
| 20 | ≥ $2,000 | Excellent |
| 16 | ≥ $1,000 | Very good |
| 12 | ≥ $750 | Good |
| 8 | ≥ $500 | Acceptable (minimum) |
| 0 | < $500 | Too low (0 points) |

**Previous**: 200-499 scored 4 points (changed to 0 points)

---

## Technology Keywords Status

| Keyword | Status | Your Stack | Notes |
|---------|--------|------------|-------|
| CAMEL | ✅ Keep | Optional | Multi-agent framework (15.9k stars) - be aware of it |
| BabyAGI | ✅ Keep | Optional | Experimental task management - conceptual knowledge |
| FAISS | ✅ Keep | ✅ Covered | Vector search - covered by vector DB knowledge, pgvector alternative |
| Milvus | ✅ Keep | Optional | Vector DB (40k stars) - learn if client requests |

---

## Processing Flow

```
Apify File → Load → Enrich → Evaluate (LLM) → Store → Rank → Display (Markdown)
                          ↓                     ↓
                    Keyword extraction    PostgreSQL DB
                    (no AI)               (all data)
```

**Enricher**: Extracts keywords, tech tags, metadata (fast, deterministic)
**Evaluator**: Calls Cerebras GLM 4.7 with job data + criteria (slower, AI-powered)

---

## Files Ready

| File | Status |
|------|--------|
| `TECH_STACK.md` | ✅ Created - Backend stack defined |
| `project.md` | ✅ Created - SeedFW conventions |
| `KEYWORD_STRATEGY_UPDATED.md` | ✅ Created + Updated - Removed n8n, Make, Zapier, Bubble |
| `CRITERIA_AI_SYSTEMS_ENGINEER.md` | ✅ Created - Budget scoring updated (min $500) |
| `ARCHITECTURE.md` | ✅ Created - Full data flow and component breakdown |
| `TECHNOLOGY_REFERENCE.md` | ✅ Created - Quick reference for FAISS, Milvus, CAMEL, etc. |

---

## Next Steps (When Ready to Implement)

1. **Create `TECH_STACK_COMPARISON.md`** - Compare your stack vs. market demand
2. **Initialize project structure** - SeedFW vertical slice layout
3. **Set up database connection** - Connect to existing PostgreSQL on VPS
4. **Implement job loader** - Parse Apify files
5. **Implement enricher** - Keyword extraction
6. **Implement evaluator** - Cerebras GLM 4.7 integration
7. **Test with sample data** - Use the 100-job JSON file for validation
8. **Terminal output** - display ranked results in Markdown

---

**Document Updated**: 2026-02-05
**Status**: Design phase complete. All config decisions made. Ready to build when you provide fresh Apify file.