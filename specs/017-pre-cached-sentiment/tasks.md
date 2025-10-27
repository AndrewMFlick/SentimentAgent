# Tasks: Pre-Cached Sentiment Analysis

**Branch**: `017-pre-cached-sentiment`  
**Input**: Design documents from `/specs/017-pre-cached-sentiment/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and cache container setup

- [ ] T001 Create `sentiment_cache` Cosmos DB container using `backend/scripts/create_cache_container.py`
- [ ] T002 Add cache configuration settings to `backend/src/config.py` (enable_sentiment_cache, cache_refresh_interval_minutes, cache_ttl_minutes, cosmos_container_sentiment_cache)
- [ ] T003 [P] Verify container creation and indexing policy (partition key: /tool_id)

**Checkpoint**: Cache infrastructure ready - container exists, configuration in place

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and base service that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `CachePeriod` enum in `backend/src/models/cache.py` (HOUR_1, HOUR_24, DAY_7, DAY_30)
- [ ] T005 Create `SentimentCacheEntry` Pydantic model in `backend/src/models/cache.py` with all fields from data-model.md
- [ ] T006 Create `CacheMetadata` Pydantic model in `backend/src/models/cache.py` with health tracking fields
- [ ] T007 Create `CacheService` class skeleton in `backend/src/services/cache_service.py` with `__init__` method accepting containers
- [ ] T008 Add cache service dependency injection in `backend/src/main.py` lifespan context
- [ ] T009 [P] Add structured logging setup for cache operations in `CacheService`

**Checkpoint**: Foundation ready - models exist, service instantiated, ready for user story implementation

---

## Phase 3: User Story 1 - View Current Tool Sentiment (Priority: P1) 🎯 MVP

**Goal**: Enable fast (<1 second) sentiment queries by serving pre-calculated data from cache with graceful fallback

**Independent Test**: Navigate to tool sentiment dashboard, select 24-hour period, verify response time <1 second with cache hit

### Tests for User Story 1

**NOTE: Write these tests FIRST in TDD fashion**

- [ ] T010 [P] [US1] Unit test for `get_cached_sentiment()` in `backend/tests/unit/test_cache_service.py` - test cache hit scenario
- [ ] T011 [P] [US1] Unit test for `get_cached_sentiment()` - test cache miss with fallback scenario
- [ ] T012 [P] [US1] Unit test for `_calculate_sentiment_aggregate()` - verify correct calculation of counts and percentages
- [ ] T013 [P] [US1] Unit test for `_map_hours_to_period()` - verify time period mapping (1h→HOUR_1, 24h→HOUR_24, etc.)
- [ ] T014 [P] [US1] Integration test in `backend/tests/integration/test_cache_integration.py` - test end-to-end cache lookup and fallback
- [ ] T015 [P] [US1] Performance test in `backend/tests/performance/test_cache_performance.py` - verify <1s response time for cache hit

### Implementation for User Story 1

- [ ] T016 [US1] Implement `_map_hours_to_period(hours)` method in `CacheService` - map request hours to CachePeriod enum
- [ ] T017 [US1] Implement `_calculate_cache_key(tool_id, period)` method in `CacheService` - generate cache document ID
- [ ] T018 [US1] Implement `_is_cache_fresh(cache_entry)` method in `CacheService` - check if cache within TTL
- [ ] T019 [US1] Implement `_calculate_sentiment_aggregate(tool_id, hours)` method in `CacheService` - query sentiment_scores and aggregate in Python
- [ ] T020 [US1] Implement `_save_to_cache(cache_entry)` method in `CacheService` - upsert to sentiment_cache container
- [ ] T021 [US1] Implement `get_cached_sentiment(tool_id, hours)` method in `CacheService` - main logic with cache lookup and fallback
- [ ] T022 [US1] Modify `backend/src/services/database.py` `get_tool_sentiment()` to use `CacheService.get_cached_sentiment()` when cache enabled
- [ ] T023 [US1] Update `backend/src/api/tools.py` sentiment endpoint to add `X-Cache-Status` and `X-Cache-Age` response headers
- [ ] T024 [US1] Add `is_cached` and `cached_at` fields to sentiment response model in `backend/src/api/tools.py`
- [ ] T025 [US1] Add error handling for cache lookup failures (log and fallback to direct query)
- [ ] T026 [US1] Add structured logging for cache hit/miss events with duration metrics

**Checkpoint**: User Story 1 complete - sentiment queries return from cache (<1s) with fallback on cache miss

---

## Phase 4: User Story 2 - Automatic Cache Refresh (Priority: P2)

**Goal**: Keep cache fresh with automatic 15-minute background refresh job without blocking user requests

**Independent Test**: Monitor logs for cache refresh jobs every 15 minutes, verify sentiment data updates include new data from sentiment_scores

### Tests for User Story 2

- [ ] T027 [P] [US2] Unit test for `refresh_all_tools()` in `backend/tests/unit/test_cache_service.py` - verify all active tools processed
- [ ] T028 [P] [US2] Unit test for `_refresh_tool_cache(tool_id)` - verify all 4 periods calculated and saved
- [ ] T029 [P] [US2] Unit test for cache refresh error handling - verify job continues on individual tool failure
- [ ] T030 [P] [US2] Unit test for `update_cache_metadata()` - verify metadata updates after refresh
- [ ] T031 [P] [US2] Integration test in `backend/tests/integration/test_cache_integration.py` - verify full refresh cycle
- [ ] T032 [P] [US2] Integration test for concurrent requests during refresh - verify users get previous cache

### Implementation for User Story 2

- [ ] T033 [P] [US2] Implement `_get_active_tool_ids()` method in `CacheService` - query Tools container for active=true tools
- [ ] T034 [US2] Implement `_refresh_tool_cache(tool_id)` method in `CacheService` - calculate and save all 4 periods for one tool
- [ ] T035 [US2] Implement `update_cache_metadata(duration_ms, tools_refreshed)` method in `CacheService` - update CacheMetadata singleton
- [ ] T036 [US2] Implement `refresh_all_tools()` method in `CacheService` - main refresh job logic with error isolation
- [ ] T037 [US2] Add `refresh_sentiment_cache` scheduled job in `backend/src/services/scheduler.py` using APScheduler
- [ ] T038 [US2] Configure refresh job with 15-minute interval from `settings.cache_refresh_interval_minutes`
- [ ] T039 [US2] Add startup task in `backend/src/main.py` lifespan to trigger initial cache population (non-blocking)
- [ ] T040 [US2] Add structured logging for refresh job start, progress, completion with duration and tool count
- [ ] T041 [US2] Add error logging with exc_info=True for refresh failures (catch-log-continue pattern)

**Checkpoint**: User Story 2 complete - cache refreshes automatically every 15 minutes in background

---

## Phase 5: User Story 3 - View Historical Trends (Priority: P3)

**Goal**: Support multiple time period queries (1h, 7d, 30d) with consistent fast performance (<2s) from pre-calculated aggregates

**Independent Test**: Switch between 1-day, 7-day, and 30-day views in dashboard, verify all load under 2 seconds

### Tests for User Story 3

- [ ] T042 [P] [US3] Unit test for 7-day period cache lookup in `backend/tests/unit/test_cache_service.py`
- [ ] T043 [P] [US3] Unit test for 30-day period cache lookup
- [ ] T044 [P] [US3] Unit test for custom time range (non-standard) - verify fallback to on-demand calculation
- [ ] T045 [P] [US3] Performance test for 7-day query in `backend/tests/performance/test_cache_performance.py` - verify <2s
- [ ] T046 [P] [US3] Performance test for 30-day query - verify <2s
- [ ] T047 [P] [US3] Integration test for time period switching - verify all periods accessible

### Implementation for User Story 3

- [ ] T048 [US3] Extend `_map_hours_to_period()` to handle hours=168 (7 days) → DAY_7 mapping
- [ ] T049 [US3] Extend `_map_hours_to_period()` to handle hours=720 (30 days) → DAY_30 mapping
- [ ] T050 [US3] Update `refresh_all_tools()` to include all 4 periods (1h, 24h, 7d, 30d) in refresh cycle
- [ ] T051 [US3] Update frontend `frontend/src/components/ToolSentiment.tsx` to support 7-day and 30-day time range selectors
- [ ] T052 [US3] Add time range selector UI component in `frontend/src/components/TimeRangeSelector.tsx`
- [ ] T053 [US3] Update API client `frontend/src/services/api.ts` to handle different time range parameters
- [ ] T054 [US3] Add visual indicator for which time range is currently selected
- [ ] T055 [US3] Add logging for non-standard time ranges (hours not in 1, 24, 168, 720)

**Checkpoint**: All user stories complete - users can query any standard time period with fast performance

---

## Phase 6: Cache Health & Monitoring

**Purpose**: Observability and monitoring across all user stories

### Tests for Monitoring

- [ ] T056 [P] Unit test for `get_cache_health()` in `backend/tests/unit/test_cache_service.py` - verify health metrics calculation
- [ ] T057 [P] Unit test for cache status determination (healthy/degraded/unhealthy thresholds)
- [ ] T058 [P] Integration test for `/api/v1/cache/health` endpoint

### Implementation for Monitoring

- [ ] T059 [P] Implement `get_cache_health()` method in `CacheService` - return CacheMetadata with computed health status
- [ ] T060 [P] Implement `GET /api/v1/cache/health` endpoint in `backend/src/api/cache.py` (new file)
- [ ] T061 [P] Add cache health metrics to main health check endpoint in `backend/src/main.py`
- [ ] T062 [P] Create `CacheStatusIndicator` React component in `frontend/src/components/CacheStatusIndicator.tsx`
- [ ] T063 Add cache freshness display to dashboard showing "Data as of [timestamp]"
- [ ] T064 Update `frontend/src/services/api.ts` to fetch and display cache health status

**Checkpoint**: Monitoring complete - cache health visible to operators and users

---

## Phase 7: Cache Invalidation (Reanalysis Integration)

**Purpose**: Ensure cache stays accurate when sentiment data changes via reanalysis

### Tests for Invalidation

- [ ] T065 [P] Unit test for `invalidate_tool_cache(tool_id)` in `backend/tests/unit/test_cache_service.py`
- [ ] T066 [P] Integration test for cache invalidation on reanalysis completion

### Implementation for Invalidation

- [ ] T067 Implement `invalidate_tool_cache(tool_id)` method in `CacheService` - delete all cache entries for tool
- [ ] T068 Implement `POST /api/v1/cache/invalidate/{tool_id}` admin endpoint in `backend/src/api/cache.py`
- [ ] T069 Update `backend/src/services/reanalysis_service.py` to call `cache_service.invalidate_tool_cache()` on job completion
- [ ] T070 Add admin authentication check for cache invalidation endpoint
- [ ] T071 Add logging for cache invalidation events with tool_id and entries_deleted count

**Checkpoint**: Cache invalidation working - reanalysis triggers cache refresh

---

## Phase 8: Cache Cleanup & Maintenance

**Purpose**: Prevent unbounded cache growth

### Tests for Cleanup

- [ ] T072 [P] Unit test for `cleanup_expired_cache()` in `backend/tests/unit/test_cache_service.py`
- [ ] T073 [P] Unit test for cleanup with configurable expiry threshold

### Implementation for Cleanup

- [ ] T074 Implement `cleanup_expired_cache(days_old)` method in `CacheService` - delete cache entries older than threshold
- [ ] T075 Add cleanup scheduled job in `backend/src/services/scheduler.py` (daily at 03:00 UTC)
- [ ] T076 Configure cleanup threshold from settings (default: 7 days)
- [ ] T077 Add logging for cleanup job with count of deleted entries

**Checkpoint**: Cleanup working - old cache entries removed automatically

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and documentation

- [ ] T078 [P] Update `docs/` with cache architecture documentation
- [ ] T079 [P] Add cache metrics to README performance benchmarks section
- [ ] T080 [P] Update `QUICKSTART.md` with cache verification steps
- [ ] T081 Code review and refactoring for consistency
- [ ] T082 [P] Add additional unit tests for edge cases in `backend/tests/unit/test_cache_service.py`
- [ ] T083 Performance optimization - batch cache writes if needed
- [ ] T084 Security review - ensure cache doesn't leak sensitive data
- [ ] T085 Run full test suite and verify all tests pass
- [ ] T086 Validate quickstart.md steps manually
- [ ] T087 Update `.github/copilot-instructions.md` with cache patterns (already done in Phase 1 of /speckit.plan)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004-T009)
- **User Story 2 (Phase 4)**: Depends on Foundational (T004-T009) and User Story 1 (T016-T026) for `get_cached_sentiment()` method
- **User Story 3 (Phase 5)**: Depends on Foundational (T004-T009) and User Story 1 (T016-T026) and User Story 2 (T033-T041) for refresh job
- **Monitoring (Phase 6)**: Can start after Foundational (T004-T009), ideally after US2 (T033-T041) for metadata
- **Invalidation (Phase 7)**: Depends on US1 (T016-T026) for invalidation method
- **Cleanup (Phase 8)**: Depends on Foundational (T004-T009)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Foundational phase - can deliver as MVP
- **User Story 2 (P2)**: Builds on US1's `get_cached_sentiment()` method for the refresh job to populate cache
- **User Story 3 (P3)**: Extends US1 and US2 to support additional time periods

### Within Each User Story

1. **Tests FIRST** (TDD) - write tests, verify they fail
2. **Models** - create data structures
3. **Core logic** - implement business logic methods
4. **Integration** - connect to existing systems
5. **Observability** - add logging and metrics
6. **Verification** - ensure tests pass

### Parallel Opportunities

**Phase 1 (Setup)**:
- All tasks can run in sequence (container setup required first)

**Phase 2 (Foundational)**:
- T004-T006: All model creation can run in parallel [P]
- T009: Logging setup can run in parallel with other setup

**Phase 3 (User Story 1)**:
- Tests: T010-T015 all parallelizable [P]
- After tests written, implementation is sequential to build on previous methods

**Phase 4 (User Story 2)**:
- Tests: T027-T032 all parallelizable [P]
- Implementation: T033 can run in parallel with T035

**Phase 5 (User Story 3)**:
- Tests: T042-T047 all parallelizable [P]
- Frontend tasks: T051-T054 can run in parallel with backend tasks T048-T050

**Phase 6 (Monitoring)**:
- Tests: T056-T058 parallelizable [P]
- Implementation: T059-T062 parallelizable [P]

**Phase 7 (Invalidation)**:
- Tests: T065-T066 parallelizable [P]

**Phase 8 (Cleanup)**:
- Tests: T072-T073 parallelizable [P]

**Phase 9 (Polish)**:
- Documentation tasks T078-T080 parallelizable [P]
- Additional tests T082 parallelizable [P]

---

## Parallel Example: User Story 1 Tests

```bash
# All tests can be written in parallel after T009 completes:
Task T010: "Unit test for get_cached_sentiment() - cache hit"
Task T011: "Unit test for get_cached_sentiment() - cache miss"  
Task T012: "Unit test for _calculate_sentiment_aggregate()"
Task T013: "Unit test for _map_hours_to_period()"
Task T014: "Integration test - end-to-end cache lookup"
Task T015: "Performance test - verify <1s response"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Minimum Viable Product - Maximum Value**

