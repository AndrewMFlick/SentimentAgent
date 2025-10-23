# Tasks: Admin Sentiment Reanalysis & Tool Categorization

**Input**: Design documents from `/specs/013-admin-feature-to/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not explicitly requested in spec - focusing on implementation with validation checkpoints

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database and configuration setup required by all features

- [ ] T001 Create ReanalysisJobs collection in CosmosDB with indexing policy for status, triggered_by, _ts fields
- [ ] T002 Update sentiment_scores collection schema to add detected_tool_ids (array), last_analyzed_at (timestamp), analysis_version (string) fields with defaults
- [ ] T003 Apply ARRAY_CONTAINS indexing to sentiment_scores.detected_tool_ids (verify Hot Topics indexes from Feature 012)
- [ ] T004 Verify admin authentication pattern from Feature 011 is working (X-Admin-Token header validation)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core reanalysis infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create ReanalysisJob Pydantic models in backend/src/models/reanalysis.py (ReanalysisJobRequest, ReanalysisJobResponse, ReanalysisJobDetail, JobStatus, TriggerType enums)
- [ ] T006 [P] Expose tool detection method from backend/src/services/sentiment_analyzer.py as public async function detect_tools_in_content(content: str) -> List[str]
- [ ] T007 Create ReanalysisService class in backend/src/services/reanalysis_service.py with basic structure (init with containers, helper methods for job CRUD)
- [ ] T008 Add tool alias resolution logic to ReanalysisService (query ToolAliases, follow chains, resolve to primary tool IDs)
- [ ] T009 Add job status validation and state transition logic to ReanalysisService (queued → running → completed/failed, no reversals)
- [ ] T010 Add active job check method to ReanalysisService (query for jobs with status IN ['queued', 'running'])

**Checkpoint**: Foundation ready - reanalysis infrastructure exists, user story implementation can now begin

---

## Phase 3: User Story 1 - Manual Ad-Hoc Tool Recategorization (Priority: P1) 🎯 MVP

**Goal**: Enable admins to manually trigger reanalysis jobs to backfill tool categorization in existing historical sentiment data

**Independent Test**: Trigger reanalysis job via POST /admin/reanalysis/jobs, verify job creates and runs, check sentiment_scores are updated with detected_tool_ids

### Implementation for User Story 1

- [ ] T011 [US1] Implement trigger_manual_reanalysis() method in backend/src/services/reanalysis_service.py (create job, validate params, check for active jobs, save to ReanalysisJobs)
- [ ] T012 [US1] Implement batch processing logic in backend/src/services/reanalysis_service.py as process_reanalysis_job() (query sentiment_scores, batch loop, checkpoint every 100 docs)
- [ ] T013 [US1] Implement tool detection and update logic in process_reanalysis_job() (call detect_tools_in_content, resolve aliases, update detected_tool_ids + last_analyzed_at + analysis_version)
- [ ] T014 [US1] Add error handling to batch processing (try/catch per document, log errors to job.error_log, continue processing)
- [ ] T015 [US1] Implement checkpoint logic (save progress.processed_count, progress.percentage, progress.last_checkpoint_id every 100 docs)
- [ ] T016 [US1] Implement job resumption logic (check for last_checkpoint_id, query sentiment_scores WHERE id > checkpoint, continue from there)
- [ ] T017 [US1] Add APScheduler job integration in backend/src/services/scheduler.py (add_reanalysis_job function that calls process_reanalysis_job with trigger='date')
- [ ] T018 [US1] Create admin API routes file backend/src/api/reanalysis.py with FastAPI router and admin auth dependency
- [ ] T019 [US1] Implement POST /api/v1/admin/reanalysis/jobs endpoint (validate request, call trigger_manual_reanalysis, return 202 with job_id)
- [ ] T020 [US1] Add admin audit logging for reanalysis_triggered event in POST endpoint (log admin_user, job_id, parameters, timestamp)
- [ ] T021 [US1] Register reanalysis router in backend/src/main.py with /api/v1 prefix
- [ ] T022 [US1] Manual validation: Trigger job via curl/Postman, verify ReanalysisJobs document created, check sentiment_scores get detected_tool_ids populated

**Checkpoint**: At this point, User Story 1 should be fully functional - admins can manually trigger reanalysis and see data updated

---

## Phase 4: User Story 2 - Automatic Recategorization on Tool Status Changes (Priority: P2)

**Goal**: Automatically trigger reanalysis when tools are created, merged, or status changes to active

**Independent Test**: Create new tool with status='active', verify automatic reanalysis job is created and runs

### Implementation for User Story 2

- [ ] T023 [US2] Implement trigger_automatic_reanalysis() method in backend/src/services/reanalysis_service.py (similar to manual but trigger_type='automatic', targeted tool_ids parameter)
- [ ] T024 [US2] Add event hook in backend/src/services/tool_service.py create_tool() method (if status='active', call trigger_automatic_reanalysis with new tool_id)
- [ ] T025 [US2] Add event hook in backend/src/services/tool_service.py update_tool() method (if status changed from archived to active, trigger reanalysis)
- [ ] T026 [US2] Implement tool merge reanalysis in backend/src/services/tool_service.py merge_tools() method (after merge, trigger reanalysis to replace source tool IDs with target)
- [ ] T027 [US2] Add specialized merge update logic in backend/src/services/reanalysis_service.py (query sentiment_scores with source_tool_id in detected_tool_ids, replace with target_tool_id)
- [ ] T028 [US2] Add admin audit logging for automatic reanalysis events (log trigger reason: tool_created, tool_activated, tool_merged)
- [ ] T029 [US2] Manual validation: Create tool, verify auto-reanalysis job created; merge tools, verify tool IDs updated in sentiment_scores

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - manual triggers AND automatic triggers on tool changes

---

## Phase 5: User Story 3 - Recategorization Monitoring & Progress Tracking (Priority: P3)

**Goal**: Enable admins to monitor job progress, view job history, and see detailed statistics

**Independent Test**: Start reanalysis job, query GET /admin/reanalysis/jobs/{job_id}, verify progress updates in real-time

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement GET /api/v1/admin/reanalysis/jobs endpoint in backend/src/api/reanalysis.py (query ReanalysisJobs with filters: status, trigger_type, pagination with limit/offset)
- [ ] T031 [P] [US3] Implement GET /api/v1/admin/reanalysis/jobs/{job_id} endpoint (query ReanalysisJobs by id, return ReanalysisJobDetail schema)
- [ ] T032 [US3] Add job statistics calculation to process_reanalysis_job() (count tools_detected per tool, track categorized vs uncategorized, update job.statistics)
- [ ] T033 [US3] Add estimated time remaining calculation in job progress updates (based on processing rate: processed_count / elapsed_time)
- [ ] T034 [P] [US3] Implement DELETE /api/v1/admin/reanalysis/jobs/{job_id} endpoint for job cancellation (update status to 'cancelled', stop APScheduler job)
- [ ] T035 [P] [US3] Create AdminReanalysisPanel.tsx component in frontend/src/components/ (form to trigger reanalysis with date_range, tool_ids, batch_size inputs)
- [ ] T036 [P] [US3] Create ReanalysisJobMonitor.tsx component in frontend/src/components/ (table showing job list, status, progress bars, refresh button)
- [ ] T037 [US3] Add reanalysis API client methods to frontend/src/services/api.ts (triggerReanalysis, listJobs, getJob, cancelJob)
- [ ] T038 [US3] Add ReanalysisJob types to frontend/src/types/index.ts (ReanalysisJobRequest, ReanalysisJobDetail, JobStatus enum)
- [ ] T039 [US3] Integrate AdminReanalysisPanel and ReanalysisJobMonitor into admin dashboard (add to admin route, require admin auth)
- [ ] T040 [US3] Add auto-refresh polling to ReanalysisJobMonitor (useEffect with 5-second interval, only when jobs are active)
- [ ] T041 [US3] Manual validation: Trigger job from UI, watch progress update in real-time, verify job history displays correctly

**Checkpoint**: All user stories should now be independently functional - manual triggers, automatic triggers, and monitoring UI

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T042 [P] Add structured logging to all reanalysis operations with contextual fields (job_id, admin_user, processed_count, tool_id)
- [ ] T043 [P] Add rate limiting to batch processing (configurable delay between batches, exponential backoff on CosmosDB 429 errors)
- [ ] T044 [P] Update README.md with reanalysis feature documentation (API endpoints, admin usage, troubleshooting)
- [ ] T045 [P] Update quickstart.md validation steps (verify database setup, test reanalysis endpoints, check frontend UI)
- [ ] T046 Add admin notification for job completion (extend existing admin notification system if present, or log completion prominently)
- [ ] T047 Add idempotency checks (verify multiple runs on same data don't cause issues, detected_tool_ids updates are safe)
- [ ] T048 Add data validation before updates (verify sentiment_score has required fields, validate tool IDs exist before adding to detected_tool_ids)
- [ ] T049 Performance testing: Run full reanalysis on 5,699 docs, verify completes in <60 seconds, check 100+ docs/sec rate
- [ ] T050 Error scenario testing: Kill job mid-processing, restart, verify resumes from checkpoint without data loss
- [ ] T051 Code review: Verify all FR-001 through FR-015 are implemented, check error handling patterns, validate admin auth on all endpoints

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with tool_service.py from Feature 011 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses US1/US2 job infrastructure but adds monitoring/UI independently

### Within Each User Story

**US1 Dependencies**:
- T011-T010 must complete before T017 (service methods before scheduler integration)
- T017 must complete before T018-T021 (scheduler before API endpoints)
- T011-T021 must complete before T022 (implementation before validation)

**US2 Dependencies**:
- T023 before T024-T026 (automatic trigger method before event hooks)
- T027 can be parallel with T024-T026 (different merge logic)
- T024-T027 before T028-T029 (implementation before logging and validation)

**US3 Dependencies**:
- T030-T031 can be parallel (different API endpoints)
- T035-T036 can be parallel (different React components)
- T037-T038 can be parallel (API client and types)
- T032-T033 before T030-T031 (statistics calculation before GET endpoints return them)
- T037-T039 before T040-T041 (API/types/components before integration and validation)

### Parallel Opportunities

**Phase 1 (Setup)**: T001-T004 are sequential (database operations on same collections)

**Phase 2 (Foundational)**: 
- T005 [P] and T006 [P] (different files: models vs sentiment_analyzer)
- T007-T010 are sequential (all modify reanalysis_service.py)

**Phase 3 (US1)**: 
- T011-T017 are sequential (all in reanalysis_service.py or scheduler.py)
- T018-T021 are sequential (API routes in same file)

**Phase 4 (US2)**:
- T024-T026 can be parallel if tool_service.py has separate methods
- T023 and T027 can be parallel (different methods in reanalysis_service.py)

**Phase 5 (US3)**:
- T030 [P] and T031 [P] (different endpoints in same file, but can be drafted in parallel)
- T034 [P], T035 [P], T036 [P] (different files: endpoint, component A, component B)
- T037 [P] and T038 [P] (different files: api.ts vs types)

**Phase 6 (Polish)**:
- T042 [P], T043 [P], T044 [P], T045 [P] can all run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Sequential: Core service implementation
T011: "Implement trigger_manual_reanalysis() in reanalysis_service.py"
T012: "Implement batch processing logic in reanalysis_service.py"
T013: "Implement tool detection and update logic in reanalysis_service.py"
# ... continue T014-T017 sequentially

# Then: API layer (sequential in same file)
T018: "Create reanalysis.py router"
T019: "Implement POST /admin/reanalysis/jobs"
T020: "Add audit logging"
T021: "Register router in main.py"
```

