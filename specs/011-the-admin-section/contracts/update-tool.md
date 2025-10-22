# API Contract: Update Tool

**Endpoint**: `PUT /api/v1/admin/tools/{tool_id}`  
**Purpose**: Update an existing tool's information  
**Authentication**: Required (Admin token)

## Request

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_id` | string (UUID) | Yes | Tool unique identifier |

### Headers

```http
PUT /api/v1/admin/tools/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
If-Match: "0000d192-0000-0200-0000-67123abc0000"
```

### Request Body

```json
{
  "name": "GitHub Copilot",
  "vendor": "GitHub",
  "categories": ["code_assistant", "autonomous_agent"],
  "description": "AI pair programmer that helps you write code faster and smarter"
}
```

**Fields**:

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | 1-200 chars, must be unique among active tools |
| `vendor` | string | Yes | 1-100 chars |
| `categories` | array[string] | Yes | 1-5 items, valid enum values |
| `description` | string | No | Max 1000 chars |

**Note**: `status`, `merged_into`, and audit fields cannot be changed via this endpoint. Use dedicated endpoints for archive/unarchive/merge operations.

## Response

### Success (200 OK)

```json
{
  "tool": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "GitHub Copilot",
    "slug": "github-copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant", "autonomous_agent"],
    "status": "active",
    "description": "AI pair programmer that helps you write code faster and smarter",
    "merged_into": null,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2025-10-21T15:45:22Z",
    "created_by": "admin-user-123",
    "updated_by": "admin-user-789",
    "_etag": "\"0000d192-0000-0200-0000-67123def0000\""
  },
  "message": "Tool updated successfully"
}
```

### Validation Errors (400 Bad Request)

```json
{
  "error": "Validation error",
  "details": {
    "name": "Tool name already exists",
    "categories": "Must contain 1-5 valid categories",
    "description": "Exceeds maximum length of 1000 characters"
  }
}
```

### Not Found (404)

```json
{
  "error": "Tool not found",
  "message": "Tool with ID 550e8400-e29b-41d4-a716-446655440000 does not exist"
}
```

### Conflict (409)

```json
{
  "error": "Conflict",
  "message": "Tool was modified by another administrator. Please refresh and try again.",
  "current_etag": "\"0000d192-0000-0200-0000-67123xyz0000\""
}
```

### Unauthorized (401)

```json
{
  "error": "Unauthorized",
  "message": "Valid admin authentication required"
}
```

## Business Rules

1. **Optimistic Concurrency**: Must provide `If-Match` header with current `_etag` to prevent lost updates
2. **Name Uniqueness**: Tool name must be unique among **active** tools (case-insensitive)
3. **Slug Generation**: Slug is auto-regenerated from name if name changes
4. **Category Validation**: All categories must be from the allowed enum list
5. **Category Limit**: Minimum 1, maximum 5 categories
6. **Immutable Fields**: Cannot change `id`, `status`, `merged_into`, `created_at`, `created_by`
7. **Audit Trail**: All changes are logged to AdminActionLog with before/after state
8. **Updated Timestamp**: `updated_at` is automatically set to current time
9. **Updated By**: `updated_by` is automatically set to authenticated admin ID

## Examples

### Example 1: Update Tool Categories

**Request**:

```http
PUT /api/v1/admin/tools/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
If-Match: "0000d192-0000-0200-0000-67123abc0000"

{
  "name": "GitHub Copilot",
  "vendor": "GitHub",
  "categories": ["code_assistant", "autonomous_agent"],
  "description": "AI pair programmer with autonomous coding capabilities"
}
```

**Response** (200):

```json
{
  "tool": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "GitHub Copilot",
    "slug": "github-copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant", "autonomous_agent"],
    "status": "active",
    "description": "AI pair programmer with autonomous coding capabilities",
    "merged_into": null,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2025-10-21T15:45:22Z",
    "created_by": "admin-user-123",
    "updated_by": "admin-user-789",
    "_etag": "\"0000d192-0000-0200-0000-67123def0000\""
  },
  "message": "Tool updated successfully"
}
```

### Example 2: Rename Tool

**Request**:

```http
PUT /api/v1/admin/tools/660e8400-e29b-41d4-a716-446655440001
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
If-Match: "0000d192-0000-0200-0000-67123abc0001"

{
  "name": "Cursor IDE",
  "vendor": "Cursor Technologies",
  "categories": ["code_assistant"],
  "description": "AI-first code editor"
}
```

**Response** (200):

```json
{
  "tool": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Cursor IDE",
    "slug": "cursor-ide",
    "vendor": "Cursor Technologies",
    "categories": ["code_assistant"],
    "status": "active",
    "description": "AI-first code editor",
    "merged_into": null,
    "created_at": "2024-03-20T10:00:00Z",
    "updated_at": "2025-10-21T15:50:10Z",
    "created_by": "admin-user-123",
    "updated_by": "admin-user-789",
    "_etag": "\"0000d192-0000-0200-0000-67123ghi0001\""
  },
  "message": "Tool updated successfully"
}
```

### Example 3: Validation Error - Duplicate Name

**Request**:

```http
PUT /api/v1/admin/tools/660e8400-e29b-41d4-a716-446655440001
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
If-Match: "0000d192-0000-0200-0000-67123abc0001"

{
  "name": "GitHub Copilot",
  "vendor": "Cursor Technologies",
  "categories": ["code_assistant"]
}
```

**Response** (400):

```json
{
  "error": "Validation error",
  "details": {
    "name": "Tool name 'GitHub Copilot' already exists"
  }
}
```

### Example 4: Concurrency Conflict

**Request**:

```http
PUT /api/v1/admin/tools/550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
If-Match: "0000d192-0000-0200-0000-67123OLD0000"

{
  "name": "GitHub Copilot",
  "vendor": "GitHub",
  "categories": ["code_assistant"]
}
```

**Response** (409):

```json
{
  "error": "Conflict",
  "message": "Tool was modified by another administrator. Please refresh and try again.",
  "current_etag": "\"0000d192-0000-0200-0000-67123NEW0000\""
}
```
