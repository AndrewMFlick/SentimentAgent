# Quickstart Guide: Pre-Cached Sentiment Analysis

**Feature**: 017-pre-cached-sentiment  
**Date**: October 27, 2025

## Overview

This feature adds pre-cached sentiment aggregates to dramatically improve query performance. Instead of loading 9K+ documents and filtering in Python (10+ seconds), the system serves pre-calculated aggregates from cache (<1 second).

**Key Benefits**:
- 24-hour sentiment queries drop from 10.57s to <1s
- 95%+ of requests served from cache
- Automatic background refresh every 15 minutes
- Graceful fallback to on-demand calculation

---

## Quick Start (Development)

### 1. Create the Cache Container

```bash
cd backend
python scripts/create_cache_container.py
```

Expected output:
```
✓ Created container: sentiment_cache
✓ Partition key: /tool_id
✓ Indexing policy applied
```

### 2. Start the Backend (Cache Enabled)

```bash
cd backend
./start.sh
```

The cache refresh job will start automatically and populate the cache within 1 minute.

### 3. Verify Cache is Working

```bash
# Check cache health
curl http://localhost:8000/api/v1/cache/health

# Expected: {"status": "healthy", "total_entries": 60, "cache_hit_rate": 0.95, ...}
```

### 4. Test Sentiment Query Performance

```bash
# Query Jules AI sentiment (24 hours) - should return from cache
time curl "http://localhost:8000/api/v1/tools/877eb2d8-661b-4643-ae62-cfc49e74c31e/sentiment?hours=24"

# Expected: <1 second response time
# Look for: "is_cached": true in response
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request Flow                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  GET /sentiment  │
                    │   (FastAPI)      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  CacheService    │
                    │  .get_cached()   │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
            Cache HIT               Cache MISS
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Return cached    │      │ Calculate on-    │
    │ data (<50ms)     │      │ demand (500ms)   │
    └──────────────────┘      └────────┬─────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Save to cache    │
                              │ Return to user   │
                              └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Background Refresh Flow                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  APScheduler     │
                    │  (every 15 min)  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  CacheService    │
                    │  .refresh_all()  │
                    └────────┬─────────┘
                             │
                             ▼
           ┌─────────────────┴─────────────────┐
           │  For each tool (Jules, Cursor...) │
           │  For each period (1h,24h,7d,30d)  │
           └─────────────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Query sentiment  │
                    │ Calculate aggs   │
                    │ Save to cache    │
                    └──────────────────┘
```

---

## Configuration

Add to `backend/.env`:

```bash
# Sentiment Cache (Feature 017)
ENABLE_SENTIMENT_CACHE=true             # Feature flag
CACHE_REFRESH_INTERVAL_MINUTES=15       # Background refresh frequency
CACHE_TTL_MINUTES=30                    # Max age before stale
COSMOS_CONTAINER_SENTIMENT_CACHE=sentiment_cache  # Container name
```

Default values in `backend/src/config.py`:

```python
enable_sentiment_cache: bool = True
cache_refresh_interval_minutes: int = 15
cache_ttl_minutes: int = 30
cosmos_container_sentiment_cache: str = "sentiment_cache"
```

---

## Key Files

### New Files Created

```
backend/src/services/cache_service.py      # Main cache logic
backend/src/models/cache.py                # Pydantic models
backend/scripts/create_cache_container.py  # Setup script
```

### Modified Files

```
backend/src/config.py                      # Add cache settings
backend/src/services/scheduler.py          # Add cache refresh job
backend/src/services/database.py           # Integrate cache lookups
backend/src/api/tools.py                   # Add cache headers
backend/src/main.py                        # Health endpoint
```

---

## Testing

### Unit Tests

```bash
cd backend
pytest tests/unit/test_cache_service.py -v
```

**Key tests**:
- Cache hit/miss logic
- Aggregate calculation correctness
- TTL expiration
- Invalidation

### Integration Tests

```bash
pytest tests/integration/test_cache_integration.py -v
```

**Key tests**:
- End-to-end cache population
- Background refresh job
- Cache invalidation on reanalysis
- Fallback to on-demand calculation

### Performance Tests

```bash
pytest tests/performance/test_cache_performance.py -v
```

