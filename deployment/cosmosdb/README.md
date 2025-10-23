# CosmosDB Index Configuration for Hot Topics

This directory contains index policy files for the Hot Topics feature.

## Index Policies

### sentiment_scores Container

**Composite Index**: `[detected_tool_ids[], _ts]`

**Purpose**: Efficiently query posts/comments mentioning specific tools within a time range.

**Query Pattern**:
```sql
SELECT * FROM c 
WHERE ARRAY_CONTAINS(c.detected_tool_ids, @tool_id) 
  AND c._ts >= @cutoff
ORDER BY c._ts DESC
```

**File**: `sentiment_scores_index_policy.json`

---

### reddit_comments Container

**Composite Index**: `[post_id, _ts]`

**Purpose**: Efficiently find recent comments for posts (engagement activity detection).

**Query Pattern**:
```sql
SELECT VALUE 1 FROM comments c 
WHERE c.post_id = @post_id 
  AND c._ts >= @cutoff
```

**File**: `reddit_comments_index_policy.json`

---

### reddit_posts Container

**Indexes**: Auto-indexed by CosmosDB (no custom policy needed)
- `id` (primary key)
- `_ts` (system timestamp)
- `comment_count` (scalar field, auto-indexed)
- `upvotes` (scalar field, auto-indexed)

**Query Pattern**:
```sql
SELECT * FROM posts p 
WHERE p._ts >= @cutoff
ORDER BY (p.comment_count + p.upvotes) DESC
```

---

## Applying Indexes

### Local Development (CosmosDB Emulator)

Indexes are automatically created on first query. No manual setup required.

```bash
# Just start the backend - indexes will be created automatically
cd backend
./start.sh
```

### Production (Azure CosmosDB)

Use the provided setup script:

```bash
# Set environment variables (from .env or Azure Portal)
export COSMOS_ENDPOINT="https://your-account.documents.azure.com:443/"
export COSMOS_KEY="your-primary-key"
export COSMOS_DATABASE="sentiment_analysis"

# Run setup script
cd deployment/scripts
./setup-hot-topics-indexes.sh --production
```

**Manual Application via Azure CLI**:

```bash
# Update sentiment_scores container
az cosmosdb sql container update \
  --account-name YOUR_ACCOUNT \
  --database-name sentiment_analysis \
  --name sentiment_scores \
  --idx @deployment/cosmosdb/sentiment_scores_index_policy.json

# Update reddit_comments container
az cosmosdb sql container update \
  --account-name YOUR_ACCOUNT \
  --database-name sentiment_analysis \
  --name reddit_comments \
  --idx @deployment/cosmosdb/reddit_comments_index_policy.json
```

**Manual Application via Azure Portal**:

1. Navigate to Azure Portal → CosmosDB Account
2. Select "Data Explorer"
3. Expand database → Select container
4. Click "Settings" → "Indexing Policy"
5. Copy the JSON from the corresponding policy file
6. Click "Save"

---

## Performance Impact

**Before Composite Indexes**:
- Full container scan for tool mentions
- Slow queries (> 10 seconds for 10,000 documents)

**After Composite Indexes**:
- Index seek for tool ID + time range
- Fast queries (< 2 seconds for same dataset)
- Meets performance requirements: SC-001 (< 5s page load), SC-005 (< 2s filtering)

---

## Monitoring

### Check Index Progress (Production)

Indexing transformation happens asynchronously. Monitor in Azure Portal:

1. Data Explorer → Container → Settings → Indexing Policy
2. Check "Indexing Progress" percentage
3. Typically completes in 5-10 minutes for existing data

### Verify Indexes Are Used

Enable query metrics in backend logs:

```python
# In database service queries
query_iterator = container.query_items(
    query=query,
    enable_cross_partition_query=True,
    populate_query_metrics=True  # Enable metrics
)

# Check logs for "Index Utilization: 100%"
```

### Slow Query Detection

The existing `monitor_query_performance` decorator logs queries > 3 seconds:

```
WARN: Slow query detected, duration=4.5s, query=SELECT * FROM c WHERE...
```

If you see slow queries after indexes are applied, verify:
1. Composite index is active (check Azure Portal)
2. Query uses indexed fields in correct order
3. Query doesn't force full scan (avoid `NOT` operators)

---

## Troubleshooting

**Issue**: Queries still slow after applying indexes

**Solution**:
- Verify indexing transformation completed (Azure Portal)
- Check query uses exact field paths from index policy
- Array fields require `ARRAY_CONTAINS`, not `IN` operator

**Issue**: "Index not found" errors

**Solution**:
- Wait for indexing transformation to complete
- Verify index policy JSON is valid
- Check CosmosDB service logs for transformation errors

**Issue**: High RU consumption

**Solution**:
- Composite indexes reduce RU cost by ~80% for range queries
- Monitor RU usage in Azure Portal metrics
- Consider increasing container throughput if needed

---

## Index Policy Structure

Each policy file contains:

```json
{
  "indexingMode": "consistent",     // Immediate consistency
  "automatic": true,                 // Auto-index new documents
  "includedPaths": [{"path": "/*"}], // Index all paths by default
  "excludedPaths": [{"path": "/\"_etag\"/?"}], // Exclude system field
  "compositeIndexes": [              // Composite indexes for multi-field queries
    [
      {"path": "/field1", "order": "ascending"},
      {"path": "/field2", "order": "descending"}
    ]
  ]
}
```

**Key Points**:
- Order matters: Query must use fields in same order as index
- Array fields use `path/*` syntax (e.g., `/detected_tool_ids/*`)
- System timestamp `_ts` always sorted descending (newest first)

---

## References

- [Azure CosmosDB Indexing Overview](https://docs.microsoft.com/en-us/azure/cosmos-db/index-overview)
- [Composite Indexes](https://docs.microsoft.com/en-us/azure/cosmos-db/index-policy#composite-indexes)
- [Query Performance Tuning](https://docs.microsoft.com/en-us/azure/cosmos-db/sql-query-performance-tips)
- Feature Spec: `specs/012-hot-topics-isn/spec.md`
- Research Document: `specs/012-hot-topics-isn/research.md` (R4: Query Performance)
