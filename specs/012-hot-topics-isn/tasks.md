# Tasks: Enhanced Hot Topics with Tool Insights

**Input**: Design documents from `/specs/012-hot-topics-isn/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hot-topics-api.yaml

**Tests**: Integration and unit tests included as per quickstart.md testing checklist

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database indexing and project structure preparation

- [x] **T001** [P] [Setup] Add composite index to `sentiment_scores` container: `[detected_tool_ids[], _ts]` via Azure Portal or index-policy.json
- [x] **T002** [P] [Setup] Add composite index to `reddit_comments` container: `[post_id, _ts]` via Azure Portal
- [x] **T003** [P] [Setup] Verify existing indexes on `reddit_posts` (id, _ts auto-indexed by CosmosDB)

**Checkpoint**: ✅ Database indexes ready for efficient queries

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and service infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] **T004** [P] [Foundation] Create `HotTopic` Pydantic model in `backend/src/models/hot_topics.py`
  - Fields: tool_id, tool_name, tool_slug, engagement_score, total_mentions, total_comments, total_upvotes, sentiment_distribution
  - Include `SentimentDistribution` nested model with counts and percentages
- [x] **T005** [P] [Foundation] Create `RelatedPost` Pydantic model in `backend/src/models/hot_topics.py`
  - Fields: post_id, title, excerpt, author, subreddit, created_utc, reddit_url, comment_count, upvotes, sentiment, engagement_score
- [x] **T006** [Foundation] Create `HotTopicsService` class in `backend/src/services/hot_topics_service.py`
  - Initialize with database service dependency
  - Add `_calculate_cutoff_timestamp(time_range: str) -> int` helper method
  - Add placeholder methods: `get_hot_topics()`, `get_related_posts()`
- [x] **T007** [P] [Foundation] Create TypeScript interfaces in `frontend/src/types/hot-topics.ts`
  - Interfaces: HotTopic, SentimentDistribution, RelatedPost, HotTopicsResponse, RelatedPostsResponse

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Hot Topics Dashboard (Priority: P1) 🎯 MVP

**Goal**: Display ranked list of tools with engagement scores and sentiment indicators

**Independent Test**: Navigate to `/hot-topics` and verify ranked list appears with engagement scores, sentiment percentages, and color-coded indicators within 5 seconds

### Implementation for User Story 1

#### Backend Implementation

- [ ] **T008** [US1] Implement `calculate_engagement_score()` method in `HotTopicsService`
  - Formula: `(mentions × 10) + (comments × 2) + upvotes`
  - Takes tool_id and time_range as parameters
  - Returns integer engagement score

- [ ] **T009** [US1] Implement `_aggregate_sentiment_distribution()` method in `HotTopicsService`
  - Query sentiment_scores for tool mentions within time range
  - Count positive, negative, neutral sentiments
  - Calculate percentages
  - Return SentimentDistribution model

- [ ] **T010** [US1] Implement `get_hot_topics()` method in `HotTopicsService`
  - Query Tools container for active tools
  - For each tool (parallel with asyncio.gather):
    - Count mentions from sentiment_scores where tool_id in detected_tool_ids AND _ts >= cutoff
    - Sum comment_count and upvotes from related posts
    - Calculate engagement score
    - Aggregate sentiment distribution
  - Sort by engagement_score DESC
  - Filter out tools with < 3 mentions (threshold)
  - Return list of HotTopic models
  - Add caching with 5-minute TTL

- [ ] **T011** [US1] Create FastAPI router in `backend/src/api/hot_topics.py`
  - Add `GET /api/hot-topics` endpoint
  - Parameters: time_range (24h|7d|30d, default 7d), limit (1-50, default 10)
  - Dependency injection for HotTopicsService
  - Call service.get_hot_topics()
  - Return HotTopicsResponse with hot_topics array, generated_at timestamp, time_range
  - Error handling: 400 for invalid time_range, 500 for server errors

- [ ] **T012** [US1] Register hot topics router in `backend/src/main.py`
  - Import hot_topics router
  - Add `app.include_router(hot_topics.router)` in FastAPI app setup

#### Frontend Implementation

- [ ] **T013** [P] [US1] Add hot topics API methods to `frontend/src/services/api.ts`
  - `getHotTopics(timeRange?: string, limit?: number): Promise<HotTopicsResponse>`
  - Use existing axios/fetch pattern
  - Include error handling

- [ ] **T014** [P] [US1] Create `HotTopicCard` component in `frontend/src/components/HotTopicCard.tsx`
  - Props: HotTopic data
  - Display: tool name, engagement score, sentiment distribution with percentages
  - Color-coded sentiment indicators (positive=emerald, negative=red, neutral=gray)
  - Glass morphism design (`glass-card` class)
  - Click handler to navigate to related posts (prepared for US2)

- [ ] **T015** [US1] Enhance `HotTopicsPage` component in `frontend/src/components/HotTopicsPage.tsx`
  - Use React Query `useQuery` hook with key `['hot-topics', timeRange]`
  - Call `api.getHotTopics(timeRange)`
  - Display loading skeleton during initial load
  - Map hot_topics array to HotTopicCard components
  - Sort display by engagement_score (already sorted by backend)
  - Show "Not enough data" message if empty results
  - Error boundary for error handling

- [ ] **T016** [P] [US1] Add `TimeRangeFilter` to `HotTopicsPage` (reuse existing component)
  - Time range options: "24 hours", "7 days", "30 days"
  - On change: update timeRange state, React Query auto-refetches
  - Debounce changes (300ms) to avoid excessive queries

#### Testing for User Story 1

- [ ] **T017** [P] [US1] Unit tests for `HotTopicsService` in `backend/tests/unit/test_hot_topics_service.py`
  - Test `calculate_engagement_score()` with known inputs
  - Test `_aggregate_sentiment_distribution()` percentage calculations
  - Mock database queries

- [ ] **T018** [P] [US1] Integration tests for hot topics API in `backend/tests/integration/test_hot_topics_api.py`
  - Test `GET /api/hot-topics` returns 200 with valid data structure
  - Test time_range parameter filtering (24h, 7d, 30d)
  - Test limit parameter (default 10, max 50)
  - Test 400 error for invalid time_range
  - Test minimum mentions threshold (tools with <3 mentions excluded)

- [ ] **T019** [P] [US1] Performance test in `backend/tests/integration/test_hot_topics_performance.py`
  - Verify `GET /api/hot-topics` responds in < 5 seconds (SC-001)
  - Verify engagement calculation for 50 tools completes in < 5 seconds
  - Monitor slow query decorator logs

- [ ] **T020** [P] [US1] Frontend component tests in `frontend/tests/components/HotTopicsPage.test.tsx`
  - Test HotTopicsPage renders loading state
  - Test HotTopicsPage displays hot topics after load
  - Test TimeRangeFilter changes trigger refetch
  - Test empty state shows "Not enough data"

**Checkpoint**: ✅ User Story 1 complete - Hot Topics dashboard functional and independently testable

---

## Phase 4: User Story 2 - Access Related Posts (Priority: P2)

**Goal**: View related Reddit posts for a selected tool with deep links to original discussions

**Independent Test**: Click any hot topic, verify list of 20 posts appears with titles, excerpts, authors, and working Reddit links that open in new tabs

### Implementation for User Story 2

#### Backend Implementation

- [ ] **T021** [US2] Implement `_get_posts_with_engagement()` method in `HotTopicsService`
  - Query posts where: (post._ts >= cutoff) OR (EXISTS comment WHERE comment.post_id = post.id AND comment._ts >= cutoff)
  - Use asyncio.gather for parallel queries (posts in range + posts with recent comments)
  - Combine results, deduplicate by post_id
  - Return list of post IDs

- [ ] **T022** [US2] Implement `get_related_posts()` method in `HotTopicsService`
  - Parameters: tool_id, time_range, offset (default 0), limit (default 20)
  - Query sentiment_scores where tool_id in detected_tool_ids, join with posts
  - Filter by engagement using `_get_posts_with_engagement()` helper
  - Sort by (comment_count + upvotes) DESC
  - Apply offset/limit for pagination
  - Generate excerpt: first 150 characters of post content
  - Return RelatedPost models with total count and has_more flag
  - Implement server-side caching (5-minute TTL) with cache key: `hot_topics:{tool_id}:{time_range}:{timestamp}`

- [ ] **T023** [US2] Add `GET /api/hot-topics/{tool_id}/posts` endpoint in `backend/src/api/hot_topics.py`
  - Path parameter: tool_id
  - Query parameters: time_range (default 7d), offset (default 0), limit (default 20, max 100)
  - Validate tool_id exists (query Tools container)
  - Call service.get_related_posts()
  - Return RelatedPostsResponse with posts array, total, has_more, offset, limit
  - Error handling: 404 if tool not found, 500 for server errors

#### Frontend Implementation

- [ ] **T024** [P] [US2] Add related posts API method to `frontend/src/services/api.ts`
  - `getRelatedPosts(toolId: string, timeRange?: string, offset?: number, limit?: number): Promise<RelatedPostsResponse>`
  - Include error handling

- [ ] **T025** [P] [US2] Create `RelatedPostCard` component in `frontend/src/components/RelatedPostCard.tsx`
  - Props: RelatedPost data
  - Display: title, excerpt (100-150 chars), author, subreddit, timestamp, comment_count, upvotes
  - Sentiment indicator (color-coded badge)
  - Reddit link button: "View on Reddit" → opens post.reddit_url in new tab (`target="_blank" rel="noopener noreferrer"`)
  - Glass morphism card design
  - Hover effect: `hover:scale-105 transition-transform`

- [ ] **T026** [US2] Create `RelatedPostsList` component in `frontend/src/components/RelatedPostsList.tsx`
  - Props: toolId, timeRange
  - Use React Query `useInfiniteQuery` hook:
    - queryKey: `['related-posts', toolId, timeRange]`
    - queryFn: calls `api.getRelatedPosts` with pageParam for offset
    - getNextPageParam: returns `pages.length * 20` if `lastPage.has_more`, else undefined
  - Render: Map pages → posts → RelatedPostCard components
  - Show loading skeleton during initial fetch
  - Show spinner on "Load More" button during pagination fetch
  - "Load More" button: calls `fetchNextPage()`, disabled when `!hasNextPage`
  - Empty state: "No posts found for this time range"

- [ ] **T027** [US2] Update `HotTopicCard` component click handler
  - On click: navigate to `/hot-topics/${tool.tool_slug}` route (or expand in-place to show RelatedPostsList)
  - Pass tool_id and current timeRange to RelatedPostsList

- [ ] **T028** [US2] Add routing or modal for related posts view
  - Option A: New route `/hot-topics/:slug` with RelatedPostsList
  - Option B: Modal/drawer that opens from HotTopicCard with RelatedPostsList
  - Ensure timeRange filter state persists

#### Testing for User Story 2

- [ ] **T029** [P] [US2] Unit tests for related posts service in `backend/tests/unit/test_hot_topics_service.py`
  - Test `_get_posts_with_engagement()` includes posts with recent comments
  - Test `get_related_posts()` pagination (offset, limit)
  - Test excerpt generation (150 char limit)
  - Test engagement-based sorting

- [ ] **T030** [P] [US2] Integration tests for related posts API in `backend/tests/integration/test_hot_topics_api.py`
  - Test `GET /api/hot-topics/{tool_id}/posts` returns 200 with valid posts
  - Test pagination: offset=0, offset=20, has_more flag accuracy
  - Test time_range filtering excludes old posts
  - Test 404 for invalid tool_id
  - Test Reddit URL format validation

- [ ] **T031** [P] [US2] Performance test for related posts in `backend/tests/integration/test_hot_topics_performance.py`
  - Verify first 20 posts query completes in < 2 seconds (SC-005)
  - Verify paginated requests (offset > 0) complete in < 1 second (cached)

- [ ] **T032** [P] [US2] Frontend component tests in `frontend/tests/components/RelatedPostsList.test.tsx`
  - Test RelatedPostsList renders 20 posts initially
  - Test "Load More" button fetches next 20 posts
  - Test "Load More" hidden when has_more=false
  - Test Reddit links have correct attributes (target="_blank", rel="noopener noreferrer")
  - Test empty state when no posts

**Checkpoint**: ✅ User Story 2 complete - Related posts accessible with deep links, independently testable

---

## Phase 5: User Story 3 - Time-Range Filtering (Priority: P3)

**Goal**: Enable users to filter hot topics and related posts by different time periods (24h, 7d, 30d)

**Independent Test**: Change time range filter, verify results update within 2 seconds showing only posts from selected period

### Implementation for User Story 3

**Note**: Much of the filtering infrastructure was built in US1 and US2. This phase focuses on integration and UX polish.

#### Backend Implementation

- [x] **T033** [US3] Add time range validation helper in `HotTopicsService`
  - Validate time_range parameter: "24h" | "7d" | "30d"
  - Raise HTTPException 400 if invalid
  - Add to both `get_hot_topics()` and `get_related_posts()` methods

- [x] **T034** [US3] Add performance monitoring to hot topics endpoints
  - Use existing `monitor_query_performance` decorator on `get_hot_topics()` and `get_related_posts()`
  - Log slow queries (> 3 seconds) for optimization
  - Verify < 2 second response time for filter changes (SC-005)

#### Frontend Implementation

- [x] **T035** [US3] Enhance `TimeRangeFilter` component with visual feedback
  - Add active state styling for selected time range
  - Add loading indicator during filter change
  - Debounce filter changes (300ms) to avoid rapid API calls
  - Ensure component is keyboard accessible (tab navigation, enter to select)

- [x] **T036** [US3] Update `HotTopicsPage` to handle time range changes
  - State: `timeRange` (default "7d")
  - On TimeRangeFilter change: update state, React Query auto-invalidates and refetches
  - Show loading overlay (not full skeleton) during refetch
  - Preserve scroll position during filter changes

- [ ] **T037** [US3] Update `RelatedPostsList` to handle time range changes
  - When timeRange changes (from parent or filter), React Query invalidates query with key `['related-posts', toolId, timeRange]`
  - Reset infinite query state (back to page 0)
  - Show loading state during refetch
  - Update empty state message to mention time range: "No posts found in last {timeRange}"

#### Testing for User Story 3

- [ ] **T038** [P] [US3] Integration tests for time range filtering in `backend/tests/integration/test_hot_topics_api.py`
  - Test 24h filter excludes posts older than 24 hours
  - Test 7d filter excludes posts older than 7 days
  - Test 30d filter includes posts up to 30 days old
  - Test filter changes return different result sets

- [ ] **T039** [P] [US3] Frontend integration tests in `frontend/tests/components/HotTopicsPage.test.tsx`
  - Test time range filter change triggers API call with new parameter
  - Test results update after filter change
  - Test multiple rapid filter changes only trigger final query (debouncing)
  - Test loading state appears during filter change

- [ ] **T040** [P] [US3] Performance test for filter changes in `backend/tests/integration/test_hot_topics_performance.py`
  - Verify time range filter change responds in < 2 seconds (SC-005)
  - Test cache invalidation works correctly (different time ranges use different cache keys)

**Checkpoint**: ✅ User Story 3 complete - Time range filtering fully functional, all user stories independently testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation across all user stories

- [x] **T041** [P] [Polish] Update `backend/src/api/routes.py` to include hot topics endpoints in API documentation
  - Add tags for Swagger UI grouping
  - Add descriptions and examples to OpenAPI schema

- [x] **T042** [P] [Polish] Add error handling for edge cases in `HotTopicsService`
  - Tool with 0 mentions: return engagement_score=0, show "Not enough data" in UI
  - Tool with <3 mentions: filter out from hot topics list (threshold)
  - No posts in time range: return empty array with appropriate message
  - CosmosDB query timeout: log error, return 500 with retry message

- [x] **T043** [P] [Polish] Add structured logging to `HotTopicsService`
  - Log engagement score calculation for each tool (debug level)
  - Log slow aggregation queries (> 2 seconds, warn level)
  - Log cache hits/misses for related posts (info level)
  - Use existing structlog pattern from project

- [x] **T044** [P] [Polish] Add accessibility improvements to frontend components
  - `HotTopicCard`: ARIA labels, keyboard navigation, focus indicators
  - `RelatedPostCard`: Semantic HTML (article tags), alt text for sentiment icons
  - `TimeRangeFilter`: ARIA role="radiogroup", clear selected state for screen readers
  - Ensure all interactive elements have `:focus-visible` ring styling

- [ ] **T045** [P] [Polish] Update frontend error handling
  - Add toast notifications for API errors (using existing toast pattern)
  - Show retry button on error states
  - Distinguish between network errors and data errors (404 vs 500)

- [ ] **T046** [Polish] Run quickstart.md validation checklist
  - Verify all manual testing scenarios pass
  - Verify API usage examples work as documented
  - Test edge cases: no data, deleted posts, rate limits
  - Verify performance benchmarks met (< 5s page load, < 2s filtering)

- [ ] **T047** [P] [Polish] Update project documentation
  - Add Hot Topics feature to main README.md
  - Update API documentation with new endpoints
  - Add screenshots/examples to quickstart.md if helpful

- [ ] **T048** [Polish] Code review and refactoring
  - Review all new code for consistency with existing patterns
  - Remove any debug logging or commented code
  - Ensure proper type hints in Python, proper types in TypeScript
  - Run linters: `ruff check backend/src/`, `npm run lint` in frontend

**Checkpoint**: ✅ Feature complete, polished, and ready for deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
  - Adds database indexes needed for efficient queries
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - Creates core models and service structure
- **User Story 1 (Phase 3)**: Depends on Foundational completion - Can proceed independently
  - MVP deliverable: Hot topics dashboard
- **User Story 2 (Phase 4)**: Depends on Foundational completion - Can proceed in parallel with US1
  - Builds on US1 (uses HotTopicCard click handler) but is independently testable
- **User Story 3 (Phase 5)**: Depends on US1 and US2 completion (integrates with both)
  - Time filtering affects both hot topics list and related posts
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: ✅ No dependencies on other stories - Can start after Foundation
- **User Story 2 (P2)**: ⚠️ Soft dependency on US1 (uses HotTopicCard component) - Can be tested independently by directly navigating to a tool's related posts
- **User Story 3 (P3)**: ❌ Hard dependency on US1 and US2 - Filters affect both features, must be integrated last

### Within Each User Story

**Backend (typical order)**:
1. Service layer methods (business logic)
2. API endpoints (routes)
3. Router registration in main.py
4. Tests (can be parallel with implementation if TDD)

**Frontend (typical order)**:
1. API service methods (api.ts)
2. Presentational components (cards, lists)
3. Container components (pages)
4. Tests (can be parallel with implementation if TDD)

**Parallelizable tasks** (marked [P]):
- All Setup tasks (different database operations)
- All Foundation models (different files)
- Backend service methods and frontend API methods (different codebases)
- All tests within a phase (different test files)
- Component implementations (different files)

### Parallel Opportunities

**Phase 1 (Setup)**: All 3 tasks can run in parallel (different index operations)

**Phase 2 (Foundation)**: 
- T004, T005, T007 can run in parallel (different files)
- T006 depends on T004 and T005 (imports models)

**Phase 3 (User Story 1)**:
- T008, T009 can run in parallel (different methods)
- T013, T014 can run in parallel (different frontend files)
- T016 can run in parallel with T015 (different files)
- All tests (T017-T020) can run in parallel

**Phase 4 (User Story 2)**:
- T024, T025 can run in parallel (different frontend files)
- All tests (T029-T032) can run in parallel

**Phase 5 (User Story 3)**:
- All tests (T038-T040) can run in parallel

**Phase 6 (Polish)**:
- Most polish tasks can run in parallel (T041-T045, T047)

---

## Parallel Example: User Story 1 Backend

```bash
# Launch these tasks together (different methods in same service):
T008: "Implement calculate_engagement_score() method"
T009: "Implement _aggregate_sentiment_distribution() method"

