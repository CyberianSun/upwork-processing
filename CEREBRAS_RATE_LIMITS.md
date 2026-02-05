# Cerebras GLM 4.7 Rate Limits

**Last Updated**: 2026-02-05
**Model**: glm-4.7 (Preview)

---

## Rate Limits

### Request Limits

| Time Window | Max Requests | Average/Second |
|-------------|--------------|----------------|
| **Per Minute** | 120 requests | 2 req/s |
| **Per Hour** | 7,200 requests | 2 req/s |
| **Per Day** | 172,800 requests | 2 req/s |

**Sustained Rate**: 2 requests per second

---

### Token Limits

| Time Window | Max Tokens | Notes |
|-------------|------------|-------|
| **Per Minute** | 1,500,000 tokens | ~12,500 tokens/request (at 2 req/s) |
| **Per Hour** | 120,000,000 tokens | ~33,333 tokens/request sustainable |
| **Per Day** | 120,000,000 tokens | ~694 tokens/request sustainable |

**Daily Constraint**: The token limit is the same as hourly (120M), meaning ~1,389 requests/day at 86k tokens each, or ~172,800 requests/day at lower token usage.

---

## Implications for Job Processing

### Worker Pool Sizing

**Based on Request Rate Limits**:
- **Max Workers**: 2 concurrent workers (to stay within 2 req/s limit)
- **Safe Workers**: 1-2 workers (with 1-2 sec gap between calls)

**Calculation**:
```
120 requests / 60 seconds = 2 req/s maximum
→ 2 workers, 0.5 sec between requests OR
→ 1 worker, 1 sec between requests
```

---

### Token Budgeting

**Assumed Average Evaluation Cost**:
- Input: ~2,000 tokens (job description + criteria)
- Output: ~500 tokens (scoring + explanation)
- Total: ~2,500 tokens per job

**Jobs Per Time Window**:

| Time Window | Token Limit | Tokens/Job | Max Jobs | Practical Limit (80%) |
|-------------|-------------|------------|----------|----------------------|
| **Per Minute** | 1,500,000 | 2,500 | 600 | 480 |
| **Per Hour** | 120,000,000 | 2,500 | 48,000 | 38,400 |
| **Per Day** | 120,000,000 | 2,500 | 48,000 | 38,400 |

**Key Insight**: The **daily token limit** is the bottleneck. At 2,500 tokens/job, you can process ~48,000 jobs/day.

---

### Semaphore Configuration

**Recommended Semaphore Settings**:

```python
import asyncio
import aiohttp
from cerebras.cloud_sdk import Cerebras

# Semaphore to respect rate limits
MAX_CONCURRENT_EVALUATIONS = 2  # Stay within 2 req/s
RATE_LIMIT_DELAY = 0.5  # Seconds between requests (2 req/s)

semaphore = asyncio.Semaphore(MAX_CONCURRENT_EVALUATIONS)

async def evaluate_job(job_data):
    async with semaphore:
        # Rate limiting delay
        await asyncio.sleep(RATE_LIMIT_DELAY)
        
        # Call Cerebras GLM 4.7
        response = await cerebras_client.chat.completions.create(
            model="glm-4.7",
            messages=[...],
            max_tokens=500
        )
        
        return response
```

---

### Batch Processing Strategy

**For Large Job Volumes** (100+ jobs):

1. **Process in Batches**: Group jobs into batches of 10-20
2. **Rate-Limited Execution**: Use semaphore + delay between calls
3. **Token Tracking**: Monitor total tokens used per hour/day
4. **Graceful Degradation**: If rate limit exceeded, pause and retry

**Example**:

```python
async def process_jobs_batch(jobs):
    tasks = []
    for job in jobs:
        task = evaluate_job(job)
        tasks.append(task)
        
        # Rate limiting between task creation
        await asyncio.sleep(0.5)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## Monitoring & Alerts

### Metrics to Track

| Metric | Limit | Alert Threshold |
|--------|-------|-----------------|
| Requests/minute | 120 | >100 (83% of limit) |
| Requests/hour | 7,200 | >6,000 (83% of limit) |
| Tokens/minute | 1.5M | >1.2M (80% of limit) |
| Tokens/hour | 120M | >96M (80% of limit) |
| Tokens/day | 120M | >96M (80% of limit) |

---

### Error Handling

**Rate Limit Error Response** (429 Too Many Requests):

```python
try:
    response = await cerebras_client.chat.completions.create(...)
