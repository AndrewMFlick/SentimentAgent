# API Contract: PUT /api/admin/tools/{tool_id}/alias

Link a tool as an alias of another primary tool. Sentiment data for the alias tool will be consolidated under the primary tool.

## Request

**Method**: `PUT`
**Path**: `/api/admin/tools/{tool_id}/alias`
**Content-Type**: `application/json`
**Authentication**: Required (Admin JWT token)

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| tool_id | string (UUID) | ID of the tool to set as alias |

### Request Body

```typescript
interface AliasLinkRequest {
  primary_tool_id: string;  // UUID of the primary tool
}
```

### Example Request

```json
{
  "primary_tool_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**URL**: `PUT /api/admin/tools/b2c3d4e5-f6a7-8901-2345-67890abcdef1/alias`

**Interpretation**: Set tool `b2c3d4e5...` (e.g., "Codex") as an alias of tool `a1b2c3d4...` (e.g., "OpenAI")

## Response

### Success Response (200 OK)

```typescript
interface AliasLinkResponse {
  message: string;
  alias_tool: {
    id: string;
    name: string;
  };
  primary_tool: {
    id: string;
    name: string;
  };
}
```

### Example Success Response

```json
{
  "message": "Alias linked successfully",
  "alias_tool": {
    "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
    "name": "Codex"
  },
  "primary_tool": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "OpenAI"
  }
}
```

### Error Responses

**400 Bad Request** - Validation error

```json
{
  "error": "Tool cannot be alias of itself"
}
```

```json
{
  "error": "Circular alias detected"
}
```

**404 Not Found** - Tool not found

```json
{
  "error": "Tool not found"
}
```

**500 Internal Server Error** - Database error

```json
{
  "error": "Internal server error"
}
```

## Validation Rules

| Rule | Check | Error Message |
|------|-------|---------------|
| Tool existence | Both tools must exist in database | "Tool not found" |
| Self-reference | `tool_id != primary_tool_id` | "Tool cannot be alias of itself" |
| Circular alias | No A→B and B→A relationships | "Circular alias detected" |
| Existing alias | Alias tool cannot already be primary for other tools | "Alias tool is already primary for other aliases" |

## Backend Implementation

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin", tags=["admin"])

class AliasLinkRequest(BaseModel):
    primary_tool_id: str = Field(..., regex="^[a-f0-9-]{36}$")

@router.put("/tools/{tool_id}/alias")
async def link_alias(
    tool_id: str,
    link: AliasLinkRequest,
    tool_service: ToolService = Depends()
):
    # Validate both tools exist
    alias_tool = await tool_service.get_tool(tool_id)
    primary_tool = await tool_service.get_tool(link.primary_tool_id)
    
    if not alias_tool or not primary_tool:
        raise HTTPException(404, "Tool not found")
    
    # Prevent self-referencing alias
    if tool_id == link.primary_tool_id:
        raise HTTPException(400, "Tool cannot be alias of itself")
    
    # Check for circular aliases
    if await tool_service.has_circular_alias(tool_id, link.primary_tool_id):
        raise HTTPException(400, "Circular alias detected")
    
    # Check if alias tool is already a primary
    existing_aliases = await tool_service.get_aliases(tool_id)
    if existing_aliases:
        raise HTTPException(400, "Alias tool is already primary for other aliases")
    
    # Create alias relationship
    try:
        await tool_service.create_alias(tool_id, link.primary_tool_id, "admin-123")
        return {
            "message": "Alias linked successfully",
            "alias_tool": {"id": alias_tool["id"], "name": alias_tool["name"]},
            "primary_tool": {"id": primary_tool["id"], "name": primary_tool["name"]}
        }
    except Exception as e:
        logger.error(f"Failed to link alias: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")
```

## Frontend Implementation

```typescript
// src/services/api.ts
export interface AliasLinkRequest {
  primary_tool_id: string;
}

export interface AliasLinkResponse {
  message: string;
  alias_tool: {
    id: string;
    name: string;
  };
  primary_tool: {
    id: string;
    name: string;
  };
}

export const linkAlias = async (
  aliasToolId: string,
  primaryToolId: string
): Promise<AliasLinkResponse> => {
  const response = await api.put(`/admin/tools/${aliasToolId}/alias`, {
    primary_tool_id: primaryToolId
  });
  return response.data;
};
```

