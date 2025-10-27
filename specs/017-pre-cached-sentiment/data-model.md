# Data Model

**Feature**: Pre-Cached Sentiment Analysis  
**Date**: October 27, 2025

## Entities

### SentimentCacheEntry

Pre-calculated sentiment aggregates for a specific tool and time period.

**Attributes**:

- `id` (string, required): Unique identifier, format: `{tool_id}:{period}` (e.g., `"877eb2d8:HOUR_24"`)
- `tool_id` (string, required): ID of the tool this cache entry represents (partition key)
- `period` (string, required): Time period granularity - one of: `"HOUR_1"`, `"HOUR_24"`, `"DAY_7"`, `"DAY_30"`
- `total_mentions` (integer, required): Total number of times tool was mentioned in this period
- `positive_count` (integer, required): Number of positive sentiment mentions
- `negative_count` (integer, required): Number of negative sentiment mentions
- `neutral_count` (integer, required): Number of neutral sentiment mentions
- `positive_percentage` (float, required): Percentage of positive mentions (0-100)
- `negative_percentage` (float, required): Percentage of negative mentions (0-100)
- `neutral_percentage` (float, required): Percentage of neutral mentions (0-100)
- `average_sentiment` (float, required): Average sentiment score (-1.0 to 1.0)
- `period_start_ts` (integer, required): Unix timestamp of period start
- `period_end_ts` (integer, required): Unix timestamp of period end (usually current time)
- `last_updated_ts` (integer, required): Unix timestamp when this cache entry was last refreshed
- `is_stale` (boolean, computed): Whether cache is older than TTL (computed from `last_updated_ts`)
- `_ts` (integer, system): Cosmos DB system timestamp

**Validation Rules**:

- `total_mentions` must equal `positive_count + negative_count + neutral_count`
- Percentages must sum to 100.0 (within 0.1 tolerance for rounding)
- `average_sentiment` must be between -1.0 and 1.0
- `period_start_ts` must be less than `period_end_ts`
- `last_updated_ts` must be less than or equal to current time

**State Transitions**:

1. **Created**: Cache entry created by background job or on-demand calculation
2. **Fresh**: `last_updated_ts` within TTL window (30 minutes)
3. **Stale**: `last_updated_ts` exceeds TTL, eligible for refresh
4. **Invalidated**: Deleted when tool's sentiment data changes (reanalysis)

**Relationships**:

- Many-to-one with Tool (via `tool_id`)
- Represents aggregate of many SentimentScore documents

---

### CacheMetadata

Tracks cache health and performance metrics for monitoring.

**Attributes**:

- `id` (string, required): Always `"metadata"` (singleton document)
- `last_refresh_ts` (integer, required): Unix timestamp of last successful cache refresh job
- `last_refresh_duration_ms` (integer, required): How long the last refresh took in milliseconds
- `total_entries` (integer, required): Current count of cache entries
- `cache_hits_24h` (integer, required): Number of cache hits in last 24 hours
- `cache_misses_24h` (integer, required): Number of cache misses in last 24 hours
- `cache_hit_rate` (float, computed): `cache_hits_24h / (cache_hits_24h + cache_misses_24h)`
- `error_count_24h` (integer, required): Number of errors in last 24 hours
- `tools_refreshed` (array of strings, required): List of tool IDs refreshed in last cycle
- `_ts` (integer, system): Cosmos DB system timestamp

**Validation Rules**:

- `last_refresh_duration_ms` must be >= 0
- `total_entries` must be >= 0
- `cache_hits_24h` and `cache_misses_24h` must be >= 0
- `cache_hit_rate` between 0.0 and 1.0

**State Transitions**:

1. **Initialized**: Created on first cache refresh
2. **Updated**: Updated after each cache refresh job
3. **Monitored**: Read by health check endpoints

**Relationships**:

- Singleton (only one CacheMetadata document)
- Tracks metrics for all SentimentCacheEntry documents

---

## Storage Schema

### Cosmos DB Container: `sentiment_cache`

**Partition Key**: `/tool_id`

