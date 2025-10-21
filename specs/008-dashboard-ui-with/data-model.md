# Phase 1: Data Model

**Feature**: AI Tools Sentiment Analysis Dashboard
**Date**: 2025-10-20
**Status**: Completed

## Entity Definitions

### 1. AI Tool

**Purpose**: Represents an AI assistant or development tool being tracked for sentiment analysis.

**Attributes**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| id | string | Yes | Unique identifier (UUID) | Auto-generated on creation |
| name | string | Yes | Official tool name | Max 100 chars, unique |
| vendor | string | No | Creator/vendor name | Max 100 chars |
| category | string | No | Tool category | Enum: "code_assistant", "chat_bot", "other" |
| aliases | list[string] | Yes | Alternative names/spellings | Min 1 alias, max 20 aliases per tool |
| status | string | Yes | Approval status | Enum: "pending", "approved", "rejected" |
| detection_threshold | integer | Yes | Min mentions for auto-detection | Default: 50 |
| first_detected_at | datetime | No | When auto-detection triggered | ISO 8601 UTC |
| approved_by | string | No | Admin who approved | Username |
| approved_at | datetime | No | Approval timestamp | ISO 8601 UTC |
| created_at | datetime | Yes | Creation timestamp | ISO 8601 UTC, auto-generated |
| updated_at | datetime | Yes | Last update timestamp | ISO 8601 UTC, auto-updated |

**Relationships**:

- Has many Tool Mentions (one-to-many)
- Has many Time Period Aggregates (one-to-many)

**Indexes**:

- Primary: `id`
- Unique: `name`
- Filter: `status` (for admin queue queries)
- Filter: `created_at` (for recent detection queries)

**State Transitions**:

1. Auto-detection creates tool with `status="pending"`
2. Admin approval: `pending` → `approved`
3. Admin rejection: `pending` → `rejected`
4. No transition from `approved` or `rejected` (terminal states)

---

### 2. Tool Mention

**Purpose**: Tracks individual mentions/references to AI tools in Reddit posts.

**Attributes**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| id | string | Yes | Unique identifier (UUID) | Auto-generated |
| tool_id | string | Yes | Reference to AI Tool | Foreign key to ai_tools.id |
| content_id | string | Yes | Reddit post/comment ID | Must match existing sentiment_scores.content_id |
| content_type | string | Yes | Content type | Enum: "post", "comment" |
| subreddit | string | Yes | Source subreddit | Max 50 chars |
| mention_text | string | No | Excerpt with mention | Max 500 chars |
| confidence | float | Yes | Detection confidence | 0.0 to 1.0 |
| detected_at | datetime | Yes | Detection timestamp | ISO 8601 UTC |
| sentiment_score_id | string | No | Link to sentiment analysis | Foreign key to sentiment_scores (optional) |

**Relationships**:

- Belongs to AI Tool (many-to-one)
- Optionally links to Sentiment Score (many-to-one)

**Indexes**:

- Primary: `id`
- Filter: `tool_id` (for tool-specific queries)
- Filter: `detected_at` (for time-based queries)
- Composite: `(tool_id, detected_at)` (for time series aggregation)

**Validation**:

- `confidence >= 0.8` to reduce false positives
- `content_id` must exist in posts or comments collection

---

### 3. Time Period Aggregate

**Purpose**: Pre-computed sentiment statistics for a specific tool within a time window (daily granularity).

**Attributes**:

| Field | Type | Required | Description | Validation Rules |
|-------|------|----------|-------------|------------------|
| id | string | Yes | Unique identifier | Composite: "{tool_id}-{date}" |
| tool_id | string | Yes | Reference to AI Tool | Foreign key to ai_tools.id |
| date | date | Yes | Aggregation date | YYYY-MM-DD format |
| total_mentions | integer | Yes | Total mentions | >= 0 |
| positive_count | integer | Yes | Positive sentiment count | >= 0 |
| negative_count | integer | Yes | Negative sentiment count | >= 0 |
| neutral_count | integer | Yes | Neutral sentiment count | >= 0 |
| avg_sentiment | float | Yes | Average compound score | -1.0 to 1.0 |
| computed_at | datetime | Yes | Computation timestamp | ISO 8601 UTC |
| deleted_at | datetime | No | Soft delete timestamp | For retention policy |