# Then (depends on T008, T009):
T010: "Implement get_hot_topics() method"

# While T010 is running, launch frontend tasks in parallel:
T013: "Add hot topics API methods to api.ts"
T014: "Create HotTopicCard component"
```

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all test files together (different files):
T017: "Unit tests for HotTopicsService"
T018: "Integration tests for hot topics API"
T019: "Performance test"
T020: "Frontend component tests"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (database indexes)
2. Complete Phase 2: Foundational (models and service structure)
3. Complete Phase 3: User Story 1 (hot topics dashboard)
4. **STOP and VALIDATE**: 
   - Navigate to `/hot-topics`
   - Verify ranked list appears in < 5 seconds
   - Verify engagement scores and sentiment percentages display correctly
   - Run tests: `pytest backend/tests/integration/test_hot_topics_api.py -v`
5. Deploy MVP if ready

**Estimated Time for MVP**: ~2-3 days
- Setup: 1-2 hours
- Foundation: 2-3 hours
- US1 Backend: 4-6 hours
- US1 Frontend: 4-6 hours
- US1 Tests: 2-3 hours
- Validation & fixes: 2-4 hours

### Incremental Delivery

1. **Sprint 1**: Setup + Foundation + US1 → Deploy MVP (hot topics dashboard)
2. **Sprint 2**: US2 → Deploy (add related posts with deep links)
3. **Sprint 3**: US3 → Deploy (add time range filtering)
4. **Sprint 4**: Polish → Final release

Each sprint delivers working, testable functionality without breaking previous features.

### Parallel Team Strategy

With 3 developers:

**Week 1**:
- All: Phase 1 (Setup) + Phase 2 (Foundation) - 1 day
- Developer A: US1 Backend (T008-T012) - 2 days
- Developer B: US1 Frontend (T013-T016) - 2 days
- Developer C: US1 Tests (T017-T020) - 2 days

**Week 2**:
- Developer A: US2 Backend (T021-T023) - 2 days
- Developer B: US2 Frontend (T024-T028) - 2 days
- Developer C: US2 Tests (T029-T032) - 2 days
- All: Integration & validation - 1 day

**Week 3**:
- All: US3 (T033-T040) - 2 days (smaller scope, mostly integration)
- All: Polish (T041-T048) - 3 days

---

## Task Count Summary

- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundation)**: 4 tasks
- **Phase 3 (US1)**: 13 tasks (8 implementation + 5 tests)
- **Phase 4 (US2)**: 12 tasks (8 implementation + 4 tests)
- **Phase 5 (US3)**: 8 tasks (5 implementation + 3 tests)
- **Phase 6 (Polish)**: 8 tasks
- **Total**: 48 tasks

**Parallel opportunities**: ~25 tasks can run in parallel (52% of total)

**Estimated effort**:
- MVP (US1): ~20 hours
- Full feature (US1+US2+US3): ~40-50 hours
- With polish: ~50-60 hours

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are included for all user stories to ensure quality and catch regressions
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Database indexes (Phase 1) are critical for performance - verify completion before proceeding
- Caching implementation (5-min TTL) is essential for < 2s filter changes
- React Query handles most cache invalidation automatically via query keys
