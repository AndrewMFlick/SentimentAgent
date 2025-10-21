# Quickstart Guide: AI Tools Sentiment Analysis Dashboard

**Feature**: 008-dashboard-ui-with
**Target Audience**: Developers implementing this feature
**Est. Reading Time**: 10 minutes

## Overview

This feature adds tool-specific sentiment tracking to the SentimentAgent dashboard. Users can view sentiment breakdowns for AI tools (GitHub Copilot, Jules, etc.), compare tools side-by-side, and track sentiment trends over time.

**Key Capabilities**:
- View sentiment breakdown per AI tool (positive/negative/neutral percentages)
- Compare sentiment between 2+ tools
- Visualize sentiment trends with time series charts
- Auto-detect new AI tools with admin approval workflow
- Filter by custom time ranges

---

## Architecture Overview

```text
Frontend (React)                Backend (FastAPI)                   Database (CosmosDB)
┌────────────────┐            ┌─────────────────┐                ┌──────────────────┐
│ ToolSentiment  │───GET────▶│ /tools/{id}/    │───Query──────▶│ time_period_     │
│ Card Component │            │ sentiment       │                │ aggregates       │
└────────────────┘            └─────────────────┘                └──────────────────┘
                                      │                                  │
┌────────────────┐                    │                                  │
│ ToolComparison │───GET────▶ /tools/compare                            │
│ Component      │            (parallel queries)                         │
└────────────────┘                    │                                  │
                                      │                           ┌──────────────────┐
┌────────────────┐                    │                           │ ai_tools         │
│ TimeSeries     │───GET────▶ /tools/{id}/timeseries              │ (approved tools) │
│ Chart          │                    │                           └──────────────────┘
└────────────────┘                    │
                              ┌───────▼────────┐                  ┌──────────────────┐
Background Jobs:              │ ToolDetector   │───Scan──────────▶│ sentiment_scores │
- Daily aggregation           │ (auto-detect)  │                  │ (existing data)  │
- Tool detection (hourly)     └───────┬────────┘                  └──────────────────┘
- Cleanup (nightly)                   │
                              ┌───────▼────────┐                  ┌──────────────────┐
                              │ ToolManager    │───Create────────▶│ tool_mentions    │
                              │ (approval flow)│                  └──────────────────┘
                              └────────────────┘
```

---

## Development Workflow

### Phase 1: Backend Implementation (P1 - Core Sentiment Display)

#### 1.1 Database Setup

```bash
# Run from project root
cd backend

# Add new models to src/models/
# - ai_tool.py
# - tool_mention.py
# - time_aggregate.py

# Create migration script
python scripts/create_containers.py
```

**Models to create** (see `data-model.md` for full schemas):

```python
# src/models/ai_tool.py
class AITool(BaseModel):
    id: str
    name: str
    aliases: List[str]
    status: str  # pending, approved, rejected
    # ... see data-model.md for complete schema
```

#### 1.2 Database Service Extension

```python
# Extend backend/src/services/database.py

async def get_tool_sentiment(
    self,
    tool_id: str,
    start_date: date,
    end_date: date
) -> ToolSentimentStats:
    """
    Query time_period_aggregates for a specific tool.
    Uses parallel query pattern from Feature 005.
    """
    # See data-model.md Query Pattern #1
```

#### 1.3 API Endpoints

```python
# Create backend/src/api/tools.py

@router.get("/tools/{tool_id}/sentiment")
async def get_tool_sentiment(
    tool_id: str,
    hours: int = 720,  # default 30 days
    db: DatabaseService = Depends(get_db)
):
    """P1: Tool sentiment breakdown endpoint."""
    # Implementation maps to contracts/openapi.yaml
```

**Success Criteria**: `GET /api/v1/tools/{tool_id}/sentiment?hours=720` returns sentiment breakdown in < 2 seconds (SC-001)

---

### Phase 2: Frontend Display (P1 - Core Sentiment Display)

#### 2.1 Install Dependencies

```bash
cd frontend
npm install recharts react-query
```

#### 2.2 Create Tool Sentiment Component

```tsx
// src/components/ToolSentimentCard.tsx

export function ToolSentimentCard({ toolId }: { toolId: string }) {
  const { data, isLoading } = useToolSentiment(toolId);
  
  if (isLoading) return <SkeletonCard />;
  
  return (
    <Card>
      <h3>{data.tool_name}</h3>
      <SentimentBreakdown statistics={data.statistics} />
      {/* Pie chart or bar chart showing positive/negative/neutral */}
    </Card>
  );
}
```

#### 2.3 Custom Hook for Data Fetching

```tsx
// src/services/toolApi.ts

export function useToolSentiment(toolId: string, hours = 720) {
  return useQuery({
    queryKey: ['tool-sentiment', toolId, hours],
    queryFn: () => fetchToolSentiment(toolId, hours),
    refetchInterval: 60000, // Poll every 60s (FR-011)
  });
}
```

