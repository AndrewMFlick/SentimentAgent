# Admin Tool Management - Implementation Guide

This document provides comprehensive guidance for the Admin Tool Management feature implemented in Phase 010.

## Overview

The Admin Tool Management system enables administrators to:
- Manually add new AI tools to the system
- Link tool aliases for data consolidation (e.g., "Codex" → "OpenAI")
- View, edit, and manage all tools in a dashboard
- Prevent circular alias relationships
- Soft delete tools with historical data

## Architecture

### Backend Components

```
backend/src/
├── models/tool.py              # Pydantic models for Tool, ToolAlias, requests/responses
├── services/tool_service.py    # Business logic for tool CRUD and alias operations
├── api/admin.py                # Admin API endpoints with authentication
└── config.py                   # Admin-specific configuration

backend/scripts/
├── create_tool_containers.py   # Create Tools and ToolAliases containers
└── seed_tools.py               # Seed initial tool data
```

### Frontend Components

```
frontend/src/
├── components/
│   ├── AdminToolManagement.tsx      # Tool creation form
│   ├── ToolTable.tsx                # Tool list with pagination/search
│   ├── ToolEditModal.tsx            # Edit tool details
│   ├── AliasLinkModal.tsx           # Link alias to primary tool
│   └── DeleteConfirmationDialog.tsx # Delete confirmation
├── services/
│   ├── api.ts                       # API client methods
│   └── toolApi.ts                   # React hooks for tool operations
└── types/index.ts                   # TypeScript type definitions
```

## Database Schema

### Tools Container

```javascript
{
  "id": "uuid",                    // Primary key
  "partitionKey": "tool",          // Fixed partition key
  "name": "GitHub Copilot",        // Display name (unique)
  "slug": "github-copilot",        // URL-friendly identifier
  "vendor": "GitHub",              // Tool vendor/creator
  "category": "code_assistant",    // Enum: code_assistant, chatbot, etc.
  "description": "...",            // Optional description
  "status": "active",              // active | inactive | deleted
  "metadata": {},                  // Extensible metadata
  "created_at": "2025-01-15T...",  // ISO 8601 timestamp
  "updated_at": "2025-01-15T..."   // ISO 8601 timestamp
}
```

### ToolAliases Container

```javascript
{
  "id": "uuid",                    // Primary key
  "partitionKey": "alias",         // Fixed partition key
  "alias_tool_id": "codex-id",     // Tool ID serving as alias
  "primary_tool_id": "openai-id",  // Primary tool ID
  "created_at": "2025-01-15T...",  // ISO 8601 timestamp
  "created_by": "admin@example"    // Admin who created alias
}
```

## API Endpoints

### Tool Management

#### Create Tool
```http
POST /admin/tools
Headers: X-Admin-Token: <token>
Body: {
  "name": "New Tool",
  "vendor": "Vendor Name",
  "category": "code_assistant",
  "description": "Optional description",
  "metadata": {}
}

Response: {
  "tool": { /* tool object */ },
  "message": "Tool created successfully"
}
```

#### List Tools
```http
GET /admin/tools?page=1&limit=20&search=copilot&category=code_assistant
Headers: X-Admin-Token: <token>

Response: {
  "tools": [ /* array of tools */ ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

#### Get Tool Details
```http
GET /admin/tools/{tool_id}
Headers: X-Admin-Token: <token>

Response: {
  "tool": { /* tool object */ },
  "aliases": [ /* array of aliases */ ]
}
```

#### Update Tool
```http
PUT /admin/tools/{tool_id}
Headers: X-Admin-Token: <token>
Body: {
  "name": "Updated Name",
  "description": "Updated description"
}

Response: {
  "tool": { /* updated tool */ },
  "message": "Tool updated successfully"
}
```

#### Delete Tool
```http
DELETE /admin/tools/{tool_id}
Headers: X-Admin-Token: <token>

Response: {
  "message": "Tool deleted successfully"
}
```

### Alias Management

#### Link Alias
```http
PUT /admin/tools/{alias_tool_id}/alias
Headers: X-Admin-Token: <token>
Body: {
  "primary_tool_id": "primary-tool-uuid"
}

Response: {
  "alias": { /* alias object */ },
  "message": "Alias linked successfully"
}
```

#### Unlink Alias
```http
DELETE /admin/tools/{alias_tool_id}/alias
Headers: X-Admin-Token: <token>

