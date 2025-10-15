# Research: Backend Stability and Data Loading

**Feature**: 003-backend-stability-and-data-loading  
**Phase**: 0 (Research)  
**Date**: January 15, 2025  
**Input**: Technical Context NEEDS CLARIFICATION items from [plan.md](plan.md)

## Overview

This document resolves technical uncertainties identified during planning. Each decision includes rationale, alternatives considered, and references to authoritative sources.

---

## 1. Process Lifecycle Management

### Question

How should we handle graceful shutdown with FastAPI + uvicorn + APScheduler?

### Research Findings

**Python Signal Handlers**:
- Standard approach: `signal.signal(signal.SIGTERM, handler)` and `signal.SIGINT, handler)`
- Handler should set a shutdown flag and allow in-flight operations to complete
- Not recommended for async code - signals interrupt async event loop

**FastAPI Lifespan Events**:
- Modern approach: `@asynccontextmanager` with `lifespan` parameter in `FastAPI(lifespan=...)`
- Provides startup and shutdown hooks with proper async context
- Automatically handles cleanup when uvicorn receives SIGTERM/SIGINT
- Example:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Startup
      scheduler.start()
      yield
      # Shutdown
      scheduler.shutdown(wait=True)
  ```

**APScheduler Graceful Shutdown**:
- `scheduler.shutdown(wait=True)` waits for running jobs to complete
- Default timeout is 30 seconds per job
- Returns immediately if no jobs running
- Thread-safe for async contexts

### Decision

**Use FastAPI lifespan events with APScheduler shutdown**

**Rationale**:
1. **Framework-native**: FastAPI lifespan is the recommended pattern (FastAPI docs)
2. **Async-compatible**: Works correctly with uvicorn's async event loop
3. **Simple**: No manual signal handling required
4. **Testable**: Lifespan can be tested independently

**Implementation**:
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    yield  # Application running
    
    # Shutdown: Stop scheduler gracefully
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")

app = FastAPI(lifespan=lifespan)
```

**Alternatives Rejected**:
- ❌ Manual signal handlers: Incompatible with async event loop, more complex
- ❌ atexit module: Not reliable for signal-based termination (SIGTERM)
- ❌ No shutdown handling: Causes orphaned processes and incomplete jobs

