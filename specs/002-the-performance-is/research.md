# Research: Asynchronous Data Collection

**Feature**: 002-the-performance-is  
**Date**: October 14, 2025  
**Purpose**: Research async patterns for integrating synchronous PRAW with async FastAPI

## Research Tasks

### 1. Async/Sync Integration Patterns in Python

**Decision**: Use `asyncio.get_event_loop().run_in_executor()` with ThreadPoolExecutor

**Rationale**:
- Standard library solution (concurrent.futures.ThreadPoolExecutor)
- Designed specifically for running blocking I/O in async contexts
- Maintains single process model (simpler than multiprocessing)
- Preserves scheduler state and database connections
- Well-documented pattern in FastAPI ecosystem

**Alternatives Considered**:

| Alternative | Why Rejected |
|-------------|--------------|
| Async PRAW (asyncpraw) | Not actively maintained; compatibility issues with latest Reddit API changes; would require rewriting all collection logic |
| Multiprocessing (ProcessPoolExecutor) | Excessive overhead for I/O-bound tasks; complicates shared state (scheduler, DB connections); serialization costs |
| Background threads without coordination | Race conditions in scheduler state; no way to await completion; error handling complexity |
| Blocking in async (asyncio.run in thread) | Defeats purpose; still blocks event loop; creates nested event loop issues |

**Implementation Pattern**:
```python
async def async_wrapper():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        thread_pool_executor,
        synchronous_blocking_function
    )
```

### 2. APScheduler Best Practices with AsyncIO

**Decision**: Use AsyncIOScheduler with delayed initial job execution

**Rationale**:
- AsyncIOScheduler natively integrates with asyncio event loop
- Supports both immediate and scheduled job execution
- Built-in job replacement and duplicate prevention
- Can schedule jobs with date triggers for startup delay

**Alternatives Considered**:

| Alternative | Why Rejected |
|-------------|--------------|
| BackgroundScheduler | Runs in separate thread; complicates async coordination; async jobs require special handling |
| Celery/Redis Queue | Over-engineering for single-service use case; adds infrastructure dependencies; unnecessary complexity |
| Custom asyncio.create_task | No built-in scheduling, interval management, or error recovery; would reinvent APScheduler features |

**Implementation Pattern**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()
scheduler.start()

# Delayed initial collection (allows app to start)
scheduler.add_job(
    async_collection_wrapper,
    trigger='date',
    run_date=datetime.now() + timedelta(seconds=5)
)

# Regular interval collection
scheduler.add_job(
    async_collection_wrapper,
    trigger='interval',
    minutes=30
)
```

### 3. Performance Testing for Async Operations

**Decision**: Use pytest-asyncio + locust for load testing

**Rationale**:
- pytest-asyncio: Native async test support, familiar pytest syntax
- locust: HTTP load testing during collection, measures real response times
- Can simulate concurrent API requests during background collection

**Test Strategy**:
1. **Unit Tests** (pytest-asyncio):
   - Verify async wrappers don't block event loop
   - Test scheduler job execution isolation
   - Validate error handling in async context

2. **Integration Tests** (pytest-asyncio):
   - Run collection while making API requests
   - Verify data integrity after async collection
   - Test startup timing with delayed collection

3. **Performance Tests** (locust):
   - 50 concurrent users requesting API during collection
   - Measure P95 response times
   - Verify <3s response time requirement

**Implementation Pattern**:
```python
# pytest-asyncio test
@pytest.mark.asyncio
async def test_api_responsive_during_collection():
    # Start collection
    collection_task = asyncio.create_task(collect_data())
    
    # Make API request
    response = await client.get("/api/v1/health")
    
    # Verify response time
    assert response.elapsed < timedelta(seconds=1)
    await collection_task
```

### 4. Thread Pool Sizing for I/O-Bound Tasks

**Decision**: Single-worker ThreadPoolExecutor (max_workers=1)

**Rationale**:
- PRAW collection is sequential by design (subreddit iteration)
- Single worker prevents concurrent Reddit API calls (avoids rate limits)
- Simpler error handling and logging (no concurrent job conflicts)
- Adequate for 30-minute collection intervals

**Alternatives Considered**:

| Alternative | Why Rejected |
|-------------|--------------|
| Multiple workers (max_workers=5) | Risk of Reddit rate limiting; concurrent DB writes complexity; no performance benefit for sequential collection |
| Dynamic pool sizing | Unnecessary complexity; collection pattern is predictable; fixed single worker sufficient |
| No thread pool (direct threading) | Harder to manage lifecycle; no built-in executor integration with asyncio |

**Implementation Pattern**:
```python
from concurrent.futures import ThreadPoolExecutor

class CollectionScheduler:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        # Single worker ensures sequential execution
```

### 5. Error Handling in Async Wrappers

**Decision**: Preserve synchronous error handling, log async wrapper failures

**Rationale**:
- Existing error handling in sync code works correctly
- Async wrapper only adds executor management errors
- APScheduler handles job failures automatically
- Maintains current error logging and retry logic

**Implementation Pattern**:
```python
async def collect_and_analyze(self):
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._collect_and_analyze_sync  # Existing sync method
        )
    except Exception as e:
        logger.error(f"Async wrapper error: {e}")
        # Sync method already logs collection errors
```

## Summary

**Primary Approach**: 
- Wrap existing synchronous collection code with `run_in_executor()`
- Use ThreadPoolExecutor with single worker
- Delay initial collection 5 seconds after app startup
- Preserve all existing error handling and data flow

**Key Benefits**:
- Minimal code changes (async wrapper layer only)
- No new dependencies
- Maintains data integrity
- Proven pattern in FastAPI ecosystem

**Risk Mitigation**:
- Comprehensive async integration tests
- Performance validation with locust
- Gradual rollout (can revert wrapper if issues)
- Single worker prevents concurrency bugs