**Rationale**: All cache entries for a tool are co-located in one partition, enabling efficient queries for a specific tool across all time periods.

**Indexing Policy**:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/tool_id/?"
    },
    {
      "path": "/period/?"
    },
    {
      "path": "/last_updated_ts/?"
    },
    {
      "path": "/_ts/?"
    }
  ],
  "excludedPaths": [
    {
      "path": "/*"
    }
  ]
}
```

**TTL Policy**: No automatic TTL - cleanup handled by background job

---

## Example Documents

### SentimentCacheEntry (24-hour period)

```json
{
  "id": "877eb2d8-661b-4643-ae62-cfc49e74c31e:HOUR_24",
  "tool_id": "877eb2d8-661b-4643-ae62-cfc49e74c31e",
  "period": "HOUR_24",
  "total_mentions": 1789,
  "positive_count": 892,
  "negative_count": 534,
  "neutral_count": 363,
  "positive_percentage": 49.9,
  "negative_percentage": 29.9,
  "neutral_percentage": 20.3,
  "average_sentiment": 0.15,
  "period_start_ts": 1730000000,
  "period_end_ts": 1730086400,
  "last_updated_ts": 1730086400,
  "_ts": 1730086400
}
```

### CacheMetadata

```json
{
  "id": "metadata",
  "tool_id": "metadata",
  "last_refresh_ts": 1730086400,
  "last_refresh_duration_ms": 12500,
  "total_entries": 60,
  "cache_hits_24h": 1250,
  "cache_misses_24h": 45,
  "cache_hit_rate": 0.965,
  "error_count_24h": 2,
  "tools_refreshed": [
    "877eb2d8-661b-4643-ae62-cfc49e74c31e",
    "a5c3e9f1-2b4d-4e1c-9a8b-3c5d7f9e1a2b"
  ],
  "_ts": 1730086400
}
```

---

## Data Flow

### Cache Population Flow

```
1. Background job triggers every 15 minutes
   ↓
2. For each active tool:
   ↓
3. For each period (HOUR_1, HOUR_24, DAY_7, DAY_30):
   ↓
4. Query sentiment_scores WHERE _ts >= period_start AND tool_id in detected_tool_ids
   ↓
5. Aggregate in Python: count mentions, calculate percentages, average sentiment
   ↓
6. Create/update SentimentCacheEntry document
   ↓
7. Update CacheMetadata with stats
```

### Cache Read Flow

```
1. API request: GET /api/v1/tools/{tool_id}/sentiment?hours=24
   ↓
2. Check cache: Query sentiment_cache WHERE id = "{tool_id}:HOUR_24"
   ↓
3a. Cache HIT → Return cached data (increment cache_hits_24h)
   ↓
3b. Cache MISS → Calculate on-demand → Save to cache → Return (increment cache_misses_24h)
```

### Cache Invalidation Flow

```
1. Reanalysis job completes for tool_id
   ↓
2. CacheService.invalidate_tool_cache(tool_id)
   ↓
3. Delete all documents WHERE tool_id = {tool_id}
   ↓
4. Next API request triggers cache MISS → repopulates
   ↓
5. Background job also detects missing entries → repopulates
```

---

## Migration Notes

**New Container Required**: `sentiment_cache`

**Creation Script**: `backend/scripts/create_cache_container.py`

```python
# Pseudo-code for container creation
database.create_container(
    id="sentiment_cache",
    partition_key=PartitionKey(path="/tool_id"),
    indexing_policy=<see above>
)
```

**No Data Migration**: New feature, starts with empty cache. Background job populates on first run.

---

## Performance Characteristics

| Operation | Complexity | Expected Time |
|-----------|-----------|---------------|
| Cache lookup by tool+period | O(1) - point read | <50ms |
| Cache refresh (all tools) | O(n×m) where n=tools, m=periods | ~15 seconds |
| Cache invalidation (one tool) | O(m) where m=periods | <200ms |
| Aggregate calculation | O(k) where k=mentions in period | 100-500ms |
| Cache metadata update | O(1) - single document | <50ms |
