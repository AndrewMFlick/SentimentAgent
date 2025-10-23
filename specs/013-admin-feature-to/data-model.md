# Data Model: Admin Sentiment Reanalysis & Tool Categorization

**Feature**: 013-admin-feature-to  
**Date**: 2025-10-23  
**Source**: Extracted from spec.md functional requirements and research.md decisions

## Entity Definitions

### 1. ReanalysisJob (NEW)

**Purpose**: Tracks asynchronous sentiment reanalysis operations for audit trail, progress monitoring, and job resumption.

**Storage**: CosmosDB collection `ReanalysisJobs`

**Schema**:

```typescript
{
  id: string;                           // Primary key: "job-{uuid}"
  status: JobStatus;                    // "queued" | "running" | "completed" | "failed"
  trigger_type: TriggerType;            // "manual" | "automatic"
  triggered_by: string;                 // Admin user ID or system identifier
  parameters: ReanalysisParameters;
  progress: JobProgress;
  statistics: JobStatistics;
  error_log: ErrorEntry[];
  start_time: string | null;            // ISO 8601 timestamp
  end_time: string | null;              // ISO 8601 timestamp
  created_at: string;                   // ISO 8601 timestamp
  _ts: number;                          // CosmosDB system timestamp
}
```

**Nested Types**:

```typescript
interface ReanalysisParameters {
  date_range?: {
    start: string;                      // ISO 8601, null = no start limit
    end: string;                        // ISO 8601, null = no end limit
  };
  tool_ids?: string[];                  // Empty/null = all tools
  batch_size: number;                   // Default: 100
}

interface JobProgress {
  total_count: number;                  // Total documents to process
  processed_count: number;              // Documents completed
  percentage: number;                   // Calculated: processed/total * 100
  last_checkpoint_id: string | null;    // For resumption: last processed doc ID
}

interface JobStatistics {
  tools_detected: Record<string, number>; // tool_id -> count
  errors_count: number;
  categorized_count: number;            // Docs with tools detected
  uncategorized_count: number;          // Docs with no tools found
}

interface ErrorEntry {
  doc_id: string;                       // sentiment_score document ID
  error: string;                        // Error message
  timestamp: string;                    // ISO 8601
}
```

**Validation Rules** (Pydantic):
- `status` must be one of: queued, running, completed, failed
- `trigger_type` must be one of: manual, automatic
- `parameters.batch_size` must be > 0 and <= 1000
- `progress.percentage` must be >= 0 and <= 100
- `start_time` required when status = running/completed/failed
- `end_time` required when status = completed/failed

**State Transitions**:

```
queued → running → completed
                 ↘ failed

(Cannot reverse from completed/failed back to running)
```

**Indexes** (CosmosDB indexing policy):
- Primary key: `/id`
- Additional indexes:
  - `/status` (for active job queries)
  - `/triggered_by` (for user job history)
  - `/_ts` (for chronological sorting)
  - `/trigger_type` (for filtering manual vs automatic)

---

### 2. SentimentScore (UPDATED)

**Purpose**: Sentiment analysis results for Reddit posts/comments. Updated to support tool categorization and reanalysis tracking.

**Storage**: Existing CosmosDB collection `sentiment_scores`

**New/Updated Fields**:

```typescript
{
  // ... existing fields (id, post_id, comment_id, sentiment, compound, etc.) ...
  
  detected_tool_ids: string[];          // NEW: Tool IDs mentioned in content
  last_analyzed_at: string | null;      // NEW: Timestamp of most recent analysis (ISO 8601)
  analysis_version: string;             // NEW: Detection algorithm version (e.g., "1.0.0")
  
  _ts: number;                          // EXISTING: CosmosDB system timestamp
}
```

**Field Details**:
- `detected_tool_ids`: Array of tool IDs from Tools collection. Empty array = no tools detected. Uses ARRAY_CONTAINS for queries (requires array index).
- `last_analyzed_at`: Tracks when tool detection last ran. Null = never analyzed for tools.
- `analysis_version`: Semantic version of tool detection logic. Enables re-reanalysis when algorithm improves.

**Validation Rules**:
- `detected_tool_ids` must be array of strings (can be empty)
- `analysis_version` must match pattern: `^\d+\.\d+\.\d+$` (semantic versioning)
- `last_analyzed_at` must be valid ISO 8601 timestamp or null

**Index Requirements** (for Hot Topics queries):
- `/detected_tool_ids[]` with ARRAY_CONTAINS support (options: 17)
- `/_ts` for time-based filtering

---

### 3. Tool (EXISTING - Event Triggers)

**Purpose**: AI tools being tracked. Updated behavior to trigger reanalysis on status changes.

**Storage**: Existing CosmosDB collection `Tools`

**Relevant Fields**:

```typescript
{
  id: string;                           // Primary key
  name: string;
  status: ToolStatus;                   // "active" | "archived"
  // ... other existing fields ...
}
```

**Event Triggers** (via API hooks):
- **Tool Created** with `status='active'` → Trigger automatic reanalysis (US2)
- **Tool Status Changed** from `archived` to `active` → Trigger automatic reanalysis (US2)
- **Tool Merged** (source → target) → Trigger automatic reanalysis to replace tool IDs (US2)

**Reanalysis Behavior**:
- Create ReanalysisJob with `trigger_type='automatic'`
- Parameters: `tool_ids=[new_tool_id]` (only reanalyze for this tool)
- Date range: null (scan all historical data)

---

### 4. ToolAlias (EXISTING - Alias Resolution)

**Purpose**: Maps alias tools to primary tools. Reanalysis must resolve aliases when updating detected_tool_ids.

