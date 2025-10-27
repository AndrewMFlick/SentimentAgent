# Research & Technical Decisions

**Feature**: Pre-Cached Sentiment Analysis  
**Date**: October 27, 2025  
**Status**: Complete

## Research Tasks Completed

### 1. Cache Storage Solution

**Decision**: New Azure Cosmos DB container named `sentiment_cache`

**Rationale**:
- Consistent with existing architecture (Azure Cosmos DB SQL API)
- Persists across restarts (unlike in-memory cache)
- Supports same query patterns as other containers
- Minimal infrastructure changes required
- Already have database client and connection management

**Alternatives Considered**:
- **In-memory cache (Python dict)**: Fast but lost on restart, no persistence, memory constraints
- **Redis/Memcached**: Additional infrastructure, cost, and complexity for local development
- **Existing sentiment_scores container**: Would mix raw data with aggregates, complicating queries

**Implementation Details**:
- Container: `sentiment_cache` in existing `sentiment_analysis` database
- Partition key: `tool_id` (ensures all time periods for a tool are co-located)
- Document structure: One document per tool-per-time-period combination

---

### 2. Cache Refresh Mechanism

**Decision**: APScheduler background job with 15-minute interval

**Rationale**:
- APScheduler already in use (`backend/src/services/scheduler.py`)
- Proven pattern for data collection, cleanup, and trending analysis jobs
- Supports async execution without blocking API requests
- Configurable intervals via settings

**Alternatives Considered**:
- **Event-driven refresh**: Complex, requires message queue, over-engineered for 15-min refresh
- **On-demand refresh**: Would still cause slow queries on first request after expiry
- **Continuous refresh loop**: Harder to manage, less predictable resource usage

**Implementation Details**:
- New scheduled job: `refresh_sentiment_cache` 
- Interval: 15 minutes (configurable via `settings.cache_refresh_interval_minutes`)
- Error handling: Log failures, continue to next tool, don't crash scheduler
- Execution pattern: Async function called by APScheduler's AsyncIOScheduler

---

### 3. Aggregate Calculation Strategy

**Decision**: Query sentiment_scores by timestamp, aggregate in Python

**Rationale**:
- Cosmos DB emulator doesn't support complex aggregations (no GROUP BY with ARRAY_CONTAINS)
- Python aggregation is acceptable for cache refresh (not user-facing)
- Can optimize by querying only new data since last cache update
- Consistent with existing pattern in `get_tool_sentiment()` 

**Alternatives Considered**:
- **Server-side aggregation**: Not supported by Cosmos DB emulator's SQL API
- **Stored procedures**: Possible but adds complexity, harder to test
- **Pre-aggregation during sentiment analysis**: Couples analysis with caching, harder to maintain

**Implementation Details**:
- For each tool, for each time period (1h, 24h, 7d, 30d):
  1. Query sentiment_scores where `_ts >= cutoff AND tool_id IN detected_tool_ids`
  2. Aggregate: count mentions, sum sentiments, calculate percentages
  3. Store result in sentiment_cache with timestamp
- Use `_datetime_to_timestamp()` helper for consistent timestamp queries (per Feature 004)

---

### 4. Cache Invalidation Strategy

**Decision**: Event-based invalidation on reanalysis completion

**Rationale**:
- Reanalysis can change detected_tool_ids for existing sentiment scores
- Must invalidate affected tool caches to show updated data
- ReanalysisService already tracks which tools were affected
- Avoids stale data after reanalysis jobs

**Alternatives Considered**:
- **Time-based expiry only**: Would show stale data up to 15 minutes after reanalysis
- **Full cache clear**: Too aggressive, invalidates unaffected tools
- **No invalidation**: Unacceptable - users would see wrong data

**Implementation Details**:
- When reanalysis job completes, call `cache_service.invalidate_tool_cache(tool_id)`
- Delete all cache entries for affected tool_id
- Next API request will trigger cache miss → on-demand calculation → repopulate cache
- Background refresh will also detect missing cache and repopulate

---

### 5. Cache Miss Handling

**Decision**: Fallback to on-demand calculation with cache population

**Rationale**:
- Graceful degradation - system works even if cache is cold/empty
- First request after invalidation gets computed and cached for future requests
- Matches current behavior but populates cache for next time

**Alternatives Considered**:
- **Return error on cache miss**: Poor UX, system appears broken
- **Always query directly**: Defeats purpose of caching
- **Block until cache populated**: Causes timeout on first request

