# Tasks: Fix CosmosDB DateTime Query Format

**Input**: Design documents from `/specs/004-fix-the-cosmosdb/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/database-service.md

**Tests**: Integration tests are included to validate datetime query compatibility with CosmosDB emulator.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Summary

**Total Tasks**: 18  
**User Stories**: 3 (organized by priority)  
**Estimated Time**: 3-4 hours total  
**MVP Scope**: User Story 1 only (Tasks T001-T007)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new setup required - this is a bug fix to existing code

*No tasks - existing project structure is sufficient*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core datetime handling utilities needed by all user stories

**⚠️ CRITICAL**: This phase must be complete before ANY user story can be implemented

- [ ] **T001** [P] Add `_datetime_to_timestamp()` helper method to `backend/src/services/database.py`
  - **Location**: After line 160 (after `sanitize_text()` function)
  - **Code**: 
    ```python
    def _datetime_to_timestamp(dt: datetime) -> int:
        """Convert datetime to Unix timestamp for CosmosDB queries.
        
        CosmosDB PostgreSQL mode has JSON parsing issues with ISO 8601 datetime
        strings in query parameters. Use Unix timestamps (integers) instead.
        
        Args:
            dt: Datetime object to convert
            
        Returns:
            Unix timestamp as integer (seconds since epoch)
        """
        return int(dt.timestamp())
    ```
  - **Testing**: Unit test to verify conversion accuracy
  - **Time**: 10 minutes

- [ ] **T002** [P] Create integration test file `backend/tests/integration/test_datetime_queries.py`
  - **Location**: New file in `backend/tests/integration/`
  - **Purpose**: Test framework for validating datetime query compatibility
  - **Contents**: Import statements, pytest fixtures for test data setup/teardown
  - **Time**: 15 minutes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Backend Startup Data Loading (Priority: P1) 🎯 MVP

**Goal**: Enable backend to successfully load recent data on startup without datetime query errors

**Independent Test**: Start backend, verify logs show "Data loading complete: N posts, M comments, K sentiment scores" instead of "temporarily disabled"

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] **T003** [US1] Add test case `test_load_recent_data_success()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify `load_recent_data()` executes without InternalServerError
  - **Setup**: Seed CosmosDB with test posts from last 24 hours
  - **Test**: Call `await db.load_recent_data()`, assert no exceptions
  - **Assertions**: 
    - No `CosmosHttpResponseError` raised
    - Logs contain "Data loading complete"
    - Actual counts logged (not zeros)
  - **Time**: 20 minutes