**Key tests**:
- 24-hour query: <1s (down from 10.57s)
- Cache hit: <50ms
- Cache miss + populate: <500ms
- Full refresh: <30s for all tools

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/v1/cache/health
```

**Healthy indicators**:
- `status: "healthy"`
- `cache_hit_rate > 0.90`
- `error_count_24h < 5`
- `last_refresh` within last 20 minutes

**Degraded indicators**:
- `status: "degraded"`
- `cache_hit_rate: 0.70-0.90`
- `error_count_24h: 5-20`

**Unhealthy indicators**:
- `status: "unhealthy"`
- `cache_hit_rate < 0.70`
- `error_count_24h > 20`
- `last_refresh` > 30 minutes ago

### Logs to Monitor

```bash
# Watch cache refresh jobs
tail -f backend/logs/app.log | grep "cache_refresh"

# Watch for cache hits/misses
tail -f backend/logs/app.log | grep "cache_status"

# Watch for errors
tail -f backend/logs/app.log | grep -E "ERROR|cache.*error"
```

---

## Troubleshooting

### Issue: Cache always shows MISS

**Symptoms**: `X-Cache-Status: MISS` on every request

**Diagnosis**:
```bash
# Check if cache container exists
curl http://localhost:8000/api/v1/cache/health

# Check if refresh job is running
tail -f backend/logs/app.log | grep "cache_refresh"
```

**Solution**:
1. Verify container exists: `python scripts/create_cache_container.py`
2. Restart backend: `./start.sh`
3. Wait 1 minute for first refresh
4. Check health: `curl http://localhost:8000/api/v1/cache/health`

---

### Issue: Slow queries despite cache

**Symptoms**: Queries still take >2 seconds

**Diagnosis**:
```bash
# Check cache age
curl "http://localhost:8000/api/v1/tools/{tool_id}/sentiment?hours=24" | jq '.cached_at'

# Check if custom time range (not cached)
# Example: hours=48 is NOT a standard period (1,24,168,720)
```

**Solution**:
- Standard periods (1h, 24h, 7d, 30d) are cached
- Custom periods calculate on-demand
- Use nearest standard period for best performance

---

### Issue: Stale data after reanalysis

**Symptoms**: Sentiment data doesn't update after reanalysis

**Diagnosis**:
```bash
# Check if invalidation is enabled
grep "enable_auto_reanalysis" backend/.env

# Check logs for invalidation
tail -f backend/logs/app.log | grep "invalidate_tool_cache"
```

**Solution**:
1. Ensure `enable_auto_reanalysis=true` in `.env`
2. Verify reanalysis service calls `cache_service.invalidate_tool_cache()`
3. Manual invalidation: `curl -X POST http://localhost:8000/api/v1/cache/invalidate/{tool_id}`

---

## Performance Benchmarks

### Before Cache (Baseline)

| Query | Response Time | Documents Loaded |
|-------|--------------|------------------|
| 1 hour | 0.01s | 0 (no data) |
| 24 hours | 10.57s | 9,275 docs |
| 7 days | ~30s | 30K+ docs |

### After Cache (Target)

| Query | Response Time | Cache Hit Rate |
|-------|--------------|----------------|
| 1 hour | <1s | 95%+ |
| 24 hours | <1s | 95%+ |
| 7 days | <2s | 95%+ |
| 30 days | <2s | 90%+ |

### Cache Operations

| Operation | Time |
|-----------|------|
| Cache lookup (hit) | <50ms |
| Cache miss + populate | 100-500ms |
| Full refresh (60 entries) | ~15s |
| Invalidate one tool | <200ms |

---

## Next Steps

After verifying the cache works:

1. **Monitor cache hit rate** for 24 hours
2. **Adjust refresh interval** if needed (default 15 min)
3. **Add cache metrics** to frontend dashboard
4. **Set up alerts** for cache health degradation
5. **Document cache behavior** for end users

---

## FAQ

**Q: What happens if the cache container is deleted?**  
A: System falls back to on-demand calculation. Performance degrades but functionality remains intact. Recreate container and restart backend to restore cache.

**Q: Can I disable caching?**  
A: Yes, set `ENABLE_SENTIMENT_CACHE=false` in `.env`. All queries will calculate on-demand.

**Q: How much storage does the cache use?**  
A: ~30 KB for 15 tools × 4 periods × 500 bytes/entry. Negligible.

**Q: What's the cache invalidation strategy?**  
A: Event-based invalidation when reanalysis completes. Time-based expiry via TTL (30 min default). Background refresh every 15 minutes.

**Q: Can I manually refresh the cache?**  
A: Yes, via admin endpoint: `POST /api/v1/cache/refresh` (requires admin token).
