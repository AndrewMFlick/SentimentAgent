# Event Specifications: AI Tools Sentiment Analysis

**Feature**: 008-dashboard-ui-with
**Date**: 2025-10-20

## Background Jobs & Events

This document specifies the asynchronous events and background jobs for the AI tools sentiment tracking feature.

---

## 1. Daily Aggregation Event

**Trigger**: Scheduled (Cron)
**Frequency**: Daily at 00:05 UTC
**Job ID**: `daily_sentiment_aggregation`

**Purpose**: Compute time period aggregates for all approved tools to enable fast dashboard queries.

**Event Flow**:

```text
Scheduler (00:05 UTC)
    │
    ├──▶ Get all approved tools
    │
    ├──▶ For each tool:
    │    ├── Query tool_mentions for yesterday
    │    ├── Join with sentiment_scores
    │    ├── Calculate aggregates:
    │    │   - total_mentions
    │    │   - positive_count (sentiment = "positive")
    │    │   - negative_count (sentiment = "negative")
    │    │   - neutral_count (sentiment = "neutral")
    │    │   - avg_sentiment (AVG(compound_score))
    │    └── Upsert to time_period_aggregates
    │
    └──▶ Log completion (execution time, records processed)
```

**Data Dependencies**:

- Input: `tool_mentions`, `sentiment_scores` (yesterday's data)
- Output: `time_period_aggregates` (new/updated records)

**Error Handling**:

- Catch-log-continue pattern: If one tool fails, continue with others
- Retry failed tools with exponential backoff (max 3 attempts)
- Alert admin if > 20% of tools fail

**Performance Target**: Complete within 5 minutes for 10 tools

---

## 2. Tool Auto-Detection Event

**Trigger**: Scheduled (Cron)
**Frequency**: Hourly
**Job ID**: `tool_auto_detection`

**Purpose**: Scan recent sentiment data for frequently mentioned tools not yet tracked, create pending records for admin approval.

**Event Flow**:

```text
Scheduler (hourly)
    │
    ├──▶ Get all approved tool aliases (for exclusion)
    │
    ├──▶ Query sentiment_scores (last 7 days)
    │    - Extract potential tool names via regex patterns
    │    - Count mentions per potential tool
    │    - Filter: mentions >= TOOL_DETECTION_THRESHOLD (50)
    │
    ├──▶ For each detected tool:
    │    - Check if already exists (any status)
    │    - If new:
    │    │   ├── Create AITool record (status="pending")
    │    │   ├── Store sample mentions (top 5 by confidence)
    │    │   └── Emit ToolDetected event
    │    - If exists with status="rejected":
    │    │   └── Skip (admin previously rejected)
    │
    └──▶ Log detection results (new tools found, samples)
```

**Data Dependencies**:

- Input: `sentiment_scores` (last 7 days), `ai_tools` (existing tools)
- Output: `ai_tools` (new pending records)

**Event Emitted**: `ToolDetected`

```json
{
  "event_type": "ToolDetected",
  "timestamp": "2025-10-20T14:30:00Z",
  "data": {
    "tool_id": "uuid",
    "tool_name": "NewAITool",
    "mention_count": 73,
    "detection_window_days": 7,
    "sample_mentions": [
      {
        "content_id": "abc123",
        "subreddit": "programming",
        "excerpt": "Just tried NewAITool and it's amazing!",
        "confidence": 0.92
      }
    ]
  }
}
```

**Error Handling**:

- Log errors but don't crash (detection is non-critical)
- Skip records with parsing errors
- Rate limit: Max 10 new pending tools per run (prevent spam)

---

## 3. Tool Approval Event

**Trigger**: Admin Action (API call)
**Endpoint**: `POST /api/v1/admin/tools/{tool_id}/approve`

**Purpose**: Admin approves auto-detected tool, making it visible in dashboard.

**Event Flow**:

```text
Admin POST /approve
    │
    ├──▶ Validate: tool exists, status="pending"
    │
    ├──▶ Update AITool:
    │    - status = "approved"
    │    - approved_by = admin_user_id
    │    - approved_at = current_timestamp
    │
    ├──▶ Backfill historical data:
    │    - Scan sentiment_scores (last 90 days)
    │    - Create tool_mentions for this tool
    │    - Trigger aggregation job for all 90 days
    │
    ├──▶ Emit ToolApproved event
    │
    └──▶ Return success response
```

**Event Emitted**: `ToolApproved`

```json
{
  "event_type": "ToolApproved",
  "timestamp": "2025-10-20T15:45:00Z",
  "data": {
    "tool_id": "uuid",
    "tool_name": "NewAITool",
    "approved_by": "admin@sentimentagent.com",
    "backfill_status": "in_progress",
    "estimated_completion": "2025-10-20T15:50:00Z"
  }
}
```

**Side Effects**:

- Tool appears in `/api/v1/tools` list
- Dashboard polls detect new tool (via `last_updated` endpoint)
- Historical data backfill runs asynchronously

---

## 4. Tool Rejection Event

**Trigger**: Admin Action (API call)
**Endpoint**: `POST /api/v1/admin/tools/{tool_id}/reject`

**Purpose**: Admin rejects auto-detected tool (false positive or out of scope).

**Event Flow**:

```text
Admin POST /reject
    │
    ├──▶ Validate: tool exists, status="pending"
    │
    ├──▶ Update AITool:
    │    - status = "rejected"
    │    - rejected_by = admin_user_id
    │    - rejected_at = current_timestamp
    │    - rejection_reason = request.body.reason
    │
    ├──▶ Emit ToolRejected event
    │
    └──▶ Return success response
```

**Event Emitted**: `ToolRejected`

```json
{
  "event_type": "ToolRejected",
  "timestamp": "2025-10-20T16:10:00Z",
  "data": {
    "tool_id": "uuid",
    "tool_name": "FalsePositive",
    "rejected_by": "admin@sentimentagent.com",
    "reason": "Not an AI tool - generic term"
  }
}
```

**Side Effects**:

- Tool never appears in dashboard
- Auto-detection skips this tool in future runs
- No historical data processing

---

## 5. Data Retention Cleanup Event

**Trigger**: Scheduled (Cron)
**Frequency**: Daily at 02:00 UTC
**Job ID**: `sentiment_data_cleanup`

**Purpose**: Enforce data retention policy by soft-deleting old aggregates.

**Event Flow**:

```text
Scheduler (02:00 UTC)
    │
    ├──▶ Calculate cutoff_date:
    │    cutoff = today - SENTIMENT_RETENTION_DAYS
    │
    ├──▶ Soft delete time_period_aggregates:
    │    UPDATE time_period_aggregates
    │    SET deleted_at = NOW()
    │    WHERE date < cutoff_date
    │      AND deleted_at IS NULL
    │
    ├──▶ Hard delete old soft-deleted records:
    │    DELETE FROM time_period_aggregates
    │    WHERE deleted_at < (NOW() - INTERVAL '30 days')
    │
    ├──▶ Log cleanup stats:
    │    - Records soft-deleted
    │    - Records hard-deleted
    │    - Storage freed
    │
    └──▶ Emit DataRetentionCleanup event
```

**Event Emitted**: `DataRetentionCleanup`

```json
{
  "event_type": "DataRetentionCleanup",
  "timestamp": "2025-10-20T02:05:00Z",
  "data": {
    "retention_days": 90,
    "cutoff_date": "2025-07-22",
    "records_soft_deleted": 450,
    "records_hard_deleted": 380,
    "storage_freed_mb": 2.3
  }
}
```

**Error Handling**:

- Fail-safe: Never delete data newer than retention period
- Transaction: Rollback if delete count > expected (data corruption check)
- Alert admin if storage freed < expected (may indicate cleanup failure)

---

## 6. Dashboard Refresh Event

**Trigger**: Frontend Poll
**Frequency**: Every 60 seconds
**Endpoint**: `GET /api/v1/tools/last_updated`

**Purpose**: Check if new sentiment data is available without re-fetching full datasets.

**Event Flow**:

```text
Frontend (every 60s)
    │
    ├──▶ GET /tools/last_updated
    │    Response: { "last_updated": "2025-10-20T22:30:00Z" }
    │
    ├──▶ Compare with cached timestamp:
    │    - If newer: Refetch tool sentiment data
    │    - If same: Skip (no changes)
    │
    └──▶ Update UI with fresh data
```

**Backend Implementation**:

```python
@router.get("/tools/last_updated")
async def get_last_updated(db: DatabaseService):
    """Return max(computed_at) across all time_period_aggregates."""
    timestamp = await db.execute_scalar_query(
        "SELECT VALUE MAX(c.computed_at) FROM time_period_aggregates c"
    )
    return {"last_updated": timestamp}
```

**Performance**: < 100ms response time (simple scalar query)

---

## Event Logging

All events are logged to structured logs with the following format:

```json
{
  "timestamp": "2025-10-20T14:30:00.123Z",
  "level": "INFO",
  "logger": "sentiment_agent.jobs",
  "event_type": "ToolDetected",
  "job_id": "tool_auto_detection",
  "execution_time_ms": 1250,
  "data": {
    "tools_detected": 2,
    "tools_created": 1,
    "tools_skipped": 1
  }
}
```

**Log Levels**:

- `INFO`: Normal job execution, tool approvals
- `WARNING`: Detection rate limits hit, retry attempts
- `ERROR`: Job failures, validation errors
- `CRITICAL`: Data corruption, retention policy failures

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Job Execution Time**
   - daily_sentiment_aggregation: < 5 minutes
   - tool_auto_detection: < 2 minutes
   - sentiment_data_cleanup: < 1 minute

2. **Job Success Rate**
   - Target: > 99% success rate
   - Alert if < 95% over 24-hour window

3. **Tool Detection Rate**
   - Typical: 0-2 new tools per week
   - Alert if > 10 pending tools (possible spam)

4. **Data Retention**
   - Storage growth should be linear (not exponential)
   - Alert if storage freed < 80% of expected

### Alerting Rules

```yaml
alerts:
  - name: AggregationJobSlow
    condition: execution_time > 300s
    severity: warning
    action: notify_dev_team

  - name: DetectionRateLimitReached
    condition: pending_tools > 10
    severity: warning
    action: notify_admin

  - name: RetentionCleanupFailed
    condition: records_deleted == 0 AND expected_deletes > 0
    severity: critical
    action: page_on_call
```

---

## Testing Events

### Unit Tests

```python
# Test auto-detection logic
def test_tool_detection_threshold():
    detector = ToolDetector()
    assert not detector.should_create_pending(mentions=49)
    assert detector.should_create_pending(mentions=50)

# Test approval flow
@pytest.mark.asyncio
async def test_tool_approval_emits_event(db, event_bus):
    tool = await db.create_pending_tool("TestTool")
    await tool_manager.approve_tool(tool.id, admin_id="admin")
    
    events = event_bus.get_emitted_events()
    assert any(e.event_type == "ToolApproved" for e in events)
```

### Integration Tests

```python
# Test end-to-end aggregation
@pytest.mark.asyncio
async def test_daily_aggregation_job(db, scheduler):
    # Seed test data
    tool = await db.create_approved_tool("TestTool")
    await db.create_test_mentions(tool.id, date="2025-10-20", count=100)
    
    # Trigger job
    await scheduler.run_job("daily_sentiment_aggregation")
    
    # Verify aggregates created
    aggregates = await db.get_aggregates(tool.id, date="2025-10-20")
    assert aggregates.total_mentions == 100
```

---

## Summary

This feature adds 6 key event types:

1. **Daily Aggregation** (scheduled): Precompute sentiment statistics
2. **Tool Auto-Detection** (scheduled): Find new tools to track
3. **Tool Approval** (admin action): Enable tool in dashboard
4. **Tool Rejection** (admin action): Dismiss false positives
5. **Data Retention Cleanup** (scheduled): Enforce 90-day retention
6. **Dashboard Refresh** (poll): Check for new data

All events follow structured logging patterns and include comprehensive error handling.