**Success Criteria**: Dashboard loads and displays sentiment breakdown for at least one tool (Copilot) within 2 seconds

---

### Phase 3: Tool Comparison (P2)

#### 3.1 Backend Endpoint

```python
# backend/src/api/tools.py

@router.get("/tools/compare")
async def compare_tools(
    tool_ids: str,  # comma-separated
    hours: int = 720,
    db: DatabaseService = Depends(get_db)
):
    """P2: Compare sentiment between multiple tools."""
    ids = tool_ids.split(',')
    # Use asyncio.gather() for parallel queries
    results = await asyncio.gather(*[
        db.get_tool_sentiment(id, ...) for id in ids
    ])
    return calculate_deltas(results)
```

#### 3.2 Frontend Comparison Component

```tsx
// src/components/ToolComparison.tsx

export function ToolComparison({ toolIds }: { toolIds: string[] }) {
  const { data } = useToolComparison(toolIds);
  
  return (
    <ComparisonGrid>
      {data.tools.map(tool => (
        <ToolColumn key={tool.tool_id} tool={tool} />
      ))}
      <DeltaHighlights deltas={data.deltas} />
    </ComparisonGrid>
  );
}
```

**Success Criteria**: Users can select 2+ tools and see side-by-side comparison within 5 seconds (SC-002)

---

### Phase 4: Time Series Visualization (P2)

#### 4.1 Backend Time Series Endpoint

```python
# backend/src/api/tools.py

@router.get("/tools/{tool_id}/timeseries")
async def get_tool_timeseries(
    tool_id: str,
    start_date: date,
    end_date: date,
    db: DatabaseService = Depends(get_db)
):
    """P2: Time series sentiment data."""
    # Query time_period_aggregates (see data-model.md Query Pattern #3)
    # Returns daily aggregates within date range
```

#### 4.2 Frontend Time Series Chart

```tsx
// src/components/SentimentTimeSeries.tsx

import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export function SentimentTimeSeries({ toolId, dateRange }) {
  const { data } = useTimeSeries(toolId, dateRange);
  
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data.data_points}>
        <XAxis dataKey="date" />
        <YAxis domain={[-1, 1]} />
        <Line type="monotone" dataKey="avg_sentiment" stroke="#8884d8" />
        <Tooltip content={<CustomTooltip />} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

**Success Criteria**: Time series chart displays 90 days of data with daily granularity, renders in < 3 seconds (SC-007)

---

### Phase 5: Tool Detection & Management (FR-010, FR-012)

#### 5.1 Tool Detector Service

```python
# backend/src/services/tool_detector.py

class ToolDetector:
    def __init__(self, db: DatabaseService):
        self.patterns = self._load_tool_patterns()
    
    async def detect_tools_in_content(self, content: str) -> List[ToolMention]:
        """
        Scan content for tool mentions using keyword patterns.
        Returns list of detected tools with confidence scores.
        """
        # Implementation from research.md Decision #1
```

#### 5.2 Auto-Detection Background Job

```python
# backend/src/services/scheduler.py (extend existing)

scheduler.add_job(
    check_auto_detection,
    trigger='interval',
    hours=1,
    id='tool_auto_detection'
)

async def check_auto_detection():
    """
    Hourly job: Scan for new tools mentioned 50+ times in 7 days.
    Create pending AI Tool record for admin approval.
    """
    # Implementation from data-model.md Query Pattern #4
```

#### 5.3 Admin Approval Interface

```tsx
// src/components/AdminToolApproval.tsx

export function AdminToolApproval() {
  const { data: pendingTools } = usePendingTools();
  
  return (
    <AdminPanel>
      <h2>Pending Tool Approvals</h2>
      <Table>
        {pendingTools.map(tool => (
          <Row key={tool.id}>
            <Cell>{tool.name}</Cell>
            <Cell>{tool.mention_count} mentions</Cell>
            <Cell>
              <Button onClick={() => approveTool(tool.id)}>Approve</Button>
              <Button onClick={() => rejectTool(tool.id)}>Reject</Button>
            </Cell>
          </Row>
        ))}
      </Table>
    </AdminPanel>
  );
}
```

---

## Background Jobs

### Daily Aggregation Job

```python
# Runs at 00:05 UTC daily
# Computes time_period_aggregates for previous 2 days
# Updates existing aggregates to handle late-arriving data

@scheduler.job('cron', hour=0, minute=5)
async def compute_daily_aggregates():
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(1, 3)]
    
    for tool in await db.get_approved_tools():
        for date in dates:
            aggregate = await compute_aggregate_for_date(tool.id, date)
            await db.upsert_time_aggregate(aggregate)
```

### Cleanup Job (Retention Policy)

```python
# Runs nightly at 02:00 UTC
# Soft deletes aggregates older than SENTIMENT_RETENTION_DAYS

