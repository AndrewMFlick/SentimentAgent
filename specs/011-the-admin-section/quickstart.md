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

### Pre-Deployment Validation

- [ ] Run all unit tests: `cd backend && pytest tests/ -v`
- [ ] Run integration tests: `pytest tests/integration/ -v`
- [ ] Check linting: `ruff check backend/src/`
- [ ] Review security scan results (CodeQL)
- [ ] Verify environment variables are set correctly
- [ ] Backup existing database containers

### Database Migration

- [ ] Run database migration script to update existing Tool schema
  ```bash
  cd backend/scripts
  python migrate_tool_schema.py --dry-run  # Preview changes
  python migrate_tool_schema.py            # Execute migration
  ```
- [ ] Create ToolMergeRecords container
  ```bash
  python create_admin_containers.py --container=ToolMergeRecords
  ```
- [ ] Create AdminActionLogs container
  ```bash
  python create_admin_containers.py --container=AdminActionLogs
  ```
- [ ] Verify composite indexes are created (production only, emulator has limitations)
- [ ] Run data validation queries to ensure schema compatibility

### Backend Deployment

- [ ] Deploy backend with new API endpoints
  ```bash
  # Build and test locally first
  cd backend
  ./start.sh
  curl http://localhost:8000/health
  ```
- [ ] Verify all 18 admin API endpoints are accessible:
  - GET/POST /admin/tools (list, create)
  - GET/PUT/DELETE /admin/tools/{tool_id} (get, update, delete)
  - POST /admin/tools/{tool_id}/archive
  - POST /admin/tools/{tool_id}/unarchive
  - PUT /admin/tools/{tool_id}/alias
  - DELETE /admin/tools/{alias_tool_id}/alias
  - POST /admin/tools/merge
  - GET /admin/tools/{tool_id}/merge-history
  - GET /admin/tools/{tool_id}/audit-log
  - POST /admin/reanalysis/trigger
  - GET /admin/reanalysis/jobs (list, get, status, cancel)
- [ ] Test admin authentication with valid/invalid tokens
- [ ] Verify error handling returns proper status codes (400, 401, 404, 409, 500)
- [ ] Check structured logging is working (view logs for admin actions)

### Frontend Deployment

- [ ] Deploy frontend with updated components
  ```bash
  cd frontend
  npm run build
  npm run preview  # Test production build
  ```
- [ ] Verify all admin components render correctly:
  - AdminToolManagement (list view, create form)
  - ToolTable (with filters, search, pagination)
  - ToolEditModal (multi-category selection)
  - ToolMergeModal (merge workflow)
  - AuditLogViewer (history tracking)
  - ErrorBoundary (error handling)
  - ToolTableSkeleton (loading states)
- [ ] Test responsive design on mobile/tablet/desktop
- [ ] Verify glass morphism styling is consistent
- [ ] Check keyboard shortcuts work (Esc to close modals, etc.)
- [ ] Test accessibility (WCAG 2.1 AA compliance)

### Post-Deployment Validation

- [ ] Verify existing tools display correctly with new schema
  - Single category migrated to categories array
  - Status field shows "active" for existing tools
  - created_by/updated_by populated with "system"
- [ ] Test full CRUD workflow:
  - Create new tool with multiple categories
  - Edit tool (change name, vendor, categories)
  - Archive tool, verify it's hidden from active list
  - Unarchive tool, verify it returns to active list
  - Delete tool (if no sentiment data)
- [ ] Test merge workflow in production:
  - Select 2-3 tools to merge
  - Verify sentiment data consolidation
  - Check merge record created
  - Validate audit log entries
- [ ] Test optimistic concurrency (edit same tool from 2 browser tabs)
- [ ] Verify cache invalidation after mutations
- [ ] Monitor audit logs for completeness
- [ ] Check performance metrics (queries <3s)

### Monitoring & Alerting

- [ ] Set up alerts for slow queries (>3s threshold)
- [ ] Monitor admin action frequency and patterns
- [ ] Track error rates on admin endpoints
- [ ] Review audit logs daily for suspicious activity
- [ ] Monitor database RU consumption for cost optimization

### Rollback Plan

If issues are detected:

1. **Database**: Keep backup containers, restore if needed
2. **Backend**: Revert to previous deployment, keep old endpoints active
3. **Frontend**: Rollback to previous version via version control
4. **Data**: Use AdminActionLog to identify and revert recent changes

## Troubleshooting

### Database Issues

#### Issue: Migration fails with category validation error

