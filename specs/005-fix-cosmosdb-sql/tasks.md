# Tasks: Fix CosmosDB SQL Aggregation for Sentiment Statistics

**Feature Branch**: `005-fix-cosmosdb-sql`  
**Input**: Design documents from `/specs/005-fix-cosmosdb-sql/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Integration and unit tests included as this is a critical bug fix affecting data accuracy

**Organization**: Tasks organized by user story. Since this is a backend bug fix, User Stories 2 and 3 have no additional implementation beyond User Story 1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This project uses web app structure:

- Backend: `backend/src/`, `backend/tests/`
- Frontend: `frontend/src/` (no changes needed for this fix)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment and branch setup

**Status**: ✅ Already complete (branch `005-fix-cosmosdb-sql` exists, prerequisites validated)

- [x] T001 Branch created and checked out: `005-fix-cosmosdb-sql`
- [x] T002 Prerequisites verified (Python 3.13.3, Azure Cosmos SDK 4.5.1, FastAPI 0.109.2, pytest 8.0.0)
- [x] T003 Planning documents created (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify existing infrastructure is ready for the fix

**⚠️ CRITICAL**: Verify these before implementing the fix

- [ ] T004 Verify CosmosDB emulator is running on localhost:8081 (or connection to Azure CosmosDB is configured)
- [ ] T005 Verify existing tests pass: `cd backend && pytest tests/ -v`
- [ ] T006 Verify backend starts successfully: `cd backend && ./start.sh`
- [ ] T007 Verify API endpoint responds: `curl http://localhost:8000/health`

**Checkpoint**: Foundation verified - bug fix implementation can now begin

---

## Phase 3: User Story 1 - API Returns Accurate Sentiment Statistics (Priority: P1) 🎯 MVP

**Goal**: Fix the `get_sentiment_stats()` method to return accurate sentiment counts instead of zeros

**Independent Test**: Query `/api/v1/sentiment/stats?hours=24` and verify `positive + negative + neutral == total` (validation rule)

### Tests for User Story 1 (Write Tests FIRST - TDD)

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Create unit test for `_execute_scalar_query()` helper method in `backend/tests/unit/test_database.py`
  - Test returns single integer from `SELECT VALUE COUNT(1)` query
  - Test returns single float from `SELECT VALUE AVG()` query
  - Test returns 0 for empty result set
  - Test handles query execution errors

- [ ] T009 [P] [US1] Add integration test for sentiment stats accuracy in `backend/tests/integration/test_datetime_queries.py`
  - Insert test posts with known sentiments (2 positive, 1 negative, 1 neutral)
  - Call `get_sentiment_stats(hours=1)`
  - Assert `total == 4`
  - Assert `positive == 2, negative == 1, neutral == 1`
  - Assert `positive + negative + neutral == total` (validation rule)
  - Assert `avg_sentiment` matches calculated average of compound scores

- [ ] T010 [P] [US1] Add integration test for subreddit filtering in `backend/tests/integration/test_datetime_queries.py`
  - Insert posts from multiple subreddits with known sentiments
  - Call `get_sentiment_stats(subreddit="politics", hours=1)`
  - Assert only posts from "politics" subreddit are counted
  - Assert validation rule passes

- [ ] T011 [P] [US1] Add integration test for time window filtering in `backend/tests/integration/test_datetime_queries.py`
  - Insert posts with different timestamps (some within window, some outside)
  - Call `get_sentiment_stats(hours=24)`
  - Assert only posts within last 24 hours are counted
  - Test multiple time windows (1 hour, 24 hours, 7 days)

- [ ] T012 [P] [US1] Add integration test for edge cases in `backend/tests/integration/test_datetime_queries.py`
  - Test empty database (no posts): should return all zeros
  - Test posts with null sentiment values: should handle gracefully
  - Test posts with null compound_score: should calculate average excluding nulls
  - Test invalid time windows (hours=0): should use default or raise error

**Run all tests**: `cd backend && pytest tests/unit/test_database.py tests/integration/test_datetime_queries.py -v`

**Expected Result**: All new tests FAIL (because bug still exists)

### Implementation for User Story 1

- [ ] T013 [US1] Add `asyncio` import to `backend/src/services/database.py` if not already present
  - Location: Top of file with other imports
  - Required for `asyncio.gather()` parallel execution

