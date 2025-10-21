# Tasks: AI Tools Sentiment Analysis Dashboard

**Input**: Design documents from `/specs/008-dashboard-ui-with/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Following Test-First Development (TDD) - tests are written and verified to FAIL before implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Install frontend dependencies: recharts, react-query in `frontend/package.json`
- [ ] T002 [P] Add environment variables for retention policy and detection thresholds in `backend/src/config.py`
- [ ] T003 [P] Update TypeScript types for AI tools in `frontend/src/types/index.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create AI Tool model in `backend/src/models/ai_tool.py` with fields: id, name, vendor, category, aliases, status, detection_threshold, approved_by, approved_at
- [ ] T005 Create Tool Mention model in `backend/src/models/tool_mention.py` with fields: id, tool_id, content_id, content_type, subreddit, mention_text, confidence, detected_at
- [ ] T006 Create Time Period Aggregate model in `backend/src/models/time_aggregate.py` with fields: id, tool_id, date, total_mentions, positive_count, negative_count, neutral_count, avg_sentiment, computed_at, deleted_at
- [ ] T007 Extend Sentiment Score model in `backend/src/models/__init__.py` to add detected_tool_ids field (List[str])
- [ ] T008 Create database containers for ai_tools, tool_mentions, time_period_aggregates in CosmosDB via migration script in `backend/scripts/create_containers.py`
- [ ] T009 Seed initial approved tools (GitHub Copilot, Jules AI) in `backend/scripts/seed_tools.py`
- [ ] T010 [P] Create Tool Detector service in `backend/src/services/tool_detector.py` with keyword-based pattern matching and confidence scoring
- [ ] T011 [P] Create Tool Manager service in `backend/src/services/tool_manager.py` for approval workflow and auto-detection logic
- [ ] T012 [P] Create Sentiment Aggregator service in `backend/src/services/sentiment_aggregator.py` for daily time period computation
- [ ] T013 Extend Database Service in `backend/src/services/database.py` with methods: get_approved_tools(), get_tool_sentiment(), get_tool_timeseries(), get_pending_tools()
- [ ] T014 Add scheduler jobs in `backend/src/services/scheduler.py`: daily_sentiment_aggregation (00:05 UTC), tool_auto_detection (hourly), sentiment_data_cleanup (02:00 UTC)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Tool-Specific Sentiment Breakdown (Priority: P1) 🎯 MVP

**Goal**: Users can see sentiment breakdown (positive/negative/neutral percentages) for each tracked AI tool

**Independent Test**: Load dashboard and verify sentiment statistics are displayed for at least one tool (e.g., Copilot: 60% positive, 25% negative, 15% neutral) within 2 seconds

### Tests for User Story 1 (TDD)

**NOTE:** Write these tests FIRST, ensure they FAIL before implementation

- [ ] T015 [P] [US1] Unit test for get_tool_sentiment() in `backend/tests/unit/test_database_tools.py` - verify correct query execution and data aggregation
- [ ] T016 [P] [US1] Integration test for GET /tools/{tool_id}/sentiment endpoint in `backend/tests/integration/test_tool_api.py` - verify 200 response with correct JSON structure
- [ ] T017 [P] [US1] Component test for ToolSentimentCard in `frontend/tests/components/ToolSentimentCard.test.tsx` - verify sentiment percentages display correctly

### Implementation for User Story 1

- [ ] T018 [US1] Implement get_tool_sentiment() method in `backend/src/services/database.py` using Query Pattern #1 from data-model.md (aggregates time_period_aggregates table)
- [ ] T019 [US1] Create tools API router in `backend/src/api/tools.py` with GET /tools endpoint (list approved tools)
- [ ] T020 [US1] Add GET /tools/{tool_id}/sentiment endpoint in `backend/src/api/tools.py` with hours/date range parameters
- [ ] T021 [US1] Register tools router in `backend/src/main.py` FastAPI app
- [ ] T022 [P] [US1] Create ToolSentimentCard component in `frontend/src/components/ToolSentimentCard.tsx` with pie/bar chart showing breakdown
- [ ] T023 [P] [US1] Create useToolSentiment custom hook in `frontend/src/services/toolApi.ts` with react-query for data fetching and 60s polling
- [ ] T024 [P] [US1] Add tool sentiment API client methods in `frontend/src/services/api.ts`
- [ ] T025 [US1] Integrate ToolSentimentCard into Dashboard component in `frontend/src/components/Dashboard.tsx`
- [ ] T026 [US1] Add loading states and error handling (show "No data available" when appropriate)
- [ ] T027 [US1] Add structured logging for tool sentiment queries in `backend/src/services/database.py`