**Relationships**:
- Belongs to AI Tool (many-to-one)

**Indexes**:
- Primary: `id` (composite key)
- Filter: `tool_id` (for tool-specific queries)
- Filter: `date` (for time range queries)
- Composite: `(tool_id, date)` (for time series queries)
- Filter: `deleted_at IS NULL` (for active records only)

**Constraints**:
- `total_mentions = positive_count + negative_count + neutral_count`
- `date` must be in the past (no future aggregates)
- Unique constraint on `(tool_id, date)` to prevent duplicates

**Computed Fields** (not stored):
- `positive_percentage = (positive_count / total_mentions) * 100`
- `negative_percentage = (negative_count / total_mentions) * 100`
- `neutral_percentage = (neutral_count / total_mentions) * 100`

---

## Extended Entities (Modifications to Existing)

### 4. Sentiment Score (EXTENDED)

**New Fields Added**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| detected_tool_ids | list[string] | No | IDs of detected tools in content |

**Purpose**: Link sentiment scores to detected tools for faster aggregation queries.

**Migration**:
- Add field to existing `sentiment_scores` container
- Default value: `[]` (empty list)
- Backfill existing records via migration script (scan for tool mentions)

---

## Database Schema (CosmosDB)

### Container Structure

```text
sentiment_analysis (database)
├── posts (existing container)
├── comments (existing container)
├── sentiment_scores (existing container) [EXTENDED: add detected_tool_ids]
├── ai_tools (new container)
│   ├── Partition Key: /id
│   └── Unique Key: /name
├── tool_mentions (new container)
│   ├── Partition Key: /tool_id
│   └── TTL: None (managed by retention policy)
└── time_period_aggregates (new container)
    ├── Partition Key: /tool_id
    └── TTL: Enabled (90 days default, configurable)
```

### Sample Data

**AI Tool (Approved)**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "GitHub Copilot",
  "vendor": "GitHub/Microsoft",
  "category": "code_assistant",
  "aliases": ["copilot", "co-pilot", "github copilot", "gh copilot", "copilot ai"],
  "status": "approved",
  "detection_threshold": 50,
  "first_detected_at": "2025-10-15T10:30:00Z",
  "approved_by": "admin@sentimentagent.com",
  "approved_at": "2025-10-15T14:20:00Z",
  "created_at": "2025-10-15T10:30:00Z",
  "updated_at": "2025-10-15T14:20:00Z"
}
```

**Tool Mention**:

```json
{
  "id": "660f9511-f39c-52e5-b827-557766551111",
  "tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_id": "1abc2def3ghi",
  "content_type": "post",
  "subreddit": "programming",
  "mention_text": "Just tried GitHub Copilot and it's amazing!",
  "confidence": 0.95,
  "detected_at": "2025-10-20T08:15:00Z",
  "sentiment_score_id": "770g0622-g40d-63f6-c938-668877662222"
}
```

**Time Period Aggregate**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000-2025-10-20",
  "tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2025-10-20",
  "total_mentions": 145,
  "positive_count": 87,
  "negative_count": 32,
  "neutral_count": 26,
  "avg_sentiment": 0.342,
  "computed_at": "2025-10-21T00:05:00Z",
  "deleted_at": null
}
```

---

## Query Patterns

### 1. Get Tool Sentiment Breakdown (P1: US1)

```sql
-- Get current sentiment for a specific tool (uses aggregates for last 30 days)
SELECT
  tool_id,
  SUM(positive_count) as total_positive,
  SUM(negative_count) as total_negative,
  SUM(neutral_count) as total_neutral,
  AVG(avg_sentiment) as overall_avg_sentiment
FROM time_period_aggregates
WHERE tool_id = @tool_id
  AND date >= @start_date
  AND date <= @end_date
  AND deleted_at IS NULL
GROUP BY tool_id
```

### 2. Compare Tools (P2: US2)

