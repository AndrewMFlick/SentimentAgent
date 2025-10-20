# API Contract

**Feature**: 005-fix-cosmosdb-sql  
**Created**: 2025-01-15  
**Status**: No changes to API contract (internal fix only)

## Overview

This feature fixes an internal database query bug. The API endpoint contract **remains unchanged**.

## Affected Endpoint

### GET /api/v1/sentiment/stats

**Purpose**: Retrieve aggregated sentiment statistics for a time window

**Changes**: None (this fix resolves incorrect data, but API contract stays the same)

---

## Request Specification

### HTTP Method

`GET`

### URL Path

`/api/v1/sentiment/stats`

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `subreddit` | string | No | `null` | Filter by specific subreddit (e.g., "politics") |
| `hours` | integer | No | `24` | Time window in hours (e.g., 24 for last 24 hours) |

### Request Headers

```http
Accept: application/json
```

### Request Examples

**Example 1: Default (last 24 hours, all subreddits)**

```bash
curl http://localhost:8000/api/v1/sentiment/stats
```

**Example 2: Specific subreddit, 7 days**

```bash
curl "http://localhost:8000/api/v1/sentiment/stats?subreddit=politics&hours=168"
```

**Example 3: Last 1 hour**

```bash
curl "http://localhost:8000/api/v1/sentiment/stats?hours=1"
```

---

## Response Specification

### Success Response (200 OK)

**Content-Type**: `application/json`

**Schema**:

```json
{
  "total": 0,
  "positive": 0,
  "negative": 0,
  "neutral": 0,
  "avg_sentiment": 0.0
}
```

**Field Descriptions**:

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `total` | integer | >= 0 | Total number of posts in time window |
| `positive` | integer | >= 0 | Count of posts with sentiment = "positive" |
| `negative` | integer | >= 0 | Count of posts with sentiment = "negative" |
| `neutral` | integer | >= 0 | Count of posts with sentiment = "neutral" |
| `avg_sentiment` | float | [-1.0, 1.0] | Average compound sentiment score |

**Validation Rules**:

- `positive + negative + neutral == total` (must sum correctly)
- `avg_sentiment` must be in range `[-1.0, 1.0]`

**Current Bug**: Before this fix, `positive`, `negative`, `neutral` all return `0` even when data exists

**After Fix**: Fields return accurate counts based on database data

### Success Response Examples

**Example 1: Mixed sentiment**

```json
{
  "total": 1250,
  "positive": 687,
  "negative": 312,
  "neutral": 251,
  "avg_sentiment": 0.234
}
```

**Example 2: No data in time window**

```json
{
  "total": 0,
  "positive": 0,
  "negative": 0,
  "neutral": 0,
  "avg_sentiment": 0.0
}
```

**Example 3: Mostly negative sentiment**

```json
{
  "total": 450,
  "positive": 89,
  "negative": 312,
  "neutral": 49,
  "avg_sentiment": -0.421
}
```

### Error Responses

**400 Bad Request** (Invalid parameters)

```json
{
  "detail": "Invalid hours parameter: must be positive integer"
}
```

**500 Internal Server Error** (Database failure)

```json
{
  "detail": "Failed to query sentiment statistics"
}
```

**Error Handling Change**: After fix, database query failures will raise exceptions instead of silently returning zeros

---

## Behavioral Changes

### Before Fix (Current Behavior)

**Problem**: Database query uses unsupported `CASE WHEN` syntax

**Result**:

```json
{
  "total": 1250,
  "positive": 0,     // ❌ Incorrect: Always 0
  "negative": 0,     // ❌ Incorrect: Always 0
  "neutral": 0,      // ❌ Incorrect: Always 0
  "avg_sentiment": 0.234
}
```

**Validation Fails**: `positive + negative + neutral = 0 != total (1250)`

### After Fix (Expected Behavior)

**Solution**: Use separate COUNT queries (CosmosDB compatible)

**Result**:

```json
{
  "total": 1250,
  "positive": 687,   // ✅ Correct: Accurate count
  "negative": 312,   // ✅ Correct: Accurate count
  "neutral": 251,    // ✅ Correct: Accurate count
  "avg_sentiment": 0.234
}
```

**Validation Passes**: `687 + 312 + 251 = 1250 ✅`

---

## Performance Characteristics

**Target**: < 2 seconds response time for 1-week windows

**Implementation**: Parallel query execution with `asyncio.gather()`

**Expected Performance**:

- Before fix: ~1-2 seconds (but returns incorrect data)
- After fix: ~1-2 seconds (accurate data with parallel queries)

---

## Backward Compatibility

**API Contract**: ✅ No breaking changes

- Same endpoint URL
- Same request parameters
- Same response schema
- Same status codes

**Client Impact**: None

- Existing clients continue working without modifications
- Dashboard receives accurate data (fixes display bug)

---

## Testing Contract

### Manual Testing

```bash
# 1. Insert test data with known sentiments
# (Use database admin tool or integration test setup)

# 2. Query API
curl "http://localhost:8000/api/v1/sentiment/stats?hours=24"

# 3. Verify response
# Expected: positive + negative + neutral == total
# Expected: avg_sentiment in range [-1.0, 1.0]
```

### Integration Test Example

```python
async def test_sentiment_stats_accuracy():
    # Insert known test data
    await db.insert_posts([
        {"id": "test1", "sentiment": "positive", "compound_score": 0.8, "_ts": now},
        {"id": "test2", "sentiment": "negative", "compound_score": -0.5, "_ts": now},
        {"id": "test3", "sentiment": "neutral", "compound_score": 0.1, "_ts": now},
    ])
    
    # Call API
    response = await client.get("/api/v1/sentiment/stats?hours=1")
    
    # Verify
    assert response.json() == {
        "total": 3,
        "positive": 1,
        "negative": 1,
        "neutral": 1,
        "avg_sentiment": 0.133  # (0.8 - 0.5 + 0.1) / 3
    }
```

---

## Summary

**Contract Status**: ✅ No changes (internal fix only)

**Key Points**:

- API endpoint URL, parameters, and response schema remain unchanged
- Fix resolves incorrect data (zeros) → accurate sentiment counts
- Error handling improved (fail-fast instead of silent zeros)
- Performance maintained (<2s) with parallel query execution
- Fully backward compatible with existing clients

**Next Step**: Create `quickstart.md` for quick reference
