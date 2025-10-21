# Implementation Plan: Admin Tool Management

## Executive Summary

This feature adds comprehensive tool management capabilities to the Sentiment AI Dashboard, enabling administrators to manually add new AI tools and link tool aliases for data consolidation.

**Timeline**: 7 days  
**Effort**: ~40 hours  
**Complexity**: Medium  
**Risk Level**: Low

## Constitution Check

### ✅ Alignment with Project Constitution

| Principle | Alignment | Notes |
|-----------|-----------|-------|
| **Modern Tech Stack** | ✅ Full | Uses Python 3.13.3, FastAPI, Azure Cosmos DB, React 18.2.0, TailwindCSS 3.4+ |
| **Cloud-Native** | ✅ Full | Leverages Azure Cosmos DB containers with proper indexing |
| **Glass UI Design** | ✅ Full | All components follow dark mode glass morphism pattern |
| **Type Safety** | ✅ Full | Pydantic models (backend) + TypeScript interfaces (frontend) |
| **Error Handling** | ✅ Full | Comprehensive validation, structured logging, user feedback |
| **Performance** | ✅ Full | Indexed queries, caching strategy, pagination |
| **Testability** | ✅ Full | Unit tests, integration tests, E2E workflow tests |

### Dependencies

- **Backend**: Existing `DatabaseService`, structured logging
- **Frontend**: Existing glass UI components, API client
- **Database**: Azure Cosmos DB (SQL API) with container creation permissions
- **None Breaking**: This is additive - no changes to existing sentiment analysis

## Phase 1: Database Foundation (Days 1-2)

### Day 1: Container Setup

**Tasks**:

1. Create Cosmos DB containers script
2. Define indexing policies
3. Seed initial tool data
4. Verify container creation

**Deliverables**:

```python
# backend/scripts/create_tool_containers.py
from azure.cosmos import CosmosClient, PartitionKey
import os

def create_containers():
    client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
    database = client.get_database_client("SentimentDB")
    
    # Tools container
    tools_container = database.create_container(
        id="Tools",
        partition_key=PartitionKey(path="/partitionKey"),
        indexing_policy={
            "includedPaths": [
                {"path": "/name/?"},
                {"path": "/category/?"},
                {"path": "/status/?"},
                {"path": "/slug/?"}
            ]
        }
    )
    
    # ToolAliases container
    aliases_container = database.create_container(
        id="ToolAliases",
        partition_key=PartitionKey(path="/partitionKey"),
        indexing_policy={
            "includedPaths": [
                {"path": "/alias_tool_id/?"},
                {"path": "/primary_tool_id/?"}
            ]
        }
    )
    
    print("Containers created successfully!")

if __name__ == "__main__":
    create_containers()
```

**Acceptance Criteria**:

- ✅ Containers visible in Azure Portal
- ✅ Indexing policies applied
- ✅ Partition key strategy validated

### Day 2: Data Models & Seed Data

**Tasks**:

1. Create Pydantic models for Tool and ToolAlias
2. Create seed data script
3. Migrate existing tool references (if needed)

**Deliverables**:

```python
# backend/src/models/tool.py
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class Tool(BaseModel):
    id: str
    partitionKey: str = "tool"
    name: str = Field(..., min_length=1, max_length=100)
    slug: str
    vendor: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., regex="^(code-completion|chat|analysis)$")
    description: str = Field(default="", max_length=500)
    status: str = Field(default="active", regex="^(active|deprecated|deleted)$")
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: str
    updated_at: str

class ToolAlias(BaseModel):
    id: str
    partitionKey: str = "alias"
    alias_tool_id: str
    primary_tool_id: str
    created_at: str
    created_by: str
```

**Acceptance Criteria**:

- ✅ Models validate correctly
- ✅ Seed data populates containers
- ✅ GitHub Copilot + Jules AI migrated

## Phase 2: Backend Implementation (Days 3-4)

### Day 3: ToolService

**Tasks**:

1. Create `ToolService` class
2. Implement CRUD operations
3. Implement alias resolution logic
4. Add validation (no circular aliases)

**Deliverables**:

```python
# backend/src/services/tool_service.py
class ToolService:
    async def create_tool(self, tool_data: Dict) -> Dict
    async def get_tool(self, tool_id: str) -> Optional[Dict]
    async def list_tools(self, page: int, limit: int, search: str, category: str) -> List[Dict]
    async def update_tool(self, tool_id: str, updates: Dict) -> Dict
    async def delete_tool(self, tool_id: str) -> bool
    async def create_alias(self, alias_tool_id: str, primary_tool_id: str, created_by: str) -> Dict
    async def get_aliases(self, primary_tool_id: str) -> List[Dict]
    async def remove_alias(self, alias_id: str) -> bool
    async def resolve_tool_id(self, tool_id: str) -> str
```