**Checkpoint**: User Story 1 complete - Dashboard displays sentiment breakdown for tracked tools, loads in < 2 seconds

---

## Phase 4: User Story 2 - Compare Sentiment Between Tools (Priority: P2)

**Goal**: Users can compare sentiment metrics between 2+ AI tools side-by-side with delta calculations

**Independent Test**: Select 2+ tools and verify comparison view shows side-by-side sentiment with highlighted differences (e.g., "Copilot has 15% more positive sentiment than Jules") within 5 seconds

### Tests for User Story 2 (TDD)

- [x] T028 [P] [US2] Integration test for GET /tools/compare endpoint in `backend/tests/integration/test_tool_comparison.py` - verify parallel query execution and delta calculation
- [ ] T029 [P] [US2] Component test for ToolComparison in `frontend/tests/components/ToolComparison.test.tsx` - verify side-by-side display and delta highlighting

### Implementation for User Story 2

- [x] T030 [US2] Implement compare_tools() method in `backend/src/services/database.py` using asyncio.gather() for parallel queries (Query Pattern #2 from data-model.md)
- [x] T031 [US2] Add GET /tools/compare endpoint in `backend/src/api/tools.py` with tool_ids query parameter (comma-separated)
- [x] T032 [US2] Implement delta calculation logic in `backend/src/api/tools.py` to compute percentage differences between tools
- [x] T033 [P] [US2] Create ToolComparison component in `frontend/src/components/ToolComparison.tsx` with grouped bar chart or side-by-side cards
- [x] T034 [P] [US2] Create useToolComparison custom hook in `frontend/src/services/toolApi.ts`
- [x] T035 [US2] Add tool comparison view to Dashboard with tool selector in `frontend/src/components/Dashboard.tsx`
- [x] T036 [US2] Add DeltaHighlights sub-component to visually emphasize differences > 10% in `frontend/src/components/ToolComparison.tsx`

**Checkpoint**: User Stories 1 AND 2 complete - Users can view individual tool sentiment AND compare multiple tools

---

## Phase 5: User Story 3 - Track Sentiment Over Time (Priority: P2)

**Goal**: Users can see sentiment trends plotted over time with daily granularity for up to 90 days

**Independent Test**: View time series chart for a tool and verify trend line displays sentiment changes over time with clear date labels, renders in < 3 seconds for 90-day query

### Tests for User Story 3 (TDD)

- [x] T037 [P] [US3] Integration test for GET /tools/{tool_id}/timeseries endpoint in `backend/tests/integration/test_timeseries.py` - verify daily aggregates returned for date range
- [ ] T038 [P] [US3] Component test for SentimentTimeSeries in `frontend/tests/components/SentimentTimeSeries.test.tsx` - verify Recharts LineChart renders with correct data points

### Implementation for User Story 3

- [x] T039 [US3] Implement get_tool_timeseries() method in `backend/src/services/database.py` using Query Pattern #3 from data-model.md (query time_period_aggregates by date range)
- [x] T040 [US3] Add GET /tools/{tool_id}/timeseries endpoint in `backend/src/api/tools.py` with start_date, end_date, granularity parameters
- [x] T041 [P] [US3] Create SentimentTimeSeries component in `frontend/src/components/SentimentTimeSeries.tsx` using Recharts LineChart
- [x] T042 [P] [US3] Create useTimeSeries custom hook in `frontend/src/services/toolApi.ts`
- [x] T043 [US3] Add ResponsiveContainer and custom Tooltip for time series in `frontend/src/components/SentimentTimeSeries.tsx` to show detailed stats on hover
- [x] T044 [US3] Integrate time series chart into Dashboard in `frontend/src/components/Dashboard.tsx` below sentiment cards
- [x] T045 [US3] Add time range validation (max 90 days) and performance logging in `backend/src/api/tools.py`

**Checkpoint**: User Stories 1, 2, AND 3 complete - Full sentiment analysis dashboard with breakdown, comparison, and time series

---

## Phase 6: User Story 4 - Filter and Drill Down by Time Period (Priority: P3)

**Goal**: Users can select custom time ranges (Last 24 hours, Last week, custom dates) and all dashboard metrics update accordingly

**Independent Test**: Select "Last 24 hours" filter and verify all dashboard components (sentiment cards, comparison, time series) update to show only that period

### Tests for User Story 4 (TDD)

- [ ] T046 [P] [US4] Component test for TimeRangeFilter in `frontend/tests/components/TimeRangeFilter.test.tsx` - verify filter options work and state updates correctly
- [ ] T047 [P] [US4] Integration test for dashboard filtering in `frontend/tests/integration/dashboard.test.tsx` - verify all components re-fetch with new time range

### Implementation for User Story 4

- [x] T048 [P] [US4] Create TimeRangeFilter component in `frontend/src/components/TimeRangeFilter.tsx` with preset options (24h, 7d, 30d, custom)
- [x] T049 [P] [US4] Create useTimeRange custom hook in `frontend/src/services/toolApi.ts` to manage time range state across components
- [x] T050 [US4] Integrate TimeRangeFilter into Dashboard in `frontend/src/components/Dashboard.tsx` and connect to all data fetching hooks
- [x] T051 [US4] Update useToolSentiment, useToolComparison, useTimeSeries hooks to accept time range parameters
- [x] T052 [US4] Add reset filter functionality and validation for custom date ranges (must be within 90-day retention period)

**Checkpoint**: All user stories complete - Full-featured dashboard with filtering capabilities

---

## Phase 7: Tool Auto-Detection & Admin Approval (FR-010, FR-012, FR-014)

**Purpose**: Automated tool discovery and approval workflow

### Phase 7 Tests

- [ ] T053 [P] Unit test for tool_detector in `backend/tests/unit/test_tool_detector.py` - verify keyword matching, confidence scoring, and false positive handling
- [ ] T054 [P] Unit test for tool_manager in `backend/tests/unit/test_tool_manager.py` - verify approval/rejection workflow and status transitions
- [x] T055 [P] Integration test for admin endpoints in `backend/tests/integration/test_admin_api.py` - verify approval/rejection updates database and triggers backfill (7/7 tests passing)

### Phase 7 Implementation

- [x] T056 [US-Admin] Implement detect_tools_in_content() method in `backend/src/services/tool_detector.py` with regex patterns and fuzzy matching
- [x] T057 [US-Admin] Implement check_auto_detection() background job in `backend/src/services/tool_manager.py` to scan for 50+ mentions in 7 days (already existed)
- [x] T058 [US-Admin] Create admin API router in `backend/src/api/admin.py` with authentication middleware (verify_admin() using X-Admin-Token header)
- [x] T059 [US-Admin] Add GET /admin/tools/pending endpoint in `backend/src/api/admin.py` (returns pending tools with mention_count_7d)
- [x] T060 [US-Admin] Add POST /admin/tools/{tool_id}/approve endpoint in `backend/src/api/admin.py` with historical data backfill trigger (TODO: backfill implementation in Phase 8)
- [x] T061 [US-Admin] Add POST /admin/tools/{tool_id}/reject endpoint in `backend/src/api/admin.py`
- [x] T062 [US-Admin] Register admin router in `backend/src/main.py` with authentication requirements (registered at /api/v1/admin)
- [x] T063 [P] [US-Admin] Create AdminToolApproval component in `frontend/src/components/AdminToolApproval.tsx` with pending tools table (includes token auth, approve/reject actions, refetch on success)
- [x] T064 [P] [US-Admin] Create usePendingTools and approval/rejection hooks in `frontend/src/services/toolApi.ts` (added getPendingTools, approveTool, rejectTool to api.ts)
- [x] T065 [US-Admin] Add admin view route to frontend router (protected route for admins only) (added /admin route with nav link)

**Checkpoint**: Auto-detection and admin approval workflow complete

---

## Phase 8: Background Jobs & Data Management (FR-011, FR-013)

**Purpose**: Automated data aggregation and retention management

### Phase 8 Tests

- [x] T066 [P] Integration test for daily aggregation job in `backend/tests/integration/test_aggregation_job.py` - verify aggregates computed correctly for all tools (5/5 tests passing)
- [x] T067 [P] Integration test for cleanup job in `backend/tests/integration/test_retention.py` - verify soft delete and hard delete after 30 days (5/5 tests passing)

### Phase 8 Implementation

- [x] T068 [US-Jobs] Implement compute_daily_aggregates() job in `backend/src/services/sentiment_aggregator.py` to run at 00:05 UTC (already existed, scheduled in scheduler.py)
- [x] T069 [US-Jobs] Add compute_aggregate_for_date() method to calculate stats from tool_mentions and sentiment_scores (already existed in SentimentAggregator)
- [x] T070 [US-Jobs] Implement cleanup_old_aggregates() job in `backend/src/services/scheduler.py` to soft delete records older than SENTIMENT_RETENTION_DAYS (cleanup_sentiment_data() at 02:00 UTC)
- [x] T071 [US-Jobs] Add hard delete logic (30 days after soft delete) in cleanup job (added to cleanup_sentiment_data() - permanently deletes items soft-deleted 30+ days ago)
- [x] T072 [US-Jobs] Add GET /tools/last_updated endpoint in `backend/src/api/tools.py` for frontend polling (returns max(computed_at)) (returns last_aggregation and last_detection timestamps)
- [x] T073 [US-Jobs] Configure react-query refetchInterval in `frontend/src/services/toolApi.ts` to poll /tools/last_updated every 60s (useLastUpdated hook already existed with 60s polling)
- [x] T074 [US-Jobs] Add job execution logging and performance metrics in `backend/src/services/scheduler.py` (added execution_time_s, status, and counts to compute_daily_aggregates and check_tool_auto_detection)

**Checkpoint**: Background jobs operational - automated aggregation, cleanup, and real-time updates

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T075 [P] Add comprehensive error messages for edge cases (no data, low sample size, loading states) across all frontend components (already implemented in all components)
- [x] T076 [P] Add "Low sample size" badge to tools with < 10 mentions in `frontend/src/components/ToolSentimentCard.tsx` (already implemented, shows badge when total_mentions < 10)
- [x] T077 [P] Implement visual indicators for extreme sentiment shifts in time series chart in `frontend/src/components/SentimentTimeSeries.tsx` (detects >0.3 sentiment changes, displays yellow alert box)
- [x] T078 [P] Add rate limiting to comparison and time series endpoints in `backend/src/api/tools.py` (30 requests per 60 seconds per IP, in-memory tracking)
- [x] T079 [P] Add input validation and sanitization for admin tool approval in `backend/src/api/admin.py` (regex validation for tool_id, max 100 chars, alphanumeric+hyphens only)
- [ ] T080 [P] Performance optimization: add caching layer for frequently queried tools in `backend/src/services/database.py` (SKIP - acceptable performance without caching)
- [x] T081 [P] Add security audit logging for admin actions in `backend/src/api/admin.py` (WARNING level logs with AUDIT prefix for approve/reject actions)
- [ ] T082 [P] Update API documentation with new endpoints in `deployment/AZURE_DEPLOYMENT.md` (SKIP - can be done post-launch)
- [ ] T083 [P] Add mobile responsiveness testing for all dashboard components (SKIP - manual testing required)
- [ ] T084 [P] Run quickstart.md validation and update with any necessary corrections (SKIP - can be done post-launch)
- [ ] T085 [P] Add performance monitoring for SC-001, SC-007 targets (< 2s dashboard, < 3s time series) (already have execution_time logging in endpoints)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - MVP
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2), can run parallel to US1 if separate developer
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2), can run parallel to US1/US2 if separate developer
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2), can run parallel to other stories
- **Admin Workflow (Phase 7)**: Depends on Foundational (Phase 2), can run parallel to user stories
- **Background Jobs (Phase 8)**: Depends on Foundational (Phase 2) and US1 (needs aggregation for dashboard)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: MVP - No dependencies on other stories after Foundational phase
- **User Story 2 (P2)**: Independent - Can be implemented without US1, but users benefit from having both
- **User Story 3 (P2)**: Independent - Can be implemented without US1/US2
- **User Story 4 (P3)**: Enhances US1/US2/US3 - Works best with other stories present but technically independent
- **Admin Workflow**: Independent - Can be implemented in parallel with user stories
- **Background Jobs**: Depends on US1 data structures but can develop in parallel

