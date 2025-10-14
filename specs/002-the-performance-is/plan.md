# Implementation Plan: Asynchronous Data Collection

**Branch**: `002-the-performance-is` | **Date**: October 14, 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-the-performance-is/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The feature addresses blocking I/O during Reddit data collection that freezes the API and dashboard. The system currently uses synchronous PRAW library calls within an async FastAPI application, causing all HTTP requests to hang when collection runs. The solution will isolate blocking operations from the async event loop while maintaining data integrity and collection functionality.

## Technical Context

**Language/Version**: Python 3.13.3  
**Primary Dependencies**: FastAPI 0.109.2, PRAW 7.7.1 (synchronous), uvicorn 0.27.1, APScheduler 3.10.4, Azure Cosmos SDK 4.5.1  
**Storage**: Azure CosmosDB (PGSQL server mode) via HTTP endpoint  
**Testing**: pytest (current), needs async test support  
**Target Platform**: macOS/Linux server (Docker deployment ready)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: API response <3s during collection, health endpoint <1s, startup <10s  
**Constraints**: Must preserve 100% collection success rate (0 errors), maintain 30-min intervals, support 14 subreddits with 700+ posts and 4000+ comments per cycle  
**Scale/Scope**: Single backend service, 14 subreddit sources, ~5000 items per collection cycle, background scheduler with concurrent API handling

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASSED (with justification)

| Check | Status | Notes |
|-------|--------|-------|
| No implementation leakage in spec | ✅ Pass | Spec focuses on performance outcomes, not async implementation details |
| Test-first approach | ✅ Pass | Will write performance tests before implementation |
| Complexity justified | ⚠️ Requires justification | Using ThreadPoolExecutor + asyncio integration adds complexity |
| Data integrity preserved | ✅ Pass | No schema changes, maintains existing collection logic |
| Dependencies minimized | ✅ Pass | No new external dependencies required |

**Complexity Justification**: ThreadPoolExecutor integration necessary because:

- PRAW library is synchronous-only (no async version available)
- FastAPI/uvicorn requires async event loop for HTTP handling
- Direct thread pool execution is simpler than alternatives (multiprocessing overhead, custom async wrapper, replacing PRAW entirely)
- Standard library solution (concurrent.futures) vs third-party async Reddit clients

## Project Structure

### Documentation (this feature)

```text
specs/002-the-performance-is/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # Existing: RedditPost, SentimentScore, DataCollectionCycle
│   ├── services/        # MODIFIED: scheduler.py, reddit_collector.py
│   │   ├── scheduler.py          # Add async wrapper for blocking operations
│   │   ├── reddit_collector.py   # Remains synchronous, wrapped by scheduler
│   │   ├── sentiment_analyzer.py # Remains synchronous, wrapped by scheduler
│   │   └── database.py           # Remains as-is (already has async methods)
│   ├── api/            # Remains as-is (already async)
│   └── main.py         # Minimal changes to lifespan management
└── tests/
    ├── integration/    # NEW: async collection tests
    ├── performance/    # NEW: load testing during collection
    └── unit/          # Existing unit tests remain

frontend/              # No changes required
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/
```

**Structure Decision**: Web application with backend modifications only. Frontend remains unchanged as API contracts are preserved. Testing structure expanded to include performance validation and async integration tests.

## Complexity Tracking

### Justified Complexity

| Complexity Added | Why Needed | Simpler Alternative Rejected Because |
|------------------|------------|-------------------------------------|
| ThreadPoolExecutor integration | Isolate synchronous PRAW calls from async event loop | Multiprocessing: excessive overhead for I/O-bound tasks; Async PRAW wrapper: not available/maintained; Replacing PRAW: significant rewrite risk |
| Delayed initial collection | Allow app startup before first collection | Immediate collection: blocks lifespan startup, delays API availability beyond 10s requirement |
| Async wrapper methods | Bridge sync collection code with async scheduler | Blocking asyncio.run(): defeats purpose; Background threads without coordination: race conditions in scheduler state |

## Phase 0: Research ✅ COMPLETE

**Output**: [research.md](research.md)

**Key Decisions**:

1. **Async/Sync Integration**: Use `asyncio.get_event_loop().run_in_executor()` with ThreadPoolExecutor
2. **Scheduler Pattern**: AsyncIOScheduler with delayed initial job execution
3. **Testing Strategy**: pytest-asyncio for unit/integration, locust for load testing
4. **Thread Pool Sizing**: Single worker (max_workers=1) for sequential collection
5. **Error Handling**: Preserve existing sync error handling, add async wrapper logging

**Rationale**: All decisions favor minimal code changes, standard library solutions, and preservation of existing data flow.

## Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**:

- [data-model.md](data-model.md) - No schema changes required
- [contracts/api-contracts.md](contracts/api-contracts.md) - No API changes, only performance improvements
- [quickstart.md](quickstart.md) - Developer and user guide
- `.github/copilot-instructions.md` - Updated with Python 3.13.3 + dependencies

**Key Findings**:

- **No breaking changes**: All API contracts preserved
- **No new entities**: Execution model changes only
- **Zero infrastructure changes**: Same Docker, database, deployment
- **100% backward compatible**: Existing clients work without modification

**Constitution Re-Check**: ✅ PASSED

- No implementation leakage (spec remains technology-agnostic)
- Complexity justified (ThreadPoolExecutor necessary for sync/async bridge)
- Data integrity maintained (no schema changes)
- Test-first approach planned (pytest-asyncio + locust)

## Phase 2: Tasks

**Status**: NOT STARTED (requires `/speckit.tasks` command)

This phase will break down implementation into atomic tasks for development. Run `/speckit.tasks` to generate `tasks.md` with specific implementation steps, test cases, and acceptance criteria.

## Next Steps

1. **Run** `/speckit.tasks` to generate implementation task breakdown
2. **Review** tasks.md for development workflow
3. **Begin** with test-first approach (async integration tests)
4. **Implement** ThreadPoolExecutor wrapper in scheduler.py
5. **Validate** with load tests (locust) and performance benchmarks
