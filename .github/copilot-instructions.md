# SentimentAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-15

## Active Technologies

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

- 009-glass-ui-redesign: Added TailwindCSS 3.4+, PostCSS 8+, glass morphism design system
- 008-dashboard-ui-with: Added Python 3.13.3 (backend), TypeScript 5.3.3/React 18.2.0 (frontend)
- 005-fix-cosmosdb-sql: Added Python 3.13.3 + Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, pytest 8.0.0, structlog 24.1.0
- 004-fix-the-cosmosdb: Added Python 3.13.3 + Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, structlog 24.1.0


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
