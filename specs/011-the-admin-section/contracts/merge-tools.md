# API Contract: Merge Tools

**Endpoint**: `POST /api/v1/admin/tools/merge`  
**Purpose**: Merge multiple tools into a single primary tool, consolidating sentiment data  
**Authentication**: Required (Admin token)

## Request

### Headers

```http
POST /api/v1/admin/tools/merge
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024
```

### Request Body

```json
{
  "target_tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_tool_ids": [
    "770e8400-e29b-41d4-a716-446655440002",
    "880e8400-e29b-41d4-a716-446655440003"
  ],
  "target_categories": ["code_assistant", "autonomous_agent"],
  "target_vendor": "GitHub",
  "notes": "Merging acquired tools after company acquisition"
}
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_tool_id` | string (UUID) | Yes | Primary tool that will receive merged data |
| `source_tool_ids` | array[string] | Yes | Tools to merge into target (1-10 tools) |
| `target_categories` | array[string] | Yes | Final categories for merged tool (1-5 items) |
| `target_vendor` | string | Yes | Final vendor name for merged tool |
| `notes` | string | No | Admin notes explaining why merge was performed |

**Validation**:

- `source_tool_ids` must contain 1-10 UUIDs
- All `source_tool_ids` must be unique
- `target_tool_id` cannot be in `source_tool_ids`
- All tools must exist and be active
- None of the tools can already be merged (have `merged_into` set)
- `target_categories` must be 1-5 valid category values

## Response

### Success (200 OK)

```json
{
  "merge_record": {
    "id": "merge-123-456",
    "target_tool_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_tool_ids": [
      "770e8400-e29b-41d4-a716-446655440002",
      "880e8400-e29b-41d4-a716-446655440003"
    ],
    "merged_at": "2025-10-21T16:30:45Z",
    "merged_by": "admin-user-789",
    "sentiment_count": 8542,
    "target_categories_before": ["code_assistant"],
    "target_categories_after": ["code_assistant", "autonomous_agent"],
    "target_vendor_before": "GitHub",
    "target_vendor_after": "GitHub",
    "source_tools_metadata": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Acquired Tool A",
        "vendor": "Acquired Company",
        "categories": ["autonomous_agent"],
        "sentiment_count": 3200
      },
      {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "name": "Acquired Tool B",
        "vendor": "Acquired Company",
        "categories": ["code_assistant"],
        "sentiment_count": 2100
      }
    ],
    "notes": "Merging acquired tools after company acquisition"
  },
  "target_tool": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "GitHub Copilot",
    "slug": "github-copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant", "autonomous_agent"],
    "status": "active",
    "description": "AI pair programmer",
    "merged_into": null,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2025-10-21T16:30:45Z",
    "created_by": "admin-user-123",
    "updated_by": "admin-user-789",
    "_etag": "\"0000d192-0000-0200-0000-67124abc0000\""
  },
  "archived_tools": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Acquired Tool A",
      "slug": "acquired-tool-a",
      "vendor": "Acquired Company",
      "categories": ["autonomous_agent"],
      "status": "archived",
      "merged_into": "550e8400-e29b-41d4-a716-446655440000",
      "updated_at": "2025-10-21T16:30:45Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "name": "Acquired Tool B",
      "slug": "acquired-tool-b",
      "vendor": "Acquired Company",
      "categories": ["code_assistant"],
      "status": "archived",
      "merged_into": "550e8400-e29b-41d4-a716-446655440000",
      "updated_at": "2025-10-21T16:30:45Z"
    }
  ],
  "message": "Successfully merged 2 tools into GitHub Copilot. Migrated 8,542 sentiment records."
}
```

### Validation Errors (400 Bad Request)

```json
{
  "error": "Validation error",
  "details": {
    "source_tool_ids": "Must contain 1-10 tool IDs",
    "target_categories": "Must contain 1-5 valid categories",
    "circular_merge": "Cannot merge tool into itself"
  }
}
```

### Conflict - Metadata Differences (200 OK with warnings)

When source and target tools have different vendors or conflicting categories, the API returns success but includes validation warnings:

```json
{
  "warnings": [
    {
      "type": "vendor_mismatch",
      "message": "Source tools have different vendors than target",
      "details": {
        "target_vendor": "GitHub",
        "source_vendors": ["Acquired Company", "Different Vendor"]
      }
    },
    {
      "type": "category_overlap",
      "message": "Some categories from source tools not included in target",
      "details": {
        "source_categories": ["code_assistant", "autonomous_agent", "testing"],
        "target_categories": ["code_assistant", "autonomous_agent"],
        "missing_categories": ["testing"]
      }
    }
  ],
  "merge_record": { 
    /* ... full merge record as above ... */
  },
  "message": "Merge completed with warnings. Please review metadata differences."
}
```

### Not Found (404)