**Symptoms**: 
- Error: "Must have 1-5 categories" during migration
- Tools with empty or >5 categories fail validation

**Cause**: Existing tools have invalid category values  

**Solution**: 
```python
# Update migration script to map old categories to new enum values
for tool in existing_tools:
    # Map old single category to array
    old_category = tool.get('category', 'code-completion')
    tool['categories'] = [map_old_to_new_category(old_category)]
    
    # Ensure categories is valid
    if not tool['categories'] or len(tool['categories']) > 5:
        tool['categories'] = ['code-completion']  # Default
```

**Prevention**: Run dry-run migration first to identify problematic records

#### Issue: Container creation fails in emulator

**Symptoms**:
- Error: "replace_container is not supported" in CosmosDB emulator
- Composite indexes not created

**Cause**: CosmosDB emulator has limited feature support

**Solution**:
- Composite indexes are optional for development
- They will be created automatically in production Azure Cosmos DB
- For emulator, use basic queries without composite indexes

**Prevention**: Test with production Azure Cosmos DB before final deployment

#### Issue: Database connection timeout during migration

**Symptoms**:
- Migration script hangs or times out
- Partial data migrated

**Cause**: Too many tools to migrate in single batch

**Solution**:
```python
# Process in batches of 100 tools
batch_size = 100
for i in range(0, len(tools), batch_size):
    batch = tools[i:i+batch_size]
    await asyncio.gather(*[migrate_tool(tool) for tool in batch])
    logger.info(f"Migrated {i+len(batch)}/{len(tools)} tools")
```

### API Issues

#### Issue: 401 Unauthorized on all admin endpoints

**Symptoms**:
- All admin API calls return 401
- Valid admin token rejected

**Cause**: Admin token not set or incorrect

**Solution**:
```bash
# Check environment variable
echo $ADMIN_SECRET_TOKEN

# Set in backend/.env
ADMIN_SECRET_TOKEN=your-secure-token-here

# Restart backend
./start.sh
```

**Prevention**: Validate admin token on startup

#### Issue: 409 Conflict on concurrent edits

**Symptoms**:
- Error: "Tool was modified by another administrator"
- Edit operation fails with 409 status

**Cause**: Another admin edited the tool simultaneously (optimistic concurrency)

**Solution**:
- This is expected behavior for concurrent edits
- Frontend should refresh tool data and prompt user to retry
- User can review latest changes and reapply their edits

**Prevention**: Design for this scenario - it's a feature, not a bug

#### Issue: Merge operation times out

**Symptoms**:
- POST /admin/tools/merge hangs or returns 504
- Sentiment data migration incomplete

**Cause**: Too many sentiment records to migrate (>10,000)

**Solution**: 
```python
# In tool_service.py, implement batching
async def _migrate_sentiment_data(self, source_id, target_id):
    batch_size = 1000
    total_migrated = 0
    
    while True:
        # Query batch
        query = f"SELECT * FROM c WHERE c.tool_id = '{source_id}' OFFSET {total_migrated} LIMIT {batch_size}"
        records = list(self.sentiment_container.query_items(query))
        
        if not records:
            break
            
        # Update and replace
        for record in records:
            record['tool_id'] = target_id
            record['original_tool_id'] = source_id
            await self.sentiment_container.upsert_item(record)
        
        total_migrated += len(records)
        logger.info(f"Migrated {total_migrated} sentiment records")
    
    return total_migrated
```

**Prevention**: Add progress tracking and consider background job for large merges

### Frontend Issues

#### Issue: Frontend shows stale tool data after merge

**Symptoms**:
- Merged tool still shows as separate tools
- Source tools not marked as archived

**Cause**: React Query cache not invalidated  

**Solution**: 
```tsx
// Ensure cache invalidation after merge
const mutation = useMutation({
  mutationFn: api.mergeTool,
  onSuccess: () => {
    // Invalidate all related queries
    queryClient.invalidateQueries(['tools']);
    queryClient.invalidateQueries(['merge-history']);
    queryClient.invalidateQueries(['audit-log']);
    
    toast.success('Tools merged successfully');
  }
});
```

**Prevention**: Always invalidate cache after mutations

#### Issue: Categories not displaying as array

**Symptoms**:
- Only one category shown instead of multiple
- Categories appear as string instead of array

**Cause**: Frontend type mismatch or backend not returning array

**Solution**:
```tsx
// Ensure categories is always treated as array
{tool.categories?.map(category => (
  <Badge key={category} variant="secondary">
    {category}
  </Badge>
)) || <Badge variant="secondary">No categories</Badge>}
```

