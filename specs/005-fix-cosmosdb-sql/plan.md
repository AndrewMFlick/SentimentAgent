# Implementation Plan: Fix CosmosDB SQL Aggregation for Sentiment Statistics

**Branch**: `005-fix-cosmosdb-sql` | **Date**: October 20, 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-fix-cosmosdb-sql/spec.md`
**Related Issue**: [#15](https://github.com/AndrewMFlick/SentimentAgent/issues/15)

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Fix the `get_sentiment_stats()` method in `backend/src/services/database.py` which currently uses CosmosDB-incompatible `CASE WHEN` SQL syntax, causing it to return zero values instead of accurate sentiment aggregation statistics. Replace with CosmosDB-compatible separate COUNT queries to provide accurate positive/negative/neutral sentiment counts and average compound scores for the specified time window.

## Technical Context

**Language/Version**: Python 3.13.3  
**Primary Dependencies**: Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, pytest 8.0.0, structlog 24.1.0  
**Storage**: Azure CosmosDB (PostgreSQL mode emulator on localhost:8081, production on Azure)  
**Testing**: pytest with pytest-asyncio for integration tests  
**Target Platform**: Linux/macOS server (Docker-compatible)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: < 2 seconds query time for 1-week time windows  
**Constraints**: Must use CosmosDB-compatible SQL syntax (no CASE WHEN support), maintain Unix timestamp datetime filtering from Feature #004  
**Scale/Scope**: Affects single method `get_sentiment_stats()` in existing codebase, must maintain backward compatibility with existing API contract

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASSED - No constitution file exists yet for this project

This is a bug fix within existing code structure. No new architectural patterns or complexity added. The fix:

- Modifies existing method `get_sentiment_stats()` in `backend/src/services/database.py`
- Maintains existing API contract (no breaking changes)
- Uses established testing patterns (integration tests already exist)
- Follows existing error handling patterns (catch-log-return defaults)

No constitution violations as no constitution has been established for this project.

## Project Structure

## Project Structure

### Documentation (this feature)

```text
specs/005-fix-cosmosdb-sql/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   └── api.md          # API contract documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # Pydantic data models (no changes needed)
│   ├── services/
│   │   └── database.py  # TARGET: Fix get_sentiment_stats() method (lines 338-375)
│   └── api/
│       └── routes.py    # API endpoint (no changes needed - uses database method)
└── tests/
    ├── integration/
    │   └── test_datetime_queries.py  # UPDATE: Add tests for accurate aggregation
    └── unit/
        └── test_database.py          # ADD: Unit tests for query logic

frontend/
└── src/                 # No changes needed (consumes API)
```

**Structure Decision**: Web application structure (backend + frontend). This is a backend-only fix affecting the `database.py` service layer. No frontend changes required since the API contract remains unchanged (same request/response format).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
