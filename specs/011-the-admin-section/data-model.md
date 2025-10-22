# Data Model: Admin Tool List Management

**Feature**: 011-the-admin-section  
**Date**: October 21, 2025  
**Status**: Draft

## Overview

This document defines the data entities, fields, relationships, and validation rules for the admin tool list management feature. The model extends the existing Tool entity with multi-category support, archive status, merge tracking, and audit logging.

## Entities

### 1. Tool (Extended)

**Container**: `Tools`  
**Partition Key**: `/partitionKey` (value: "TOOL")  
**Purpose**: Represents a software tool or product tracked for sentiment analysis

**Fields**:

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `id` | string (UUID) | Yes | Generated | UUID format | Unique identifier |
| `partitionKey` | string | Yes | "TOOL" | Fixed value | Cosmos DB partition key |
| `name` | string | Yes | - | 1-200 chars, unique among active tools | Tool display name |
| `slug` | string | Yes | Generated | Lowercase, hyphenated, unique | URL-friendly identifier |
| `vendor` | string | Yes | - | 1-100 chars | Company/organization name |
| `categories` | array[string] | Yes | [] | 1-5 items, valid enum values | Tool categories (NEW: array instead of single) |
| `status` | string | Yes | "active" | Enum: "active", "archived" | Tool status (NEW) |
| `description` | string | No | null | Max 1000 chars | Tool description |
| `merged_into` | string (UUID) | No | null | Valid tool ID or null | Reference to primary tool if merged (NEW) |
| `created_at` | datetime (ISO 8601) | Yes | Now | - | Creation timestamp |
| `updated_at` | datetime (ISO 8601) | Yes | Now | Auto-update | Last modification timestamp |
| `created_by` | string | Yes | - | Admin ID | Administrator who created |
| `updated_by` | string | Yes | - | Admin ID | Administrator who last updated |
| `_etag` | string | Auto | Cosmos | - | Optimistic concurrency token |

**Category Enum Values**:

- `code_assistant` - Code completion, suggestions
- `autonomous_agent` - Autonomous coding agents
- `code_review` - Code review and quality tools
- `testing` - Testing and QA tools
- `devops` - DevOps and deployment tools
- `project_management` - Project management tools
- `collaboration` - Team collaboration tools
- `other` - Uncategorized tools

**Validation Rules**:

1. `name` must be unique among active tools (case-insensitive)
2. `slug` must be unique across all tools (active + archived)
3. `categories` must contain 1-5 valid enum values (no duplicates)
4. `status` can only be "active" or "archived"
5. If `status` is "archived" and `merged_into` is set, the referenced tool must exist and be active
6. `vendor` cannot be empty string or whitespace only
7. Cannot archive a tool that is referenced as `merged_into` by other tools

**Indexes**:

```json
{
  "indexingPolicy": {
    "automatic": true,
    "includedPaths": [{"path": "/*"}],
    "compositeIndexes": [
      [
        {"path": "/status", "order": "ascending"},
        {"path": "/name", "order": "ascending"}
      ],
      [
        {"path": "/status", "order": "ascending"},
        {"path": "/vendor", "order": "ascending"}
      ],
      [
        {"path": "/status", "order": "ascending"},
        {"path": "/updated_at", "order": "descending"}
      ]
    ]
  }
}
```

**State Transitions**:

```
[New Tool] --create--> [Active]
[Active] --archive--> [Archived]
[Archived] --unarchive--> [Active]
[Active] --delete--> [Deleted] (permanent)
[Archived] --delete--> [Deleted] (permanent)
[Active] --merge--> [Archived with merged_into set]
```

---

### 2. ToolMergeRecord (NEW)

