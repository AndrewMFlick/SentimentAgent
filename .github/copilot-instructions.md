# SentimentAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-15

## Active Technologies
- Python 3.13.3 (backend), TypeScript 5.3.3 (frontend) + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, React 18.2.0, TailwindCSS 3.4+, Pydantic 2.x (011-the-admin-section)
- Azure Cosmos DB (SQL API) - Tools and ToolAliases containers already exis (011-the-admin-section)
- Python 3.13.3 + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, APScheduler 3.10.4, Pydantic 2.x, structlog 24.1.0 (013-admin-feature-to)
- Azure CosmosDB (SQL API) - sentiment_scores, Tools, ToolAliases collections; ReanalysisJobs collection (NEW) (013-admin-feature-to)
- Azure Cosmos DB (SQL API) - emulator on localhost:8081, production on Azure (017-pre-cached-sentiment)

- Python 3.13.3 + Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, structlog 24.1.0 (004-fix-the-cosmosdb)
- Azure CosmosDB (PostgreSQL mode emulator on localhost:8081, production on Azure) (004-fix-the-cosmosdb)
- Python 3.13.3 + Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, pytest 8.0.0, structlog 24.1.0 (005-fix-cosmosdb-sql)
- Python 3.13.3 (backend), TypeScript 5.3.3/React 18.2.0 (frontend) (008-dashboard-ui-with)
- **TailwindCSS 3.4+, PostCSS 8+, Vite 5.1.0 (frontend glass UI)** (009-glass-ui-redesign)
- Python 3.13.3 + FastAPI 0.109.2, PRAW 7.7.1 (synchronous), uvicorn 0.27.1, APScheduler 3.10.4, Azure Cosmos SDK 4.5.1, psutil (002-the-performance-is, 003-backend-stability-and-data-loading)

## Project Structure

```text
backend/
├── src/
│   ├── main.py           # FastAPI app with lifespan management
│   ├── config.py         # pydantic-settings configuration
│   ├── models/           # Pydantic data models
│   ├── services/         # Business logic (database, scheduler, health)
│   └── api/              # FastAPI routes
└── tests/
    ├── unit/             # Unit tests
    └── integration/      # Integration tests (including stability tests)

frontend/
├── tailwind.config.js    # TailwindCSS configuration
├── postcss.config.js     # PostCSS setup
├── src/
│   ├── components/       # React components (glass morphism design)
│   ├── services/         # API client
│   └── index.css         # Tailwind directives + glass utilities
```

## Commands

```bash
# Start backend (development with auto-reload)
cd backend
./start.sh

# Run tests
pytest backend/tests/

# Check backend health
curl http://localhost:8000/health

# Lint code
ruff check backend/src/

# Start frontend
cd frontend
npm run dev
```

## Code Style

**Python 3.13.3**: Follow standard PEP 8 conventions

- Use type hints for all functions
- Async functions for I/O operations (database, HTTP)
- Pydantic models for data validation
- Structured logging with context

**TypeScript/React 18.2.0 + TailwindCSS 3.4+**: Modern frontend patterns

- No inline styles (`style={{}}`) - use TailwindCSS utility classes
- Glass morphism design: `bg-white/5 backdrop-blur-md border-white/10`
- Semantic color classes: `text-positive` (emerald), `text-negative` (red), `text-neutral` (gray)
- Responsive design: Mobile-first (`md:`, `lg:` breakpoints)
- Accessibility: WCAG 2.1 AA contrast, focus rings on all interactive elements

**TailwindCSS Best Practices**:

```tsx
// Good: Utility classes
<div className="glass-card p-6 hover:scale-105 transition-transform">

// Bad: Inline styles
<div style={{ padding: '24px', backgroundColor: '#1a1a1a' }}>

// Glass card pattern
<div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-xl shadow-glass">

// Sentiment indicators
<span className="sentiment-indicator sentiment-positive">Positive</span>
```

**Error Handling Pattern**:

```python
# Background jobs: Catch-log-continue
async def collect_data_job():
    for subreddit in subreddits:
        try:
            await collect(subreddit)
        except Exception as e:
            logger.error(f"Failed to collect {subreddit}: {e}", exc_info=True)
            # Continue to next subreddit

# Startup: Fail-fast
async def startup():
    try:
        await db.connect()
    except Exception as e:
        logger.critical(f"DB connection failed: {e}")
        raise  # Crash immediately
```

**Process Lifecycle Pattern**:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.connect()
    scheduler.start()
    asyncio.create_task(load_recent_data())  # Background, non-blocking
    yield
    # Shutdown
    scheduler.shutdown(wait=True)
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
```

## Recent Changes
- 017-pre-cached-sentiment: Added Python 3.13.3 + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, APScheduler 3.10.4, Pydantic 2.x, structlog 24.1.0
- 013-admin-feature-to: Added Python 3.13.3 + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, APScheduler 3.10.4, Pydantic 2.x, structlog 24.1.0
- 012-hot-topics-isn: Added Hot Topics dashboard with engagement scoring, related posts API, timeline filtering, Load More pagination


## Admin Tool Management Patterns (Feature 010)

**Service Layer Architecture**:

```python
# ToolService handles all business logic
class ToolService:
    def __init__(self, tools_container, aliases_container):
        self.tools_container = tools_container
        self.aliases_container = aliases_container
    
    async def create_tool(self, tool_data: ToolCreateRequest):
        # 1. Validate duplicate names
        # 2. Generate slug from name
        # 3. Create with default status='active'
        # 4. Log operation
    
    async def create_alias(self, alias_tool_id, primary_tool_id, created_by):
        # 1. Validate both tools exist
        # 2. Prevent self-reference
        # 3. Check circular aliases
        # 4. Create alias relationship
```

**Admin API Patterns**:

```python
# Dependency injection for ToolService
async def get_tool_service() -> ToolService:
    tools_container = db.database.get_container_client("Tools")
    aliases_container = db.database.get_container_client("ToolAliases")
    return ToolService(tools_container, aliases_container)

