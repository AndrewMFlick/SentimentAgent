# Feature #010: Admin Tool Management & Aliasing

**Status**: PLANNING  
**Priority**: P1 (High - Essential for multi-tool comparison)  
**Estimated Effort**: 5-7 days

## Problem Statement

The current Sentiment AI Dashboard has several limitations in tool management:

1. **Limited tool comparison** - Only GitHub Copilot and Jules AI in preload data
2. **No manual tool addition** - Cannot add new tools without database migration
3. **Duplicate tool entries** - "Codex" and "OpenAI" tracked separately when they should consolidate
4. **No alias linking** - Cannot link renamed/rebranded tools to their historical data
5. **Manual database edits required** - No admin UI for tool management

These limitations prevent comprehensive AI tool comparison and make the dashboard less valuable for users tracking multiple AI assistants.

## User Stories

### US1: Manual Tool Addition (P1)

**As an** administrator  
**I want** to manually add new AI tools via the admin interface  
**So that** I can expand tool comparison without database migrations

**Acceptance Criteria**:

- ✅ Admin page has "Add New Tool" section with form
- ✅ Form collects: tool name, description, vendor, category
- ✅ POST /api/admin/tools endpoint creates new tool records
- ✅ New tools immediately available in comparison dropdowns
- ✅ Validation prevents duplicate tool names
- ✅ Success/error feedback with glass-themed alerts

**Technical Notes**:

- Backend: New `Tool` table with fields: id, name, description, vendor, category, created_at
- Backend: Admin route with validation (no duplicate names)
- Frontend: Glass-card form with glass-input fields
- Frontend: Auto-refresh tool list after successful addition

### US2: Tool Alias Linking (P1)

**As an** administrator  
**I want** to link tool aliases (e.g., "Codex" → "OpenAI")  
**So that** sentiment data consolidates under a single tool identity

**Acceptance Criteria**:

- ✅ Admin page shows list of all tools with "Link Alias" action
- ✅ "Link Alias" opens modal to select primary tool
- ✅ PUT /api/admin/tools/{id}/alias endpoint creates alias relationship
- ✅ Sentiment queries automatically resolve aliases to primary tool
- ✅ Historical data from aliases shows under primary tool
- ✅ Admin can view and remove alias links

**Technical Notes**:

- Backend: `ToolAlias` table with fields: alias_tool_id, primary_tool_id, created_at
- Backend: Sentiment aggregation queries JOIN through aliases
- Frontend: Glass modal with tool selector dropdown
- Frontend: Visual indicator showing alias relationships (e.g., "Codex → OpenAI")

### US3: Tool Management Dashboard (P2)

**As an** administrator  
**I want** a comprehensive tool management dashboard  
**So that** I can view, edit, and organize all AI tools in one place

**Acceptance Criteria**:

- ✅ Table view of all tools with name, vendor, category, alias status
- ✅ Edit tool details (name, description, vendor, category)
- ✅ Delete tool (with confirmation if sentiment data exists)
- ✅ Search/filter tools by name, vendor, category
- ✅ Sort tools by name, created date, sentiment volume
- ✅ Glass-themed table with hover effects

**Technical Notes**:

- Backend: GET /api/admin/tools with pagination, sorting, filtering
- Backend: PUT /api/admin/tools/{id} for updates
- Backend: DELETE /api/admin/tools/{id} with cascade warnings
- Frontend: Reusable table component with glass styling
- Frontend: Confirmation dialog for destructive actions

## Success Metrics

1. **Tool Coverage**: Expand from 2 tools to 10+ tools in first month
2. **Admin Efficiency**: Add new tool in < 2 minutes
3. **Data Consolidation**: Reduce duplicate tool entries by 100%
4. **User Satisfaction**: Admin users rate tool management 8+/10

## Dependencies

- **Database**: Azure Cosmos DB (SQL API) for tool and alias tables
- **Backend**: FastAPI admin routes with authentication
- **Frontend**: Glass-themed forms and modals matching dark mode design
- **Existing**: AdminToolApproval component (extend with new sections)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Alias relationships create data inconsistencies | High | Add database constraints (no circular aliases, cascading updates) |
| Admin adds malicious/spam tools | Medium | Require admin authentication, add approval workflow |
| Deleting tool breaks historical sentiment data | High | Soft delete + cascade warnings, prevent delete if data exists |
| Performance degradation with many aliases | Medium | Index foreign keys, optimize JOIN queries |

## Out of Scope

- **User-submitted tools**: Only admins can add tools (avoid spam)
- **Auto-detection of tools**: No scraping/API integration (manual only)
- **Tool versioning**: No tracking of tool version changes over time
- **Bulk import**: No CSV upload (add one tool at a time)

## Open Questions

1. Should tool deletion be hard delete or soft delete?
2. Should alias relationships be reversible (swap primary/alias)?
3. Should we allow multiple aliases per tool (e.g., "Codex" + "ChatGPT" → "OpenAI")?
4. Should tool categories be predefined or free-text?
