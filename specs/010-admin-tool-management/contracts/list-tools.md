# API Contract: GET /api/admin/tools

List all AI tools with pagination, search, and filtering.

## Request

**Method**: `GET`
**Path**: `/api/admin/tools`
**Authentication**: Required (Admin JWT token)

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (min: 1) |
| limit | integer | No | 20 | Results per page (min: 1, max: 100) |
| search | string | No | "" | Search query (matches tool name) |
| category | string | No | null | Filter by category (enum) |

### Example Requests

**Basic**:

```http
GET /api/admin/tools
```

**Pagination**:

```http
GET /api/admin/tools?page=2&limit=10
```

**Search**:

```http
GET /api/admin/tools?search=copilot
```

**Filter by category**:

```http
GET /api/admin/tools?category=code-completion
```

**Combined**:

```http
GET /api/admin/tools?page=1&limit=10&search=ai&category=chat
```

## Response

### Success Response (200 OK)

```typescript
interface ToolListResponse {
  tools: Tool[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

interface Tool {
  id: string;
  name: string;
  slug: string;
  vendor: string;
  category: string;
  description: string;
  status: string;
  aliases?: ToolAlias[];        // Only if tool is primary
  primary_tool?: ToolReference;  // Only if tool is alias
  created_at: string;
  updated_at: string;
}

interface ToolAlias {
  id: string;
  alias_tool_id: string;
  alias_tool_name: string;
  created_at: string;
}

interface ToolReference {
  id: string;
  name: string;
}
```

### Example Success Response

```json
{
  "tools": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "GitHub Copilot",
      "slug": "github-copilot",
      "vendor": "GitHub",
      "category": "code-completion",
      "description": "AI pair programmer",
      "status": "active",
      "aliases": [],
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
      "name": "OpenAI",
      "slug": "openai",
      "vendor": "OpenAI",
      "category": "chat",
      "description": "GPT-powered AI assistant",
      "status": "active",
      "aliases": [
        {
          "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
          "alias_tool_id": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
          "alias_tool_name": "Codex",
          "created_at": "2025-01-15T12:00:00Z"
        }
      ],
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
      "name": "Codex",
      "slug": "codex",
      "vendor": "OpenAI",
      "category": "code-completion",
      "description": "Code generation model (deprecated)",
      "status": "active",
      "primary_tool": {
        "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
        "name": "OpenAI"
      },
      "created_at": "2025-01-14T08:00:00Z",
      "updated_at": "2025-01-15T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "pages": 1
  }
}
```

### Error Responses

**400 Bad Request** - Invalid query parameters

```json
{
  "error": "Invalid page number (must be >= 1)"
}
```

**500 Internal Server Error** - Database error

```json
{
  "error": "Internal server error"
}
```

## Backend Implementation

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/tools")
async def list_tools(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    category: Optional[str] = Query(None, regex="^(code-completion|chat|analysis)$"),
    tool_service: ToolService = Depends()
):
    try:
        # Get tools with pagination
        offset = (page - 1) * limit
        tools = await tool_service.list_tools(page, limit, search, category)
        
        # Enrich with alias information
        enriched_tools = []
        for tool in tools:
            # Get aliases where this tool is primary
            aliases = await tool_service.get_aliases(tool["id"])
            tool["aliases"] = aliases
            
            # Get primary tool if this tool is an alias
            primary = await tool_service.get_primary_tool(tool["id"])
            if primary:
                tool["primary_tool"] = {"id": primary["id"], "name": primary["name"]}
            
            enriched_tools.append(tool)
        
        # Get total count for pagination
        total = await tool_service.count_tools(search, category)
        pages = (total + limit - 1) // limit
        
        return {
            "tools": enriched_tools,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": pages
            }
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

## Frontend Implementation

```typescript
// src/services/api.ts
export interface ToolListParams {
  page?: number;
  limit?: number;
  search?: string;
  category?: 'code-completion' | 'chat' | 'analysis';
}

export interface ToolListResponse {
  tools: Tool[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export const listTools = async (params: ToolListParams = {}): Promise<ToolListResponse> => {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.search) queryParams.append('search', params.search);
  if (params.category) queryParams.append('category', params.category);
  
  const response = await api.get(`/admin/tools?${queryParams.toString()}`);
  return response.data;
};
```

## Testing

### Unit Test (Backend)

```python
def test_list_tools_success():
    response = await client.get("/api/admin/tools")
    assert response.status_code == 200
    assert "tools" in response.json()
    assert "pagination" in response.json()

def test_list_tools_pagination():
    response = await client.get("/api/admin/tools?page=2&limit=5")
    assert response.status_code == 200
    assert response.json()["pagination"]["page"] == 2
    assert response.json()["pagination"]["limit"] == 5

def test_list_tools_search():
    response = await client.get("/api/admin/tools?search=copilot")
    assert response.status_code == 200
    assert all("copilot" in tool["name"].lower() for tool in response.json()["tools"])

def test_list_tools_filter_category():
    response = await client.get("/api/admin/tools?category=chat")
    assert response.status_code == 200
    assert all(tool["category"] == "chat" for tool in response.json()["tools"])
```

### Integration Test

```bash
# List all tools
curl http://localhost:8000/api/admin/tools

# List page 2 with 10 results
curl http://localhost:8000/api/admin/tools?page=2&limit=10

# Search for "copilot"
curl http://localhost:8000/api/admin/tools?search=copilot

# Filter by category
curl http://localhost:8000/api/admin/tools?category=code-completion
```