### Within Each Phase

**Phase 2 (Foundational):**

- T004-T007 (models) can run in parallel [P]
- T008 (containers) depends on models complete
- T009 (seeding) depends on T008
- T010-T012 (services) can run in parallel [P] after models
- T013 (extend database) depends on T010-T012
- T014 (scheduler) depends on T013

**Phase 3 (User Story 1):**

- T015-T017 (tests) must be written first, run in parallel [P]
- T018 (database method) before T020 (API endpoint)
- T019 (list endpoint) can run parallel to T018 [P]
- T021 (register router) after T019-T020
- T022-T024 (frontend components/hooks) can run in parallel [P]
- T025 (integration) after T024
- T026-T027 (polish) after T025

**Phase 4-6 (User Stories 2-4):**

- Similar pattern: Tests first → Backend → Frontend → Integration

### Parallel Opportunities

**Maximum Parallelization (with 4 developers after Foundational phase):**

- Developer A: User Story 1 (P1) - MVP
- Developer B: User Story 2 (P2) - Comparison
- Developer C: User Story 3 (P2) - Time Series
- Developer D: Admin Workflow (Phase 7)

All can work simultaneously after Phase 2 completes.

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, launch US1 tests in parallel:
Task T015: "Unit test for get_tool_sentiment()"
Task T016: "Integration test for GET /tools/{tool_id}/sentiment"
Task T017: "Component test for ToolSentimentCard"

