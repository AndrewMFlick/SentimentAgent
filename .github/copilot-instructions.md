# SentimentAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-15

## Active Technologies
- Python 3.13.3 (backend), TypeScript 5.3.3 (frontend) + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, React 18.2.0, TailwindCSS 3.4+, Pydantic 2.x (011-the-admin-section)
- Azure Cosmos DB (SQL API) - Tools and ToolAliases containers already exis (011-the-admin-section)

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
- 011-the-admin-section: Added Python 3.13.3 (backend), TypeScript 5.3.3 (frontend) + FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, React 18.2.0, TailwindCSS 3.4+, Pydantic 2.x

- 010-admin-tool-management: Added admin tool CRUD operations, alias linking, tool management dashboard
- 009-glass-ui-redesign: Added TailwindCSS 3.4+, PostCSS 8+, glass morphism design system

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
<!-- MANUAL ADDITIONS END -->