- [ ] T014 [US1] Create `_execute_scalar_query()` helper method in `backend/src/services/database.py`
  - Location: Add as private method in `DatabaseService` class (before `get_sentiment_stats()`)
  - Signature: `async def _execute_scalar_query(self, query: str, parameters: List[Dict]) -> Union[int, float]`
  - Implementation:
    - Execute query with `self.container.query_items(query, parameters=parameters, enable_cross_partition_query=True)`
    - Convert result to list
    - Return first item if exists, otherwise return 0
    - Add type hints: `from typing import List, Dict, Union`
  - Add docstring explaining this executes queries that return single scalar values

- [ ] T015 [US1] Rewrite `get_sentiment_stats()` method in `backend/src/services/database.py` (lines 338-375)
  - Location: Replace entire method body, keep method signature unchanged
  - Step 1: Calculate cutoff timestamp (keep existing logic)
  - Step 2: Build query parameters list (keep existing logic)
  - Step 3: Define 5 separate queries:
    - `total_query`: `SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff`
    - `positive_query`: `SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'positive'`
    - `negative_query`: `SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'negative'`
    - `neutral_query`: `SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'neutral'`
    - `avg_query`: `SELECT VALUE AVG(c.compound_score) FROM c WHERE c._ts >= @cutoff`
  - Step 4: Add subreddit filter to all queries if subreddit parameter provided
  - Step 5: Execute queries in parallel with `asyncio.gather()`
  - Step 6: Unpack results into variables
  - Step 7: Return dictionary with results (keep existing response format)

