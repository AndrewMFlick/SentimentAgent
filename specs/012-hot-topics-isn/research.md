# Research: Enhanced Hot Topics with Tool Insights

**Feature**: 012-hot-topics-isn  
**Date**: 2025-10-23

## Research Tasks

### R1: Engagement Score Calculation Formula

**Decision**: Engagement score = (mention_count × 10) + (total_comments × 2) + total_upvotes

**Rationale**:
- **Mention count weighted highest**: Core metric showing how often a tool is discussed
- **Comments weighted medium**: Indicates active discussion (2x multiplier)
- **Upvotes weighted lowest**: Shows agreement but less engagement than comments (1x multiplier)
- **Simple additive formula**: Easy to understand and debug
- **Time-agnostic**: Time filtering handled separately via query constraints, keeps score calculation simple

**Alternatives Considered**:
- **Time-decay formula** (e.g., exponential decay): Rejected - complexity not justified for MVP, time filtering via UI controls sufficient
- **Normalized 0-100 score**: Rejected - absolute values more intuitive, no need for normalization
- **Weighted average with custom weights**: Rejected - fixed formula ensures consistency and predictability

**Implementation**: Backend service method `calculate_engagement_score(tool_id, time_range)` aggregates counts from database.

---

### R2: Timeline Filtering & Engagement Definition

**Decision**: 
- **Engagement = Post created OR comment activity** within time range
- **Query strategy**: Use existing `_ts` field pattern (Unix timestamp) for performance
- **Filter logic**: `(post._ts >= cutoff) OR (EXISTS comment WHERE comment.post_id = post.id AND comment._ts >= cutoff)`

**Rationale**:
- **Inclusive definition**: Post with recent comments is "engaged" even if post itself is old
- **Consistent with spec**: User specified "posts that haven't had engagement in the specific timeline doesn't display"
- **Leverages existing patterns**: Project already uses `_ts` field for datetime queries (see database.py)
- **Performance**: Indexed system field `_ts` enables fast range queries

**Alternatives Considered**:
- **Post timestamp only**: Rejected - misses ongoing discussions on older posts
- **Last comment timestamp field**: Rejected - requires maintaining denormalized field, adds complexity
- **Upvotes as engagement**: Rejected - Reddit API doesn't provide upvote timestamps reliably

**Implementation**: 
- Backend: Two-step query (posts in range + posts with recent comments)
- Use `asyncio.gather()` for parallel execution (existing pattern from sentiment_stats)

---

### R3: Load More Pagination Strategy

**Decision**: **Offset-based pagination** with server-side caching

**Rationale**:
- **CosmosDB limitation**: No native cursor support for SQL API
- **Consistent ordering**: Sort by engagement score (calculated field) makes cursor pagination complex
- **20 items per page**: Small enough offset that OFFSET/LIMIT performance acceptable
- **Session cache**: Backend caches full result set for 5 minutes, subsequent "Load More" uses cached results

**Alternatives Considered**:
- **Continuation token (cursor)**: Rejected - CosmosDB continuation tokens don't work with complex ORDER BY
- **Keyset pagination**: Rejected - engagement score is calculated, not stored, makes keyset unstable
- **No pagination**: Rejected - requirement specifies Load More button

**Implementation**:
- Backend: `GET /api/hot-topics/{tool_id}/posts?offset=0&limit=20`
- Cache key: `hot_topics:{tool_id}:{time_range}:{timestamp}`
- Frontend: Track `offset` state, increment by 20 on "Load More"

---

### R4: CosmosDB Query Performance for Related Posts

**Decision**: 
- **Index strategy**: Composite index on `[detected_tool_ids[], _ts]`
- **Query pattern**: `SELECT * FROM c WHERE ARRAY_CONTAINS(c.detected_tool_ids, @tool_id) AND c._ts >= @cutoff ORDER BY (c.comment_count + c.upvotes) DESC`
- **Engagement sort**: Calculate inline as `(comment_count + upvotes)` since both fields indexed