**Prevention**: Add TypeScript strict null checks

#### Issue: Modal doesn't close on Esc key

**Symptoms**:
- Esc key has no effect
- Modal can only be closed via button

**Cause**: Keyboard event listener not attached or removed incorrectly

**Solution**:
```tsx
// Ensure proper cleanup
useEffect(() => {
  const handleEsc = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && !isSubmitting) {
      onClose();
    }
  };

  if (isOpen) {
    document.addEventListener('keydown', handleEsc);
  }

  return () => {
    document.removeEventListener('keydown', handleEsc);
  };
}, [isOpen, isSubmitting, onClose]);
```

**Prevention**: Test keyboard shortcuts in all modals

### Performance Issues

#### Issue: Slow query warnings in logs

**Symptoms**:
- Log entries: "Slow query detected" (>3s)
- Tool list takes >5s to load

**Cause**: Missing composite indexes or inefficient query

**Solution**:
1. **Add composite indexes** (production only):
   ```python
   composite_indexes = [
       {"path": ["/status", "/name"]},
       {"path": ["/status", "/vendor"]},
       {"path": ["/status", "/updated_at"]}
   ]
   ```

2. **Optimize query**:
   ```python
   # Instead of filtering in Python
   query = "SELECT * FROM c WHERE c.partitionKey = 'TOOL'"
   tools = [t for t in tools if t.status == 'active']
   
   # Use CosmosDB query
   query = "SELECT * FROM c WHERE c.partitionKey = 'TOOL' AND c.status = 'active'"
   ```

3. **Add pagination**:
   ```python
   # Limit results
   query += f" OFFSET {(page-1)*limit} LIMIT {limit}"
   ```

**Prevention**: Monitor query performance and add indexes proactively

#### Issue: High RU consumption on audit log queries

**Symptoms**:
- Cosmos DB RU charges spike during admin operations
- Audit log queries consume >100 RUs

**Cause**: Partition key strategy or inefficient queries

**Solution**:
```python
# Use partition key in queries
partition_key = datetime.now().strftime("%Y%m")  # Current month
query = f"SELECT * FROM c WHERE c.partitionKey = '{partition_key}' AND c.tool_id = '{tool_id}'"

# Instead of cross-partition query
query = f"SELECT * FROM c WHERE c.tool_id = '{tool_id}'"  # Scans all partitions
```

**Prevention**: Design partition keys for common query patterns

### Security Issues

#### Issue: Sensitive data in audit logs

**Symptoms**:
- API keys or tokens in before/after state
- User PII in logs

**Cause**: No sanitization of logged data

**Solution**:
```python
# Sanitize before logging
def sanitize_state(state: dict) -> dict:
    """Remove sensitive fields from state."""
    sensitive_fields = ['api_key', 'token', 'password', 'secret']
    return {k: v for k, v in state.items() if k not in sensitive_fields}

# In _log_admin_action
before_state = sanitize_state(before) if before else None
after_state = sanitize_state(after) if after else None
```

**Prevention**: Never log sensitive data, use field redaction

### Common Error Messages

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| 400 | "Must have 1-5 categories" | Invalid categories count | Ensure 1-5 categories selected |
| 400 | "Tool name already exists" | Duplicate tool name | Choose unique name |
| 400 | "Circular alias detected" | Tool aliases itself | Check alias chain |
| 401 | "Unauthorized" | Missing/invalid admin token | Set ADMIN_SECRET_TOKEN |
| 404 | "Tool not found" | Invalid tool_id | Verify tool exists |
| 409 | "Tool was modified" | Concurrent edit (ETag mismatch) | Refresh and retry |
| 409 | "Cannot archive tool with references" | Other tools reference this tool | Remove references first |
| 500 | "Failed to merge tools" | Database error during merge | Check logs, retry |

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: `tail -f backend/logs/app.log`
2. **Review audit log**: Use AuditLogViewer to see recent admin actions
3. **Verify environment**: `cat backend/.env` and compare with `.env.example`
4. **Test with curl**: Isolate frontend vs backend issues
5. **Contact support**: Include error message, timestamp, and reproduction steps

## Next Steps

After implementation:

1. Monitor AdminActionLog for usage patterns
2. Optimize queries based on most common filters
3. Consider implementing bulk operations (archive multiple tools)
4. Add export functionality for audit logs
5. Implement tool usage analytics based on sentiment data