except rate_limit_error:
    # Exponential backoff
    await asyncio.sleep(5)  # Wait 5 seconds
    # Retry
    response = await cerebras_client.chat.completions.create(...)
```

---

## Cost Estimation

### Free Tier (Preview)

The rates above are for the **Preview** tier (likely free or heavily discounted).

**Assumptions** (pricing not provided):
- If free tier: No cost concern, just rate limits
- If paid tier: Check pricing for overages

---

### Processing Capacity

**Daily Processing Capacity**:

| Metric | Value |
|--------|-------|
| Max Jobs/Day (Token Limit) | 48,000 jobs |
| Max Jobs/Day (Request Limit) | 172,800 jobs |
| **Bottleneck** | Token limit (48,000 jobs/day) |
| **Workers** | 2 concurrent |
| **Throughput** | ~2 jobs/second (sustained) |

**In Practice**:
- Process ~38,400 jobs/day (80% safety margin)
- ~1,600 jobs/hour
- ~27 jobs/minute

---

## Configuration Recommendations

### Environment Variables

```bash
# Cerebras API Rate Limits (auto-enforced in code)
CEREBRAS_MAX_CONCURRENT=2
CEREBRAS_RATE_LIMIT_DELAY=0.5  # Seconds

# Token Budgeting
CEREBRAS_MINUTES_BUDGET=1200000  # 1.5M tokens/minute
CEREBRAS_HOURS_BUDGET=120000000   # 120M tokens/hour
CEREBRAS_DAYS_BUDGET=120000000    # 120M tokens/day
```

### Python Configuration

```python
from dataclasses import dataclass

@dataclass
class CerebrasRateLimits:
    requests_per_minute: int = 120
    requests_per_hour: int = 7200
    requests_per_day: int = 172800
    
    tokens_per_minute: int = 1500000
    tokens_per_hour: int = 120000000
    tokens_per_day: int = 120000000
    
    @property
    def max_concurrent(self) -> int:
        return 2  # 120 req/min ÷ 60 sec = 2 req/s
    
    @property
    def min_delay_seconds(self) -> float:
        return 0.5  # 60 sec ÷ 120 req = 0.5 sec/req

CEREBRAS_LIMITS = CerebrasRateLimits()
```

---

## Testing Rate Limits

### Load Test Script

```python
import asyncio
import time
from cerebras.cloud_sdk import Cerebras

cerebras = Cerebras(api_key="YOUR_KEY")

async def test_rate_limits():
    start_time = time.time()
    jobs_processed = 0
    total_tokens = 0
    
    for i in range(10):  # Test 10 requests
        try:
            response = cerebras.chat.completions.create(
                model="glm-4.7",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            jobs_processed += 1
            total_tokens += response.usage.total_tokens
            await asyncio.sleep(0.5)  # 2 req/s
        except Exception as e:
            print(f"Error: {e}")
    
    elapsed = time.time() - start_time
    print(f"Processed: {jobs_processed} jobs in {elapsed:.2f}s")
    print(f"Rate: {jobs_processed/elapsed:.2f} jobs/sec")
    print(f"Tokens used: {total_tokens}")

asyncio.run(test_rate_limits())
```

---

## Summary

| Limit Type | Value | Bottleneck? |
|------------|-------|-------------|
| Requests/minute | 120 req/min (2 req/s) | No |
| Requests/hour | 7,200 req/hour | No |
| Requests/day | 172,800 req/day | No |
| Tokens/minute | 1.5M tokens/min | No |
| Tokens/hour | 120M tokens/hour | No |
| **Tokens/day** | **120M tokens/day** | **YES** ✋ |

**Key Takeaways**:
1. **Token/day limit is the bottleneck** - caps at ~48,000 jobs/day (at 2.5k tokens/job)
2. Use **2 concurrent workers** with **0.5s delay** between requests
3. Monitor token usage to stay within limits
4. Implement rate limiting with semaphore + delays
5. Exponential backoff on 429 errors

---

**Document Created**: 2026-02-05
**Purpose**: Document Cerebras GLM 4.7 rate limits for worker pool configuration
**Model**: glm-4.7 (Preview)