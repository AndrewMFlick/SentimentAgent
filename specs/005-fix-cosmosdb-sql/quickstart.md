# Quick Start Guide

**Feature**: 005-fix-cosmosdb-sql  
**Branch**: `005-fix-cosmosdb-sql`  
**Created**: 2025-01-15

## Overview

Fix the `get_sentiment_stats()` method in `backend/src/services/database.py` to use CosmosDB-compatible SQL queries instead of unsupported `CASE WHEN` syntax.

---

## Problem Summary

**Current Bug**: Sentiment counts always return 0

```json
{
  "total": 1250,
  "positive": 0,     // ❌ Always 0
  "negative": 0,     // ❌ Always 0
  "neutral": 0       // ❌ Always 0
}
```

**Root Cause**: CosmosDB PostgreSQL mode doesn't support `SUM(CASE WHEN ...)` syntax

---

## Solution Summary

Replace 1 complex query with 5 separate queries:

1. Total count
2. Positive count
3. Negative count
4. Neutral count
5. Average sentiment

Execute in parallel using `asyncio.gather()` for performance.

---

## Quick Implementation Steps

### 1. Update database.py

**File**: `backend/src/services/database.py`  
**Method**: `get_sentiment_stats()` (lines 338-375)

**Replace**:

```python
# OLD: Single query with CASE WHEN (broken)
query = """
SELECT 
    COUNT(1) as total,
    SUM(CASE WHEN c.sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
    ...
FROM c WHERE c._ts >= @cutoff
"""
```

**With**:

```python
# NEW: Separate queries (CosmosDB compatible)
total_query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
positive_query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'positive'"
negative_query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'negative'"
neutral_query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'neutral'"
avg_query = "SELECT VALUE AVG(c.compound_score) FROM c WHERE c._ts >= @cutoff"

# Execute in parallel
results = await asyncio.gather(
    self._execute_scalar_query(total_query, parameters),
    self._execute_scalar_query(positive_query, parameters),
    self._execute_scalar_query(negative_query, parameters),
    self._execute_scalar_query(neutral_query, parameters),
    self._execute_scalar_query(avg_query, parameters)
)

total, positive, negative, neutral, avg_sentiment = results
```

### 2. Add Helper Method

```python
async def _execute_scalar_query(self, query: str, parameters: List[Dict]) -> Union[int, float]:
    """Execute a query that returns a single scalar value."""
    result = self.container.query_items(query, parameters=parameters, enable_cross_partition_query=True)
    items = list(result)
    return items[0] if items else 0
```

### 3. Update Error Handling

```python
try:
    results = await asyncio.gather(...)
except Exception as e:
    logger.error(f"Failed to query sentiment stats: {e}", exc_info=True)
    raise  # Fail-fast, don't return zeros
```

---

## Testing

### Run Existing Tests

```bash
cd backend
pytest tests/ -v
```

### Add Integration Test

**File**: `backend/tests/integration/test_datetime_queries.py`

```python
async def test_sentiment_stats_accuracy():
    """Test that sentiment counts are accurate (not zeros)."""
    # Insert known test data
    now = int(time.time())
    test_posts = [
        {"id": "test1", "sentiment": "positive", "compound_score": 0.8, "_ts": now},
        {"id": "test2", "sentiment": "positive", "compound_score": 0.6, "_ts": now},
        {"id": "test3", "sentiment": "negative", "compound_score": -0.5, "_ts": now},
        {"id": "test4", "sentiment": "neutral", "compound_score": 0.1, "_ts": now},
    ]
    
    # TODO: Insert test_posts into database
    
    # Query stats
    stats = await database.get_sentiment_stats(hours=1)
    
    # Verify accurate counts
    assert stats["total"] == 4
    assert stats["positive"] == 2
    assert stats["negative"] == 1
    assert stats["neutral"] == 1
    assert abs(stats["avg_sentiment"] - 0.25) < 0.01  # (0.8 + 0.6 - 0.5 + 0.1) / 4
    
    # Verify validation rule
    assert stats["positive"] + stats["negative"] + stats["neutral"] == stats["total"]
```

### Manual Testing

```bash
# 1. Start backend
cd backend
./start.sh

# 2. Query API
curl http://localhost:8000/api/v1/sentiment/stats

# 3. Verify response
# Expected: positive + negative + neutral == total
# Expected: Values are NOT all zeros
```

---

## Validation Checklist

- [ ] `get_sentiment_stats()` uses 5 separate queries
- [ ] Queries use `SELECT VALUE COUNT(1)` syntax
- [ ] Queries execute in parallel with `asyncio.gather()`
- [ ] Error handling raises exceptions (no silent zeros)
- [ ] All existing tests pass
- [ ] Integration test verifies accurate counts
- [ ] Manual testing shows non-zero sentiment counts
- [ ] Response validation: `positive + negative + neutral == total`
- [ ] Performance: < 2 seconds for 1-week windows

---

## Common Issues

### Issue 1: "asyncio.gather not found"

**Solution**: Add import at top of file:

```python
import asyncio
```

### Issue 2: Query returns empty list

**Problem**: No data in time window

**Solution**: Check `_ts` values in database, verify time window calculation

### Issue 3: Performance > 2 seconds

**Problem**: Parallel execution not working

**Solution**: Verify `asyncio.gather()` is used (not sequential queries)

---

## Performance Monitoring

```python
import time

start = time.time()
stats = await database.get_sentiment_stats(hours=168)  # 7 days
elapsed = time.time() - start

logger.info(f"get_sentiment_stats took {elapsed:.2f}s")
assert elapsed < 2.0, "Performance target missed"
```

---

## References

- **Specification**: `specs/005-fix-cosmosdb-sql/spec.md`
- **Implementation Plan**: `specs/005-fix-cosmosdb-sql/plan.md`
- **Research**: `specs/005-fix-cosmosdb-sql/research.md`
- **Data Model**: `specs/005-fix-cosmosdb-sql/data-model.md`
- **API Contract**: `specs/005-fix-cosmosdb-sql/contracts/api.md`
- **GitHub Issue**: https://github.com/AndrewMFlick/SentimentAgent/issues/15

---

## Summary

**Quick Steps**:

1. Update `backend/src/services/database.py` with 5 separate queries
2. Use `asyncio.gather()` for parallel execution
3. Add `_execute_scalar_query()` helper method
4. Update error handling to fail-fast
5. Add integration test for accuracy
6. Verify performance < 2s

**Expected Result**: Dashboard shows accurate sentiment counts (not zeros)