1. **Complete Phase 1**: Setup (T001-T003) - ~1 hour
2. **Complete Phase 2**: Foundational (T004-T009) - ~2 hours
3. **Complete Phase 3**: User Story 1 (T010-T026) - ~8 hours
4. **STOP and VALIDATE**: 
   - Run tests (should all pass)
   - Manually test: Query 24-hour sentiment, verify <1s response
   - Verify cache hit/miss logging
   - Check cache container has entries
5. **Deploy/Demo**: MVP delivers 10x performance improvement!

**Total MVP effort**: ~11 hours of focused development

### Incremental Delivery

1. **Foundation** (Phases 1-2): ~3 hours → Cache infrastructure ready
2. **+ User Story 1** (Phase 3): ~8 hours → **MVP READY** - Fast sentiment queries working
3. **+ User Story 2** (Phase 4): ~6 hours → Automatic refresh, cache stays fresh
4. **+ User Story 3** (Phase 5): ~4 hours → Multiple time periods supported
5. **+ Monitoring** (Phase 6): ~3 hours → Observability complete
6. **+ Invalidation** (Phase 7): ~2 hours → Reanalysis integration working
7. **+ Cleanup** (Phase 8): ~2 hours → Maintenance automated
8. **+ Polish** (Phase 9): ~3 hours → Production ready

