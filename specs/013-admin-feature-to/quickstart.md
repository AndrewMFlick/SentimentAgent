# Quickstart: Admin Sentiment Reanalysis Development

**Feature**: 013-admin-feature-to  
**Last Updated**: 2025-10-23

## Overview

This guide helps developers set up and work on the Admin Sentiment Reanalysis feature. The feature enables admins to backfill tool categorization in existing sentiment data through manual triggers or automatic tool status change events.

## Prerequisites

- Python 3.13.3 installed
- Local CosmosDB emulator running on `localhost:8081`
- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- Admin token configured in environment (`ADMIN_TOKEN` env var)

## Database Setup

### 1. Create ReanalysisJobs Collection

The ReanalysisJobs collection stores job metadata for tracking, resumption, and audit trail.

```bash
# Run from repository root
cd deployment/scripts

# Create collection with indexing policy
./create-reanalysis-jobs-collection.sh
```

**Manual creation** (if script unavailable):

```python
# In Python REPL or script
from azure.cosmos import CosmosClient, PartitionKey

client = CosmosClient("https://localhost:8081", "<emulator-key>")
database = client.get_database_client("sentiment_analysis")

# Create collection
database.create_container(
    id="ReanalysisJobs",
    partition_key=PartitionKey(path="/id"),
    indexing_policy={
        "indexingMode": "consistent",
        "includedPaths": [
            {"path": "/*"}
        ],
        "compositeIndexes": [
            [
                {"path": "/status", "order": "ascending"},
                {"path": "/_ts", "order": "descending"}
            ]
        ]
    }
)
```

### 2. Update sentiment_scores Indexing

Apply array indexing for detected_tool_ids field (required for Hot Topics queries).

```bash
# This should have been run for Feature 012, but verify:
cd deployment/scripts
./setup-hot-topics-indexes.sh
```

**Verify index** exists:

```bash
# Check for ARRAY_CONTAINS support on detected_tool_ids
curl -X POST https://localhost:8081/dbs/sentiment_analysis/colls/sentiment_scores/docs \
  -H "x-ms-documentdb-isquery: true" \
  -H "x-ms-documentdb-query-enablecrosspartition: true" \
  -d '{"query": "SELECT * FROM c WHERE ARRAY_CONTAINS(c.detected_tool_ids, \"test\")"}'

# If you get "Index does not have options 17" error, indexes are missing
```

### 3. Add Schema Fields to Existing Documents

Update existing sentiment_scores to include new fields with defaults.

```python
# Run migration script
from backend.src.services.database import DatabaseService

db = DatabaseService()
await db.connect()

container = db.database.get_container_client("sentiment_scores")

# Update all documents
async for item in container.query_items(
    "SELECT * FROM c",
    enable_cross_partition_query=True
):
    if "detected_tool_ids" not in item:
        item["detected_tool_ids"] = []
        item["last_analyzed_at"] = None
        item["analysis_version"] = "1.0.0"
        await container.upsert_item(item)
```

## Running the Backend

### Start Backend Server

```bash
cd backend
python -m src.main
# Or use start script:
./start.sh
```

Server starts on `http://localhost:8000`

### Verify Reanalysis Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List reanalysis jobs (requires admin token)
curl -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/v1/admin/reanalysis/jobs

# Expected: 200 OK with empty jobs array
```

## Development Workflow

### 1. Trigger Manual Reanalysis Job

**Via API**:

```bash
curl -X POST http://localhost:8000/api/v1/admin/reanalysis/jobs \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{
    "batch_size": 100
  }'

# Response:
# {
#   "job_id": "job-abc123",
#   "status": "queued",
#   "message": "Reanalysis job created successfully",
#   "created_at": "2025-10-23T10:00:00Z"
# }
```

**Via Python Client**:

```python
from backend.src.services.reanalysis_service import ReanalysisService

service = ReanalysisService(...)
job = await service.trigger_manual_reanalysis(
    admin_user="admin@example.com",
    parameters={"batch_size": 100}
)
print(f"Job ID: {job['id']}, Status: {job['status']}")
```

### 2. Monitor Job Progress

```bash
# Poll job status
JOB_ID="job-abc123"
curl -H "X-Admin-Token: your-admin-token" \
  http://localhost:8000/api/v1/admin/reanalysis/jobs/$JOB_ID