- [ ] T016 [US1] Update error handling in `get_sentiment_stats()` method
  - Location: Wrap `asyncio.gather()` call in try/except block
  - Catch `Exception` and log with `logger.error(f"Failed to query sentiment stats: {e}", exc_info=True)`
  - Re-raise exception (fail-fast, don't return zeros)
  - Remove any existing silent error handling that returns default zeros

- [ ] T017 [US1] Add structured logging for query execution in `get_sentiment_stats()`
  - Log query start with parameters (subreddit, hours, cutoff timestamp)
  - Log query completion with execution time
  - Log result summary (total, positive, negative, neutral counts)
  - Use existing `logger` from `backend/src/services/database.py`

**Checkpoint**: At this point, User Story 1 should be fully implemented. Run tests to verify:

- [ ] T018 [US1] Run unit tests: `cd backend && pytest tests/unit/test_database.py -v`
  - Expected: All unit tests for `_execute_scalar_query()` PASS

- [ ] T019 [US1] Run integration tests: `cd backend && pytest tests/integration/test_datetime_queries.py -v`
  - Expected: All integration tests for sentiment stats accuracy PASS
  - Expected: Validation rule `positive + negative + neutral == total` passes

- [ ] T020 [US1] Run all existing tests to verify no regressions: `cd backend && pytest tests/ -v`
  - Expected: All existing tests still pass (backward compatibility maintained)

- [ ] T021 [US1] Manual API test: `curl http://localhost:8000/api/v1/sentiment/stats`
  - Expected: Response shows non-zero sentiment counts (not all zeros)
  - Expected: `positive + negative + neutral == total`
  - Expected: Response time < 2 seconds

**Checkpoint**: User Story 1 is complete and verified ✅

---

## Phase 4: User Story 2 - Dashboard Displays Real-Time Sentiment Trends (Priority: P2)

**Goal**: Verify dashboard automatically displays accurate sentiment data from the fixed API

**Independent Test**: Open dashboard at `http://localhost:3000`, verify sentiment distribution chart shows non-zero values matching database contents

### Verification for User Story 2 (No Implementation Needed)

**Note**: User Story 2 has no code changes. The dashboard already consumes the `/api/v1/sentiment/stats` endpoint. Once US1 is fixed, the dashboard automatically receives accurate data.

- [ ] T022 [US2] Start frontend: `cd frontend && npm run dev`
  - Verify frontend starts on http://localhost:3000

- [ ] T023 [US2] Verify dashboard loads without errors
  - Open browser to http://localhost:3000
  - Check browser console for errors
  - Verify sentiment stats component renders

- [ ] T024 [US2] Verify dashboard displays accurate sentiment data
  - Compare dashboard sentiment counts to API response: `curl http://localhost:8000/api/v1/sentiment/stats`
  - Verify pie chart shows non-zero segments
  - Verify percentages match API response proportions
  - Verify validation rule: displayed counts sum to total

- [ ] T025 [US2] Test dashboard auto-refresh behavior
  - Wait 5 minutes for auto-refresh (or trigger manually if refresh button exists)
  - Verify dashboard updates with latest data
  - Verify no errors in browser console during refresh

**Checkpoint**: User Story 2 verified - Dashboard displays accurate sentiment data ✅

---

## Phase 5: User Story 3 - Historical Trend Analysis Works Correctly (Priority: P3)

**Goal**: Verify sentiment statistics work correctly for different time windows (1 hour, 24 hours, 7 days)

**Independent Test**: Request stats with different time windows and verify results match database contents for those windows

### Verification for User Story 3 (No Implementation Needed)

**Note**: User Story 3 has no code changes. The time window filtering already works correctly (from Feature #004). This verifies it works with the fixed aggregation.

- [ ] T026 [US3] Test 1-hour time window
  - API: `curl "http://localhost:8000/api/v1/sentiment/stats?hours=1"`
  - Verify only posts from last 1 hour are counted
  - Verify validation rule passes
  - Verify response time < 2 seconds

- [ ] T027 [US3] Test 24-hour time window (default)
  - API: `curl "http://localhost:8000/api/v1/sentiment/stats?hours=24"`
  - Verify only posts from last 24 hours are counted
  - Verify validation rule passes
  - Verify response time < 2 seconds

- [ ] T028 [US3] Test 7-day time window (1 week)
  - API: `curl "http://localhost:8000/api/v1/sentiment/stats?hours=168"`
  - Verify only posts from last 7 days are counted
  - Verify validation rule passes
  - Verify response time < 2 seconds (performance target)

- [ ] T029 [US3] Test 30-day time window (1 month)
  - API: `curl "http://localhost:8000/api/v1/sentiment/stats?hours=720"`
  - Verify only posts from last 30 days are counted
  - Verify validation rule passes
  - Verify response time (may exceed 2s for large datasets - note if it does)

- [ ] T030 [US3] Test time window with subreddit filter
  - API: `curl "http://localhost:8000/api/v1/sentiment/stats?hours=168&subreddit=politics"`
  - Verify only posts from specified subreddit AND time window are counted
  - Verify validation rule passes

- [ ] T031 [US3] Verify dashboard time window selector (if exists)
  - Open dashboard, change time window selector
  - Verify displayed stats update to match selected time window
  - Verify matches API response for same time window

**Checkpoint**: User Story 3 verified - Historical trend analysis works correctly ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation updates

- [ ] T032 [P] Update `backend/src/services/database.py` docstrings
  - Update `get_sentiment_stats()` docstring to document the fix and parallel execution
  - Add docstring for `_execute_scalar_query()` helper method
  - Include performance notes (<2s for 1-week windows)

- [ ] T033 [P] Code cleanup: Remove any commented-out old CASE WHEN query code
  - Remove old broken query from `backend/src/services/database.py`
  - Ensure no leftover debug print statements

- [ ] T034 [P] Run linting: `cd backend && ruff check src/`
  - Fix any linting errors
  - Ensure code follows project style guidelines

- [ ] T035 Performance validation: Monitor query execution time
  - Add temporary performance logging if not already present
  - Run queries with different time windows
  - Verify all complete in < 2 seconds for 1-week windows
  - Document any performance issues

- [ ] T036 Run quickstart.md validation checklist
  - Follow all steps in `specs/005-fix-cosmosdb-sql/quickstart.md`
  - Verify all validation checklist items pass
  - Note any discrepancies

- [ ] T037 Update IMPLEMENTATION_SUMMARY.md (if exists in repo root)
  - Add Feature #005 summary
  - Document SQL aggregation fix approach
  - Note performance characteristics

- [ ] T038 Create Feature #005 COMPLETION.md
  - Location: `specs/005-fix-cosmosdb-sql/COMPLETION.md`
  - Document implementation approach
  - Include test results
  - Note any deviations from plan
  - Include performance measurements

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ Already complete
- **Foundational (Phase 2)**: Verification only - can start immediately
- **User Story 1 (Phase 3)**: Depends on Foundational verification - This is the ONLY implementation work
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion - Verification only
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion - Verification only
- **Polish (Phase 6)**: Depends on all user stories being verified

### User Story Dependencies

- **User Story 1 (P1)**: Core bug fix - MUST complete first
- **User Story 2 (P2)**: Depends on US1 (API must return accurate data for dashboard to display)
- **User Story 3 (P3)**: Depends on US1 (time filtering only works with accurate aggregation)

### Within User Story 1 (Critical Implementation Phase)

1. **Tests (T008-T012)**: Write ALL tests first - they should FAIL
2. **Import (T013)**: Add asyncio import
3. **Helper Method (T014)**: Create `_execute_scalar_query()` - unit tests should now PASS
4. **Main Fix (T015)**: Rewrite `get_sentiment_stats()` - integration tests should now PASS
5. **Error Handling (T016)**: Add fail-fast error handling
6. **Logging (T017)**: Add structured logging
7. **Verification (T018-T021)**: Run all tests and manual verification

### Parallel Opportunities

**Phase 2: Foundational (can run in parallel)**

- T004, T005, T006, T007 can all be verified simultaneously

**Phase 3: User Story 1 Tests (write in parallel)**

- T008, T009, T010, T011, T012 can all be written in parallel (different test functions)

**Phase 3: User Story 1 Verification (run in parallel)**

- T018 and T019 can run simultaneously (unit vs integration tests)

**Phase 4: User Story 2 Verification (can run in parallel)**

- T022, T023 can be done simultaneously (start frontend while checking for errors)

**Phase 5: User Story 3 Verification (can run in parallel)**

- T026-T030 can all be tested simultaneously (different API calls)

**Phase 6: Polish (can run in parallel)**

- T032, T033, T034 can all be done simultaneously (different files/concerns)

---

## Parallel Example: User Story 1 Tests

```bash
# Write all tests in parallel (T008-T012):
# Terminal 1: Unit test for helper method
Task: "Create unit test for _execute_scalar_query() in backend/tests/unit/test_database.py"

# Terminal 2: Integration test for accuracy
Task: "Add integration test for sentiment stats accuracy in backend/tests/integration/test_datetime_queries.py"

# Terminal 3: Integration test for filtering
Task: "Add integration test for subreddit filtering in backend/tests/integration/test_datetime_queries.py"

# Terminal 4: Integration test for time windows
Task: "Add integration test for time window filtering in backend/tests/integration/test_datetime_queries.py"

# Terminal 5: Integration test for edge cases
Task: "Add integration test for edge cases in backend/tests/integration/test_datetime_queries.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only - Recommended)

1. **Phase 1**: ✅ Already complete
2. **Phase 2**: Verify foundation (T004-T007) - ~5 minutes
3. **Phase 3**: Fix the bug (T008-T021) - ~2-3 hours
   - Write tests first (T008-T012) - ~30 minutes
   - Implement fix (T013-T017) - ~1 hour
   - Verify and validate (T018-T021) - ~30 minutes
4. **STOP and VALIDATE**: Test User Story 1 independently
5. **Deploy/Merge to main** if ready (MVP complete!)

**MVP Delivers**: Accurate sentiment statistics API that passes validation rules

### Full Feature Delivery (All User Stories)

1. Complete MVP (User Story 1) → ~3 hours
2. Verify User Story 2 (T022-T025) → ~30 minutes
3. Verify User Story 3 (T026-T031) → ~30 minutes
4. Polish (T032-T038) → ~1 hour

**Total Estimated Time**: ~5 hours

### Incremental Delivery (Recommended for Safety)

1. **Merge 1**: MVP (US1 fixed and tested) → Deploy to production → Monitor
2. **Merge 2**: After 24 hours, if no issues, verify US2+US3 and update docs → Deploy final version

This allows testing the critical bug fix in production before closing the issue.

---

## Notes

- **[P]** tasks = different files/test functions, no dependencies
- **[Story]** label (US1, US2, US3) maps task to specific user story for traceability
- User Story 1 is the ONLY implementation work (bug fix in database.py)
- User Stories 2 and 3 are verification only (existing code works once US1 is fixed)
- Write tests FIRST (TDD) - ensure they FAIL before implementation
- Commit after each logical group of tasks
- **Critical**: Verify `positive + negative + neutral == total` validation rule in all tests
- **Performance**: Monitor query execution time - target < 2 seconds for 1-week windows
- **Error Handling**: Fail-fast, no silent zeros
- Stop at any checkpoint to validate independently

---

## Success Criteria Validation

After completing all tasks, verify all success criteria from spec.md are met:

- **SC-001**: ✅ API endpoint returns non-zero statistics when posts exist (T019, T021)
- **SC-002**: ✅ Statistics calculations complete within 2 seconds for 1-week windows (T028, T035)
- **SC-003**: ✅ Dashboard displays accurate sentiment distribution (T024)
- **SC-004**: ✅ All aggregation queries execute without SQL syntax errors (T018, T019, T020)
- **SC-005**: ✅ System handles edge cases without crashes or incorrect results (T012, T020)