**Rationale**:
- **ARRAY_CONTAINS**: Efficient for multi-value lookups on indexed array field
- **Existing field**: `detected_tool_ids` already populated (feature 004)
- **Inline calculation**: Avoids stored computed field, keeps data model simple
- **Index coverage**: Query uses only indexed fields for filtering and sorting

**Alternatives Considered**:
- **Separate engagement_score field**: Rejected - adds storage overhead, requires denormalization updates
- **Client-side sorting**: Rejected - doesn't scale, negates offset pagination
- **Separate table for tool mentions**: Rejected - over-engineering for current scale

**Implementation**:
- Add composite index to `reddit_posts` container in CosmosDB
- Monitor with existing `monitor_query_performance` decorator (feature 011)
- Baseline: <2s for top 100 posts (success criteria SC-005)

---

### R5: Frontend State Management for Load More

**Decision**: **React Query with infinite queries** pattern

**Rationale**:
- **Already in use**: Project uses React Query (`@tanstack/react-query`)
- **Built-in support**: `useInfiniteQuery` hook handles Load More pattern
- **Automatic cache invalidation**: When time range changes, query key changes, triggers refetch
- **Optimistic updates**: React Query provides built-in optimistic update support

**Alternatives Considered**:
- **Manual state management**: Rejected - reinventing React Query features
- **Redux**: Rejected - not currently used in project, adds complexity
- **SWR**: Rejected - switching libraries not justified

**Implementation**:
```typescript
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['related-posts', toolId, timeRange],
  queryFn: ({ pageParam = 0 }) => api.getRelatedPosts(toolId, timeRange, pageParam),
  getNextPageParam: (lastPage, pages) => 
    lastPage.length === 20 ? pages.length * 20 : undefined,
});
```

**Best Practices**:
- Debounce time range filter changes (300ms) to avoid excessive queries
- Show loading skeleton during initial fetch
- Show spinner on "Load More" button during pagination fetch
- Disable "Load More" when `hasNextPage === false`

---

## Technology Stack Summary

**Backend (Python 3.13.3)**:
- FastAPI 0.109.2 - API endpoints
- Azure Cosmos SDK 4.5.1 - Database queries
- Pydantic 2.x - Data validation
- structlog 24.1.0 - Logging

**Frontend (TypeScript 5.3.3)**:
- React 18.2.0 - UI framework
- TailwindCSS 3.4+ - Styling (glass morphism)
- React Query - Data fetching & caching
- Vite 5.1.0 - Build tool

**Database**:
- Azure CosmosDB (SQL API)
- Existing containers: `reddit_posts`, `reddit_comments`, `sentiment_scores`, `Tools`
- Query pattern: `_ts` field for time range filtering (Unix timestamp)

**Performance Targets**:
- Hot Topics page load: <5 seconds (SC-001)
- Time range filter change: <2 seconds (SC-005)
- Related posts query: <2 seconds for 20 posts
- Load More pagination: <1 second for subsequent pages (cached)

---

## Dependencies Confirmed

✅ **Tool Detection**: `detected_tool_ids` field populated (feature 004)  
✅ **Sentiment Analysis**: `sentiment_scores` container with tool associations  
✅ **Database Service**: `database.py` with `_ts` query patterns  
✅ **Frontend Components**: Glass UI components (Dashboard, TimeRangeFilter exist)  
✅ **React Query**: Already configured in frontend  

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Slow queries on large datasets | User experience degraded | Composite indexes, caching, monitoring with existing decorator |
| Cache invalidation bugs | Stale data shown | React Query automatic invalidation, 5-minute TTL for safety |
| Comment count denormalization lag | Engagement scores slightly off | Acceptable for MVP, comment counts updated on collection cycle (30 min) |
| Reddit API rate limits | Missing post links | Links stored at collection time, no real-time API calls needed |

---

## Open Questions (None)

All clarifications resolved during specification phase:
- ✅ Sort order: Engagement (most comments/upvotes first)
- ✅ Timeline filtering: Exclude posts without engagement in range
- ✅ Pagination: Load More button (20 per page)