```sql
-- Get sentiment comparison for multiple tools
SELECT
  t.id as tool_id,
  t.name as tool_name,
  SUM(a.positive_count) as positive_count,
  SUM(a.negative_count) as negative_count,
  SUM(a.neutral_count) as neutral_count,
  SUM(a.total_mentions) as total_mentions,
  AVG(a.avg_sentiment) as avg_sentiment
FROM ai_tools t
JOIN time_period_aggregates a ON t.id = a.tool_id
WHERE t.id IN (@tool_ids)
  AND a.date >= @start_date
  AND a.date <= @end_date
  AND a.deleted_at IS NULL
GROUP BY t.id, t.name
ORDER BY avg_sentiment DESC
```

### 3. Time Series Data (P2: US3)

```sql
-- Get sentiment trend over time for a specific tool
SELECT
  date,
  total_mentions,
  positive_count,
  negative_count,
  neutral_count,
  avg_sentiment
FROM time_period_aggregates
WHERE tool_id = @tool_id
  AND date >= @start_date
  AND date <= @end_date
  AND deleted_at IS NULL
ORDER BY date ASC
```

### 4. Auto-Detection Check (FR-012)

```sql
-- Find tools mentioned 50+ times in last 7 days that aren't tracked yet
SELECT
  REGEXP_EXTRACT(content, @pattern) as potential_tool,
  COUNT(*) as mention_count
FROM sentiment_scores
WHERE analyzed_at >= @seven_days_ago
  AND content ~* @tool_patterns
  AND content_id NOT IN (SELECT content_id FROM tool_mentions)
GROUP BY potential_tool
HAVING COUNT(*) >= 50
```

### 5. Admin Pending Tools (FR-014)

```sql
-- Get pending tools for admin review
SELECT *
FROM ai_tools
WHERE status = 'pending'
ORDER BY created_at ASC
```

---

## Migration Plan

### Phase 1: Schema Creation

1. Create `ai_tools` container with partition key `/id`
2. Create `tool_mentions` container with partition key `/tool_id`
3. Create `time_period_aggregates` container with partition key `/tool_id`

### Phase 2: Seed Initial Tools

```json
[
  {
    "name": "GitHub Copilot",
    "aliases": ["copilot", "co-pilot", "github copilot", "gh copilot"],
    "status": "approved",
    "category": "code_assistant"
  },
  {
    "name": "Jules AI",
    "aliases": ["jules", "jules ai", "julesai"],
    "status": "approved",
    "category": "code_assistant"
  }
]
```

### Phase 3: Backfill Historical Data

1. Scan existing `sentiment_scores` (last 90 days)
2. Detect tool mentions using keyword patterns
3. Create `tool_mentions` records for matched content
4. Run initial aggregate computation for all detected mentions

### Phase 4: Enable TTL

- Set TTL on `time_period_aggregates` to `SENTIMENT_RETENTION_DAYS` config value
- Records auto-delete after retention period expires

---

## Data Validation Rules

### Tool Detection Quality
- Min confidence: 0.8 (80% certainty)
- Max 10 tool mentions per post (prevent spam detection)
- Case-insensitive matching with word boundaries

### Aggregation Consistency
- Daily job runs at 00:05 UTC
- Recompute last 2 days to handle late-arriving data
- Validate: `total_mentions = sum(positive + negative + neutral)`
- Alert if aggregate values drift > 5% from raw counts

### Retention Policy
- Soft delete: Set `deleted_at` timestamp
- Hard delete: 30 days after soft delete
- Admin override: Exclude specific tools from retention

---

## Performance Considerations

### Indexes
- All foreign keys indexed for fast joins
- Composite indexes for time-based queries
- Partition keys aligned with query patterns (tool_id)

### Query Optimization
- Pre-computed aggregates avoid full table scans
- Time range filters use indexed `date` field
- Limit results to 90 days max (SC-007: < 3s queries)

### Storage Estimates
- AI Tools: ~50 records × 1KB = 50KB (negligible)
- Tool Mentions: 10,000/tool/90days × 5 tools × 1KB = ~50MB
- Time Period Aggregates: 90 days × 5 tools × 0.5KB = ~225KB

**Total: ~50MB additional storage for 90-day retention**
