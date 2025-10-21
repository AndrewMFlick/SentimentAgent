# Phase 0: Research & Technical Decisions

**Feature**: AI Tools Sentiment Analysis Dashboard
**Date**: 2025-10-20
**Status**: Completed

## Research Questions

### 1. Tool Mention Detection Strategy

**Question**: How should the system detect and extract AI tool mentions from Reddit posts?

**Decision**: Keyword-based pattern matching with fuzzy matching for common variations

**Rationale**:

- Reddit posts are informal with varied spelling ("copilot", "co-pilot", "GitHub Copilot", "GH Copilot")
- NLP/NER solutions (spaCy, Hugging Face NER) are overkill for well-known tool names
- Keyword matching is fast, predictable, and sufficient for 90% accuracy requirement (SC-004)
- Can expand to NER later if accuracy drops below threshold

**Implementation Approach**:

- Define tool aliases/patterns in database (e.g., Copilot → ["copilot", "co-pilot", "github copilot", "gh copilot"])
- Case-insensitive regex matching with word boundaries
- Score matches by confidence (exact match = 1.0, variation = 0.8-0.9)
- Filter matches below confidence threshold to reduce false positives

**Alternatives Considered**:

- **NER (spaCy/Hugging Face)**: Rejected - too slow for real-time detection, requires training data
- **LLM-based extraction**: Rejected - expensive API calls, latency issues, unnecessary for known tool names
- **Exact string matching only**: Rejected - misses common variations, too rigid

---

### 2. Time Series Data Aggregation

**Question**: How should we aggregate sentiment data over time for efficient time series queries?

**Decision**: Pre-computed daily aggregates stored in dedicated Time Period Aggregate table

**Rationale**:

- Raw sentiment records can reach 10,000+ per tool across 90 days
- Computing aggregates on-the-fly for every dashboard load violates SC-001 (< 2s load time)
- Daily granularity sufficient per spec requirement (SC-003)
- Follows established CosmosDB query optimization pattern from Feature 005

**Implementation Approach**:

- Background job runs daily (via APScheduler) to compute aggregates
- For each tool + date: calculate total mentions, positive/negative/neutral counts, avg sentiment
- Store in `time_period_aggregates` container with compound key (tool_id + date)
- Dashboard queries only aggregates table, not raw sentiment_scores
- Incremental updates: recompute only last 2 days to handle late-arriving data

**Alternatives Considered**:

- **On-the-fly aggregation**: Rejected - too slow (>3s for 90-day queries), violates SC-007
- **Hourly granularity**: Rejected - increases storage 24x, daily sufficient for trends
- **Materialized views**: Rejected - CosmosDB PostgreSQL mode doesn't support materialized views

---

### 3. Chart Library Selection

**Question**: Which charting library should be used for time series visualization in React?

**Decision**: Recharts

**Rationale**:

- Built for React (not a wrapper around D3)
- Responsive by default (mobile + desktop requirement)
- Simple API for common chart types (line, bar, area)
- Supports interactive tooltips and drill-down (FR-008 requirement)
- Smaller bundle size than Chart.js (better performance)
- TypeScript support built-in

**Implementation Approach**:

- Use `<LineChart>` for time series sentiment trends
- Use `<BarChart>` with grouped bars for tool comparison
- Use `<ResponsiveContainer>` for mobile responsiveness
- Custom tooltip component for detailed time period stats (US3, Scenario 4)

**Alternatives Considered**:

- **Chart.js**: Rejected - not React-native, requires react-chartjs-2 wrapper
- **D3.js**: Rejected - too low-level, longer development time, steeper learning curve
- **Nivo**: Rejected - larger bundle size, less active community than Recharts
- **Victory**: Rejected - performance issues with large datasets (90 days × 5 tools)

---

### 4. Real-Time Dashboard Updates

**Question**: How should the dashboard refresh when new sentiment data is available?

**Decision**: WebSocket-free polling with smart update detection

**Rationale**:

- SC-008 allows 10-minute update latency - WebSockets unnecessary
- Polling every 60 seconds is simple and sufficient
- Use HTTP ETag/Last-Modified headers to avoid unnecessary re-renders
- Frontend checks `/api/v1/tools/last_updated` endpoint

**Implementation Approach**:

- Backend exposes `/api/v1/tools/last_updated` returning max(analyzed_at) across all tools
- Frontend polls every 60s, compares timestamp to cached value
- If timestamp newer: fetch fresh tool sentiment data
- If unchanged: skip fetch, reducing server load
- Use React Query or SWR for automatic polling + caching

**Alternatives Considered**:

- **WebSockets (Socket.io)**: Rejected - overkill for 10-minute latency requirement, adds complexity
- **Server-Sent Events (SSE)**: Rejected - same complexity as WebSockets, not needed
- **Manual refresh button only**: Rejected - violates FR-011 (automatic updates required)
- **Aggressive polling (5s)**: Rejected - unnecessary server load, data doesn't change that fast

---

### 5. Admin Approval Workflow

**Question**: How should the admin approval workflow be implemented for auto-detected tools?

**Decision**: Simple queue-based workflow with approval/reject actions

**Rationale**:

- Hybrid approach (FR-012) requires human-in-the-loop for quality control
- Admin interface should be simple: list pending tools, approve/reject buttons
- Queue prevents duplicate submissions (same tool detected multiple times)
- Email notifications not required initially (can add later based on admin feedback)

**Implementation Approach**:

- `ai_tools` table has `status` field: "pending", "approved", "rejected"
- Auto-detection creates tool with status="pending" when threshold reached (50+ mentions/7d)
- Admin endpoint: `POST /api/v1/admin/tools/{tool_id}/approve` sets status="approved"
- Admin endpoint: `POST /api/v1/admin/tools/{tool_id}/reject` sets status="rejected"
- Dashboard only shows approved tools
- Admin UI component: React table with approve/reject buttons

**Alternatives Considered**:

- **Full workflow engine (Temporal, Airflow)**: Rejected - massive overkill for simple approve/reject
- **Multi-stage approval**: Rejected - one approver sufficient for MVP
- **Automatic approval after X days**: Rejected - spec requires explicit admin approval

---

### 6. Data Retention Implementation

**Question**: How should 90-day rolling retention be implemented and made extensible?

**Decision**: Configurable retention via environment variable + scheduled cleanup job

**Rationale**:

- 90-day retention is initial requirement, but spec allows future extension (FR-013)
- Environment variable makes it easy to adjust without code changes
- Scheduled job pattern already established in project (APScheduler)
- Soft delete initially (add `deleted_at` field) for easier recovery

**Implementation Approach**:

- Add `SENTIMENT_RETENTION_DAYS=90` to config
- Nightly cleanup job: flag records older than retention period with `deleted_at`
- Queries filter `WHERE deleted_at IS NULL`
- After 30 days, hard delete flagged records (gives recovery window)
- Admin can adjust retention period via config for future scaling

**Alternatives Considered**:

- **Hard delete immediately**: Rejected - no recovery option if misconfigured
- **Archive to cold storage**: Rejected - not needed for MVP, can add later
- **No cleanup (indefinite retention)**: Rejected - violates FR-013 requirement
- **Fixed 90-day hardcoded**: Rejected - spec requires extensibility

---

## Best Practices Applied

### CosmosDB PostgreSQL Mode

- **Parallel query execution**: Use `asyncio.gather()` for multiple queries (established in Feature 005)
- **Avoid complex aggregations**: Pre-compute aggregates instead of on-the-fly (Feature 005 pattern)
- **Use `_ts` field for time queries**: Unix timestamps avoid datetime parsing issues (Feature 004 pattern)

### FastAPI Patterns

- **Async endpoints**: All database operations use `async def` for non-blocking I/O
- **Pydantic models**: Request/response validation with clear error messages
- **Structured logging**: Use `structlog` for all operations with execution time tracking
- **Error handling**: Fail-fast on startup, catch-log-continue in background jobs

### React Best Practices

- **Component composition**: Break down dashboard into small, testable components (Card, Chart, Filter)
- **Custom hooks**: Create `useToolSentiment()`, `useTimeSeriesData()` for data fetching logic
- **Loading states**: Show skeletons/spinners during data fetch (don't leave users waiting)
- **Error boundaries**: Catch component errors gracefully, show fallback UI

### Testing Strategy

- **Test-first**: Write tests before implementation (constitution requirement)
- **Integration tests**: Test API contracts and database queries end-to-end
- **Component tests**: Test React components with React Testing Library (user-centric)
- **Performance tests**: Verify SC-001, SC-007 requirements (< 2s load, < 3s time series)

---

## Integration Points

### Existing Services to Leverage

1. **Reddit Collector** (`backend/src/services/reddit_collector.py`)
   - Already collecting posts from target subreddits
   - Add tool detection post-processing step after collection

2. **Sentiment Analyzer** (`backend/src/services/sentiment_analyzer.py`)
   - Already computing sentiment scores for posts
   - No changes needed, consume existing sentiment_scores data

3. **Database Service** (`backend/src/services/database.py`)
   - Extend with tool-specific queries
   - Follow existing retry/logging patterns

4. **Scheduler** (`backend/src/services/scheduler.py`)
   - Add new jobs: daily aggregation, auto-detection check, cleanup
   - Use existing APScheduler infrastructure

### New Dependencies Required

- **Frontend**: `recharts` (chart library), `react-query` or `swr` (data fetching)
- **Backend**: No new dependencies (use existing FastAPI, Azure Cosmos SDK, APScheduler)

---

## Security & Privacy Considerations

- **Admin endpoints**: Require authentication (add auth middleware)
- **Rate limiting**: Apply to comparison/time series queries to prevent abuse
- **Input validation**: Sanitize tool names in admin approval to prevent injection
- **No PII exposure**: Tool sentiment is aggregate data, no user-identifiable information

---

## Summary

All technical unknowns resolved. Implementation can proceed to Phase 1 (Data Model & Contracts) with:

- Clear tool detection strategy (keyword-based with fuzzy matching)
- Efficient time series architecture (pre-computed daily aggregates)
- Appropriate chart library (Recharts)
- Simple real-time updates (60s polling with change detection)
- Straightforward admin workflow (queue + approve/reject)
- Extensible retention system (config-driven with soft delete)
