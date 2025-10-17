# Database Service Contract Changes

**Feature**: 004-fix-the-cosmosdb  
**Date**: 2025-10-17  
**Scope**: Internal contract changes to database service methods

## Overview

This document describes the internal contract changes to the `DatabaseService` class in `backend/src/services/database.py`. These are implementation changes that fix datetime query compatibility while maintaining the same public API signatures.

## Modified Methods

### 1. `get_recent_posts()`

**Signature** (unchanged):
```python
def get_recent_posts(
    self, 
    subreddit: Optional[str] = None, 
    hours: int = 24, 
    limit: int = 100
) -> List[RedditPost]
```

**Contract Changes**:
- **Query Parameter Format**: Changed from ISO 8601 string to Unix timestamp integer
- **Behavior**: Same - returns posts from the last N hours
- **Error Handling**: Should no longer throw InternalServerError on datetime filters

**Before**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
parameters = [{"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}]
# FAILS with HTTP 500
```

**After**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
cutoff_ts = int(cutoff.timestamp())
parameters = [{"name": "@cutoff", "value": cutoff_ts}]
# SUCCEEDS
```

### 2. `get_sentiment_stats()`

**Signature** (unchanged):
```python
def get_sentiment_stats(
    self, 
    subreddit: Optional[str] = None, 
    hours: int = 24
) -> Dict[str, Any]
```

**Contract Changes**:
- **Query Parameter Format**: Changed from ISO 8601 string to Unix timestamp integer
- **Behavior**: Same - returns aggregated sentiment statistics
- **Error Handling**: Should no longer throw InternalServerError on datetime filters

### 3. `cleanup_old_data()`

**Signature** (unchanged):
```python
def cleanup_old_data(self) -> None
```

**Contract Changes**:
- **Query Parameter Format**: Changed from ISO 8601 string to Unix timestamp integer
- **Behavior**: Same - deletes data older than retention period
- **Error Handling**: Should no longer throw InternalServerError on datetime filters

### 4. `load_recent_data()`

**Signature** (unchanged):
```python
async def load_recent_data(self) -> None
```

**Contract Changes**:
- **Query Parameter Format**: Changed from ISO 8601 string to Unix timestamp integer
- **Behavior**: Changed - now actually loads data instead of skipping with warning
- **Error Handling**: Should no longer throw InternalServerError on datetime filters
- **Logging**: Changed from "Data loading temporarily disabled" to actual counts

**Before**:
```python
# Temporarily disabled with warning
logger.warning("Data loading temporarily disabled - datetime format issue with CosmosDB")
posts_count = 0
comments_count = 0
```

**After**:
```python
# Actually queries and loads data
posts = self.get_recent_posts(hours=hours, limit=1000)
posts_count = len(posts)
# ... continues with actual data loading
```

## Storage Method Changes

### `save_post()`, `save_comment()`, `save_sentiment()`, `save_trending_topic()`

**Contract Changes** (Optional - Phase 1):
- **Add**: Unix timestamp fields alongside ISO 8601 fields
- **Behavior**: Same external behavior
- **Fields Added** (for each datetime field):
  - `created_utc_ts: int` - Unix timestamp version of `created_utc`
  - `collected_at_ts: int` - Unix timestamp version of `collected_at`
  - `analyzed_at_ts: int` - Unix timestamp version of `analyzed_at`
  - `peak_time_ts: int` - Unix timestamp version of `peak_time`

**Example for `save_post()`**:
```python
# Before (unchanged for backward compatibility)
item['created_utc'] = post.created_utc.isoformat()
item['collected_at'] = post.collected_at.isoformat()

# After (additive)
item['created_utc'] = post.created_utc.isoformat()  # Keep
item['created_utc_ts'] = int(post.created_utc.timestamp())  # Add
item['collected_at'] = post.collected_at.isoformat()  # Keep
item['collected_at_ts'] = int(post.collected_at.timestamp())  # Add
```

## Query Changes

### Query String Modifications

All datetime-filtered queries will be updated to use numeric comparison:

**Option A: Using added timestamp fields** (Recommended):
```sql
-- Before
SELECT * FROM c WHERE c.collected_at >= @cutoff

-- After
SELECT * FROM c WHERE c.collected_at_ts >= @cutoff
```

**Option B: Using _ts system field** (Alternative):
```sql
-- Use system modification timestamp
SELECT * FROM c WHERE c._ts >= @cutoff
```

**Option C: Using string comparison** (Fallback):
```sql
-- Cosmos DB allows string comparison for ISO 8601 dates
SELECT * FROM c WHERE c.collected_at >= @cutoff_str
-- But parameter still needs special handling
```

## Backward Compatibility

### Document Structure

**Old documents** (before this fix):
```json
{
  "id": "abc123",
  "created_utc": "2025-10-17T14:53:28.639801Z",
  "collected_at": "2025-10-17T14:53:28.639801Z"
}
```

**New documents** (after this fix):
```json
{
  "id": "abc123",
  "created_utc": "2025-10-17T14:53:28.639801Z",
  "created_utc_ts": 1729177108,
  "collected_at": "2025-10-17T14:53:28.639801Z",
  "collected_at_ts": 1729177108
}
```

### Query Compatibility

**Handling mixed documents**:
```python
# Query checks for timestamp field, falls back to _ts system field
query = """
    SELECT * FROM c 
    WHERE (IS_DEFINED(c.collected_at_ts) 
           ? c.collected_at_ts 
           : c._ts) >= @cutoff
"""
```

Or simpler approach - just query using `_ts` for old documents:
```python
# Use _ts which exists on all documents
query = "SELECT * FROM c WHERE c._ts >= @cutoff"
```

## API Contract (No Changes)

All public API endpoints remain unchanged:

### GET `/api/v1/posts`
- Query parameters: Same
- Response format: Same
- Behavior: Same (but now works without errors)

### GET `/api/v1/sentiment/stats`
- Query parameters: Same
- Response format: Same
- Behavior: Same (but now works without errors)

### Background Jobs
- Scheduler: Same triggers
- Job signatures: Same
- Behavior: Same (but now works without errors)

## Testing Contracts

### Integration Tests Required

```python
# tests/integration/test_datetime_queries.py

def test_get_recent_posts_with_datetime_filter():
    """Verify posts query works with Unix timestamp parameters"""
    # Arrange: Insert posts with known timestamps
    # Act: Query for recent posts
    # Assert: No InternalServerError, correct results returned

def test_query_mixed_document_formats():
    """Verify queries work with both old and new document formats"""
    # Arrange: Insert old-format and new-format documents
    # Act: Query with datetime filter
    # Assert: Both formats returned in results

def test_backward_compatibility():
    """Verify existing API behavior unchanged"""
    # Arrange: Use existing API client
    # Act: Call API endpoints with time filters
    # Assert: Same response format as before fix
```

## Error Handling

### Before Fix
```python
try:
    posts = db.get_recent_posts(hours=24)
except exceptions.CosmosHttpResponseError as e:
    # HTTP 500: InternalServerError
    # Message: '/' is invalid after a value
    logger.error(f"Query failed: {e}")
    return []
```

### After Fix
```python
try:
    posts = db.get_recent_posts(hours=24)
    # Should succeed now
except exceptions.CosmosHttpResponseError as e:
    # Should not occur for datetime format issues
    logger.error(f"Unexpected query failure: {e}")
    raise
```

## Migration Path

### Phase 1: Fix Query Parameters (This PR)
- Update query parameter format to Unix timestamps
- Keep ISO 8601 storage format
- Use `_ts` system field for queries if needed
- No migration required

### Phase 2: Add Timestamp Fields (Optional Future PR)
- Add `_ts` suffix fields to save methods
- Backfill existing documents lazily
- Update queries to use new fields

### Phase 3: Optimize (Optional Future PR)
- Add indexes on timestamp fields
- Remove ISO format from queries (keep in documents)
- Performance testing

## Summary

| Contract | Change Type | Breaking? | Migration Required? |
|----------|-------------|-----------|---------------------|
| Query parameters | Implementation detail | No | No |
| Storage format | Additive (optional) | No | No |
| API endpoints | None | No | No |
| Method signatures | None | No | No |
| Error behavior | Fixed (improvement) | No | No |
| Test contracts | New tests added | No | No |
