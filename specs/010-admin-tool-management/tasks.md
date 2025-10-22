# Tasks: Admin Tool Management & Aliasing

**Input**: Design documents from `/specs/010-admin-tool-management/`

- **plan.md**: Python 3.13.3, FastAPI, Azure Cosmos DB, React 18.2.0, TailwindCSS 3.4+
- **spec.md**: 3 user stories (US1: Manual Tool Addition P1, US2: Alias Linking P1, US3: Tool Dashboard P2)
- **data-model.md**: Tools container, ToolAliases container, API models
- **contracts/**: create-tool.md, link-alias.md, list-tools.md

**Tests**: Not explicitly requested in spec - focusing on implementation tasks

**Organization**: Tasks grouped by user story for independent implementation

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

## Path Conventions

- Backend: `backend/src/`, `backend/scripts/`, `backend/tests/`
- Frontend: `frontend/src/components/`, `frontend/src/services/`
- Database scripts: `backend/scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database foundation

- [ ] T001 Create database setup script at `backend/scripts/create_tool_containers.py` to create Tools and ToolAliases containers in Azure Cosmos DB
- [ ] T002 Create seed data script at `backend/scripts/seed_tools.py` to populate initial tools (GitHub Copilot, Jules AI)
- [ ] T003 [P] Create Pydantic models at `backend/src/models/tool.py` for Tool and ToolAlias entities
- [ ] T004 Run `backend/scripts/create_tool_containers.py` to create containers in Cosmos DB
- [ ] T005 Run `backend/scripts/seed_tools.py` to populate initial tool data

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core service layer that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement `ToolService` class in `backend/src/services/tool_service.py` with methods: `create_tool()`, `get_tool()`, `list_tools()`, `update_tool()`, `delete_tool()`
- [ ] T007 Implement alias methods in `backend/src/services/tool_service.py`: `create_alias()`, `get_aliases()`, `remove_alias()`, `resolve_tool_id()`, `has_circular_alias()`
- [ ] T008 Update `DatabaseService` in `backend/src/services/database.py` to add container client accessors for Tools and ToolAliases
- [ ] T009 Create TypeScript interfaces at `frontend/src/types/index.ts` for Tool, ToolAlias, ToolCreateRequest, ToolListResponse, AliasLinkRequest

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Manual Tool Addition (Priority: P1) 🎯 MVP

**Goal**: Enable admins to manually add new AI tools via web form

**Independent Test**: Admin can fill form, submit, and see new tool in comparison dropdowns

### Backend for User Story 1

- [ ] T010 [US1] Create admin routes file at `backend/src/api/admin_routes.py` with FastAPI router initialization
- [ ] T011 [US1] Implement POST `/api/admin/tools` endpoint in `backend/src/api/admin_routes.py` with ToolCreateRequest validation
- [ ] T012 [US1] Add duplicate name validation in POST `/api/admin/tools` endpoint
- [ ] T013 [US1] Add error handling and structured logging for tool creation endpoint
- [ ] T014 [US1] Register admin_routes router in `backend/src/main.py` with `app.include_router(admin_router)`

### Frontend for User Story 1

- [ ] T015 [P] [US1] Create `AdminToolManagement` component at `frontend/src/components/AdminToolManagement.tsx` with glass-card form
- [ ] T016 [US1] Add form state management (toolName, vendor, category, description) to `AdminToolManagement.tsx`
- [ ] T017 [US1] Implement form validation (required fields, character limits) in `AdminToolManagement.tsx`
- [ ] T018 [US1] Add API integration in `AdminToolManagement.tsx` to call POST `/api/admin/tools`
- [ ] T019 [US1] Add success/error feedback alerts with glass-themed styling in `AdminToolManagement.tsx`
- [ ] T020 [US1] Integrate `AdminToolManagement` component into `frontend/src/components/AdminToolApproval.tsx` admin page

**Checkpoint**: At this point, User Story 1 should be fully functional - admins can add tools via form

---

## Phase 4: User Story 2 - Tool Alias Linking (Priority: P1)

**Goal**: Enable admins to link tool aliases for data consolidation

**Independent Test**: Admin can select tool, link to primary tool, and see consolidated sentiment data

### Backend for User Story 2

- [ ] T021 [US2] Implement PUT `/api/admin/tools/{tool_id}/alias` endpoint in `backend/src/api/admin_routes.py` with AliasLinkRequest validation
- [ ] T022 [US2] Add circular alias detection in PUT `/api/admin/tools/{tool_id}/alias` using `has_circular_alias()` method
- [ ] T023 [US2] Add self-reference validation in alias endpoint (tool cannot be alias of itself)
- [ ] T024 [US2] Implement DELETE `/api/admin/tools/{tool_id}/alias` endpoint to remove alias relationships
- [ ] T025 [US2] Update sentiment aggregation in `backend/src/services/database.py` to resolve aliases via LEFT JOIN on ToolAliases

### Frontend for User Story 2

- [ ] T026 [P] [US2] Create `AliasLinkModal` component at `frontend/src/components/AliasLinkModal.tsx` with glass modal styling
- [ ] T027 [US2] Add tool selector dropdown in `AliasLinkModal.tsx` to choose primary tool
- [ ] T028 [US2] Implement modal state management (show/hide, selected tool) in parent component
- [ ] T029 [US2] Add API integration in `AliasLinkModal.tsx` to call PUT `/api/admin/tools/{id}/alias`
- [ ] T030 [US2] Add visual indicator in tool list showing alias relationships (e.g., "Codex → OpenAI")
- [ ] T031 [US2] Add "Link Alias" button to tool table rows that opens modal

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - admins can add tools and link aliases

---

## Phase 5: User Story 3 - Tool Management Dashboard (Priority: P2)

**Goal**: Provide comprehensive tool management table with view/edit/delete/search

**Independent Test**: Admin can view all tools in table, search/filter, edit details, delete tools

### Backend for User Story 3

- [ ] T032 [US3] Implement GET `/api/admin/tools` endpoint in `backend/src/api/admin_routes.py` with pagination parameters
- [ ] T033 [US3] Add search functionality (matches tool name) to GET `/api/admin/tools` endpoint
- [ ] T034 [US3] Add category filtering to GET `/api/admin/tools` endpoint
- [ ] T035 [US3] Implement PUT `/api/admin/tools/{id}` endpoint for updating tool details
- [ ] T036 [US3] Implement DELETE `/api/admin/tools/{id}` endpoint with cascade warnings
- [ ] T037 [US3] Add soft delete logic (set status="deleted") in delete endpoint if sentiment data exists

### Frontend for User Story 3

- [ ] T038 [P] [US3] Create `ToolTable` component at `frontend/src/components/ToolTable.tsx` with glass-themed table
- [ ] T039 [US3] Add table columns: name, vendor, category, alias status, actions
- [ ] T040 [US3] Implement pagination controls in `ToolTable.tsx`
- [ ] T041 [US3] Add search input with debouncing in `ToolTable.tsx`
- [ ] T042 [US3] Add category filter dropdown in `ToolTable.tsx`
- [ ] T043 [P] [US3] Create `ToolEditModal` component at `frontend/src/components/ToolEditModal.tsx` for editing tool details
- [ ] T044 [P] [US3] Create `DeleteConfirmationDialog` component at `frontend/src/components/DeleteConfirmationDialog.tsx`
- [ ] T045 [US3] Add edit action button that opens `ToolEditModal` with pre-filled form
- [ ] T046 [US3] Add delete action button that opens `DeleteConfirmationDialog` with cascade warnings
- [ ] T047 [US3] Integrate `ToolTable` component into `frontend/src/components/AdminToolApproval.tsx`

**Checkpoint**: All user stories should now be independently functional - complete tool management system

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Add comprehensive error handling across all admin endpoints with consistent error response format
- [ ] T049 [P] Add structured logging for all admin operations (create, update, delete, alias)
- [ ] T050 [P] Update API client in `frontend/src/services/api.ts` with typed methods: `createTool()`, `listTools()`, `linkAlias()`
- [ ] T051 [P] Add loading states and spinners to all admin forms/modals
- [ ] T052 [P] Add optimistic UI updates (show changes immediately before API confirmation)
- [ ] T053 Add cache invalidation for tool list after create/update/delete operations
- [ ] T054 Update `backend/src/config.py` with admin-specific configuration (e.g., max tools per page)
- [ ] T055 [P] Add accessibility improvements (ARIA labels, keyboard navigation) to all admin components
- [ ] T056 [P] Update `.github/copilot-instructions.md` with admin tool management patterns
- [ ] T057 Run validation workflow from `specs/010-admin-tool-management/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T005) - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase (T006-T009)
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US1 (P1) → US2 (P1) → US3 (P2)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Integrates with US1 (uses tool list) but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 (displays all tools/aliases) but independently testable

### Within Each User Story

- Backend endpoints before frontend integration
- Core implementation before polish
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup (Phase 1)**: T003 can run in parallel with T001-T002
- **Foundational (Phase 2)**: T006-T009 are sequential (service layer dependencies)
- **User Story 1**: T015 can start in parallel with backend (T010-T014) once ToolService exists
- **User Story 2**: T026 can start in parallel with backend (T021-T025)
- **User Story 3**: T038, T043, T044 can all start in parallel with backend (T032-T037)
- **Polish (Phase 6)**: T048, T049, T050, T051, T052, T055, T056 can all run in parallel

---

## Parallel Example: User Story 1

```bash
# Backend tasks can run sequentially:
T010: "Create admin routes file at backend/src/api/admin_routes.py"
T011: "Implement POST /api/admin/tools endpoint"

# While frontend can start in parallel (marked [P]):
T015: "Create AdminToolManagement component at frontend/src/components/AdminToolManagement.tsx"

# Once both tracks complete, integrate:
T020: "Integrate AdminToolManagement into AdminToolApproval.tsx"
```

---

## Parallel Example: User Story 3

```bash
# Launch all frontend components together:
T038: "Create ToolTable component at frontend/src/components/ToolTable.tsx"
T043: "Create ToolEditModal component at frontend/src/components/ToolEditModal.tsx"
T044: "Create DeleteConfirmationDialog component at frontend/src/components/DeleteConfirmationDialog.tsx"

# Backend endpoints can proceed in parallel:
T032: "Implement GET /api/admin/tools endpoint"
T035: "Implement PUT /api/admin/tools/{id} endpoint"
T036: "Implement DELETE /api/admin/tools/{id} endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T009) - CRITICAL
3. Complete Phase 3: User Story 1 (T010-T020)
4. **STOP and VALIDATE**: Test manual tool addition independently
5. Deploy/demo if ready - admins can now add tools!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (T001-T009)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Manual tool addition works)
3. Add User Story 2 → Test independently → Deploy/Demo (Alias linking works)
4. Add User Story 3 → Test independently → Deploy/Demo (Full dashboard works)
5. Add Polish → Final release (Production-ready)

### Parallel Team Strategy

With 2 developers after Foundational phase completes:

- **Developer A**: User Story 1 (T010-T020)
- **Developer B**: User Story 2 (T021-T031)
- Both stories integrate seamlessly since they're independent

With 3 developers:

- **Developer A**: User Story 1 (T010-T020)
- **Developer B**: User Story 2 (T021-T031)
- **Developer C**: User Story 3 (T032-T047)
- All stories complete in parallel, then integrate

---

## Task Summary

- **Total Tasks**: 57
- **Setup Tasks**: 5 (T001-T005)
- **Foundational Tasks**: 4 (T006-T009)
- **User Story 1 Tasks**: 11 (T010-T020)
- **User Story 2 Tasks**: 11 (T021-T031)
- **User Story 3 Tasks**: 16 (T032-T047)
- **Polish Tasks**: 10 (T048-T057)
- **Parallel Opportunities**: 15 tasks marked [P]

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Database containers (T001-T005) are one-time setup - may already exist in production
- Authentication/authorization mentioned in contracts but implementation deferred to future phase
- Soft delete strategy prevents data loss when tools have historical sentiment data