**Acceptance Criteria**:

- ✅ Create tool returns tool object
- ✅ List tools supports pagination
- ✅ Alias linking validates no self-reference
- ✅ Resolve tool ID follows alias chain

### Day 4: Admin Routes

**Tasks**:

1. Create `/api/admin/tools` routes
2. Add request/response models
3. Implement error handling
4. Add structured logging

**Deliverables**:

```python
# backend/src/api/admin_routes.py
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/tools")
async def create_tool(tool: ToolCreateRequest, tool_service: ToolService = Depends())

@router.get("/tools")
async def list_tools(page: int = 1, limit: int = 20, search: str = "", category: str = None)

@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str)

@router.put("/tools/{tool_id}")
async def update_tool(tool_id: str, updates: ToolUpdateRequest)

@router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str)

@router.put("/tools/{tool_id}/alias")
async def link_alias(tool_id: str, link: AliasLinkRequest)

@router.delete("/tools/{tool_id}/alias")
async def unlink_alias(tool_id: str)
```

**Acceptance Criteria**:

- ✅ All endpoints return correct HTTP status codes
- ✅ Validation errors return 400 with details
- ✅ Missing resources return 404
- ✅ Server errors return 500 with logs

## Phase 3: Frontend Implementation (Days 5-6)

### Day 5: AdminToolManagement Component

**Tasks**:

1. Create "Add New Tool" form
2. Add form validation
3. Implement API integration
4. Add success/error feedback

**Deliverables**:

```tsx
// frontend/src/components/AdminToolManagement.tsx
export function AdminToolManagement() {
  // Form state
  const [toolName, setToolName] = useState('');
  const [vendor, setVendor] = useState('');
  const [category, setCategory] = useState('code-completion');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');
  
  // Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/admin/tools', { name: toolName, vendor, category, description });
      setMessage('✓ Tool created successfully');
    } catch (error) {
      setMessage(`✗ ${error.message}`);
    }
  };
  
  // Glass-themed form
  return (
    <div className="glass-card p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Form fields with glass-input styling */}
      </form>
    </div>
  );
}
```

**Acceptance Criteria**:

- ✅ Form validates required fields
- ✅ Success message shows after creation
- ✅ Error message shows on failure
- ✅ Form resets after successful submission

### Day 6: Tool Management Table & Alias Linking

**Tasks**:

1. Create tool list table component
2. Add "Link Alias" modal
3. Add edit/delete actions
4. Implement alias visualization

**Deliverables**:

```tsx
// frontend/src/components/ToolTable.tsx
export function ToolTable() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [showAliasModal, setShowAliasModal] = useState(false);
  
  // Fetch tools on mount
  useEffect(() => {
    fetchTools();
  }, []);
  
  const fetchTools = async () => {
    const response = await api.get('/admin/tools');
    setTools(response.data.tools);
  };
  
  const handleLinkAlias = async (primaryToolId: string) => {
    await api.put(`/admin/tools/${selectedTool.id}/alias`, { primary_tool_id: primaryToolId });
    setShowAliasModal(false);
    fetchTools();
  };
  
  return (
    <>
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          {/* Table with edit/delete/link alias actions */}
        </table>
      </div>
      
      {showAliasModal && (
        <AliasLinkModal
          aliasToolName={selectedTool.name}
          tools={tools}
          onLink={handleLinkAlias}
          onClose={() => setShowAliasModal(false)}
        />
      )}
    </>
  );
}
```

**Acceptance Criteria**:

- ✅ Table displays all tools
- ✅ Alias status column shows linked relationships
- ✅ Modal allows selecting primary tool
- ✅ Alias link updates table immediately

## Phase 4: Integration & Testing (Day 7)

### Day 7: End-to-End Testing

**Tasks**:

1. Write backend unit tests
2. Write frontend component tests
3. E2E workflow testing
4. Performance testing

**Test Scenarios**:

**Backend Tests**:

```python
# backend/tests/test_tool_service.py
def test_create_tool():
    tool = await tool_service.create_tool({
        "name": "Cursor IDE",
        "vendor": "Anysphere",
        "category": "code-completion",
        "description": "AI-first code editor"
    })
    assert tool["name"] == "Cursor IDE"
    assert tool["slug"] == "cursor-ide"

def test_create_duplicate_tool():
    await tool_service.create_tool({"name": "Test Tool", ...})
    with pytest.raises(ValueError):
        await tool_service.create_tool({"name": "Test Tool", ...})

def test_link_alias():
    alias = await tool_service.create_alias("alias-id", "primary-id", "admin-123")
    assert alias["alias_tool_id"] == "alias-id"
    assert alias["primary_tool_id"] == "primary-id"

def test_resolve_alias():
    await tool_service.create_alias("codex-id", "openai-id", "admin-123")
    resolved_id = await tool_service.resolve_tool_id("codex-id")
    assert resolved_id == "openai-id"

def test_prevent_circular_alias():
    await tool_service.create_alias("a-id", "b-id", "admin-123")
    with pytest.raises(ValueError):
        await tool_service.create_alias("b-id", "a-id", "admin-123")
```

**Frontend Tests**:

```tsx
// frontend/src/components/__tests__/AdminToolManagement.test.tsx
describe('AdminToolManagement', () => {
  it('renders form correctly', () => {
    render(<AdminToolManagement />);
    expect(screen.getByLabelText('Tool Name')).toBeInTheDocument();
  });
  
  it('submits form and shows success message', async () => {
    const mockApi = jest.spyOn(api, 'post').mockResolvedValue({ data: { message: 'Success' } });
    render(<AdminToolManagement />);
    
    fireEvent.change(screen.getByLabelText('Tool Name'), { target: { value: 'Cursor IDE' } });
    fireEvent.change(screen.getByLabelText('Vendor'), { target: { value: 'Anysphere' } });
    fireEvent.click(screen.getByText('Add Tool'));
    
    await waitFor(() => {
      expect(screen.getByText('✓ Tool created successfully')).toBeInTheDocument();
    });
  });
});
```

**E2E Workflow**:

1. Create "Cursor IDE" tool via UI
2. Verify tool appears in database
3. Create "Codex" tool via UI
4. Link "Codex" → "OpenAI" via UI
5. Verify alias relationship in database
6. Query sentiment data and verify alias resolution

**Acceptance Criteria**:

- ✅ All backend tests pass (>90% coverage)
- ✅ All frontend tests pass
- ✅ E2E workflow completes successfully
- ✅ Performance: Tool creation < 500ms

## Rollout Strategy

### Production Deployment

**Pre-Deployment Checklist**:

- [ ] Backup existing database
- [ ] Create Cosmos DB containers in production
- [ ] Seed production data
- [ ] Verify environment variables
- [ ] Test admin routes in staging

**Deployment Steps**:

1. Deploy backend with new routes (non-breaking)
2. Create database containers in production
3. Run seed data script
4. Deploy frontend with new components
5. Smoke test: Create one tool manually
6. Monitor logs for errors

**Rollback Plan**:

- Backend: Revert to previous deployment (routes unused)
- Frontend: Revert to previous deployment
- Database: Containers remain (no impact on existing data)

### Post-Deployment

**Monitoring**:

- Track `/api/admin/tools` endpoint latency
- Monitor database query performance
- Alert on 5xx errors from admin routes

**Success Metrics** (Week 1):

- ✅ 3+ new tools added by admins
- ✅ 1+ alias link created
- ✅ 0 critical bugs reported
- ✅ Average tool creation time < 2 minutes

## Risk Mitigation

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| **Duplicate tool names** | Medium | Unique constraint + validation | ✅ Covered |
| **Circular aliases** | High | Graph traversal validation | ✅ Covered |
| **Database migration fails** | High | Backup + rollback script | ✅ Planned |
| **Performance degradation** | Medium | Indexing + caching strategy | ✅ Covered |
| **Admin authentication missing** | High | Phase 2: Add JWT auth | ⚠️ Future |

## Out of Scope (Future Enhancements)

- **Admin authentication**: Phase 2 (add JWT middleware)
- **Bulk tool import**: Phase 3 (CSV upload)
- **Tool versioning**: Phase 4 (track version changes)
- **Auto-detection**: Phase 5 (scrape tool names from Reddit)

## Open Questions

1. **Authentication**: When to add admin JWT auth? **→ Phase 2 (Week 2)**
2. **Soft vs hard delete**: How to handle tool deletion? **→ Soft delete (set status: "deleted")**
3. **Alias transitivity**: Should A→B→C resolve to C? **→ No, require direct link**
4. **Category management**: Predefined or admin-configurable? **→ Predefined for now**

## Next Steps After Approval

1. Create feature branch: `010-admin-tool-management`
2. Run `setup-plan.sh` to initialize spec structure
3. Start Day 1: Create Cosmos DB containers
4. Daily standups to track progress
5. Demo after Day 7 for user feedback
