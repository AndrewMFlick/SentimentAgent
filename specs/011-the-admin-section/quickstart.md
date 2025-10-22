# Quickstart: Admin Tool List Management

**Feature**: 011-the-admin-section  
**Purpose**: Get started with implementing comprehensive tool list management  
**Audience**: Developers implementing this feature

## Overview

This feature extends the existing admin tool management system (Feature 010) with comprehensive CRUD operations, multi-category support, archive/unarchive, permanent deletion, and tool merging for acquisition scenarios.

## Prerequisites

Before starting implementation:

1. ✅ Feature 010 (admin-tool-management) is merged and deployed
2. ✅ Existing Tools and ToolAliases containers in Cosmos DB
3. ✅ Admin authentication system in place
4. ✅ Frontend has AdminPanel and AdminToolManagement components
5. ✅ Backend has tool_service.py and admin.py routes

## Quick Reference

### New Containers to Create

```python
# backend/scripts/create_admin_containers.py
containers_to_create = [
    {
        "name": "ToolMergeRecords",
        "partition_key": "/partitionKey",
        "indexes": [...]
    },
    {
        "name": "AdminActionLogs",
        "partition_key": "/partitionKey",  # YYYYMM format
        "indexes": [...]
    }
]
```

### Data Migration Required

Existing Tool documents need schema updates:

```python
# Migration script
for tool in existing_tools:
    # Convert category (single) to categories (array)
    tool['categories'] = [tool['category']]
    del tool['category']
    
    # Add new fields
    tool['status'] = 'active'
    tool['merged_into'] = None
    tool['created_by'] = 'system'
    tool['updated_by'] = 'system'
```

## Implementation Path

### Phase 1: Data Layer (Backend)

**Estimated Time**: 4-6 hours

1. **Update Data Models** (`backend/src/models/tool.py`):

   ```python
   class Tool(BaseModel):
       id: str
       partitionKey: str = Field(default="TOOL")
       name: str
       slug: str
       vendor: str
       categories: List[str]  # Changed from single category
       status: Literal["active", "archived"] = "active"  # New
       description: Optional[str] = None
       merged_into: Optional[str] = None  # New
       created_at: datetime
       updated_at: datetime
       created_by: str  # New
       updated_by: str  # New
       
       @field_validator('categories')
       @classmethod
       def validate_categories(cls, v):
           if not (1 <= len(v) <= 5):
               raise ValueError("Must have 1-5 categories")
           if len(v) != len(set(v)):
               raise ValueError("Categories must be unique")
           return v
   ```

2. **Create New Models**:

   ```python
   class ToolMergeRecord(BaseModel):
       id: str
       partitionKey: str
       target_tool_id: str
       source_tool_ids: List[str]
       merged_at: datetime
       merged_by: str
       sentiment_count: int
       # ... other fields from data-model.md
   
   class AdminActionLog(BaseModel):
       id: str
       partitionKey: str  # YYYYMM
       timestamp: datetime
       admin_id: str
       action_type: Literal["create", "edit", "archive", "unarchive", "delete", "merge"]
       tool_id: str
       # ... other fields from data-model.md
   ```

3. **Extend Tool Service** (`backend/src/services/tool_service.py`):

   ```python
   class ToolService:
       # Existing methods: create_tool, get_tool, list_tools...
       
       # New methods:
       def archive_tool(self, tool_id: str, admin_id: str) -> Tool
       def unarchive_tool(self, tool_id: str, admin_id: str) -> Tool
       def delete_tool(self, tool_id: str, admin_id: str) -> None
       def merge_tools(
           self, 
           target_tool_id: str,
           source_tool_ids: List[str],
           target_categories: List[str],
           target_vendor: str,
           admin_id: str,
           notes: Optional[str] = None
       ) -> ToolMergeRecord
       
       # Helper methods:
       def _validate_merge(self, target_id, source_ids) -> List[str]  # Returns warnings
       def _migrate_sentiment_data(self, source_id, target_id) -> int  # Returns count
       def _log_admin_action(self, action_type, tool_id, before, after, admin_id) -> None
   ```

### Phase 2: API Layer (Backend)

**Estimated Time**: 3-4 hours