# Response includes progress:
# {
#   "id": "job-abc123",
#   "status": "running",
#   "progress": {
#     "total_count": 5699,
#     "processed_count": 2500,
#     "percentage": 43.9
#   },
#   ...
# }
```

### 3. Test Automatic Triggers

**Tool Creation**:

```bash
# Create new tool with status='active' → triggers reanalysis
curl -X POST http://localhost:8000/api/v1/admin/tools \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{
    "name": "New AI Tool",
    "vendor": "Vendor",
    "category": "code_assistant",
    "status": "active"
  }'

# Check that reanalysis job was auto-created
curl -H "X-Admin-Token: your-admin-token" \
  "http://localhost:8000/api/v1/admin/reanalysis/jobs?trigger_type=automatic"
```

**Tool Merge**:

```bash
# Merge tools → triggers reanalysis to update tool IDs
curl -X POST http://localhost:8000/api/v1/admin/tools/merge \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: your-admin-token" \
  -d '{
    "target_tool_id": "copilot",
    "source_tool_ids": ["github-copilot-individual"],
    "merged_by": "admin@example.com"
  }'
```

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/unit/test_reanalysis_service.py -v
pytest tests/unit/test_reanalysis_models.py -v
```

### Run Integration Tests

```bash
# Requires CosmosDB emulator running
pytest tests/integration/test_reanalysis_api.py -v
```

### Test Coverage

```bash
pytest --cov=src.services.reanalysis_service \
       --cov=src.api.reanalysis \
       --cov-report=html
```

## Common Issues

### "Index does not have options 17" Error

**Symptom**: Hot Topics queries fail with CosmosDB indexing error

**Fix**: Apply array indexing policy to sentiment_scores collection

```bash
cd deployment/scripts
./setup-hot-topics-indexes.sh
```

### Reanalysis Job Stuck in "queued" Status

**Symptom**: Job created but never starts processing

**Cause**: APScheduler not running or job scheduling failed

**Debug**:

```python
# Check scheduler status
from backend.src.services.scheduler import scheduler
print(scheduler.get_jobs())

# Check job logs
import structlog
logger = structlog.get_logger()
# Look for "Reanalysis job started" log entry
```

### Job Fails with "Tool detection failed"

**Symptom**: Error log shows tool detection errors for many documents

**Cause**: sentiment_analyzer.detect_tools() logic may have changed

**Debug**:

```python
from backend.src.services.sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
# Test on sample document
result = await analyzer.detect_tools("My Reddit post about GitHub Copilot")
print(result)  # Should return ["github-copilot"] or similar
```

## API Documentation

Full API specification: [contracts/reanalysis-api.yaml](contracts/reanalysis-api.yaml)

Interactive docs (when server running):
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Schema

Full data model: [data-model.md](data-model.md)

**Key Collections**:
- `ReanalysisJobs`: Job tracking and progress
- `sentiment_scores`: Sentiment data with detected_tool_ids (updated)
- `Tools`: AI tools (triggers reanalysis on status changes)
- `ToolAliases`: Tool alias resolution

## Performance Tuning

### Batch Size Configuration

Default: 100 documents per checkpoint

**Smaller batches** (50):
- Pros: More frequent progress updates, faster resumption
- Cons: More DB writes, slightly slower overall

**Larger batches** (500):
- Pros: Fewer DB writes, faster overall processing
- Cons: Less frequent progress, more reprocessing on failure

**Recommended**: 100 (balances all factors)

### CosmosDB Provisioning

**Development** (local emulator):
- Unlimited RU/s, no throttling concerns

**Production**:
- Provision at least 400 RU/s for ReanalysisJobs collection
- Provision at least 1000 RU/s for sentiment_scores during backfill
- Use autoscale if available for burst capacity

## Next Steps

After setting up:

1. **Run initial backfill**: Trigger manual reanalysis for all historical data
2. **Verify Hot Topics**: Check that tool-specific queries return data
3. **Test automatic triggers**: Create/merge tools to verify event hooks
4. **Monitor performance**: Check job completion times and error rates
5. **Review audit logs**: Verify admin actions are logged correctly

## Related Documentation

- Feature Specification: [spec.md](spec.md)
- Implementation Plan: [plan.md](plan.md)
- Research & Decisions: [research.md](research.md)
- Data Model: [data-model.md](data-model.md)
- API Contracts: [contracts/reanalysis-api.yaml](contracts/reanalysis-api.yaml)

---

**Questions?** Check logs with `structlog` or review [IMPLEMENTATION_SUMMARY.md](../../IMPLEMENTATION_SUMMARY.md)
