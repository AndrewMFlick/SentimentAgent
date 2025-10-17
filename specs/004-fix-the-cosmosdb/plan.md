# Implementation Plan: Fix CosmosDB DateTime Query Format

**Branch**: `004-fix-the-cosmosdb` | **Date**: 2025-10-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-fix-the-cosmosdb/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Fix datetime query parameter format incompatibility between Python application and CosmosDB PostgreSQL mode emulator. Currently, datetime-filtered queries fail with HTTP 500 InternalServerError due to JSON serialization issues. The fix must enable startup data loading, historical queries, cleanup jobs, and duplicate detection while maintaining backward compatibility with existing stored data.

## Technical Context

**Language/Version**: Python 3.13.3  
**Primary Dependencies**: Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, structlog 24.1.0  
**Storage**: Azure CosmosDB (PostgreSQL mode emulator on localhost:8081, production on Azure)  
**Testing**: pytest (existing test suite in backend/tests/)  
**Target Platform**: Linux/macOS server (backend API)  
**Project Type**: Web application (backend + frontend, but this fix is backend-only)  
**Performance Goals**: Query execution <2 seconds, startup data loading <5 seconds  
**Constraints**: Must maintain backward compatibility with existing stored datetime formats, no breaking API changes, must work with both emulator and Azure CosmosDB  
**Scale/Scope**: Affects 4 query methods in database service, impacts startup sequence and 3+ scheduled jobs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: N/A - Project constitution is not populated (template only exists)

**Note**: No constitution gates to enforce. Proceeding with standard best practices:
- Changes localized to database service layer
- Backward compatibility maintained
- Integration tests required for datetime queries
- No new dependencies or architectural changes

## Project Structure

### Documentation (this feature)

```
specs/004-fix-the-cosmosdb/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── models/          # Pydantic data models (RedditPost, RedditComment, etc.)
│   ├── services/
│   │   └── database.py  # PRIMARY FILE TO MODIFY - contains datetime query logic
│   ├── api/             # FastAPI routes (not modified for this fix)
│   ├── config.py        # Settings (may need datetime format config)
│   └── main.py          # App startup (calls load_recent_data)
└── tests/
    ├── unit/            # Unit tests for individual methods
    ├── integration/     # Integration tests for database queries
    └── test_*.py        # Existing test files

frontend/
└── [Not affected by this fix]
```

**Structure Decision**: Web application with backend-only changes. All modifications isolated to `backend/src/services/database.py` with new integration tests in `backend/tests/integration/` to verify datetime query compatibility.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

N/A - No constitution violations. This is a bug fix with no architectural changes.

## Phase 0: Research Complete ✅

**Status**: Complete  
**Output**: [research.md](./research.md)

**Key Decisions**:

1. **Query Parameter Format**: Use Unix timestamp (integer) instead of ISO 8601 strings
   - Rationale: Avoids JSON parsing errors in CosmosDB PostgreSQL mode
   - Evidence: Error occurs at byte position 18, suggesting character parsing issue

2. **Storage Format**: Keep ISO 8601 for backward compatibility
   - Only change query parameters, not stored values
   - Maintains human readability in database

3. **Query Strategy**: Use `_ts` system field or add timestamp fields
   - Option A: Use `_ts` (modification time) - immediate, no migration
   - Option B: Add `collected_at_ts` fields - accurate, requires backfill

4. **Testing Strategy**: Integration tests with CosmosDB emulator
   - Validates actual behavior, not mocked responses
   - Tests all datetime query scenarios

**Research Questions Resolved**: 4/4
- ✅ What datetime format does CosmosDB accept?
- ✅ How to maintain backward compatibility?
- ✅ What testing strategy validates compatibility?
- ✅ What are best practices from other projects?

## Phase 1: Design & Contracts Complete ✅

**Status**: Complete  
**Outputs**:
- [data-model.md](./data-model.md) - Entity analysis and format changes
- [contracts/database-service.md](./contracts/database-service.md) - Method contract changes
- [quickstart.md](./quickstart.md) - Implementation guide

**Design Decisions**:

1. **Data Model**: No changes to Pydantic models
   - Existing datetime fields remain unchanged
   - Optional: Add `_ts` suffix fields for optimized queries
   - Backward compatible with existing documents

2. **API Contracts**: No public API changes
   - Internal implementation only
   - Same method signatures
   - Same response formats
   - Fixes existing bugs without breaking changes

3. **Implementation Approach**: Phased rollout
   - Phase 1: Fix query parameters (this PR)
   - Phase 2: Add timestamp fields (optional future PR)
   - Phase 3: Optimize with indexes (optional future PR)

4. **Agent Context**: Updated
   - Added technologies: Python 3.13.3, Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, structlog 24.1.0
   - Added database: Azure CosmosDB (PostgreSQL mode)
   - Updated project type: Web application (backend focus)

**Artifacts Generated**:
- ✅ Data model analysis (no schema changes)
- ✅ Database service contract documentation
- ✅ Quickstart implementation guide
- ✅ Agent context updated (.github/copilot-instructions.md)

## Next Steps

Run `/speckit.tasks` to generate implementation tasks from this plan.

The following will be created:
- `tasks.md` - Detailed implementation checklist organized by user story
- Task breakdown for each method modification
- Test implementation tasks
- Verification steps

**Estimated Implementation Time**: 2-3 hours
**Estimated Testing Time**: 1 hour
**Total Effort**: 3-4 hours

## Implementation Summary

### Files to Modify

1. **`backend/src/services/database.py`** (Primary changes)
   - Add `_datetime_to_timestamp()` helper method
   - Update `get_recent_posts()` - change query parameter format
   - Update `get_sentiment_stats()` - change query parameter format
   - Update `cleanup_old_data()` - change query parameter format
   - Update `load_recent_data()` - enable actual data loading, change format

2. **`backend/tests/integration/test_datetime_queries.py`** (New file)
   - Test datetime queries with CosmosDB emulator
   - Test backward compatibility with existing data
   - Test all query scenarios (>=, <, BETWEEN)

### Files NOT Modified

- Pydantic models (no changes needed)
- API routes (internal fix only)
- Configuration (no new settings)
- Frontend (not affected)

### Success Criteria

- ✅ Backend starts without "Data loading temporarily disabled" warning
- ✅ Startup logs show actual data counts: "Data loading complete: N posts, M comments"
- ✅ All datetime-filtered queries succeed (zero HTTP 500 errors)
- ✅ Integration tests pass
- ✅ API endpoints return results for time-based queries
- ✅ Scheduled jobs complete successfully

### Risk Assessment

**Low Risk** - This is a targeted bug fix with:
- No architectural changes
- No new dependencies
- No breaking API changes
- Backward compatible storage format
- Isolated to database service layer
- Integration tests validate behavior

**Rollback Plan**: Revert database.py changes, restart backend (data loading will be disabled again but system remains functional)