Response: {
  "message": "Alias unlinked successfully"
}
```

## Business Logic

### Duplicate Name Validation

```python
async def create_tool(self, tool_data: ToolCreateRequest):
    # Check for duplicate name
    existing = await self.get_tool_by_name(tool_data.name)
    if existing:
        raise ValueError(f"Tool name '{tool_data.name}' already exists")
    
    # Create tool...
```

### Circular Alias Detection

```python
async def has_circular_alias(self, alias_tool_id: str, primary_tool_id: str) -> bool:
    """Detect circular alias references by traversing alias chain."""
    visited = set()
    current_id = primary_tool_id
    
    while current_id:
        if current_id in visited:
            return True  # Circular reference detected
        
        visited.add(current_id)
        
        # Check if current_id is an alias of something else
        alias = await self.get_alias_for_tool(current_id)
        if alias:
            current_id = alias["primary_tool_id"]
        else:
            break
    
    return alias_tool_id in visited
```

### Alias Resolution

```python
async def resolve_tool_id(self, tool_id: str) -> str:
    """Resolve tool ID to primary tool ID (follows alias chain)."""
    alias = await self.get_alias_for_tool(tool_id)
    return alias["primary_tool_id"] if alias else tool_id
```

### Soft Delete Strategy

```python
async def delete_tool(self, tool_id: str, hard_delete: bool = False) -> bool:
    """
    Delete tool with soft delete by default.
    
    Soft delete: Set status='deleted' (preserves historical data)
    Hard delete: Permanently remove from database
    """
    tool = await self.get_tool(tool_id)
    if not tool:
        return False
    
    if hard_delete:
        await self.tools_container.delete_item(item=tool_id, partition_key="tool")
    else:
        tool["status"] = "deleted"
        tool["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.tools_container.replace_item(item=tool_id, body=tool)
    
    return True
```

## Frontend Patterns

### Form Validation

```tsx
const [errors, setErrors] = useState<Record<string, string>>({});

const validateForm = (): boolean => {
  const newErrors: Record<string, string> = {};
  
  if (!formData.name.trim()) {
    newErrors.name = 'Tool name is required';
  } else if (formData.name.length > 100) {
    newErrors.name = 'Tool name must be less than 100 characters';
  }
  
  if (!formData.vendor.trim()) {
    newErrors.vendor = 'Vendor is required';
  }
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  if (!validateForm()) return;
  
  // Submit form...
};
```

### Loading States

```tsx
const [isLoading, setIsLoading] = useState(false);

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setIsLoading(true);
  
  try {
    const result = await api.createTool(formData, adminToken);
    toast.success(result.message);
  } catch (error) {
    toast.error(error.message);
  } finally {
    setIsLoading(false);
  }
};

return (
  <button disabled={isLoading}>
    {isLoading ? 'Creating...' : 'Create Tool'}
  </button>
);
```

### Cache Invalidation

```tsx
import { useQueryClient } from '@tanstack/react-query';

const queryClient = useQueryClient();

const handleCreate = async () => {
  const result = await api.createTool(formData, adminToken);
  
  // Invalidate tools list cache to trigger refetch
  queryClient.invalidateQueries(['tools']);
  queryClient.invalidateQueries(['tool', result.tool.id]);
};
```

## Testing

### Unit Tests

```python
# backend/tests/test_tool_service.py

