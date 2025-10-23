# Quickstart: Enhanced Hot Topics Feature

**Feature**: 012-hot-topics-isn  
**Prerequisites**: Backend and frontend running, tools registered, sentiment data collected

## Development Setup

### 1. Backend Changes

**No new dependencies required** - uses existing FastAPI, CosmosDB, and React Query.

**Add composite indexes to CosmosDB**:

```bash
# Via Azure CLI (if using cloud CosmosDB)
az cosmosdb sql container update \
  --account-name <your-account> \
  --database-name sentiment_analysis \
  --name sentiment_scores \
  --idx @index-policy.json

# index-policy.json:
{
  "compositeIndexes": [
    [
      {"path": "/detected_tool_ids/*", "order": "ascending"},
      {"path": "/_ts", "order": "descending"}
    ]
  ]
}
```

**For local emulator**: Indexes auto-created by first query (may be slow initially).

### 2. Start Services

```bash
# Terminal 1: Backend
cd backend
./start.sh

# Terminal 2: Frontend  
cd frontend
npm run dev
```

### 3. Verify Data Availability

```bash
# Check if tools have detected_tool_ids
curl http://localhost:8000/api/tools | jq '.[0].detected_tool_ids'

# Check sentiment data exists
curl http://localhost:8000/api/sentiment/stats | jq
```

**Expected**: Tools should have non-empty `detected_tool_ids`, sentiment stats should show counts > 0.

### 4. Access Hot Topics

Navigate to: `http://localhost:5173/hot-topics`

**Expected UI**:
- Ranked list of tools with engagement scores
- Time range filter (24h, 7d, 30d)
- Click tool → view related posts
- Click post → opens Reddit in new tab
- "Load More" button for pagination

---

## API Usage Examples

### Get Hot Topics

```bash
# Default (7 days)
curl http://localhost:8000/api/hot-topics

# Last 24 hours, top 5 tools
curl "http://localhost:8000/api/hot-topics?time_range=24h&limit=5"
```

**Response**:
```json
{
  "hot_topics": [
    {
      "tool_id": "copilot-001",
      "tool_name": "GitHub Copilot",
      "tool_slug": "github-copilot",
      "engagement_score": 1250,
      "total_mentions": 45,
      "total_comments": 230,
      "total_upvotes": 560,
      "sentiment_distribution": {
        "positive_count": 30,
        "negative_count": 5,
        "neutral_count": 10,
        "positive_percent": 66.7,
        "negative_percent": 11.1,
        "neutral_percent": 22.2
      }
    }
  ],
  "generated_at": "2025-10-23T10:30:00Z",
  "time_range": "7d"
}
```

### Get Related Posts

```bash
# First page (20 posts)
curl "http://localhost:8000/api/hot-topics/copilot-001/posts?time_range=7d"

# Load more (next 20)
curl "http://localhost:8000/api/hot-topics/copilot-001/posts?time_range=7d&offset=20&limit=20"
```

**Response**:
```json
{
  "posts": [
    {
      "post_id": "1a2b3c",
      "title": "GitHub Copilot vs Amazon CodeWhisperer",
      "excerpt": "I've been using both Copilot and CodeWhisperer...",
      "author": "developer_user",
      "subreddit": "programming",
      "created_utc": "2025-10-20T14:30:00Z",
      "reddit_url": "https://reddit.com/r/programming/comments/1a2b3c",
      "comment_count": 45,
      "upvotes": 120,
      "sentiment": "positive",
      "engagement_score": 165
    }
  ],
  "total": 87,
  "has_more": true,
  "offset": 0,
  "limit": 20
}
```

---

## Testing Checklist

### Backend Tests

```bash
cd backend

# Unit tests for hot topics service
pytest tests/unit/test_hot_topics_service.py -v

# Integration tests (requires CosmosDB)
pytest tests/integration/test_hot_topics_api.py -v

# Performance test (engagement calculation < 5s)
pytest tests/integration/test_hot_topics_performance.py -v
```

### Frontend Tests

```bash
cd frontend

# Component tests
npm test -- HotTopicsPage
npm test -- RelatedPostsList

# E2E test (requires backend running)
npm run test:e2e -- hot-topics.spec.ts
```

### Manual Testing