# Endpoint with authentication
@router.post("/admin/tools")
async def create_tool(
    tool_data: ToolCreateRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    admin_user = verify_admin(x_admin_token)
    try:
        tool = await tool_service.create_tool(tool_data)
        logger.info("Tool created", tool_id=tool["id"], admin=admin_user)
        return {"tool": tool, "message": "Tool created successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create tool", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create tool")
```

**Frontend Admin Components**:

```tsx
// Admin tool management component
export default function AdminToolManagement() {
  const [formData, setFormData] = useState<ToolCreateRequest>({
    name: '',
    vendor: '',
    category: ToolCategory.CODE_ASSISTANT
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await api.createTool(formData, adminToken);
      toast.success(result.message);
      // Invalidate cache and refresh list
      queryClient.invalidateQueries(['tools']);
    } catch (error) {
      toast.error(error.message);
    }
  };
  
  return (
    <div className="glass-card p-6">
      <form onSubmit={handleSubmit}>
        {/* Form fields with validation */}
      </form>
    </div>
  );
}
```

**Alias Management Best Practices**:

- Always validate for self-reference (`alias_tool_id !== primary_tool_id`)
- Check circular aliases before creating (traverse alias chain)
- Use soft delete for tools with sentiment data
- Resolve aliases in sentiment aggregation queries
- Visual indicators in UI for alias relationships (`Tool A → Tool B`)

**Testing Patterns**:

```python
# Unit tests with async mocks
@pytest.mark.asyncio
async def test_create_alias_circular_detection(tool_service, mock_containers):
    # Mock existing alias chain
    async def alias_iter():
        yield {"alias_tool_id": "b", "primary_tool_id": "a"}
    aliases_container.query_items.return_value = alias_iter()
    
    # Try to create circular alias
    with pytest.raises(ValueError, match="Circular alias"):
        await tool_service.create_alias("a", "b", "admin")
```


<!-- MANUAL ADDITIONS START -->

## Admin Tool Management Patterns (Phase 7-8)

**Tool Merge Operations**:

```python
# Merge tools with full audit trail
async def merge_tools(
    self,
    target_tool_id: str,
    source_tool_ids: List[str],
    target_categories: List[str],
    target_vendor: str,
    merged_by: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    # 1. Validate merge prerequisites
    target_tool, source_tools, warnings = await self._validate_merge(
        target_tool_id, source_tool_ids
    )
    
    # 2. Migrate sentiment data with source attribution
    sentiment_count = await self._migrate_sentiment_data(
        source_tool_ids, target_tool_id
    )
    
    # 3. Update target tool metadata
    target_tool["categories"] = target_categories
    target_tool["vendor"] = target_vendor
    
    # 4. Archive source tools with merged_into reference
    for source_tool in source_tools:
        source_tool["status"] = "archived"
        source_tool["merged_into"] = target_tool_id
    
    # 5. Create merge record for audit trail
    merge_record = {
        "id": f"merge-{uuid.uuid4()}",
        "target_tool_id": target_tool_id,
        "source_tool_ids": source_tool_ids,
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "merged_by": merged_by,
        "sentiment_count": sentiment_count,
        "notes": notes
    }
    
    # 6. Log admin action
    await self._log_admin_action(...)
    
    return {
        "merge_record": merge_record,
        "target_tool": target_tool,
        "archived_tools": source_tools,
        "warnings": warnings
    }
```

**Modal Components with Keyboard Shortcuts**:

```tsx
// All modals should support Esc to close
useEffect(() => {
  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && !isSubmitting) {
      onClose();
    }
  };

  if (isOpen) {
    document.addEventListener('keydown', handleEsc);
  }

  return () => {
    document.removeEventListener('keydown', handleEsc);
  };
}, [isOpen, isSubmitting, onClose]);
```

**Loading States with Skeletons**:

```tsx
// Use skeletons instead of spinners for better UX
if (isLoading && data.length === 0) {
  return <ToolTableSkeleton rows={5} />;
}

// Overlay spinner for subsequent loads
if (isLoading && data.length > 0) {
  return <LoadingOverlay />;
}
```

**Error Boundaries**:

```tsx
// Wrap app in ErrorBoundary
<ErrorBoundary>
  <Router>
    <App />
  </Router>
</ErrorBoundary>

// Custom fallback UI
<ErrorBoundary fallback={<CustomErrorUI />}>
  <AdminPanel />
</ErrorBoundary>
```

**React Query Patterns**:

```tsx
// Always invalidate cache after mutations
const mutation = useMutation({
  mutationFn: api.mergeTool,
  onSuccess: () => {
    queryClient.invalidateQueries(['tools']);
    queryClient.invalidateQueries(['merge-history']);
    toast.success('Tools merged successfully');
  },
  onError: (error) => {
    toast.error(error.message);
  }
});
```

**Audit Logging Best Practices**:

- Log all admin actions (create, edit, delete, archive, merge)
- Include before/after states for edit operations
- Store IP address and user agent for security
- Use structured logging with consistent fields
- Create separate audit records for complex operations (merges)

**Performance Monitoring**:

```python
# Log slow queries
import time

async def query_with_monitoring(query: str, container):
    start = time.time()
    try:
        result = await container.query_items(query)
        return result
    finally:
        duration = time.time() - start
        if duration > 3.0:
            logger.warning(
                "Slow query detected",
                query=query,
                duration=duration,
                container=container.id
            )
```

<!-- MANUAL ADDITIONS END -->

## Sentiment Cache Patterns (Feature 017)

**Pre-Cached Sentiment Analysis**: 10x performance improvement for sentiment queries

### Cache Service Architecture

```python
# backend/src/services/cache_service.py
class CacheService:
    def __init__(
        self,
        cache_container: ContainerProxy,
        sentiment_container: ContainerProxy,
        tools_container: ContainerProxy
    ):
        self.cache_container = cache_container
        self.sentiment_container = sentiment_container
        self.tools_container = tools_container
        self.cache_enabled = settings.enable_sentiment_cache
        self.cache_ttl_minutes = settings.cache_ttl_minutes
    
    async def get_cached_sentiment(
        self,
        tool_id: str,
        hours: int
    ) -> dict:
        """Main entry point: lookup cache or calculate on-demand."""
        # 1. Map hours to standard period (1h, 24h, 7d, 30d)
        period = self._map_hours_to_period(hours)
        if not period:
            # Non-standard period: calculate on-demand (no cache)
            return await self._calculate_sentiment_aggregate(tool_id, hours)
        
        # 2. Try cache lookup
        cache_entry = await self._lookup_cache(tool_id, period)
        if cache_entry and self._is_cache_fresh(cache_entry):
            return cache_entry  # Cache hit
        
        # 3. Cache miss: calculate and populate
        result = await self._calculate_sentiment_aggregate(tool_id, hours)
        await self._save_to_cache(result, period)
        return result
```

### Standard Cache Periods

```python
# Only these periods are pre-cached:
CachePeriod.HOUR_1 = 1     # 1 hour
CachePeriod.HOUR_24 = 24   # 24 hours (most common)
CachePeriod.DAY_7 = 168    # 7 days
CachePeriod.DAY_30 = 720   # 30 days

# Non-standard periods (e.g., 48h, 72h) fall back to on-demand calculation
```

### Cache Data Model

```python
# backend/src/models/cache.py
class SentimentCacheEntry(BaseModel):
    id: str  # "{tool_id}:{period}"
    tool_id: str  # Partition key
    period: CachePeriod
    total_mentions: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    average_sentiment: float
    last_updated_ts: int  # Unix timestamp
    period_start_ts: int
    period_end_ts: int
```

### Background Refresh Pattern

```python
# Scheduled job (APScheduler) refreshes all tools every 15 minutes
async def refresh_all_tools():
    tool_ids = await self._get_active_tool_ids()
    
    for tool_id in tool_ids:
        try:
            # Refresh all 4 periods for this tool
            await self._refresh_tool_cache(tool_id)
        except Exception as e:
            logger.error("Failed to refresh tool", tool_id=tool_id, error=str(e))
            # Continue processing other tools (error isolation)
            continue
    
    # Update cache metadata
    await self.update_cache_metadata(...)

# Refresh a single tool (all 4 periods)
async def _refresh_tool_cache(self, tool_id: str):
    periods = [
        (1, CachePeriod.HOUR_1),
        (24, CachePeriod.HOUR_24),
        (168, CachePeriod.DAY_7),
        (720, CachePeriod.DAY_30)
    ]
    
    for hours, period in periods:
        result = await self._calculate_sentiment_aggregate(tool_id, hours)
        await self._save_to_cache(result, period)
```

### Cache Invalidation

```python
# Invalidate cache after data changes
async def invalidate_tool_cache(self, tool_id: str):
    """Delete all cache entries for a tool.
    
    Called after:
    - Reanalysis job completion (new tool associations)
    - Tool merge (sentiment data migrated)
    - Manual admin cache clear
    """
    periods = [
        CachePeriod.HOUR_1,
        CachePeriod.HOUR_24,
        CachePeriod.DAY_7,
        CachePeriod.DAY_30
    ]
    
    for period in periods:
        cache_id = self._calculate_cache_key(tool_id, period)
        try:
            await self.cache_container.delete_item(
                item=cache_id,
                partition_key=tool_id
            )
        except CosmosResourceNotFoundError:
            pass  # Already deleted
```

### API Response Headers

```python
# Add cache metadata to sentiment API responses
@router.get("/tools/{tool_id}/sentiment")
async def get_tool_sentiment(...):
    result = await cache_service.get_cached_sentiment(tool_id, hours)
    
    # Add cache headers
    headers = {
        "X-Cache-Status": "HIT" if result["is_cached"] else "MISS",
        "X-Cache-Age": str(result.get("cache_age_minutes", 0))
    }
    
    return JSONResponse(content=result, headers=headers)
```

### Cache Health Monitoring

```python
# Public health endpoint
@router.get("/cache/health")
async def cache_health():
    metadata = await cache_service.get_cache_metadata()
    
    return {
        "status": "healthy",  # healthy | degraded | unhealthy
        "cache_enabled": settings.enable_sentiment_cache,
        "total_entries": metadata.total_entries,
        "last_refresh_at": metadata.last_refresh_at,
        "last_refresh_duration_ms": metadata.last_refresh_duration_ms,
        "cache_hit_rate_24h": metadata.cache_hit_rate,
        "oldest_entry_age_minutes": metadata.oldest_entry_age_minutes
    }
```

### Performance Best Practices

1. **Always use standard periods** (1h, 24h, 7d, 30d) for cached responses
2. **Non-standard periods** calculate on-demand (slower but still <2s)
3. **Cache TTL**: 30 minutes (configurable)
4. **Refresh interval**: 15 minutes (ensures cache always fresh)
5. **Error isolation**: Individual tool failures don't stop refresh job

### Security Considerations

- ✅ **No PII**: Cache contains only aggregate counts
- ✅ **Read-only for users**: Only backend service can write to cache
- ✅ **Admin invalidation**: Requires authentication token
- ✅ **Parameterized queries**: No SQL injection risk
- ✅ **Bounded size**: 4 entries per tool (DoS protection)

### Testing Patterns

```python
# Unit test: Cache hit scenario
@pytest.mark.asyncio
async def test_get_cached_sentiment_cache_hit():
    # Mock fresh cache entry
    cache_entry = {
        "id": "tool-id:HOUR_24",
        "tool_id": "tool-id",
        "period": "HOUR_24",
        "total_mentions": 100,
        "positive_count": 60,
        "last_updated_ts": now_ts - 300  # 5 minutes ago (fresh)
    }
    cache_container.read_item.return_value = cache_entry
    
    # Execute
    result = await cache_service.get_cached_sentiment("tool-id", 24)
    
    # Verify cache hit
    assert result["is_cached"] is True
    assert result["total_mentions"] == 100

# Unit test: Cache miss with fallback
@pytest.mark.asyncio
async def test_get_cached_sentiment_cache_miss():
    # Mock cache miss
    cache_container.read_item.side_effect = CosmosResourceNotFoundError()
    
    # Mock sentiment data for calculation
    async def mock_query():
        for i in range(50):
            yield {"sentiment_label": "positive", "sentiment_score": 0.7}
    sentiment_container.query_items = mock_query
    
    # Execute
    result = await cache_service.get_cached_sentiment("tool-id", 24)
    
    # Verify on-demand calculation
    assert result["is_cached"] is False
    assert result["total_mentions"] == 50
```

### Configuration

```python
# backend/src/config.py
class Settings(BaseSettings):
    # Cache feature flag
    enable_sentiment_cache: bool = True
    
    # Refresh job frequency (minutes)
    cache_refresh_interval_minutes: int = 15
    
    # Cache TTL - data older than this is stale
    cache_ttl_minutes: int = 30
    
    # Cosmos DB container
    cosmos_container_sentiment_cache: str = "sentiment_cache"
```

### Troubleshooting

**High cache miss rate**:
- Check if refresh job is running: `curl /api/v1/cache/health`
- Verify cache container exists in Cosmos DB
- Check logs for refresh failures

**Stale data**:
- Invalidate cache: `POST /api/v1/admin/cache/invalidate/all`
- Verify TTL is not too long (default: 30 minutes)
- Check if refresh job is scheduled (every 15 minutes)

**Slow queries despite cache**:
- Verify using standard periods (1, 24, 168, 720)
- Check cache status in response headers: `X-Cache-Status: HIT`
- Non-standard periods (e.g., 48h) always calculate on-demand

### References

- **Architecture**: `docs/cache-architecture.md`
- **Security Review**: `docs/cache-security-review.md`
- **Specification**: `specs/017-pre-cached-sentiment/spec.md`
- **Implementation**: `backend/src/services/cache_service.py`
- **Tests**: `backend/tests/unit/test_cache_service.py`



