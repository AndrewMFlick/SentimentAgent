# Quickstart: Fix CosmosDB DateTime Query Format

**Feature**: 004-fix-the-cosmosdb  
**Estimated Time**: 2-3 hours  
**Prerequisites**: Backend running, CosmosDB emulator installed

## Problem Summary

DateTime-filtered queries against CosmosDB PostgreSQL mode fail with HTTP 500 InternalServerError. This fix changes query parameter format from ISO 8601 strings to Unix timestamps while maintaining backward compatibility.

## Quick Fix Steps

### 1. Update Query Parameter Helper (5 min)

Add utility function to `backend/src/services/database.py`:

```python
def _datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp for CosmosDB queries.
    
    CosmosDB PostgreSQL mode has JSON parsing issues with ISO 8601 datetime
    strings. Use Unix timestamps (integers) instead.
    """
    return int(dt.timestamp())
```

### 2. Update `get_recent_posts()` (10 min)

**File**: `backend/src/services/database.py`

**Find**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
query = "SELECT * FROM c WHERE c.collected_at >= @cutoff"
parameters = [{"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}]
```

**Replace with**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
query = "SELECT * FROM c WHERE c._ts >= @cutoff"
parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
```

**Note**: Using `_ts` system field (modification time) as it exists on all documents.

### 3. Update `get_sentiment_stats()` (10 min)

**File**: `backend/src/services/database.py`

**Find**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
query = """..."""
parameters = [{"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}]
```

**Replace with**:
```python
cutoff = datetime.utcnow() - timedelta(hours=hours)
query = """..."""  # Same query, change field to c._ts
parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
```

### 4. Update `cleanup_old_data()` (10 min)

**File**: `backend/src/services/database.py`

**Find**:
```python
cutoff = datetime.utcnow() - timedelta(days=settings.data_retention_days)
cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
query = "SELECT c.id, c.subreddit FROM c WHERE c.collected_at < @cutoff"
parameters = [{"name": "@cutoff", "value": cutoff_str}]
```

**Replace with**:
```python
cutoff = datetime.utcnow() - timedelta(days=settings.data_retention_days)
query = "SELECT c.id, c.subreddit FROM c WHERE c._ts < @cutoff"
parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
```

### 5. Update `load_recent_data()` (15 min)

**File**: `backend/src/services/database.py`

**Find**:
```python
# TODO: Fix datetime query format for CosmosDB PostgreSQL mode
# Temporarily skip data loading until we resolve the datetime format issue
logger.warning("Data loading temporarily disabled - datetime format issue with CosmosDB")
posts_count = 0
comments_count = 0
stats = {"total": 0}
```

**Replace with**:
```python
# Load recent posts
posts = self.get_recent_posts(hours=hours, limit=1000)
posts_count = len(posts)

# Load recent comments count
cutoff = datetime.utcnow() - timedelta(hours=hours)
query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
parameters = [
    {"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}
]

comments_result = list(self.comments_container.query_items(
    query=query,
    parameters=parameters,
    enable_cross_partition_query=True
))
comments_count = comments_result[0] if comments_result else 0

# Load sentiment stats
stats = self.get_sentiment_stats(hours=hours)
```

### 6. Test the Fix (30 min)

**Start backend**:
```bash
cd backend
bash start.sh
```

**Watch logs**:
```bash
tail -f /tmp/backend-startup.log
```

**Expected output**:
```
Data loading complete: 100 posts, 250 comments, 75 sentiment scores loaded in 2.35s
Application startup complete
```

**Test API**:
```bash
curl http://localhost:8000/api/v1/posts?hours=24
```

Should return posts without HTTP 500 errors.

### 7. Add Integration Tests (45 min)

**Create**: `backend/tests/integration/test_datetime_queries.py`

```python
import pytest
from datetime import datetime, timedelta
from src.services.database import db
from src.models import RedditPost

@pytest.fixture
async def setup_test_data():
    """Insert test posts with known timestamps"""
    # Insert posts from 12 hours ago and 48 hours ago
    old_post = RedditPost(
        id="old_post",
        title="Old post",
        subreddit="test",
        created_utc=datetime.utcnow() - timedelta(hours=48),
        collected_at=datetime.utcnow() - timedelta(hours=48),
        # ... other required fields
    )
    recent_post = RedditPost(
        id="recent_post",
        title="Recent post",
        subreddit="test",
        created_utc=datetime.utcnow() - timedelta(hours=12),
        collected_at=datetime.utcnow() - timedelta(hours=12),
        # ... other required fields
    )
    db.save_post(old_post)
    db.save_post(recent_post)
    
    yield
    
    # Cleanup
    db.posts_container.delete_item("old_post", partition_key="test")
    db.posts_container.delete_item("recent_post", partition_key="test")

@pytest.mark.asyncio
async def test_get_recent_posts_datetime_filter(setup_test_data):
    """Verify datetime queries work without InternalServerError"""
    posts = db.get_recent_posts(hours=24)
    
    assert len(posts) >= 1, "Should find recent post"
    assert any(p.id == "recent_post" for p in posts), "Should include recent post"
    assert not any(p.id == "old_post" for p in posts), "Should exclude old post"

@pytest.mark.asyncio
async def test_startup_data_loading():
    """Verify load_recent_data completes without errors"""
    await db.load_recent_data()
    # Should complete without raising exceptions
```

**Run tests**:
```bash
cd backend
pytest tests/integration/test_datetime_queries.py -v
```

## Verification Checklist

- [ ] Backend starts without "Data loading temporarily disabled" warning
- [ ] Startup logs show actual post/comment counts
- [ ] API endpoint `/api/v1/posts?hours=24` returns results (no HTTP 500)
- [ ] Integration tests pass
- [ ] No InternalServerError exceptions in logs
- [ ] Scheduled jobs complete successfully

## Alternative Approaches

### Option A: Use _ts System Field (Implemented Above)

**Pros**: No migration, works immediately  
**Cons**: Uses modification time, not collection time  

### Option B: Add Timestamp Fields

**Modify save methods to add `_ts` fields**:

```python
def save_post(self, post: RedditPost):
    item = post.model_dump()
    # ... existing code ...
    item['collected_at'] = post.collected_at.isoformat()
    item['collected_at_ts'] = int(post.collected_at.timestamp())  # ADD THIS
    # ... rest of save logic
```

**Update queries to use new fields**:
```python
query = "SELECT * FROM c WHERE c.collected_at_ts >= @cutoff"
```

**Pros**: Accurate timestamps, indexable  
**Cons**: Requires migration or backfill  

## Rollback Plan

If this fix causes issues:

1. **Revert database.py changes**:
   ```bash
   git checkout main -- backend/src/services/database.py
   ```

2. **Restart backend**:
   ```bash
   pkill -f uvicorn
   cd backend && bash start.sh
   ```

3. **Data loading will be disabled again**, but backend will start

## Common Issues

### Issue: Tests fail with "Container not found"

**Solution**: Ensure CosmosDB emulator is running:
```bash
# Check if emulator is running
lsof -i :8081

# Start emulator if needed (macOS)
open /Applications/Azure\ Cosmos\ DB\ Emulator.app
```

### Issue: Still getting HTTP 500 on queries

**Solution**: Check query field name:
- Use `c._ts` for system modification time
- Use `c.collected_at_ts` only if field was added
- Verify parameter is integer: `type(cutoff_timestamp)` should be `int`

### Issue: Wrong results returned

**Solution**: Verify timestamp calculation:
```python
# Print timestamp for debugging
cutoff = datetime.utcnow() - timedelta(hours=24)
print(f"Cutoff: {cutoff}")
print(f"Timestamp: {int(cutoff.timestamp())}")
```

## Next Steps

After this fix is working:

1. **Monitor production**: Watch for any datetime query errors
2. **Consider adding timestamp fields**: For better performance and accuracy
3. **Backfill if needed**: Script to add `_ts` fields to existing documents
4. **Update documentation**: Document datetime query patterns

## Time Estimate

- Code changes: 1 hour
- Testing: 1 hour
- Documentation: 30 minutes
- **Total**: 2-3 hours

## Success Criteria

✅ Backend starts and loads data  
✅ All datetime queries succeed  
✅ Integration tests pass  
✅ No HTTP 500 errors in logs  
✅ API endpoints return results