```json
{
  "error": "Tool not found",
  "message": "Tool with ID 770e8400-e29b-41d4-a716-446655440002 does not exist",
  "missing_tool_ids": ["770e8400-e29b-41d4-a716-446655440002"]
}
```

### Conflict - Already Merged (409)

```json
{
  "error": "Conflict",
  "message": "One or more tools have already been merged",
  "details": {
    "770e8400-e29b-41d4-a716-446655440002": {
      "status": "archived",
      "merged_into": "different-tool-id",
      "merged_at": "2025-09-15T10:00:00Z"
    }
  }
}
```

### Server Error (500)

```json
{
  "error": "Merge failed",
  "message": "An error occurred during the merge operation. All changes have been rolled back.",
  "details": "Database transaction failed at step 3/5"
}
```

## Business Rules

1. **Atomicity**: Merge operation is atomic - either all changes succeed or all are rolled back
2. **Source Tool Archiving**: Source tools are set to status="archived" and merged_into=target_tool_id
3. **Sentiment Data Migration**: All sentiment records for source tools are linked to target tool with original source attribution
4. **Category Consolidation**: Target tool receives combined categories (admin must specify final set)
5. **Vendor Override**: Admin specifies final vendor (handles acquisition scenarios)
6. **Validation Warnings**: System shows warnings for metadata conflicts but allows merge to proceed
7. **Audit Trail**: Creates ToolMergeRecord and AdminActionLog entries
8. **Irreversible**: Merge cannot be undone (though source tools remain archived for reference)
9. **Performance**: Should complete within 60 seconds for up to 10,000 sentiment records per tool
10. **Limits**: Maximum 10 source tools per merge operation

## Merge Process Steps

1. **Validation Phase**:
   - Verify all tools exist and are active
   - Check for circular merges
   - Validate categories and vendor
   - Check for already-merged tools

2. **Warning Check Phase**:
   - Compare vendors between source and target
   - Compare categories
   - Generate warnings for discrepancies

3. **Data Migration Phase**:
   - Copy sentiment data from source tools to target
   - Add source attribution metadata
   - Preserve timestamp and source tool reference

4. **Tool Update Phase**:
   - Update target tool with new categories/vendor
   - Set source tools to status="archived"
   - Set source tools merged_into=target_tool_id

5. **Audit Phase**:
   - Create ToolMergeRecord
   - Create AdminActionLog entry
   - Log sentiment migration count

## Examples

### Example 1: Simple Merge (No Warnings)

**Request**:

```http
POST /api/v1/admin/tools/merge
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024

{
  "target_tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_tool_ids": ["770e8400-e29b-41d4-a716-446655440002"],
  "target_categories": ["code_assistant"],
  "target_vendor": "GitHub",
  "notes": "Consolidating duplicate entries"
}
```

**Response** (200):

```json
{
  "merge_record": {
    "id": "merge-789-012",
    "target_tool_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_tool_ids": ["770e8400-e29b-41d4-a716-446655440002"],
    "merged_at": "2025-10-21T17:00:00Z",
    "merged_by": "admin-user-789",
    "sentiment_count": 1250,
    "target_categories_before": ["code_assistant"],
    "target_categories_after": ["code_assistant"],
    "target_vendor_before": "GitHub",
    "target_vendor_after": "GitHub",
    "source_tools_metadata": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "GitHub Copilot Duplicate",
        "vendor": "GitHub",
        "categories": ["code_assistant"],
        "sentiment_count": 1250
      }
    ],
    "notes": "Consolidating duplicate entries"
  },
  "target_tool": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "GitHub Copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant"],
    "status": "active",
    "updated_at": "2025-10-21T17:00:00Z"
  },
  "archived_tools": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "GitHub Copilot Duplicate",
      "status": "archived",
      "merged_into": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "message": "Successfully merged 1 tool into GitHub Copilot. Migrated 1,250 sentiment records."
}
```

### Example 2: Merge with Metadata Warnings

**Request**:

```http
POST /api/v1/admin/tools/merge
Content-Type: application/json
X-Admin-Token: dev-admin-secret-key-2024

{
  "target_tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_tool_ids": ["770e8400-e29b-41d4-a716-446655440002"],
  "target_categories": ["code_assistant", "autonomous_agent"],
  "target_vendor": "GitHub",
  "notes": "Acquisition of Smaller Company by GitHub"
}
```

**Response** (200 with warnings):

```json
{
  "warnings": [
    {
      "type": "vendor_mismatch",
      "message": "Source tools have different vendors than target",
      "details": {
        "target_vendor": "GitHub",
        "source_vendors": ["Smaller Company"]
      }
    }
  ],
  "merge_record": {
    /* ... */
  },
  "target_tool": {
    /* ... */
  },
  "archived_tools": [
    /* ... */
  ],
  "message": "Merge completed with warnings. Please review metadata differences."
}
```
