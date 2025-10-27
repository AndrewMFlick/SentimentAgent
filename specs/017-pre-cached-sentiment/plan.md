# Implementation Plan: Pre-Cached Sentiment Analysis

**Branch**: `017-pre-cached-sentiment` | **Date**: October 27, 2025 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/017-pre-cached-sentiment/spec.md`

## Summary

This feature addresses severe performance issues with tool sentiment queries (24-hour queries taking 10+ seconds). The solution implements a pre-cached sentiment aggregation system that:

1. Pre-calculates sentiment aggregates for standard time periods (1h, 24h, 7d, 30d)
2. Stores results in a new `sentiment_cache` Cosmos DB container
3. Automatically refreshes cache every 15 minutes via APScheduler background job
4. Serves 95%+ of requests from cache (<1 second response time)
5. Falls back to on-demand calculation on cache miss
6. Invalidates cache when reanalysis modifies sentiment data

**Performance Impact**: 24-hour queries drop from 10.57s to <1s (10x improvement).

## Technical Context

**Language/Version**: Python 3.13.3  
**Primary Dependencies**: FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, APScheduler 3.10.4, Pydantic 2.x, structlog 24.1.0  
**Storage**: Azure Cosmos DB (SQL API) - emulator on localhost:8081, production on Azure  
**Testing**: pytest 8.0.0 with async support, coverage via pytest-cov  
**Target Platform**: Linux/macOS server (development), Azure Container Instances (production)  
**Project Type**: Web application (backend API + frontend UI)  
**Performance Goals**: 
- 24-hour sentiment queries: <1 second (down from 10.57s)
- Cache hit rate: >95%
- Background refresh: <30 seconds for all tools
- Cache lookup: <50ms

**Constraints**:
- Cosmos DB emulator limitations: No ARRAY_CONTAINS, EXISTS, JOIN, CASE WHEN support
- Must use timestamp queries with `_ts` field and `_datetime_to_timestamp()` helper (Feature 004 pattern)
- Data freshness: 15-minute max staleness acceptable
- Storage: Minimal overhead (~30 KB for cache)

**Scale/Scope**:
- Active tools: ~15 (Jules AI, Cursor, GitHub Copilot, etc.)
- Cache entries: ~60 (15 tools × 4 time periods)
- Sentiment scores: 34K+ documents (growing)
- Time periods: 1-hour, 24-hour, 7-day, 30-day
- API requests: 100-1000/day (dashboard usage)

**Existing Architecture**:
- Database: `sentiment_analysis` database with containers: `sentiment_scores`, `Tools`, `ToolAliases`, `ReanalysisJobs`
- Scheduler: APScheduler with jobs: data collection (30 min), cleanup (24h), trending (1h), daily aggregation (00:05 UTC)
- Services: DatabaseService, ReanalysisService, HotTopicsService, ToolService
- Current bottleneck: `get_tool_sentiment()` loads 9K+ documents for 24-hour queries, filters in Python

## Constitution Check

*No formal constitution defined. Using project best practices from `.github/copilot-instructions.md`.*

### ✅ Code Style & Architecture

- **Async Functions**: All I/O operations use async/await ✅
- **Type Hints**: All functions have type annotations ✅
- **Pydantic Models**: Data validation via Pydantic ✅
- **Structured Logging**: contextual logging with structlog ✅
- **Error Handling**: Catch-log-continue for background jobs, fail-fast for startup ✅

### ✅ Testing Requirements

- **Unit Tests**: Test service logic in isolation ✅
- **Integration Tests**: Test cache + database interaction ✅
- **Performance Tests**: Verify <1s response time target ✅

### ✅ Process Lifecycle

- **Lifespan Management**: FastAPI lifespan context manager ✅
- **Graceful Shutdown**: APScheduler shutdown with wait=True ✅
- **Background Jobs**: Non-blocking cache refresh ✅

### ✅ No Violations

All patterns align with existing project architecture. No complexity justification needed.

## Project Structure

### Documentation (this feature)

```text
specs/017-pre-cached-sentiment/
├── spec.md              # Feature specification ✅
├── plan.md              # This file (implementation plan) ✅
├── research.md          # Phase 0: Technical decisions ✅
├── data-model.md        # Phase 1: Entity definitions ✅
├── quickstart.md        # Phase 1: Developer guide ✅
├── contracts/           # Phase 1: API contracts ✅
│   └── api.yaml         # OpenAPI specification
└── checklists/          # Validation
    └── requirements.md  # Spec quality checklist ✅
```

### Source Code (repository root)

**Structure Decision**: Web application (backend + frontend)

```text
backend/
├── src/
│   ├── models/
│   │   └── cache.py                    # NEW: SentimentCacheEntry, CacheMetadata models
│   ├── services/
│   │   ├── cache_service.py            # NEW: Core cache logic
│   │   ├── database.py                 # MODIFIED: Add cache lookups
│   │   └── scheduler.py                # MODIFIED: Add cache refresh job
│   ├── api/
│   │   └── tools.py                    # MODIFIED: Add cache headers
│   └── main.py                         # MODIFIED: Add /cache/health endpoint
├── scripts/
│   └── create_cache_container.py       # NEW: Setup script
└── tests/
    ├── unit/
    │   └── test_cache_service.py       # NEW: Cache logic tests
    ├── integration/
    │   └── test_cache_integration.py   # NEW: End-to-end cache tests
    └── performance/
        └── test_cache_performance.py   # NEW: Performance benchmarks

frontend/
├── src/
│   ├── components/
│   │   └── CacheStatusIndicator.tsx   # NEW: Show cache freshness
│   └── services/
│       └── api.ts                      # MODIFIED: Handle X-Cache-Status headers
```

## Complexity Tracking

**No violations** - all patterns align with existing project architecture.
