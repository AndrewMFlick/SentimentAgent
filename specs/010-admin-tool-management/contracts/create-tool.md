# API Contract: POST /api/admin/tools

Create a new AI tool in the system.

## Request

**Method**: `POST`
**Path**: `/api/admin/tools`
**Content-Type**: `application/json`
**Authentication**: Required (Admin JWT token)

### Request Body

```typescript
interface ToolCreateRequest {
  name: string;           // Required, 1-100 chars, must be unique
  vendor: string;         // Required, 1-100 chars
  category: string;       // Required, enum: "code-completion" | "chat" | "analysis"
  description?: string;   // Optional, max 500 chars
}
```

### Example Request

```json
{
  "name": "Cursor IDE",
  "vendor": "Anysphere",
  "category": "code-completion",
  "description": "AI-first code editor with advanced autocomplete"
}
```

## Response

### Success Response (200 OK)

```typescript
interface ToolCreateResponse {
  id: string;
  message: string;
}
```

### Example Success Response

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Tool created successfully"
}
```

### Error Responses

**400 Bad Request** - Validation error

```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "name",
      "message": "Tool name is required"
    }
  ]
}
```

**409 Conflict** - Duplicate tool name

```json
{
  "error": "Tool name already exists"
}
```

**500 Internal Server Error** - Database error

```json
{
  "error": "Internal server error"
}
```

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| name | Required | "Tool name is required" |
| name | 1-100 characters | "Tool name must be 1-100 characters" |
| name | Unique | "Tool name already exists" |
| name | Alphanumeric + spaces/hyphens | "Tool name contains invalid characters" |
| vendor | Required | "Vendor name is required" |
| vendor | 1-100 characters | "Vendor name must be 1-100 characters" |
| category | Required | "Category is required" |
| category | Enum value | "Category must be code-completion, chat, or analysis" |
| description | Max 500 characters | "Description too long (max 500 characters)" |

## Backend Implementation

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin", tags=["admin"])

class ToolCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vendor: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., regex="^(code-completion|chat|analysis)$")
    description: str = Field(default="", max_length=500)

@router.post("/tools")
async def create_tool(tool: ToolCreateRequest, tool_service: ToolService = Depends()):
    # Check for duplicate name
    existing = await tool_service.get_tool_by_name(tool.name)
    if existing:
        raise HTTPException(409, "Tool name already exists")
    
    # Create tool
    try:
        result = await tool_service.create_tool(tool.dict())
        return {"id": result["id"], "message": "Tool created successfully"}
    except Exception as e:
        logger.error(f"Failed to create tool: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

## Frontend Implementation

```typescript
// src/services/api.ts
export interface ToolCreateRequest {
  name: string;
  vendor: string;
  category: 'code-completion' | 'chat' | 'analysis';
  description?: string;
}

export interface ToolCreateResponse {
  id: string;
  message: string;
}

export const createTool = async (tool: ToolCreateRequest): Promise<ToolCreateResponse> => {
  const response = await api.post('/admin/tools', tool);
  return response.data;
};
```

## Testing

### Unit Test (Backend)

```python
def test_create_tool_success():
    tool_data = {
        "name": "Cursor IDE",
        "vendor": "Anysphere",
        "category": "code-completion",
        "description": "AI-first code editor"
    }
    response = await client.post("/api/admin/tools", json=tool_data)
    assert response.status_code == 200
    assert "id" in response.json()

def test_create_tool_duplicate_name():
    tool_data = {"name": "GitHub Copilot", "vendor": "GitHub", "category": "code-completion"}
    response = await client.post("/api/admin/tools", json=tool_data)
    assert response.status_code == 409
    assert "already exists" in response.json()["error"]
```

### Integration Test

```bash
# Create tool via API
curl -X POST http://localhost:8000/api/admin/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cursor IDE",
    "vendor": "Anysphere",
    "category": "code-completion",
    "description": "AI-first code editor"
  }'

# Expected response
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Tool created successfully"
}
```