**Total full feature effort**: ~31 hours

### Parallel Team Strategy

With 3 developers after Foundational phase (T004-T009):

**Week 1**: Foundation + MVP
- **All devs**: Complete Setup (T001-T003) and Foundational (T004-T009) together
- **Dev A**: User Story 1 tests (T010-T015)
- **Dev B**: User Story 1 backend implementation (T016-T022)
- **Dev C**: User Story 1 API integration (T023-T026)
- **Result**: MVP ready by end of week 1

**Week 2**: Automatic Refresh + Historical Trends
- **Dev A**: User Story 2 (T027-T041) - Automatic refresh
- **Dev B**: User Story 3 (T042-T055) - Historical trends
- **Dev C**: Monitoring (T056-T064) - Health metrics
- **Result**: Full feature with all 3 user stories complete

**Week 3**: Hardening
- **All devs**: Invalidation (T065-T071), Cleanup (T072-T077), Polish (T078-T087)
- **Result**: Production-ready, battle-tested

---

## Notes

- **[P] markers**: Parallelizable tasks (different files, no code conflicts)
- **[Story] labels**: US1, US2, US3 map tasks to user stories for traceability
- **TDD enforced**: Tests written first, must fail before implementation
- **Independent stories**: Each user story delivers value on its own
- **Commit strategy**: Commit after each task or logical group of [P] tasks
- **Checkpoints**: Stop and validate at each checkpoint before proceeding
- **Performance targets**: <1s for cache hit, <2s for any standard period
- **Error handling**: Catch-log-continue for background jobs, fail-fast for startup
- **Cache key format**: `{tool_id}:{period}` (e.g., `"877eb2d8:HOUR_24"`)

---

## Summary

- **Total Tasks**: 87
- **MVP Tasks (US1 only)**: 26 tasks (T001-T026)
- **Full Feature**: All 3 user stories + monitoring + hardening
- **Parallel Opportunities**: 35+ tasks marked [P]
- **Independent Test Criteria**: Each user story has clear acceptance scenarios
- **Suggested MVP**: Phase 1-3 only (Setup + Foundational + User Story 1)
- **Performance Impact**: 24-hour queries 10.57s → <1s (10x improvement)