@scheduler.job('cron', hour=2, minute=0)
async def cleanup_old_aggregates():
    cutoff_date = date.today() - timedelta(days=settings.sentiment_retention_days)
    await db.soft_delete_aggregates_before(cutoff_date)
```

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/unit/test_tool_detector.py

def test_detect_copilot_mention():
    detector = ToolDetector()
    mentions = detector.detect_tools("I love GitHub Copilot!")
    assert len(mentions) == 1
    assert mentions[0].tool_name == "GitHub Copilot"
    assert mentions[0].confidence >= 0.9

def test_case_insensitive_detection():
    detector = ToolDetector()
    mentions = detector.detect_tools("copilot is great")
    assert len(mentions) == 1
```

### Integration Tests

```python
# backend/tests/integration/test_tool_api.py

@pytest.mark.asyncio
async def test_get_tool_sentiment_endpoint(client, db):
    # Seed database with test data
    tool = await db.create_tool(name="TestTool", status="approved")
    await db.create_aggregates(tool.id, test_data)
    
    # Call API
    response = await client.get(f"/api/v1/tools/{tool.id}/sentiment?hours=720")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "TestTool"
    assert data["statistics"]["total_mentions"] > 0
```

### Frontend Component Tests

```tsx
// frontend/tests/components/ToolSentimentCard.test.tsx

import { render, screen } from '@testing-library/react';

test('renders tool sentiment breakdown', async () => {
  const mockData = {
    tool_name: "GitHub Copilot",
    statistics: { positive: { count: 750, percentage: 60 }, ... }
  };
  
  render(<ToolSentimentCard toolId="test-id" />);
  
  await waitFor(() => {
    expect(screen.getByText("GitHub Copilot")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument(); // positive percentage
  });
});
```

---

## Configuration

### Environment Variables

```bash
# backend/.env

# Data retention (days)
SENTIMENT_RETENTION_DAYS=90

# Tool detection threshold
TOOL_DETECTION_THRESHOLD=50

# Auto-detection time window (days)
TOOL_DETECTION_WINDOW_DAYS=7

# Admin authentication (if implementing auth)
ADMIN_JWT_SECRET=your-secret-key
```

### Frontend Config

```typescript
// frontend/src/config.ts

export const config = {
  apiBaseUrl: process.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  pollInterval: 60000, // 60 seconds
  defaultTimeRange: 720, // 30 days in hours
  maxToolsToCompare: 5,
};
```

---

## Deployment Checklist

- [ ] Backend: Create CosmosDB containers (ai_tools, tool_mentions, time_period_aggregates)
- [ ] Backend: Seed initial tools (Copilot, Jules) with status="approved"
- [ ] Backend: Run historical data backfill script
- [ ] Backend: Start aggregation job for last 90 days
- [ ] Backend: Configure retention policy (SENTIMENT_RETENTION_DAYS)
- [ ] Frontend: Install new dependencies (recharts, react-query)
- [ ] Frontend: Add new routes to dashboard
- [ ] Verify: P1 endpoints return < 2s (SC-001)
- [ ] Verify: Time series queries < 3s (SC-007)
- [ ] Verify: Admin approval workflow functional
- [ ] Documentation: Update API docs with new endpoints

---

## Troubleshooting

### Issue: Sentiment values all zero

**Cause**: Aggregates not computed or tool mentions not detected

**Solution**:

```bash
# Check if tool detection is running
curl http://localhost:8000/api/v1/tools

# Manually trigger aggregation
python scripts/compute_aggregates.py --tool-id <uuid> --date 2025-10-20
```

### Issue: Time series chart not loading

**Cause**: Date range exceeds 90-day retention or no data for period

**Solution**:
- Check date range is within last 90 days
- Verify aggregates exist: `SELECT * FROM time_period_aggregates WHERE tool_id = '...' AND date >= '...'`

### Issue: Tool detection creates false positives

**Cause**: Low confidence threshold or overly broad aliases

**Solution**:
- Increase confidence threshold in tool_detector.py
- Refine tool aliases to be more specific
- Review and reject false positives via admin interface

---

## Next Steps After Implementation

1. **Monitor Performance**: Track query execution times, ensure SC-001 and SC-007 are met
2. **Tune Detection**: Adjust confidence thresholds based on false positive rate (target < 10%)
3. **User Feedback**: Gather input on comparison view, time series granularity
4. **Expand Tools**: Add more AI tools beyond Copilot and Jules as they gain popularity
5. **Long-term Retention**: If storage budget allows, extend retention beyond 90 days

---

## Resources

- **Specification**: `specs/008-dashboard-ui-with/spec.md`
- **Data Model**: `specs/008-dashboard-ui-with/data-model.md`
- **API Contract**: `specs/008-dashboard-ui-with/contracts/openapi.yaml`
- **Research Decisions**: `specs/008-dashboard-ui-with/research.md`
- **Recharts Docs**: https://recharts.org/
- **React Query Docs**: https://tanstack.com/query/latest/docs/react/overview