**Implementation Details**:
- API endpoint checks cache first
- If cache miss (no entry or expired):
  1. Call `db.get_tool_sentiment()` (existing method)
  2. Save result to cache with current timestamp
  3. Return result to user
- Background job prevents most cache misses by pre-populating

---

### 6. Time Period Granularities

**Decision**: Support 1-hour, 24-hour, 7-day, 30-day periods

**Rationale**:
- Matches common user query patterns
- Balances storage cost vs. query coverage
- 1-hour: Recent activity, fast queries
- 24-hour: Daily trends (current pain point - 10+ seconds)
- 7-day: Weekly patterns
- 30-day: Monthly analysis (spec requirement)

**Alternatives Considered**:
- **Only 24-hour**: Doesn't solve all slow queries
- **Arbitrary time ranges**: Infinite cache storage, can't pre-calculate
- **More granularities (6h, 12h)**: Diminishing returns, more storage

**Implementation Details**:
- Enum: `CachePeriod` with values: HOUR_1, HOUR_24, DAY_7, DAY_30
- Each tool has 4 cache entries (one per period)
- Cache key: `{tool_id}:{period}` 

---

## Best Practices Applied

### Azure Cosmos DB (SQL API)
- **Partition key choice**: Use `tool_id` for cache container (high cardinality, aligns with queries)
- **Minimize cross-partition queries**: Each tool's cache is in one partition
- **Timestamp queries**: Use `_ts` field and `_datetime_to_timestamp()` helper (Feature 004 pattern)
- **Async SDK usage**: All Cosmos operations use `await` for better throughput
- **Error handling**: Retry on 429 (rate limit), log diagnostics on failures

### FastAPI Best Practices
- **Dependency injection**: CacheService via `Depends(get_cache_service)`
- **Async endpoints**: Cache lookup and fallback are async
- **Structured logging**: Include tool_id, period, cache_hit/miss, duration
- **Health checks**: Add cache health metrics (hit rate, last refresh time)

### APScheduler Patterns
- **Async jobs**: Use `async def` for scheduler jobs
- **Error isolation**: Wrap each tool refresh in try/except, continue on failure
- **Idempotent jobs**: Cache refresh can run multiple times safely
- **Non-blocking**: Jobs don't block API request handling

---

## Configuration Additions

Add to `backend/src/config.py`:

```python
# Sentiment Cache (Feature 017)
enable_sentiment_cache: bool = True  # Feature flag
cache_refresh_interval_minutes: int = 15  # Background refresh frequency
cache_ttl_minutes: int = 30  # Max age before considered stale
cosmos_container_sentiment_cache: str = "sentiment_cache"  # Container name
```

---

## Dependencies Confirmed

- **Existing**: Azure Cosmos SDK 4.5.1 ✅
- **Existing**: APScheduler 3.10.4 ✅
- **Existing**: FastAPI 0.109.2 ✅
- **Existing**: Pydantic 2.x ✅
- **Existing**: structlog 24.1.0 ✅
- **No new dependencies required** ✅

---

## Performance Estimates

### Storage Requirements
- Sentiment cache entries: ~4 per tool (one per time period)
- Active tools: ~15 (from Tools container)
- Total cache documents: ~60 (15 tools × 4 periods)
- Document size: ~500 bytes (tool_id, period, counts, timestamp)
- **Total storage: ~30 KB (negligible)**

### Query Performance
- **Cache hit (expected 95%+)**: <50ms (single document lookup by id)
- **Cache miss + populate**: ~500ms (calculate + save + return)
- **Background refresh**: ~15 seconds for all 60 cache entries (1 per second)
- **Target met**: 24-hour queries drop from 10.57s to <1s ✅

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Cache refresh failure | Stale data up to 30 min | Log errors, alert on repeated failures, fallback to direct query |
| Cache storage growth | Unbounded storage | Implement cleanup job, delete expired entries older than 7 days |
| Invalidation race condition | Brief stale data | Acceptable - 15-min refresh will correct, or cache miss triggers update |
| Cold start (empty cache) | First requests slow | Background job pre-populates on startup, API has fallback |
| Cosmos DB rate limiting | Refresh job throttled | Use exponential backoff, spread refreshes over 15-min window |

---

## Open Questions

None - all technical decisions resolved.