**User Story 1 - Dashboard**:
- [ ] Navigate to `/hot-topics`
- [ ] Verify top 10 tools displayed
- [ ] Verify engagement scores visible
- [ ] Verify sentiment percentages displayed
- [ ] Verify sentiment color-coded (green/red/gray)

**User Story 2 - Related Posts**:
- [ ] Click on a hot topic
- [ ] Verify 20 related posts shown
- [ ] Verify each post has title, excerpt, author, subreddit, timestamp
- [ ] Click "Load More", verify next 20 posts load
- [ ] Click Reddit link, verify opens in new tab

**User Story 3 - Filters**:
- [ ] Change time range to "24h", verify results update
- [ ] Change to "30d", verify results update
- [ ] Verify filter change takes <2 seconds

**Edge Cases**:
- [ ] Tool with 0 mentions shows "Not enough data"
- [ ] Tool with <3 mentions excluded from hot topics
- [ ] "Load More" hidden when all posts loaded
- [ ] Graceful error if Reddit link broken

---

## Performance Benchmarks

**Target Performance** (from Success Criteria):

| Operation | Target | Test Command |
|-----------|--------|--------------|
| Hot topics page load | <5s | `time curl http://localhost:8000/api/hot-topics` |
| Time range filter change | <2s | Monitor network tab in DevTools |
| Related posts query | <2s | `time curl "http://localhost:8000/api/hot-topics/copilot-001/posts"` |
| Load More pagination | <1s | Monitor subsequent "Load More" clicks |

**Monitoring**:
- Backend logs show slow queries >3s (existing `monitor_query_performance` decorator)
- Frontend React Query DevTools show query times

---

## Troubleshooting

### No tools appear in hot topics

**Cause**: Tools don't have sentiment data with `detected_tool_ids`

**Fix**:
```bash
# Verify tool detection is working
curl http://localhost:8000/api/sentiment/recent | jq '.[0].detected_tool_ids'

# If empty, re-run sentiment analysis
curl -X POST http://localhost:8000/api/admin/reanalyze
```

### Slow queries (>5 seconds)

**Cause**: Missing composite indexes

**Fix**:
```bash
# Check backend logs for "Slow query detected"
tail -f backend/logs/app.log | grep "Slow query"

# Add indexes via Azure Portal:
# 1. Navigate to CosmosDB account
# 2. Data Explorer → sentiment_scores → Settings → Indexing Policy
# 3. Add composite index: [detected_tool_ids[], _ts]
```

### "Load More" not appearing

**Cause**: Less than 20 posts returned, or `has_more: false`

**Verify**:
```bash
# Check total count
curl "http://localhost:8000/api/hot-topics/copilot-001/posts" | jq '.total'

# If total < 20, this is expected (no more pages)
```

### Stale data after time range change

**Cause**: Frontend cache not invalidated

**Fix**: React Query automatically invalidates on query key change. If persisting:
```typescript
// In RelatedPostsList component, verify queryKey includes timeRange:
queryKey: ['related-posts', toolId, timeRange]  // ✅ Correct
queryKey: ['related-posts', toolId]             // ❌ Wrong - won't invalidate
```

---

## Deployment Notes

### Production Checklist

- [ ] Composite indexes created in production CosmosDB
- [ ] Cache TTL configured (default: 5 minutes in `hot_topics_service.py`)
- [ ] Rate limiting enabled for hot topics endpoints (if using API gateway)
- [ ] CORS origins updated to include production frontend URL
- [ ] Monitoring alerts configured for slow queries (>5s)
- [ ] Verify Reddit links work from production domain (no CORS issues)

### Environment Variables

No new environment variables required - uses existing CosmosDB config.

**Optional tuning**:
```env
# .env (backend)
HOT_TOPICS_CACHE_TTL_SECONDS=300           # Default: 300 (5 minutes)
HOT_TOPICS_MIN_MENTIONS_THRESHOLD=3        # Default: 3
HOT_TOPICS_MAX_LIMIT=50                    # Default: 50
```

---

## Next Steps

After feature is working:

1. **Monitor performance**: Track query times via backend logs
2. **Gather user feedback**: Understand which time ranges most used
3. **Optimize indexes**: Add additional indexes if specific queries slow
4. **Consider caching strategy**: Evaluate Redis for multi-instance deployments

**Phase 2 enhancements** (out of scope for MVP):
- Real-time updates via WebSocket
- User-specific filters (saved preferences)
- Export hot topics to CSV
- Historical trending charts