**Storage**: Existing CosmosDB collection `ToolAliases`

**Relevant Fields**:

```typescript
{
  id: string;
  alias_tool_id: string;                // Tool that is an alias
  primary_tool_id: string;              // Tool being aliased to
  // ... other existing fields ...
}
```

**Reanalysis Integration**:
- When updating `detected_tool_ids`, resolve aliases to primary tools
- Follow alias chains (A→B→C should resolve to C)
- Prevents duplicate tool IDs in detected_tool_ids array

**Example**:
```
Content mentions: "GitHub Copilot" (alias) → Resolve to "Copilot" (primary)
detected_tool_ids = ["copilot"]  // Not ["github-copilot", "copilot"]
```

---

### 5. AdminAuditLog (EXISTING - Extended Events)

**Purpose**: Audit trail for admin actions. Extended to capture reanalysis operations.

**Storage**: Existing collection (location TBD - may be in Tools or separate)

**New Event Types**:
- `reanalysis_triggered`: Admin manually triggers reanalysis job
- `reanalysis_completed`: Job finishes successfully
- `reanalysis_failed`: Job encounters fatal error

**Event Payload Examples**:

```typescript
// reanalysis_triggered
{
  event_type: "reanalysis_triggered",
  admin_user: "admin@example.com",
  timestamp: "2025-10-23T10:00:00Z",
  job_id: "job-abc123",
  parameters: {
    date_range: { start: "2025-01-01T00:00:00Z", end: null },
    tool_ids: ["github-copilot"],
    batch_size: 100
  },
  ip_address: "192.168.1.1",
  user_agent: "Mozilla/5.0..."
}

// reanalysis_completed
{
  event_type: "reanalysis_completed",
  job_id: "job-abc123",
  timestamp: "2025-10-23T10:05:00Z",
  statistics: {
    tools_detected: { "github-copilot": 245, "claude": 123 },
    total_processed: 5699,
    categorized: 368,
    uncategorized: 5331,
    errors: 0
  },
  duration_seconds: 57
}
```

---

## Entity Relationships

```
ReanalysisJob
  ├─ triggered_by → AdminUser (external, not modeled)
  ├─ processes → SentimentScore[] (via batch queries)
  └─ affects → Tool[] (via parameters.tool_ids)

SentimentScore
  ├─ detected_tool_ids[] → Tool[] (many-to-many)
  └─ analyzed_by → ReanalysisJob (implicit, via last_analyzed_at)

Tool
  ├─ triggers_creation_of → ReanalysisJob (on status change)
  └─ referenced_in → SentimentScore.detected_tool_ids[]

ToolAlias
  ├─ alias_tool_id → Tool
  ├─ primary_tool_id → Tool
  └─ resolved_during → ReanalysisJob processing
```

---

## Data Migration Requirements

### Phase 1: Schema Updates

**sentiment_scores collection**:

1. Add new fields with default values:
   ```python
   {
     "detected_tool_ids": [],           # Empty array
     "last_analyzed_at": null,          # Never analyzed
     "analysis_version": "1.0.0"        # Initial version
   }
   ```

2. Update indexing policy to support ARRAY_CONTAINS:
   ```json
   {
     "indexingMode": "consistent",
     "includedPaths": [
       { "path": "/detected_tool_ids/*" }
     ],
     "compositeIndexes": [
       [
         { "path": "/detected_tool_ids", "order": "ascending" },
         { "path": "/_ts", "order": "descending" }
       ]
     ]
   }
   ```

**ReanalysisJobs collection** (NEW):

1. Create collection with partition key `/id`
2. Apply indexing policy for status, triggered_by, _ts
3. Set default TTL to null (keep job history indefinitely)

### Phase 2: Data Backfill

**Run initial reanalysis** (manually triggered):

1. Create ReanalysisJob with:
   - trigger_type: "manual"
   - triggered_by: "system_migration"
   - parameters: { batch_size: 100 } (all tools, all dates)

2. Process all 5,699 existing sentiment_scores:
   - Re-run tool detection on original post/comment content
   - Update detected_tool_ids, last_analyzed_at, analysis_version
   - Checkpoint every 100 documents

3. Expected result:
   - ~95% of documents categorized (per SC-003)
   - Hot Topics feature becomes functional
   - Tool-specific dashboards populate with historical data

**Rollback Plan** (if needed):

- sentiment_scores: No rollback needed (new fields default to empty/null)
- ReanalysisJobs: Drop collection if unused
- Indexes: Revert indexing policy to pre-migration state

---

## Performance Considerations

**Write Volume**:
- Initial backfill: 5,699 updates to sentiment_scores (~11,400 RU)
- Ongoing: ~100-500 updates per tool status change
- RU cost per update: ~2 RU (read + write)

**Query Patterns**:
- Active job check: `SELECT * FROM c WHERE c.status IN ('queued', 'running')`
- Job history: `SELECT * FROM c WHERE c.triggered_by = @user ORDER BY c._ts DESC`
- Resume job: `SELECT * FROM c WHERE c.id > @checkpoint_id ORDER BY c.id LIMIT @batch_size`

**Index Impact**:
- ARRAY_CONTAINS index on detected_tool_ids: Required for Hot Topics queries
- Status index on ReanalysisJobs: Enables fast active job checks
- Composite index (detected_tool_ids + _ts): Optimizes time-filtered tool queries

**Data Size**:
- ReanalysisJobs: ~1 KB per job, ~100 jobs/year = 100 KB/year (negligible)
- sentiment_scores: +100 bytes per document = +570 KB for existing data
- Total storage impact: <1 MB

---

**Phase 1 Data Model Complete** - Ready for contract generation.
