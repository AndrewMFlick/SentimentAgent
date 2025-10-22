# API Contract: List Tools

**Endpoint**: `GET /api/v1/admin/tools`  
**Purpose**: Retrieve a filtered, paginated list of tools  
**Authentication**: Required (Admin token)

## Request

### Headers

```http
GET /api/v1/admin/tools?status=active&category=code_assistant&vendor=GitHub&search=copilot&page=1&limit=50
Authorization: Bearer {admin_token}
X-Admin-Token: {admin_token}
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | "active" | Filter by status: "active", "archived", "all" |
| `category` | string | No | null | Filter by single category (can specify multiple times) |
| `vendor` | string | No | null | Filter by exact vendor name |
| `search` | string | No | null | Search in tool name (case-insensitive, prefix match) |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `limit` | integer | No | 50 | Items per page (max 100) |
| `sort_by` | string | No | "name" | Sort field: "name", "vendor", "created_at", "updated_at" |
| `sort_order` | string | No | "asc" | Sort order: "asc", "desc" |

**Examples**:

```http
# Get all active tools
GET /api/v1/admin/tools

# Get archived tools only
GET /api/v1/admin/tools?status=archived

# Filter by category (code assistants only)
GET /api/v1/admin/tools?category=code_assistant

# Search for GitHub tools
GET /api/v1/admin/tools?vendor=GitHub

# Search by name
GET /api/v1/admin/tools?search=copilot

# Combined filters
GET /api/v1/admin/tools?status=active&category=code_assistant&vendor=GitHub

# Pagination
GET /api/v1/admin/tools?page=2&limit=25
```

## Response

### Success (200 OK)

```json
{
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "GitHub Copilot",
      "slug": "github-copilot",
      "vendor": "GitHub",
      "categories": ["code_assistant", "autonomous_agent"],
      "status": "active",
      "description": "AI pair programmer that helps you write code faster",
      "merged_into": null,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2025-10-20T14:30:00Z",
      "created_by": "admin-user-123",
      "updated_by": "admin-user-456",
      "_etag": "\"0000d192-0000-0200-0000-67123abc0000\""
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Cursor",
      "slug": "cursor",
      "vendor": "Cursor Technologies",
      "categories": ["code_assistant"],
      "status": "active",
      "description": "AI-first code editor",
      "merged_into": null,
      "created_at": "2024-03-20T10:00:00Z",
      "updated_at": "2024-03-20T10:00:00Z",
      "created_by": "admin-user-123",
      "updated_by": "admin-user-123",
      "_etag": "\"0000d192-0000-0200-0000-67123abc0001\""
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 127,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "filters_applied": {
    "status": "active",
    "category": null,
    "vendor": null,
    "search": null
  }
}
```

### Validation Errors (400 Bad Request)

```json
{
  "error": "Invalid request parameters",
  "details": {
    "status": "Must be one of: active, archived, all",
    "limit": "Must be between 1 and 100",
    "sort_by": "Must be one of: name, vendor, created_at, updated_at"
  }
}
```

### Unauthorized (401)

```json
{
  "error": "Unauthorized",
  "message": "Valid admin authentication required"
}
```

### Server Error (500)

```json
{
  "error": "Internal server error",
  "message": "Failed to retrieve tools"
}
```

## Business Rules

1. **Default Filter**: If no `status` parameter provided, default to "active" tools only
2. **Category Filter**: Can filter by multiple categories by specifying parameter multiple times: `?category=code_assistant&category=autonomous_agent`
3. **Search**: Case-insensitive prefix matching on tool name
4. **Pagination**: 
   - Maximum 100 items per page
   - Returns empty array if page exceeds total pages
   - Page numbers are 1-indexed
5. **Sorting**: 
   - Default sort: alphabetically by name ascending
   - Multiple sort fields not supported
6. **Performance**: 
   - Should return results in <3 seconds even for 500+ tools
   - Uses indexed queries for filtering

## Examples

### Example 1: Get All Active Code Assistants

**Request**:
```http
GET /api/v1/admin/tools?status=active&category=code_assistant
X-Admin-Token: dev-admin-secret-key-2024
```

**Response** (200):
```json
{
  "tools": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "GitHub Copilot",
      "slug": "github-copilot",
      "vendor": "GitHub",
      "categories": ["code_assistant", "autonomous_agent"],
      "status": "active",
      "description": "AI pair programmer",
      "merged_into": null,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2025-10-20T14:30:00Z",
      "created_by": "admin-user-123",
      "updated_by": "admin-user-456",
      "_etag": "\"0000d192-0000-0200-0000-67123abc0000\""
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 15,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "filters_applied": {
    "status": "active",
    "category": "code_assistant",
    "vendor": null,
    "search": null
  }
}
```

### Example 2: Search for Archived Tools

**Request**:
```http
GET /api/v1/admin/tools?status=archived&search=old
X-Admin-Token: dev-admin-secret-key-2024
```

**Response** (200):
```json
{
  "tools": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Old Code Tool",
      "slug": "old-code-tool",
      "vendor": "Defunct Inc",
      "categories": ["code_assistant"],
      "status": "archived",
      "description": "Discontinued tool",
      "merged_into": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2020-01-15T10:00:00Z",
      "updated_at": "2024-06-01T09:00:00Z",
      "created_by": "admin-user-123",
      "updated_by": "admin-user-789",
      "_etag": "\"0000d192-0000-0200-0000-67123abc0002\""
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "filters_applied": {
    "status": "archived",
    "category": null,
    "vendor": null,
    "search": "old"
  }
}
```