@pytest.mark.asyncio
async def test_create_tool_duplicate_name(tool_service, mock_containers):
    """Test creating tool with duplicate name raises error."""
    # Mock existing tool with same name
    async def existing_tool_iter():
        yield {"name": "Existing Tool"}
    
    mock_containers[0].query_items.return_value = existing_tool_iter()
    
    tool_data = ToolCreateRequest(
        name="Existing Tool",
        vendor="Vendor",
        category=ToolCategory.CODE_ASSISTANT
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await tool_service.create_tool(tool_data)
```

### Integration Tests

```python
# backend/tests/test_admin_api.py

def test_create_tool_success(client, admin_token):
    """Test successful tool creation via API."""
    response = client.post(
        "/admin/tools",
        json={
            "name": "New Tool",
            "vendor": "Test Vendor",
            "category": "code_assistant"
        },
        headers={"X-Admin-Token": admin_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["tool"]["name"] == "New Tool"
    assert "message" in data
```

## Configuration

Admin-specific settings in `backend/src/config.py`:

```python
class Settings(BaseSettings):
    # Admin Tool Management
    admin_tools_max_per_page: int = 100
    admin_tools_default_per_page: int = 20
    admin_tool_name_max_length: int = 100
    admin_tool_description_max_length: int = 500
    admin_alias_max_per_tool: int = 50
```

## Error Handling

### Backend Error Responses

```python
try:
    tool = await tool_service.create_tool(tool_data)
    return {"tool": tool, "message": "Tool created successfully"}
except ValueError as e:
    # Validation errors (400 Bad Request)
    raise HTTPException(status_code=400, detail=str(e))
except HTTPException:
    # Re-raise HTTP exceptions
    raise
except Exception as e:
    # Unexpected errors (500 Internal Server Error)
    logger.error("Failed to create tool", error=str(e), exc_info=True)
    raise HTTPException(status_code=500, detail="Failed to create tool")
```

### Frontend Error Handling

```tsx
try {
  const result = await api.createTool(formData, adminToken);
  toast.success(result.message);
} catch (error: any) {
  if (error.response?.status === 400) {
    // Validation error
    toast.error(error.response.data.detail);
  } else if (error.response?.status === 401) {
    // Authentication error
    toast.error('Authentication required');
  } else {
    // Generic error
    toast.error('Failed to create tool. Please try again.');
  }
}
```

## Security Considerations

### Authentication

```python
def verify_admin(x_admin_token: Optional[str] = Header(None)) -> str:
    """Verify admin authentication token."""
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    # TODO: Implement proper token validation
    # - Verify JWT token
    # - Check user has admin role
    # - Validate token expiration
    
    return "admin"  # Placeholder
```

### Input Validation

- Use Pydantic models for request validation
- Sanitize tool names and descriptions
- Validate UUID format for tool IDs
- Check field length constraints
- Prevent SQL injection via parameterized queries

### Audit Logging

```python
logger.warning(
    "AUDIT: Tool created",
    action="create_tool",
    tool_id=tool["id"],
    tool_name=tool["name"],
    admin_user=admin_user,
    timestamp=datetime.utcnow().isoformat(),
    status="success"
)
```

## Performance Optimizations

### Pagination

```python
async def list_tools(self, page: int = 1, limit: int = 20):
    """List tools with pagination to limit query size."""
    offset = (page - 1) * limit
    
    query = f"""
        SELECT * FROM Tools t
        WHERE t.partitionKey = 'tool' AND t.status = 'active'
        ORDER BY t.name
        OFFSET {offset} LIMIT {limit}
    """
    
    # Execute query...
```

### Search Indexing

Tools container uses indexing policy optimized for name searches:

```python
indexing_policy = {
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [
        {"path": "/metadata/*"},
        {"path": '/"_etag"/?'}
    ]
}
```

### Caching Strategy

```tsx
// Frontend caching with React Query
const { data: tools } = useQuery(
  ['tools', page, search, category],
  () => api.listTools(page, limit, search, category, adminToken),
  {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  }
);
```

## Troubleshooting

### Common Issues

**Issue**: Duplicate name error when name is unique
- **Cause**: Case-insensitive comparison not implemented
- **Fix**: Normalize names to lowercase before comparison

**Issue**: Circular alias not detected
- **Cause**: Infinite loop in alias chain traversal
- **Fix**: Limit traversal depth and use visited set

**Issue**: Deleted tools appear in list
- **Cause**: Query not filtering by status
- **Fix**: Add `WHERE t.status != 'deleted'` to queries

**Issue**: Alias link fails silently
- **Cause**: Missing error handling in API endpoint
- **Fix**: Wrap in try-catch and return proper error response

## Future Enhancements

- [ ] Bulk import tools from CSV
- [ ] Tool versioning and change history
- [ ] Advanced search with full-text indexing
- [ ] Tool categories management UI
- [ ] Export tools to JSON/CSV
- [ ] Role-based access control (RBAC)
- [ ] Approval workflow for tool changes
- [ ] API rate limiting for admin endpoints
- [ ] Tool logo/icon upload
- [ ] Integration with external tool databases

## References

- **Spec**: `/specs/010-admin-tool-management/spec.md`
- **Data Model**: `/specs/010-admin-tool-management/data-model.md`
- **API Contracts**: `/specs/010-admin-tool-management/contracts/`
- **Implementation Plan**: `/specs/010-admin-tool-management/plan.md`
- **Tasks**: `/specs/010-admin-tool-management/tasks.md`