1. **Extend Admin Routes** (`backend/src/api/admin.py`):

   ```python
   # New endpoints:
   @router.get("/admin/tools")  # Extended with filtering, pagination
   async def list_tools(
       status: str = "active",
       category: Optional[List[str]] = Query(None),
       vendor: Optional[str] = None,
       search: Optional[str] = None,
       page: int = 1,
       limit: int = 50
   )
   
   @router.put("/admin/tools/{tool_id}")  # New
   async def update_tool(tool_id: str, data: ToolUpdateRequest, if_match: str = Header(...))
   
   @router.post("/admin/tools/{tool_id}/archive")  # New
   async def archive_tool(tool_id: str)
   
   @router.post("/admin/tools/{tool_id}/unarchive")  # New
   async def unarchive_tool(tool_id: str)
   
   @router.delete("/admin/tools/{tool_id}")  # New
   async def delete_tool(tool_id: str)
   
   @router.post("/admin/tools/merge")  # New
   async def merge_tools(data: ToolMergeRequest)
   
   @router.get("/admin/tools/{tool_id}/merge-history")  # New
   async def get_merge_history(tool_id: str)
   
   @router.get("/admin/tools/{tool_id}/audit-log")  # New
   async def get_audit_log(tool_id: str)
   ```

### Phase 3: Frontend Components

**Estimated Time**: 6-8 hours

1. **Extend AdminToolManagement Component**:

   ```tsx
   // frontend/src/components/AdminToolManagement.tsx
   export default function AdminToolManagement() {
     // State for filters
     const [statusFilter, setStatusFilter] = useState<'active' | 'archived' | 'all'>('active');
     const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
     const [searchQuery, setSearchQuery] = useState('');
     
     // New actions
     const handleEdit = (tool: Tool) => { /* Open edit modal */ };
     const handleArchive = (tool: Tool) => { /* Show confirmation, call API */ };
     const handleDelete = (tool: Tool) => { /* Strong confirmation, call API */ };
     const handleMerge = (tools: Tool[]) => { /* Open merge modal */ };
     
     return (
       <div className="glass-card p-6">
         {/* Filters */}
         <ToolFilters 
           statusFilter={statusFilter}
           categoryFilter={categoryFilter}
           searchQuery={searchQuery}
           onStatusChange={setStatusFilter}
           onCategoryChange={setCategoryFilter}
           onSearchChange={setSearchQuery}
         />
         
         {/* Tool Table */}
         <ToolTable 
           tools={filteredTools}
           onEdit={handleEdit}
           onArchive={handleArchive}
           onDelete={handleDelete}
           onMerge={handleMerge}
         />
         
         {/* Modals */}
         <ToolEditModal />
         <ToolMergeModal />
         <DeleteConfirmationDialog />
       </div>
     );
   }
   ```

2. **Create ToolMergeModal Component**:

   ```tsx
   // frontend/src/components/ToolMergeModal.tsx
   export default function ToolMergeModal({ 
     isOpen, 
     onClose, 
     targetTool, 
     sourceTools 
   }: ToolMergeModalProps) {
     const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
     const [warnings, setWarnings] = useState<MergeWarning[]>([]);
     
     const handleMerge = async () => {
       const result = await toolApi.mergeTools({
         target_tool_id: targetTool.id,
         source_tool_ids: sourceTools.map(t => t.id),
         target_categories: selectedCategories,
         target_vendor: targetTool.vendor,
         notes: mergeNotes
       });
       
       if (result.warnings) {
         setWarnings(result.warnings);
       }
       
       toast.success(`Merged ${sourceTools.length} tools successfully`);
       onClose();
     };
     
     return (
       <Dialog open={isOpen} onOpenChange={onClose}>
         <DialogContent className="glass-card">
           {/* Merge details */}
           {/* Metadata comparison */}
           {/* Warning display */}
           {/* Confirm button */}
         </DialogContent>
       </Dialog>
     );
   }
   ```

### Phase 4: Testing

**Estimated Time**: 4-5 hours