## Parallel Example: User Story 3

```bash
# Launch in parallel:
Task T030: "Implement GET /admin/reanalysis/jobs in reanalysis.py"
Task T031: "Implement GET /admin/reanalysis/jobs/{job_id} in reanalysis.py"
Task T035: "Create AdminReanalysisPanel.tsx"
Task T036: "Create ReanalysisJobMonitor.tsx"
Task T037: "Add reanalysis API client methods to api.ts"
Task T038: "Add types to types/index.ts"

# Then integrate:
Task T039: "Integrate components into admin dashboard"
Task T040: "Add auto-refresh polling"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010) - CRITICAL BLOCKING PHASE
3. Complete Phase 3: User Story 1 (T011-T022)
4. **STOP and VALIDATE**: Test manual reanalysis independently
   - Trigger job via API
   - Verify sentiment_scores updated
   - Check Hot Topics shows historical data
5. Deploy/demo if ready - **This is your MVP!**

### Incremental Delivery

1. Complete Setup + Foundational (T001-T010) → Foundation ready
2. Add User Story 1 (T011-T022) → Test independently → **Deploy MVP!**
3. Add User Story 2 (T023-T029) → Test independently → Deploy enhancement
4. Add User Story 3 (T030-T041) → Test independently → Deploy full feature
5. Add Polish (T042-T051) → Production hardening → Final deployment

### Parallel Team Strategy

With multiple developers:

1. **Together**: Complete Setup (T001-T004) + Foundational (T005-T010)
2. **Once Foundational done, split work**:
   - **Developer A**: User Story 1 Backend (T011-T021)
   - **Developer B**: User Story 2 (T023-T029) - Can start in parallel
   - **Developer C**: User Story 3 Backend (T030-T034)
3. **Frontend**: Developer D can work on US3 Frontend (T035-T041) in parallel with backend
4. **Integration**: Team validates each story independently, then together

---

## Notes

- Database setup (T001-T003) is critical - Hot Topics feature currently broken without array indexes
- T022 validation will verify that 5,699 existing sentiment_scores get detected_tool_ids populated
- Tool alias resolution (T008) is essential for preventing duplicate tool IDs in arrays
- Checkpoint logic (T015-T016) enables resumption - test by killing job mid-run and restarting
- Auto-refresh in UI (T040) should only poll when jobs are active (status = running/queued)
- Performance target (T049): 100 docs/sec = 5,699 docs in ~57 seconds
- Idempotency (T047) is critical - reanalysis should be safe to run multiple times
- Each checkpoint validates story works independently before moving to next priority
