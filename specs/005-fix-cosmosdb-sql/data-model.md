# Data Model

**Feature**: 005-fix-cosmosdb-sql  
**Created**: 2025-01-15  
**Status**: Complete ✅

## Overview

This feature does NOT introduce new data models. It fixes an existing query method that aggregates sentiment statistics from the `Post` collection.

## Existing Entities

### Post (CosmosDB Document)

**Collection**: `reddit_posts`  
**Managed By**: `backend/src/services/database.py`

**Schema**:

```python
{
    "id": "t3_abc123",              # Reddit post ID (unique)
    "subreddit": "politics",         # Subreddit name
    "title": "Breaking news...",     # Post title
    "text": "Full text content",     # Post body text
    "score": 1250,                   # Reddit upvote score
    "created_utc": 1705334400,       # Unix timestamp (int)
    "url": "https://...",            # Post URL
    "sentiment": "positive",         # Computed: "positive" | "negative" | "neutral"
    "compound_score": 0.7834,        # Computed: float [-1.0, 1.0]
    "_ts": 1705334400                # CosmosDB system timestamp (Unix epoch)
}
```

**Indexes**:

- Primary: `id` (automatic)
- Query indexes: `subreddit`, `_ts`, `sentiment` (used in aggregation queries)

**Relationships**:

- None (denormalized document)

### SentimentStatistics (Response Model)

**Type**: Pydantic model (not persisted)  
**Defined In**: `backend/src/models/` (or inline in `database.py`)

**Schema**:

```python
class SentimentStatistics:
    total: int              # Total posts in time window
    positive: int           # Count where sentiment = "positive"
    negative: int           # Count where sentiment = "negative"
    neutral: int            # Count where sentiment = "neutral"
    avg_sentiment: float    # Average compound_score
```

**Validation Rules**:

- `total >= 0`
- `positive + negative + neutral == total` (must sum correctly)
- `avg_sentiment` in range `[-1.0, 1.0]`

**Current Problem**: `positive`, `negative`, `neutral` all return 0 due to broken CASE WHEN query

## Query Patterns

### get_sentiment_stats() Method

**Current (Broken) Implementation**:

```sql
SELECT 
    COUNT(1) as total,
    SUM(CASE WHEN c.sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
    SUM(CASE WHEN c.sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
    SUM(CASE WHEN c.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
    AVG(c.compound_score) as avg_sentiment
FROM c 
WHERE c._ts >= @cutoff
```

**Problem**: CosmosDB does not support `CASE WHEN` in aggregations → returns 0 for sentiment counts

**Fixed Implementation** (4 separate queries):

```python
# Query 1: Total count
total_query = """
SELECT VALUE COUNT(1) 
FROM c 
WHERE c._ts >= @cutoff
"""

# Query 2: Positive count
positive_query = """
SELECT VALUE COUNT(1) 
FROM c 
WHERE c._ts >= @cutoff AND c.sentiment = 'positive'
"""

# Query 3: Negative count
negative_query = """
SELECT VALUE COUNT(1) 
FROM c 
WHERE c._ts >= @cutoff AND c.sentiment = 'negative'
"""

# Query 4: Neutral count
neutral_query = """
SELECT VALUE COUNT(1) 
FROM c 
WHERE c._ts >= @cutoff AND c.sentiment = 'neutral'
"""

# Query 5: Average sentiment
avg_query = """
SELECT VALUE AVG(c.compound_score) 
FROM c 
WHERE c._ts >= @cutoff
"""
```

**Execution**: Parallel execution using `asyncio.gather()` for performance

### Query Parameters

**Common Parameters**:

- `@cutoff`: Unix timestamp (int) - filters `c._ts >= @cutoff`
- Optional: `@subreddit` - filters `c.subreddit = @subreddit`

**Example**:

```python
cutoff = int(time.time()) - (hours * 3600)
parameters = [{"name": "@cutoff", "value": cutoff}]
```

## Data Flow

```text
1. API Request → /api/v1/sentiment/stats?hours=24
2. Route Handler → database.get_sentiment_stats(hours=24)
3. Database Service:
   a. Calculate cutoff timestamp
   b. Execute 5 queries in parallel (asyncio.gather)
   c. Aggregate results into SentimentStatistics
4. Response → JSON: {"total": 1250, "positive": 687, ...}
```

## Schema Changes

**Changes Required**: None

**Backward Compatibility**: ✅ Fully compatible

- Same API request/response format
- Same database schema
- Same query parameters
- Only changes: query execution logic (internal implementation detail)

## Test Data Requirements

**For Integration Tests**:

```python
# Insert known test data
test_posts = [
    {"id": "test1", "sentiment": "positive", "compound_score": 0.8, "_ts": now},
    {"id": "test2", "sentiment": "positive", "compound_score": 0.6, "_ts": now},
    {"id": "test3", "sentiment": "negative", "compound_score": -0.5, "_ts": now},
    {"id": "test4", "sentiment": "neutral", "compound_score": 0.1, "_ts": now},
]

# Expected results
expected = {
    "total": 4,
    "positive": 2,
    "negative": 1,
    "neutral": 1,
    "avg_sentiment": 0.25  # (0.8 + 0.6 - 0.5 + 0.1) / 4
}
```

## Performance Considerations

**Query Execution Time**:

- Target: < 2 seconds for 1-week time windows
- Strategy: Parallel execution reduces latency
- Indexes: Ensure `_ts` and `sentiment` are indexed

**Data Volume**:

- Expected: ~10,000 posts per week (low volume)
- Query impact: Minimal with proper indexes

## Summary

This is a **query fix**, not a data model change. All entities and schemas remain unchanged. The fix replaces broken CASE WHEN aggregation with separate, CosmosDB-compatible COUNT queries.

**Key Points**:

- ✅ No new entities
- ✅ No schema changes
- ✅ Maintains backward compatibility
- ✅ Queries execute in parallel for performance
- ✅ Results match expected validation rules

**Next Step**: Create API contract documentation in `contracts/api.md`