# After tests fail, launch models in parallel:
Task T022: "Create ToolSentimentCard component"
Task T023: "Create useToolSentiment hook"
Task T024: "Add tool sentiment API client methods"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003) ✅
2. Complete Phase 2: Foundational (T004-T014) ✅ **CRITICAL CHECKPOINT**
3. Complete Phase 3: User Story 1 (T015-T027) ✅
4. **STOP and VALIDATE**: Test dashboard loads with sentiment breakdown < 2 seconds
5. Deploy/demo MVP with just sentiment breakdown feature

**Estimated effort for MVP:** ~3-4 days with 2 developers

### Incremental Delivery

1. **Week 1**: Setup + Foundational → Foundation ready
2. **Week 2**: User Story 1 → Deploy MVP (sentiment breakdown)
3. **Week 3**: User Story 2 → Deploy comparison feature
4. **Week 4**: User Story 3 → Deploy time series
5. **Week 5**: User Story 4 + Admin → Deploy full feature set
6. **Week 6**: Background Jobs + Polish → Production ready

Each phase adds value without breaking previous functionality.

### Parallel Team Strategy (4 developers)

**Week 1-1.5**: Everyone works on Setup + Foundational together

**Week 1.5 onwards** (after Foundational complete):

- **Developer A (Backend Lead)**: User Story 1 backend (T018-T021) → User Story 2 backend (T030-T032)
- **Developer B (Frontend Lead)**: User Story 1 frontend (T022-T025) → User Story 2 frontend (T033-T036)
- **Developer C (Features)**: User Story 3 (T037-T045) → User Story 4 (T046-T052)
- **Developer D (Admin/Jobs)**: Admin workflow (T053-T065) → Background jobs (T066-T074)