- [ ] **T004** [US1] Add test case `test_startup_logs_actual_counts()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify startup logs show real data counts
  - **Setup**: Insert known number of test documents
  - **Test**: Call `load_recent_data()`, check log output
  - **Assertions**: 
    - Logs contain actual counts (e.g., "5 posts, 3 comments")
    - No "temporarily disabled" warning
  - **Time**: 15 minutes

### Implementation for User Story 1

- [ ] **T005** [US1] Update `load_recent_data()` method in `backend/src/services/database.py`
  - **Location**: Lines 385-420 (replace temporary disable logic)
  - **Changes**:
    1. Remove warning: `logger.warning("Data loading temporarily disabled...")`
    2. Re-enable: `posts = self.get_recent_posts(hours=hours, limit=1000)`
    3. Update comments query to use `_datetime_to_timestamp()`:
       ```python
       cutoff = datetime.utcnow() - timedelta(hours=hours)
       query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
       parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
       ```
    4. Keep sentiment stats call as-is (will be fixed in T006)
  - **Dependencies**: T001 (needs helper method)
  - **Time**: 20 minutes

- [ ] **T006** [US1] Update `get_recent_posts()` method in `backend/src/services/database.py`
  - **Location**: Lines 208-230
  - **Changes**:
    1. Replace: `parameters = [{"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}]`
    2. With: `parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]`
    3. Update query to use `_ts` field: `query = "SELECT * FROM c WHERE c._ts >= @cutoff"`
  - **Dependencies**: T001 (needs helper method)
  - **Time**: 15 minutes

- [ ] **T007** [US1] Verify startup data loading works end-to-end
  - **Action**: Start backend with `bash backend/start.sh`
  - **Verification**:
    - Watch logs: `tail -f /tmp/backend-startup.log`
    - Confirm: "Data loading complete: N posts, M comments, K sentiment scores"
    - No InternalServerError exceptions
    - Backend remains running (no crash)
  - **Time**: 10 minutes

**Checkpoint**: User Story 1 complete - Backend successfully loads data on startup ✅

---

## Phase 4: User Story 2 - Historical Data Queries (Priority: P2)

**Goal**: Enable API endpoints and background jobs to query historical data by time ranges without errors

**Independent Test**: Call API endpoint `GET /api/v1/posts?hours=24` and verify results returned without HTTP 500 errors

### Tests for User Story 2

- [ ] **T008** [P] [US2] Add test case `test_get_recent_posts_datetime_filter()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify posts query works with datetime parameters
  - **Setup**: Insert posts from 12 hours ago and 48 hours ago
  - **Test**: Call `get_recent_posts(hours=24)`
  - **Assertions**:
    - Returns recent post (12h old)
    - Excludes old post (48h old)
    - No InternalServerError
  - **Time**: 20 minutes

- [ ] **T009** [P] [US2] Add test case `test_get_sentiment_stats_time_range()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify sentiment stats query works with time ranges
  - **Setup**: Insert sentiment data from various time periods
  - **Test**: Call `get_sentiment_stats(hours=168)` for last week
  - **Assertions**:
    - Returns aggregated stats
    - Correct counts for time window
    - No InternalServerError
  - **Time**: 20 minutes

- [ ] **T010** [P] [US2] Add test case `test_cleanup_old_data_datetime_filter()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify cleanup job can query old data
  - **Setup**: Insert posts older than retention period
  - **Test**: Call `cleanup_old_data()`
  - **Assertions**:
    - Old posts are deleted
    - Recent posts remain
    - No InternalServerError
  - **Time**: 20 minutes

### Implementation for User Story 2

- [ ] **T011** [US2] Update `get_sentiment_stats()` method in `backend/src/services/database.py`
  - **Location**: Lines 288-324
  - **Changes**:
    1. Replace parameter format (lines 303-306):
       ```python
       parameters = [
           {"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}
       ]
       ```
    2. Update query to use `_ts` field in WHERE clause
  - **Dependencies**: T001, T006 (pattern established)
  - **Time**: 15 minutes

- [ ] **T012** [US2] Update `cleanup_old_data()` method in `backend/src/services/database.py`
  - **Location**: Lines 358-385
  - **Changes**:
    1. Remove: `cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")`
    2. Replace with: `cutoff_ts = self._datetime_to_timestamp(cutoff)`
    3. Update parameter: `parameters = [{"name": "@cutoff", "value": cutoff_ts}]`
    4. Update query to use `_ts` field: `query = "SELECT c.id, c.subreddit FROM c WHERE c._ts < @cutoff"`
  - **Dependencies**: T001
  - **Time**: 15 minutes

- [ ] **T013** [US2] Verify API endpoints work with time filters
  - **Action**: Test API with curl commands
  - **Tests**:
    ```bash
    # Should return results without HTTP 500
    curl http://localhost:8000/api/v1/posts?hours=24
    curl http://localhost:8000/api/v1/sentiment/stats?hours=168
    ```
  - **Verification**: 
    - HTTP 200 responses
    - Valid JSON data returned
    - No InternalServerError in backend logs
  - **Time**: 10 minutes

**Checkpoint**: User Story 2 complete - Historical queries work without errors ✅

---

## Phase 5: User Story 3 - Data Collection and Analysis Jobs (Priority: P2)

**Goal**: Enable background jobs to query existing data by timestamp to avoid duplicates

**Independent Test**: Trigger data collection job manually, verify it queries existing posts without errors

### Tests for User Story 3

- [ ] **T014** [P] [US3] Add test case `test_query_for_duplicate_detection()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify collection jobs can check for existing posts
  - **Setup**: Insert posts from specific time period
  - **Test**: Query for posts in same time window (simulate duplicate check)
  - **Assertions**:
    - Finds existing posts
    - Can compare timestamps to avoid re-collection
    - No InternalServerError
  - **Time**: 20 minutes

- [ ] **T015** [P] [US3] Add test case `test_query_mixed_document_formats()` to `backend/tests/integration/test_datetime_queries.py`
  - **Purpose**: Verify backward compatibility with existing stored ISO format dates
  - **Setup**: Insert documents with old ISO format (no _ts suffix fields)
  - **Test**: Query using new timestamp parameters
  - **Assertions**:
    - Old format documents are included in results (using _ts system field)
    - New format documents work
    - No InternalServerError
  - **Time**: 25 minutes

### Implementation for User Story 3

- [ ] **T016** [US3] Verify scheduled jobs execute without datetime errors
  - **Action**: Manually trigger background jobs
  - **Tests**:
    - Start backend and wait for scheduler to run
    - Check logs for job execution: `grep "Collect Reddit data" /tmp/backend-startup.log`
    - Or manually trigger: Call scheduler methods directly in Python REPL
  - **Verification**:
    - Jobs complete successfully
    - No InternalServerError in logs
    - Data collection jobs can query for existing posts
  - **Time**: 15 minutes

**Checkpoint**: User Story 3 complete - Background jobs work with datetime queries ✅

---

## Phase 6: Polish & Integration

**Purpose**: Final validation, documentation, and cross-cutting concerns

- [ ] **T017** [P] Run all integration tests and verify 100% pass rate
  - **Command**: `cd backend && pytest tests/integration/test_datetime_queries.py -v`
  - **Expected**: All tests pass, no errors
  - **Time**: 10 minutes

- [ ] **T018** [P] Update documentation in `backend/src/services/database.py`
  - **Action**: Add docstring comments explaining:
    - Why Unix timestamps are used in query parameters
    - Reference to CosmosDB PostgreSQL mode JSON parsing issue
    - Link to this feature spec in comments
  - **Location**: Add comment block near `_datetime_to_timestamp()` function
  - **Time**: 10 minutes

**Final Checkpoint**: All user stories complete, integration tests passing ✅

---

## Dependencies & Execution Order

### Story Completion Order

```
Phase 2 (Foundation)
    ↓
Phase 3 (US1: P1) ← MVP - Can ship this alone
    ↓
Phase 4 (US2: P2) ← Can run in parallel with Phase 5
    ↓
Phase 5 (US3: P2) ← Can run in parallel with Phase 4
    ↓
Phase 6 (Polish)
```

### Task Dependencies

**Sequential (must complete in order)**:
- T001 → T003-T016 (all tasks need the helper function)
- T003-T004 → T005-T007 (tests before implementation for US1)
- T008-T010 → T011-T013 (tests before implementation for US2)
- T014-T015 → T016 (tests before implementation for US3)

**Parallel Opportunities**:
- T001 + T002 (helper method + test file creation)
- T003 + T004 (separate test cases)
- T008 + T009 + T010 (different test cases)
- T014 + T015 (different test cases)
- T017 + T018 (testing + documentation)

### Parallel Execution Examples

**Phase 2 (Foundation)**:
```
Developer A: T001 (helper method)
Developer B: T002 (test file)
→ Complete in parallel (~15 min)
```

**Phase 3 (US1)**:
```
Developer A: T003 (test case 1)
Developer B: T004 (test case 2)
→ Then both work on T005-T007 sequentially
→ Complete US1 in ~1.5 hours
```

**Phase 4 + 5 (US2 + US3)** - Can run in parallel:
```
Team A focuses on US2:
  - T008, T009, T010 (parallel)
  - T011, T012, T013 (sequential)

Team B focuses on US3:
  - T014, T015 (parallel)
  - T016 (sequential)

→ Complete both in ~1.5 hours (if parallelized)
→ Or ~3 hours if done sequentially
```

---

## Implementation Strategy

### MVP First (Recommended)

**Minimum Viable Product**: Complete only Phase 2 + Phase 3 (US1)
- **Tasks**: T001-T007 (7 tasks)
- **Time**: ~1.5 hours
- **Deliverable**: Backend starts successfully and loads data
- **Business Value**: Unblocks feature #003, fixes immediate pain point

**Rationale**: US1 is P1 and independently testable. Can ship this alone, then add US2 and US3 incrementally.

### Incremental Delivery

**Sprint 1**: Foundation + US1 (T001-T007)
- Backend startup works
- Data loading enabled
- Ship to production

**Sprint 2**: US2 (T008-T013)
- Historical queries work
- API endpoints functional
- Ship to production

**Sprint 3**: US3 + Polish (T014-T018)
- Background jobs work
- Full test coverage
- Documentation complete
- Ship to production

### Full Implementation

**If implementing all at once**:
- Complete phases 2-6 sequentially
- Leverage parallel opportunities within each phase
- Total time: 3-4 hours
- Delivers all 3 user stories in one release

---

## Task Execution Checklist

### Before Starting
- [ ] CosmosDB emulator running on localhost:8081
- [ ] Backend test environment setup
- [ ] Git branch `004-fix-the-cosmosdb` checked out

### During Implementation
- [ ] Run tests after each implementation task
- [ ] Commit after each checkpoint
- [ ] Monitor backend logs for errors

### After Completion
- [ ] All integration tests pass (T017)
- [ ] Backend starts without warnings (T007)
- [ ] API endpoints respond correctly (T013)
- [ ] Documentation updated (T018)
- [ ] Ready for code review

---

## Success Criteria

### User Story 1 (P1)
✅ Backend logs: "Data loading complete: N posts, M comments, K sentiment scores"  
✅ No "Data loading temporarily disabled" warning  
✅ No InternalServerError exceptions on startup  

### User Story 2 (P2)
✅ API endpoint `/api/v1/posts?hours=24` returns results  
✅ API endpoint `/api/v1/sentiment/stats?hours=168` returns stats  
✅ Cleanup job executes without errors  

### User Story 3 (P2)
✅ Background jobs can query for existing posts  
✅ Duplicate detection works via timestamp queries  
✅ Backward compatibility with old document formats  

### Overall
✅ All 15-18 integration tests pass  
✅ Zero datetime-related HTTP 500 errors  
✅ Backend runs continuously without crashes  
✅ Performance goals met (<2s queries, <5s startup)
