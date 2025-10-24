# Research: Admin Sentiment Reanalysis & Tool Categorization

**Feature**: 013-admin-feature-to  
**Date**: 2025-10-23  
**Purpose**: Resolve technical unknowns and document decision rationale for implementation

## Research Tasks

### 1. Job Queue Implementation Strategy

**Unknown**: Use existing APScheduler or add dedicated task queue (Celery/RQ)?

**Research Findings**:

**Current System Context**:
- APScheduler 3.10.4 already in use for scheduled Reddit data collection
- Backend uses `lifespan` pattern for startup/shutdown
- No external message broker (Redis/RabbitMQ) currently deployed
- Jobs are background collection tasks, not user-triggered workloads

**Options Evaluated**:

| Option | Pros | Cons | Fit for Feature |
|--------|------|------|-----------------|
| **APScheduler** | Already integrated, no new dependencies, simple for infrequent jobs, in-memory state | Limited scalability, no persistence across restarts, no distributed workers | ✅ Good - Reanalysis is infrequent, single-worker acceptable |
| **Celery** | Robust task queue, distributed workers, result backend, retry logic | Requires Redis/RabbitMQ broker, adds deployment complexity, overkill for current scale | ❌ Over-engineered - Not needed for 5.7k documents |
| **RQ (Redis Queue)** | Simpler than Celery, Redis-based, better than APScheduler | Still requires Redis deployment, adds infrastructure burden | ❌ Unnecessary - APScheduler sufficient |

**Decision**: **Use APScheduler with BackgroundScheduler**

**Rationale**:
1. Already integrated - zero new dependencies
2. Reanalysis jobs are infrequent (admin-triggered or tool changes)
3. Current dataset size (5.7k docs) doesn't require distributed processing
4. Can migrate to Celery/RQ later if scale demands it
5. Consistent with existing scheduled task patterns

**Implementation Approach**:
- Add reanalysis job functions to `scheduler.py`
- Use `add_job()` with `trigger='date'` for one-time execution
- Store job metadata in CosmosDB ReanalysisJobs collection
- Job progress tracked in database, not scheduler state

---

### 2. Progress Tracking Storage Strategy

**Unknown**: Add fields to sentiment_scores or create separate JobProgress collection?

**Research Findings**:

**Options Evaluated**:

| Option | Pros | Cons | Fit for Feature |
|--------|------|------|-----------------|
| **Add to sentiment_scores** | No new collection, progress embedded with data | Pollutes sentiment schema, hard to query job progress, couples job metadata to data | ❌ Poor - Schema pollution |
| **Separate ReanalysisJobs collection** | Clean separation, easy job queries, independent lifecycle, supports job history | One additional collection | ✅ Excellent - Clean architecture |
| **In-memory only** | Fastest, no storage overhead | No persistence, lost on restart, no job history | ❌ Unacceptable - FR-013 requires resumability |

**Decision**: **Create dedicated ReanalysisJobs collection**

**Rationale**:
1. Separation of concerns - job metadata ≠ sentiment data
2. Easy to query active/completed jobs without scanning sentiment_scores
3. Supports job history for audit trail (FR-008)
4. Enables checkpoint resumption (FR-013)
5. Consistent with admin feature patterns (Tools, ToolAliases separate)

**Schema Design**:
```python
{
  "id": "job-{uuid}",                    # Partition key
  "status": "queued|running|completed|failed",
  "trigger_type": "manual|automatic",
  "triggered_by": "admin_user_id",
  "parameters": {
    "date_range": {"start": "ISO8601", "end": "ISO8601"},
    "tool_ids": ["tool1", "tool2"],      # Empty = all tools
    "batch_size": 100
  },
  "progress": {
    "total_count": 5699,
    "processed_count": 2500,
    "percentage": 43.9,
    "last_checkpoint_id": "doc-xyz"      # For resumption
  },
  "statistics": {
    "tools_detected": {
      "github-copilot": 245,
      "claude": 123
    },
    "errors_count": 2,
    "categorized_count": 2498,
    "uncategorized_count": 2
  },
  "error_log": [
    {"doc_id": "abc", "error": "Missing content field"}
  ],
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "created_at": "ISO8601",
  "_ts": 1234567890
}
```

---

### 3. Checkpoint Strategy for Resumability

**Unknown**: Document-level or batch-level checkpointing?

**Research Findings**:

**Options Evaluated**:

| Option | Pros | Cons | Fit for Feature |
|--------|------|------|-----------------|
| **Document-level** | Granular resumption, no duplicate processing, accurate progress | Higher checkpoint overhead, more DB writes | ✅ Good - Ensures zero duplicates (FR-009 idempotent) |
| **Batch-level (every N docs)** | Less overhead, fewer DB writes | May reprocess up to N-1 docs on resume, less accurate progress | ⚠️ Acceptable if N small (e.g., 50-100) |
| **No checkpointing** | Simplest implementation | Must restart from beginning on failure | ❌ Violates FR-013 |

**Decision**: **Batch-level checkpointing every 100 documents**

**Rationale**:
1. Balances resumability with performance overhead
2. At 100 docs/sec, 100-doc batches = 1 second of work
3. Worst case: reprocess 99 docs (~1 second) on failure
4. Detected_tool_ids update is idempotent - safe to reprocess
5. Progress updates every 1 second provide good UX

**Implementation Approach**:
```python
async def process_batch(job_id, batch):
    for i, doc in enumerate(batch):
        await update_detected_tools(doc)
        if (i + 1) % 100 == 0:
            await checkpoint_progress(job_id, doc["id"])
```

**Resumption Logic**:
1. Load job from ReanalysisJobs
2. Query sentiment_scores WHERE id > last_checkpoint_id (lexicographic order)
3. Continue processing from checkpoint

---

### 4. Concurrent Job Handling Strategy

**Unknown**: Allow parallel jobs or enforce sequential processing?

**Research Findings**:

**CosmosDB Throughput Context**:
- Local emulator: Unlimited RU/s for development
- Production: Need to provision adequate RU/s for write-heavy workloads
- Reanalysis = read sentiment_scores + write updates = ~2 RU per doc
- 5.7k docs × 2 RU = 11,400 RU for full reanalysis

**Options Evaluated**:

| Option | Pros | Cons | Fit for Feature |
|--------|------|------|-----------------|
| **Sequential (one job at a time)** | No RU contention, simpler logic, predictable progress | Slower if multiple jobs needed, blocks other admins | ✅ Good - Simple, sufficient for current scale |
| **Parallel (concurrent jobs)** | Faster for multiple jobs, better admin UX | RU contention, complex progress tracking, potential throttling | ⚠️ Premature - Not needed yet |
| **Parallel with RU limits** | Best of both, fair resource sharing | Most complex, requires rate limiting per job | ❌ Over-engineered |

**Decision**: **Sequential processing with job queue**

**Rationale**:
1. Simpler implementation - no RU contention logic needed
2. Reanalysis is infrequent (initial backfill + tool changes)
3. Full dataset (5.7k docs) completes in ~57 seconds at 100 docs/sec
4. Multiple admins triggering simultaneously is unlikely
5. Can add concurrent processing later if needed

**Implementation Approach**:
- Check for active jobs before starting new one
- If active job exists: reject with 409 Conflict or queue as PENDING
- Status flow: queued → running → completed/failed
- APScheduler ensures only one job runs at a time

**Future Enhancement** (if needed):
- Add `priority` field for job ordering
- Implement parallel processing with per-job RU budgets
- Use distributed lock for job coordination

---

## Summary of Decisions

| Decision Area | Choice | Key Rationale |
|---------------|--------|---------------|
| **Job Queue** | APScheduler | Already integrated, sufficient for current scale |
| **Progress Storage** | ReanalysisJobs collection | Clean separation, supports history and resumption |
| **Checkpointing** | Batch-level (100 docs) | Balances performance with resumability |
| **Concurrency** | Sequential processing | Simple, sufficient, avoids RU contention |

**Technology Stack** (no changes):
- Python 3.13.3 + FastAPI 0.109.2
- APScheduler 3.10.4 (existing)
- Azure Cosmos SDK 4.5.1 (existing)
- Pydantic 2.x for models
- structlog 24.1.0 for logging

**New Dependencies**: None - feature uses only existing dependencies

**Performance Expectations**:
- 100 docs/sec processing rate → 5.7k docs in ~57 seconds
- <2 second API response for job triggers
- <5 second progress query latency
- 1-second checkpoint intervals for progress updates

**Risks & Mitigations**:
1. **Risk**: APScheduler state lost on restart  
   **Mitigation**: Job metadata in CosmosDB, jobs resume from checkpoint
   
2. **Risk**: Tool detection logic changes invalidate results  
   **Mitigation**: Store analysis_version in sentiment_scores, allow re-reanalysis
   
3. **Risk**: CosmosDB throttling on large batches  
   **Mitigation**: Batch processing with rate limiting, exponential backoff

---

**Phase 0 Complete** - All NEEDS CLARIFICATION items resolved. Ready for Phase 1 (Design & Contracts).