**Container**: `ToolMergeRecords`  
**Partition Key**: `/partitionKey` (value: target_tool_id)  
**Purpose**: Tracks tool merge operations for audit and traceability

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string (UUID) | Yes | Generated | Unique merge operation ID |
| `partitionKey` | string | Yes | target_tool_id | Partition by target tool |
| `target_tool_id` | string (UUID) | Yes | - | Primary tool (data merged into) |
| `source_tool_ids` | array[string] | Yes | - | Tools being merged (1+ items) |
| `merged_at` | datetime | Yes | Now | Merge timestamp |
| `merged_by` | string | Yes | - | Administrator who performed merge |
| `sentiment_count` | integer | Yes | - | Number of sentiment records migrated |
| `target_categories_before` | array[string] | Yes | - | Target tool categories before merge |
| `target_categories_after` | array[string] | Yes | - | Target tool categories after merge |
| `target_vendor_before` | string | Yes | - | Target tool vendor before merge |
| `target_vendor_after` | string | Yes | - | Target tool vendor after merge |
| `source_tools_metadata` | array[object] | Yes | - | Snapshot of source tools at merge time |
| `notes` | string | No | null | Admin notes about why merge was performed |

**Example**:

```json
{
  "id": "merge-123-456",
  "partitionKey": "tool-primary-uuid",
  "target_tool_id": "tool-primary-uuid",
  "source_tool_ids": ["tool-acquired-uuid"],
  "merged_at": "2025-10-21T10:30:00Z",
  "merged_by": "admin-user-123",
  "sentiment_count": 5432,
  "target_categories_before": ["code_assistant"],
  "target_categories_after": ["code_assistant", "autonomous_agent"],
  "target_vendor_before": "Company A",
  "target_vendor_after": "Company A",
  "source_tools_metadata": [
    {
      "id": "tool-acquired-uuid",
      "name": "Acquired Tool",
      "vendor": "Company B",
      "categories": ["autonomous_agent"]
    }
  ],
  "notes": "Merger of Company B into Company A - consolidating products"
}
```

---

### 3. AdminActionLog (NEW)

**Container**: `AdminActionLogs`  
**Partition Key**: `/partitionKey` (value: YYYYMM for time-series partitioning)  
**Purpose**: Immutable audit trail of all administrative actions

**Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string (UUID) | Yes | Generated | Unique log entry ID |
| `partitionKey` | string | Yes | YYYYMM | Time-series partition (e.g., "202510") |
| `timestamp` | datetime | Yes | Now | Action timestamp |
| `admin_id` | string | Yes | - | Administrator who performed action |
| `action_type` | string | Yes | - | Enum: "create", "edit", "archive", "unarchive", "delete", "merge" |
| `tool_id` | string (UUID) | Yes | - | Primary tool affected |
| `tool_name` | string | Yes | - | Tool name (denormalized for readability) |
| `before_state` | object | No | null | Tool state before action (JSON snapshot) |
| `after_state` | object | No | null | Tool state after action (JSON snapshot) |
| `metadata` | object | No | {} | Additional context (e.g., merge sources, validation warnings shown) |
| `ip_address` | string | No | null | Admin IP address for security audit |
| `user_agent` | string | No | null | Browser/client info |

**Action Type Descriptions**:

- `create`: New tool added to system
- `edit`: Existing tool modified (name, vendor, categories, description)
- `archive`: Tool moved from active to archived status
- `unarchive`: Tool restored from archived to active status
- `delete`: Tool permanently deleted (includes sentiment data deletion)
- `merge`: Multiple tools merged into one

**Retention**: Keep indefinitely (minimum 1 year, recommended 7 years for compliance)

**Example**:

```json
{
  "id": "log-789-012",
  "partitionKey": "202510",
  "timestamp": "2025-10-21T14:22:33Z",
  "admin_id": "admin-user-123",
  "action_type": "edit",
  "tool_id": "tool-uuid-456",
  "tool_name": "GitHub Copilot",
  "before_state": {
    "name": "GitHub Copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant"]
  },
  "after_state": {
    "name": "GitHub Copilot",
    "vendor": "GitHub",
    "categories": ["code_assistant", "autonomous_agent"]
  },
  "metadata": {
    "changed_fields": ["categories"],
    "reason": "Added autonomous agent category after new features released"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

---

## Relationships

### Tool → Tool (Merge Relationship)

- Type: One-to-One (optional)
- Field: `Tool.merged_into` → `Tool.id`
- Constraint: Referenced tool must exist and be active
- Cascade: Cannot delete/archive tool that is referenced by `merged_into`

### Tool → ToolMergeRecord

- Type: One-to-Many
- Relationship: One tool can be the target of multiple merge operations over time
- Query: Find all merges for a tool via `target_tool_id`

### Tool → AdminActionLog

- Type: One-to-Many
- Relationship: One tool has many audit log entries
- Query: Find all actions for a tool via `tool_id`
- Note: Log entries are immutable

---

## Query Patterns

### 1. List Active Tools with Filtering

```sql
-- All active tools
SELECT * FROM Tools t WHERE t.status = "active" ORDER BY t.name

