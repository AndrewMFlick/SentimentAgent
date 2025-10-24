# Implementation Plan: Admin Sentiment Reanalysis & Tool Categorization

**Branch**: `013-admin-feature-to` | **Date**: 2025-10-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-admin-feature-to/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature enables admins to rerun sentiment analysis on existing Reddit data to backfill tool categorization (detected_tool_ids). The system must support both manual ad-hoc triggers and automatic triggers on tool status changes (create, merge, activate). Jobs process asynchronously with progress tracking, checkpointing for resumability, and comprehensive audit logging. Primary use case: fix the current data gap where sentiment_scores exist but lack tool associations, blocking Hot Topics and tool-specific dashboards.

## Technical Context

**Language/Version**: Python 3.13.3  
**Primary Dependencies**: FastAPI 0.109.2, Azure Cosmos SDK 4.5.1, APScheduler 3.10.4, Pydantic 2.x, structlog 24.1.0  
**Storage**: Azure CosmosDB (SQL API) - sentiment_scores, Tools, ToolAliases collections; ReanalysisJobs collection (NEW)  
**Testing**: pytest 8.0.0, pytest-asyncio, pytest-mock  
**Target Platform**: Linux server (production: Azure), macOS (development: local CosmosDB emulator)  
**Project Type**: Web application (existing backend/frontend structure)  
**Performance Goals**: 100+ documents/sec processing rate, <2s API response for job triggers, <5s job status latency  
**Constraints**: <1 hour for 10k document batches, 95%+ categorization success rate, idempotent operations, zero data loss  
**Scale/Scope**: 5,699 sentiment_scores currently (growing), 4 tools (expandable), batch job processing with checkpointing

**Key Unknowns**:
- NEEDS CLARIFICATION: Job queue implementation - Use existing APScheduler or add dedicated task queue (Celery/RQ)?
- NEEDS CLARIFICATION: Progress tracking storage - Add fields to sentiment_scores or create separate JobProgress collection?
- NEEDS CLARIFICATION: Checkpoint strategy - Document-level or batch-level checkpointing for resumability?
- NEEDS CLARIFICATION: Concurrent job handling - Allow parallel jobs or enforce sequential processing?

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is template-only. Checking against existing project patterns from `.github/copilot-instructions.md`:

✅ **Follows existing Python 3.13.3 + FastAPI patterns** - Uses established backend architecture  
✅ **Service layer pattern** - ReanalysisService follows ToolService, DatabaseService patterns  
✅ **Async/await for I/O** - All database operations and batch processing use async  
✅ **Pydantic models for validation** - ReanalysisJobRequest, ReanalysisJobResponse models  
✅ **Structured logging** - Consistent with existing structlog usage  
✅ **Admin authentication pattern** - Reuses admin token verification from Feature 011  
✅ **Error handling pattern** - Background jobs: catch-log-continue; Startup: fail-fast  
✅ **Process lifecycle pattern** - Integrates with existing lifespan management  
✅ **Testing pattern** - pytest with async mocks, unit + integration tests  

**No Constitution Violations** - Feature aligns with all existing architectural patterns.

## Project Structure

### Documentation (this feature)

```
specs/013-admin-feature-to/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file (IN PROGRESS)
├── research.md          # Phase 0 output - Technical decisions
├── data-model.md        # Phase 1 output - Entity definitions
├── quickstart.md        # Phase 1 output - Developer guide
├── contracts/           # Phase 1 output - API contracts
│   └── reanalysis-api.yaml
└── tasks.md             # Phase 2 output - Implementation tasks (NOT created by /speckit.plan)
```

### Source Code (existing repository structure)

```
backend/
├── src/
│   ├── main.py                           # [EXTEND] Add reanalysis routes
│   ├── config.py                         # [EXISTING] Configuration
│   ├── models/
│   │   ├── __init__.py                   # [EXTEND] Export ReanalysisJob models
│   │   └── reanalysis.py                 # [NEW] ReanalysisJob, ReanalysisJobRequest, ReanalysisJobResponse
│   ├── services/
│   │   ├── __init__.py                   # [EXTEND] Export ReanalysisService
│   │   ├── database.py                   # [EXISTING] Database connection
│   │   ├── sentiment_analyzer.py         # [EXTEND] Expose tool detection logic
│   │   ├── scheduler.py                  # [EXTEND] Add reanalysis job scheduling
│   │   └── reanalysis_service.py         # [NEW] Core reanalysis logic
│   └── api/
│       ├── __init__.py                   # [EXISTING] Router registration
│       ├── routes.py                     # [EXISTING] Existing routes
│       └── reanalysis.py                 # [NEW] Reanalysis admin endpoints
└── tests/
    ├── unit/
    │   ├── test_reanalysis_service.py    # [NEW] Service unit tests
    │   └── test_reanalysis_models.py     # [NEW] Model validation tests
    └── integration/
        └── test_reanalysis_api.py        # [NEW] End-to-end API tests

frontend/
├── src/
│   ├── components/
│   │   ├── AdminReanalysisPanel.tsx      # [NEW] Admin UI for triggering jobs
│   │   └── ReanalysisJobMonitor.tsx      # [NEW] Job progress monitoring
│   ├── services/
│   │   └── api.ts                        # [EXTEND] Add reanalysis API client methods
│   └── types/
│       └── index.ts                      # [EXTEND] Add ReanalysisJob types
└── tests/
    └── AdminReanalysisPanel.test.tsx     # [NEW] Component tests
```

**Structure Decision**: Follows existing "Option 2: Web application" structure. New reanalysis functionality integrates into established backend service layer and admin frontend components. No new top-level directories required - all additions fit cleanly into existing architecture.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations identified** - Feature follows all existing patterns and architectural conventions.