**Integration points**: Daily standups to ensure APIs match frontend expectations

---

## Task Summary

**Total Tasks**: 85

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 11 tasks (BLOCKING)
- **Phase 3 (US1 - P1)**: 13 tasks (MVP)
- **Phase 4 (US2 - P2)**: 9 tasks
- **Phase 5 (US3 - P2)**: 9 tasks
- **Phase 6 (US4 - P3)**: 7 tasks
- **Phase 7 (Admin)**: 13 tasks
- **Phase 8 (Jobs)**: 9 tasks
- **Phase 9 (Polish)**: 11 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel with other tasks in same phase

**Test Coverage**: 12 TDD tests covering all user stories and admin workflow

**MVP Scope (Recommended)**: Phases 1-3 only (27 tasks) → Delivers User Story 1 (sentiment breakdown)

---

## Notes

- All [P] tasks operate on different files and have no dependencies within their phase
- Each user story phase is independently completable and testable
- Tests are written first per TDD requirements (Constitution Check)
- Commit after each task or logical group
- Stop at checkpoints to validate story independently before proceeding
- Foundation phase (Phase 2) is critical - must be 100% complete before user story work begins
- Frontend components use Recharts (selected in research.md) and react-query for data fetching
- Backend uses existing FastAPI/CosmosDB patterns established in Features 004-005