-- Filter by category (multi-category support)
SELECT * FROM Tools t 
WHERE t.status = "active" 
AND ARRAY_CONTAINS(t.categories, "code_assistant")

-- Filter by vendor
SELECT * FROM Tools t 
WHERE t.status = "active" 
AND t.vendor = "GitHub"

-- Search by name
SELECT * FROM Tools t 
WHERE t.status = "active" 
AND STARTSWITH(t.name, "GitHub")

-- Combined filters
SELECT * FROM Tools t 
WHERE t.status = "active"
AND ARRAY_CONTAINS(t.categories, "code_assistant")
AND t.vendor = "GitHub"
```

### 2. Get Tool with Merge History

```sql
-- Get tool details
SELECT * FROM Tools t WHERE t.id = "tool-uuid"

-- Get merge records for this tool (if it's a merge target)
SELECT * FROM ToolMergeRecords m 
WHERE m.target_tool_id = "tool-uuid"
ORDER BY m.merged_at DESC

-- Get source tools that were merged into this tool
SELECT * FROM Tools t 
WHERE t.merged_into = "tool-uuid"
AND t.status = "archived"
```

### 3. Audit Trail for Tool

```sql
-- Get all actions for a specific tool
SELECT * FROM AdminActionLogs a 
WHERE a.tool_id = "tool-uuid"
ORDER BY a.timestamp DESC

-- Get recent admin actions (last 30 days)
SELECT * FROM AdminActionLogs a 
WHERE a.timestamp >= "2025-09-21T00:00:00Z"
ORDER BY a.timestamp DESC
```

### 4. Validate Merge Operation

```sql
-- Check if source tools exist and are active
SELECT * FROM Tools t 
WHERE t.id IN ("source-1", "source-2") 
AND t.status = "active"

-- Check if target tool exists and is active
SELECT * FROM Tools t 
WHERE t.id = "target-uuid" 
AND t.status = "active"

-- Check if any tool is already merged
SELECT * FROM Tools t 
WHERE t.id IN ("source-1", "source-2", "target-uuid")
AND t.merged_into != null
```

---

## Migration Notes

### Upgrading Existing Tools

Existing tools in the database need schema migration:

1. **Add `categories` array**: Convert single `category` field to array `categories`
   ```python
   # Migration script
   for tool in existing_tools:
       tool['categories'] = [tool['category']]  # Wrap in array
       del tool['category']  # Remove old field
   ```

2. **Add `status` field**: Default all existing tools to "active"
   ```python
   for tool in existing_tools:
       tool['status'] = 'active'
   ```

3. **Add `merged_into` field**: Set to null for all existing tools
   ```python
   for tool in existing_tools:
       tool['merged_into'] = null
   ```

4. **Add audit fields**: Set creator/updater to "system" for existing tools
   ```python
   for tool in existing_tools:
       tool['created_by'] = 'system'
       tool['updated_by'] = 'system'
   ```

### Backward Compatibility

- Existing API endpoints continue to work
- New fields are optional in read operations
- Clients unaware of new fields ignore them gracefully

---

## Validation Summary

| Entity | Validation Type | Rule |
|--------|----------------|------|
| Tool | Uniqueness | Active tool names must be unique (case-insensitive) |
| Tool | Uniqueness | Slugs must be globally unique |
| Tool | Range | 1-5 categories per tool |
| Tool | Enum | Categories must be from allowed list |
| Tool | Referential | merged_into must reference active tool |
| Tool | State | Cannot archive tool if it's referenced by other tool's merged_into |
| ToolMergeRecord | Required | Must have at least 1 source tool |
| ToolMergeRecord | Referential | All source and target tools must exist |
| AdminActionLog | Immutable | Cannot edit or delete log entries |
| AdminActionLog | Partition | Uses YYYYMM partitioning for efficient time-based queries |