## Circular Alias Detection

### Algorithm

```python
async def has_circular_alias(self, alias_tool_id: str, primary_tool_id: str) -> bool:
    """
    Detect circular aliases by checking if primary_tool_id is already
    an alias of alias_tool_id (directly or transitively).
    """
    visited = set()
    current_id = primary_tool_id
    
    while current_id:
        if current_id in visited:
            return True  # Circular reference detected
        
        visited.add(current_id)
        
        # Check if current_id is an alias of anything
        query = "SELECT * FROM ToolAliases ta WHERE ta.alias_tool_id = @id"
        items = list(self.aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": current_id}],
            enable_cross_partition_query=True
        ))
        
        if items:
            current_id = items[0]["primary_tool_id"]
        else:
            break
    
    return alias_tool_id in visited
```

### Example Scenarios

**Valid**: A → B (no circular reference)

```json
{
  "alias_tool_id": "codex-id",
  "primary_tool_id": "openai-id"
}
```

**Invalid**: A → B and B → A (circular reference)

```json
[
  {"alias_tool_id": "a-id", "primary_tool_id": "b-id"},
  {"alias_tool_id": "b-id", "primary_tool_id": "a-id"}  // ❌ Circular
]
```

**Invalid**: A → B → C → A (transitive circular reference)

```json
[
  {"alias_tool_id": "a-id", "primary_tool_id": "b-id"},
  {"alias_tool_id": "b-id", "primary_tool_id": "c-id"},
  {"alias_tool_id": "c-id", "primary_tool_id": "a-id"}  // ❌ Circular
]
```

## Testing

### Unit Test (Backend)

```python
def test_link_alias_success():
    response = await client.put(
        "/api/admin/tools/codex-id/alias",
        json={"primary_tool_id": "openai-id"}
    )
    assert response.status_code == 200
    assert response.json()["alias_tool"]["name"] == "Codex"
    assert response.json()["primary_tool"]["name"] == "OpenAI"

def test_link_alias_self_reference():
    response = await client.put(
        "/api/admin/tools/codex-id/alias",
        json={"primary_tool_id": "codex-id"}
    )
    assert response.status_code == 400
    assert "cannot be alias of itself" in response.json()["error"]

def test_link_alias_circular():
    # Create A → B
    await client.put("/api/admin/tools/a-id/alias", json={"primary_tool_id": "b-id"})
    
    # Try to create B → A
    response = await client.put("/api/admin/tools/b-id/alias", json={"primary_tool_id": "a-id"})
    assert response.status_code == 400
    assert "Circular alias" in response.json()["error"]
```

### Integration Test

```bash
# Link Codex as alias of OpenAI
curl -X PUT http://localhost:8000/api/admin/tools/codex-id/alias \
  -H "Content-Type: application/json" \
  -d '{
    "primary_tool_id": "openai-id"
  }'

# Expected response
{
  "message": "Alias linked successfully",
  "alias_tool": {
    "id": "codex-id",
    "name": "Codex"
  },
  "primary_tool": {
    "id": "openai-id",
    "name": "OpenAI"
  }
}

# Verify alias resolution in sentiment query
curl http://localhost:8000/api/sentiment/trends?tool_id=codex-id

# Should return sentiment data consolidated under "OpenAI"
```

## Impact on Sentiment Queries

### Before Alias Link

```sql
SELECT tool_id, AVG(sentiment_score)
FROM Sentiments
WHERE tool_id IN ('codex-id', 'openai-id')
GROUP BY tool_id
```

**Result**:

```text
codex-id   | 0.7
openai-id  | 0.6
```

### After Alias Link

```sql
SELECT 
  COALESCE(ta.primary_tool_id, s.tool_id) as resolved_tool_id,
  AVG(s.sentiment_score)
FROM Sentiments s
LEFT JOIN ToolAliases ta ON s.tool_id = ta.alias_tool_id
WHERE s.tool_id IN ('codex-id', 'openai-id')
GROUP BY COALESCE(ta.primary_tool_id, s.tool_id)
```

**Result**:

```text
openai-id  | 0.65  // Consolidated average
```