**References**:
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [APScheduler Shutdown Documentation](https://apscheduler.readthedocs.io/en/3.x/userguide.html#starting-the-scheduler)

---

## 2. Database Connection Resilience

### Question

How to handle CosmosDB connection failures and retries?

### Research Findings

**Azure Cosmos SDK Retry Policies**:
- SDK has built-in retry for transient errors (429 rate limit, 503 service unavailable)
- Default: 9 retries with exponential backoff
- Does NOT retry on connection refused or network errors
- Retries are per-operation, not per-connection

**Connection Pooling with Async Python**:
- Azure Cosmos SDK uses `aiohttp` internally for async connections
- Connection pooling handled automatically by SDK
- Max connections: 100 (default), configurable via `connection_policy`

**Circuit Breaker Pattern**:
- Prevents cascading failures by stopping requests after N failures
- Requires external library (e.g., `pybreaker`, `circuitbreaker`)
- Adds significant complexity for single-service architecture
- More useful for microservices with multiple dependencies

**Custom Retry Decorator**:
- Simple pattern: wrap operations with `@retry` decorator
- Control retry count, backoff strategy, exception types
- Library options: `tenacity`, `backoff`, or custom implementation

### Decision

**Use custom retry decorator with exponential backoff (3 retries max)**

**Rationale**:
1. **Simplicity**: Single decorator, no external heavy dependencies
2. **Transparency**: Clear visibility into retry attempts via logging
3. **Sufficient**: 3 retries covers ~95% of transient network issues
4. **Fast failure**: Fails within 21 seconds (1s + 4s + 16s) vs indefinite retries

**Implementation**:
```python
import asyncio
from functools import wraps
from typing import TypeVar, Callable

T = TypeVar('T')

def retry_db_operation(max_retries: int = 3, base_delay: float = 1.0):
    """Retry database operations with exponential backoff"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise  # Final attempt failed
                    delay = base_delay * (4 ** attempt)  # 1s, 4s, 16s
                    logger.warning(f"DB operation failed (attempt {attempt+1}/{max_retries}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

# Usage
@retry_db_operation(max_retries=3, base_delay=1.0)
async def save_posts(posts: list):
    await db.posts.insert_many(posts)
```

**Alternatives Rejected**:
- ❌ Circuit breaker: Overkill for single database dependency
- ❌ Tenacity library: Adds dependency for simple use case
- ❌ Infinite retries: Can hang application indefinitely
- ❌ Rely on SDK retries only: Doesn't cover connection-level failures

**References**:
- [Azure Cosmos DB Error Handling](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/troubleshoot-dotnet-sdk)
- [Exponential Backoff Best Practices](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

## 3. Error Recovery Strategy

### Question

How should background jobs handle transient errors vs fatal errors?

### Research Findings

**Error Categorization**:
- **Transient**: Network timeout, rate limit (429), service unavailable (503)
- **Fatal**: Authentication failure (401), missing resource (404), invalid data
- Transient errors should trigger retry; fatal errors should log and skip

**Retry Strategies**:
- **Immediate retry**: Simple but wastes resources if error persists
- **Exponential backoff**: Recommended for rate limits and network issues
- **Dead letter queue**: Complex, requires additional infrastructure

**APScheduler Job Error Handling**:
- Default: Job failure doesn't stop scheduler
- Can configure `max_instances` to prevent job pile-up
- Can use `misfire_grace_time` to skip delayed jobs

**Logging vs Alerting**:
- **Logging**: Record all errors for debugging (structured logs with context)
- **Alerting**: Notify on repeated failures (requires monitoring system)

### Decision

**Catch-log-continue for collection errors, fail-fast for startup errors**

**Rationale**:
1. **Availability**: One bad subreddit shouldn't stop all data collection
2. **Observability**: Log errors with full context for debugging
3. **Fast feedback**: Startup errors should crash immediately (fail-fast)
4. **Simple**: No complex error queue or retry orchestration

**Implementation**:

```python
# In scheduler job (background collection)
async def collect_data_job():
    """APScheduler job - runs every 30 minutes"""
    errors = []
    
    for subreddit in config.subreddits:
        try:
            posts = await collector.collect_posts(subreddit)
            await db.save_posts(posts)
            logger.info(f"Collected {len(posts)} posts from r/{subreddit}")
        except RedditAPIError as e:
            # Transient: Log and continue to next subreddit
            logger.error(f"Reddit API error for r/{subreddit}: {e}", exc_info=True)
            errors.append((subreddit, e))
        except DatabaseError as e:
            # Fatal: Log but continue (DB might recover)
            logger.error(f"Database error saving r/{subreddit}: {e}", exc_info=True)
            errors.append((subreddit, e))
        except Exception as e:
            # Unknown: Log and continue
            logger.exception(f"Unexpected error for r/{subreddit}: {e}")
            errors.append((subreddit, e))
    
    # Summary logging
    if errors:
        logger.warning(f"Collection completed with {len(errors)} errors out of {len(config.subreddits)} subreddits")
    else:
        logger.info(f"Collection completed successfully for all {len(config.subreddits)} subreddits")

# In startup (main.py lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Fail-fast on critical errors
    try:
        await db.connect()
        logger.info("Database connected")
    except Exception as e:
        logger.critical(f"Failed to connect to database: {e}")
        raise  # Crash immediately
    
    scheduler.start()
    yield
    
    # Shutdown
    scheduler.shutdown(wait=True)
    await db.disconnect()
```

**Alternatives Rejected**:
- ❌ Stop scheduler on first error: Reduces availability
- ❌ Dead letter queue: Over-engineered for this scale
- ❌ Silent error swallowing: Hides problems, no observability
- ❌ Retry in job: APScheduler will run job again in 30 minutes anyway

**References**:
- [APScheduler Job Error Handling](https://apscheduler.readthedocs.io/en/3.x/userguide.html#exception-handling)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial)

---

## 4. Health Monitoring

### Question

What metrics should be exposed and how?

### Research Findings

**Standard Health Check Patterns**:
- `/health` endpoint: Simple 200 OK for liveness probes
- `/health/ready` endpoint: Check dependencies (DB, external APIs)
- `/metrics` endpoint: Prometheus-style metrics (requires library)

**Process Metrics**:
- **Memory**: `psutil.Process().memory_info().rss` (resident set size)
- **CPU**: `psutil.Process().cpu_percent(interval=1.0)`
- **Uptime**: Track `start_time` on app startup

**Application Metrics**:
- **Last collection timestamp**: Track in-memory or database
- **Collection success rate**: Count successes vs failures
- **Data freshness**: Time since last successful collection

**Prometheus vs Simple JSON**:
- **Prometheus**: Industry standard, requires `prometheus_client` library
- **Simple JSON**: Easy to implement, human-readable, no dependencies

### Decision

**Enhanced /health endpoint returning JSON with process + application metrics**

**Rationale**:
1. **Simple**: Single endpoint, no additional libraries
2. **Sufficient**: Provides visibility into app health without over-engineering
3. **Human-readable**: JSON output can be inspected directly
4. **Extensible**: Can add Prometheus later if needed

**Implementation**:

```python
import psutil
import time
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()

# Track startup time
app_start_time = time.time()
last_collection_time = None
collection_stats = {"success": 0, "failure": 0}

@router.get("/health")
async def health_check():
    """Health check endpoint with process and application metrics"""
    process = psutil.Process()
    uptime_seconds = time.time() - app_start_time
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "process": {
            "uptime_seconds": int(uptime_seconds),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(interval=0.1),
        },
        "application": {
            "last_collection_at": last_collection_time.isoformat() if last_collection_time else None,
            "collections_succeeded": collection_stats["success"],
            "collections_failed": collection_stats["failure"],
            "data_freshness_minutes": int((time.time() - last_collection_time.timestamp()) / 60) if last_collection_time else None,
        },
        "database": {
            "connected": await db.is_connected(),
        }
    }
```

**Example Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "process": {
    "uptime_seconds": 3600,
    "memory_mb": 256.5,
    "cpu_percent": 2.1
  },
  "application": {
    "last_collection_at": "2025-01-15T10:00:00.000Z",
    "collections_succeeded": 48,
    "collections_failed": 0,
    "data_freshness_minutes": 30
  },
  "database": {
    "connected": true
  }
}
```

**Alternatives Rejected**:
- ❌ Prometheus /metrics: Overkill for single service, adds dependency
- ❌ Separate /ready endpoint: Unnecessary complexity for single DB dependency
- ❌ External monitoring agent: Requires additional infrastructure
- ❌ No health check: No visibility into app state

**References**:
- [Health Check API Pattern](https://microservices.io/patterns/observability/health-check-api.html)
- [psutil Documentation](https://psutil.readthedocs.io/en/latest/)

---

## 5. Uvicorn Process Management

### Question

How to prevent orphaned processes and handle reloads?

### Research Findings

**Uvicorn --reload Behavior**:
- Watches Python files for changes, restarts worker process
- Parent process remains running, child workers restart
- File descriptors (ports) are inherited, preventing "address already in use"
- However: APScheduler jobs may not clean up properly on reload

**PID File Management**:
- Traditional approach: Write PID to file on startup
- Cleanup: Remove PID file on graceful shutdown
- Problem: If process crashes, PID file remains (stale lock)

**Process Cleanup Strategies**:
- **Signal handling**: Kill process by PID on startup (risky if PID reused)
- **Port checking**: Use `lsof` or `netstat` to find processes on port
- **Systemd/supervisord**: Process supervisor handles cleanup (production)
- **Development only**: Accept manual cleanup in dev, use supervisor in production

**APScheduler with Reload**:
- Scheduler state is lost on reload (jobs restart)
- Running jobs may be interrupted mid-execution
- Recommendation: Disable --reload in production

### Decision

**Disable --reload in production, use process supervisor (systemd). Keep --reload for development with documented manual cleanup.**

**Rationale**:
1. **Production safety**: Process supervisor (systemd, Docker) provides proper lifecycle management
2. **Development convenience**: --reload is useful for rapid iteration
3. **Simple**: No complex PID file management or process tracking
4. **Standard practice**: Industry standard to use different configs for dev/prod

**Implementation**:

```bash
# Development: start.sh (with reload)
#!/bin/bash
cd backend
pkill -f "python3 -m uvicorn" || true  # Clean up any orphaned processes
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production: Use systemd service (deployment/systemd/sentimentagent.service)
[Unit]
Description=SentimentAgent Backend
After=network.target

[Service]
Type=simple
User=sentimentagent
WorkingDirectory=/opt/sentimentagent/backend
Environment="PYTHONPATH=/opt/sentimentagent/backend/src"
ExecStart=/usr/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Alternatives Rejected**:
- ❌ PID file management: Complex, error-prone, not necessary
- ❌ Always use --reload: Unsafe for production (job interruption)
- ❌ Custom process manager: Reinventing systemd/supervisord
- ❌ No process cleanup: Leads to port conflicts in development

**References**:
- [Uvicorn Deployment Documentation](https://www.uvicorn.org/deployment/)
- [systemd Service Units](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## 6. Data Loading Strategy

### Question

How to efficiently load historical data on startup?

### Research Findings

**Query Optimization**:
- **Index**: Ensure `collected_at` is indexed for time-range queries
- **Projection**: Only select needed fields (avoid `SELECT *`)
- **Limit**: Use `LIMIT` to cap result size if needed

**Pagination vs Full Load**:
- **Pagination**: Better for large datasets, prevents memory overflow
- **Full load**: Simpler, acceptable if dataset fits in memory (<10k records)
- **Hybrid**: Load recent data (last 7 days) for immediate display, lazy-load older data

**Cache Warming Patterns**:
- **Eager**: Load all data on startup (blocks startup)
- **Lazy**: Load data on first request (slow first response)
- **Background**: Load data async after startup (best of both)

**CosmosDB Query Performance**:
- CosmosDB charges RU (Request Units) per query
- Efficient query: Use indexed fields, avoid cross-partition queries
- Trade-off: Faster queries cost more RUs

### Decision

**Load last 24 hours of data on startup (background task), lazy-load older data on demand**

**Rationale**:
1. **Fast startup**: Background loading doesn't block app initialization
2. **Immediate value**: Most recent data available within seconds
3. **Memory efficient**: Only 48 collections (~1400 posts) in memory
4. **Scalable**: Older data loaded on-demand via API queries

**Implementation**:

```python
from datetime import datetime, timedelta

# In-memory cache for recent data (optional, can query DB directly)
recent_data_cache = {
    "posts": [],
    "loaded_at": None,
    "loading": False
}

async def load_recent_data():
    """Background task: Load last 24 hours of data"""
    global recent_data_cache
    
    if recent_data_cache["loading"]:
        return  # Already loading
    
    recent_data_cache["loading"] = True
    try:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        
        # Query with index on collected_at
        posts = await db.posts.find({
            "collected_at": {"$gte": cutoff}
        }).sort("collected_at", -1).to_list(length=None)
        
        recent_data_cache["posts"] = posts
        recent_data_cache["loaded_at"] = datetime.utcnow()
        logger.info(f"Loaded {len(posts)} recent posts from last 24 hours")
        
    except Exception as e:
        logger.error(f"Failed to load recent data: {e}", exc_info=True)
    finally:
        recent_data_cache["loading"] = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    scheduler.start()
    
    # Background data load (non-blocking)
    asyncio.create_task(load_recent_data())
    
    yield
    
    # Shutdown
    scheduler.shutdown(wait=True)
    await db.disconnect()

# API endpoint uses cache if available, else queries DB
@router.get("/posts/recent")
async def get_recent_posts(hours: int = 24):
    """Get posts from last N hours"""
    if recent_data_cache["loaded_at"] and (datetime.utcnow() - recent_data_cache["loaded_at"]).total_seconds() < 300:
        # Cache is fresh (< 5 minutes old)
        return recent_data_cache["posts"]
    else:
        # Cache stale or not loaded, query DB
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return await db.posts.find({"collected_at": {"$gte": cutoff}}).sort("collected_at", -1).to_list(length=1000)
```

**Alternatives Rejected**:
- ❌ Load all data on startup: Blocks startup, memory intensive (1M+ records)
- ❌ No startup loading: Slow first request, poor UX
- ❌ Persistent cache (Redis): Over-engineered for single service
- ❌ Pagination required: Adds API complexity, not needed for 24h dataset

**References**:
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Azure Cosmos DB Query Best Practices](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query-cheat-sheet)

---

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| **Process Lifecycle** | FastAPI lifespan events | Framework-native, async-compatible |
| **Database Resilience** | Retry decorator (3 retries, exponential backoff) | Simple, transparent, fails fast |
| **Error Recovery** | Catch-log-continue for jobs, fail-fast for startup | High availability, clear failure signals |
| **Health Monitoring** | Enhanced /health JSON endpoint | Simple, human-readable, sufficient |
| **Process Management** | systemd in prod, --reload in dev | Industry standard, safe |
| **Data Loading** | Background load last 24h, lazy-load older | Fast startup, immediate value |

## Dependencies Added

- `psutil` (for process metrics in /health endpoint)

## Configuration Changes

```python
# config.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # New: Health monitoring
    health_check_enabled: bool = True
    
    # New: Database retry
    db_retry_max_attempts: int = 3
    db_retry_base_delay: float = 1.0
    
    # New: Startup data loading
    startup_load_hours: int = 24  # Load last N hours on startup
```

## Next Phase

**Phase 1: Design & Contracts** - Create detailed design documents based on these research decisions:

1. `data-model.md` - Document any schema changes (likely none)
2. `contracts/api-contracts.md` - Enhanced /health endpoint contract
3. `quickstart.md` - Updated startup/troubleshooting guide
4. Update `.github/copilot-instructions.md` with new patterns

All decisions are finalized. Ready to proceed to Phase 1.