1. **Backend Unit Tests**:

   ```python
   # backend/tests/test_tool_service.py
   def test_archive_tool():
       # Test archiving active tool
       # Verify status changed to archived
       # Verify sentiment data preserved
   
   def test_merge_tools():
       # Test merging 2 tools
       # Verify sentiment data migrated
       # Verify source tools archived
       # Verify merge record created
   
   def test_merge_with_warnings():
       # Test merging tools with different vendors
       # Verify warnings returned
       # Verify merge still succeeds
   ```

2. **Backend Integration Tests**:

   ```python
   # backend/tests/integration/test_admin_tool_management.py
   async def test_full_tool_lifecycle():
       # Create tool
       # Edit tool (add categories)
       # Archive tool
       # Unarchive tool
       # Delete tool
       # Verify audit log
   
   async def test_merge_workflow():
       # Create 3 tools
       # Merge 2 into 1
       # Verify sentiment data consolidated
       # Verify merge history queryable
   ```

3. **Frontend Component Tests**:

   ```tsx
   // frontend/tests/components/ToolMergeModal.test.tsx
   describe('ToolMergeModal', () => {
     it('shows metadata warnings when vendors differ', () => {
       // Render with different vendors
       // Verify warning displayed
     });
     
     it('allows multi-select categories', () => {
       // Select multiple categories
       // Verify all selected
       // Verify max 5 limit
     });
   });
   ```

## Common Patterns

### Pattern 1: Multi-Category Rendering

```tsx
// Display tool with multiple categories
<div className="flex gap-2 flex-wrap">
  {tool.categories.map(category => (
    <Badge key={category} variant="secondary">
      {category}
    </Badge>
  ))}
</div>
```

### Pattern 2: Optimistic Concurrency

```python
# Backend: Use ETag for concurrent edits
try:
    container.replace_item(
        item=tool_id,
        body=updated_tool,
        match_condition=MatchConditions.IfNotModified,
        etag=request_etag
    )
except PreconditionFailedError:
    raise HTTPException(
        status_code=409,
        detail="Tool was modified by another administrator"
    )
```

```tsx
// Frontend: Handle 409 conflicts
try {
  await toolApi.updateTool(tool.id, updates, tool._etag);
} catch (error) {
  if (error.status === 409) {
    toast.error('Tool was modified by another admin. Refreshing...');
    await refetchTools();
  }
}
```

### Pattern 3: Audit Logging

```python
# Log every admin action
async def _log_admin_action(
    self,
    action_type: str,
    tool_id: str,
    before_state: Optional[dict],
    after_state: Optional[dict],
    admin_id: str
):
    log_entry = AdminActionLog(
        id=str(uuid.uuid4()),
        partitionKey=datetime.now().strftime("%Y%m"),
        timestamp=datetime.now(),
        admin_id=admin_id,
        action_type=action_type,
        tool_id=tool_id,
        tool_name=after_state.get('name') if after_state else before_state.get('name'),
        before_state=before_state,
        after_state=after_state,
        metadata={}
    )
    await self.logs_container.create_item(log_entry.dict())
```

## Deployment Checklist

- [ ] Run database migration script to update existing Tool schema
- [ ] Create ToolMergeRecords container
- [ ] Create AdminActionLogs container  
- [ ] Deploy backend with new API endpoints
- [ ] Deploy frontend with updated components
- [ ] Test admin authentication still works
- [ ] Verify existing tools display correctly with new schema
- [ ] Test full merge workflow in production
- [ ] Monitor audit logs for completeness

## Troubleshooting

### Issue: Migration fails with category validation error

**Cause**: Existing tools have invalid category values  
**Solution**: Update migration script to map old categories to new enum values

### Issue: Merge operation times out

**Cause**: Too many sentiment records to migrate  
**Solution**: Implement batching in sentiment migration, process 1000 records at a time

### Issue: Frontend shows stale tool data after merge

**Cause**: Cache not invalidated  
**Solution**: Ensure `queryClient.invalidateQueries(['tools'])` is called after merge

## Next Steps

After implementation:

1. Monitor AdminActionLog for usage patterns
2. Optimize queries based on most common filters
3. Consider implementing bulk operations (archive multiple tools)
4. Add export functionality for audit logs
5. Implement tool usage analytics based on sentiment data
