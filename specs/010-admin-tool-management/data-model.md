# Data Model: Admin Tool Management

## Entity Relationship Diagram

```text
┌──────────────────┐
│      Tools       │
├──────────────────┤
│ id (PK)          │
│ partitionKey     │
│ name (unique)    │
│ slug             │
│ vendor           │
│ category         │
│ description      │
│ status           │
│ metadata         │
│ created_at       │
│ updated_at       │
└──────────────────┘
         │
         │ 1:N (primary tool)
         │
         ▼
┌──────────────────┐
│   ToolAliases    │
├──────────────────┤
│ id (PK)          │
│ partitionKey     │
│ alias_tool_id    │───┐
│ primary_tool_id  │   │ FK to Tools.id
│ created_at       │   │
│ created_by       │   │
└──────────────────┘   │
         │             │
         └─────────────┘
         
         │ N:1 (alias tool)
         │
         ▼
┌──────────────────┐
│    Sentiments    │
├──────────────────┤
│ id (PK)          │
│ partitionKey     │
│ tool_id          │───→ Resolved via ToolAliases
│ sentiment_score  │
│ text             │
│ source           │
│ timestamp        │
└──────────────────┘
```

## Container Schemas

### Tools Container

**Partition Key**: `/partitionKey` (static value "tool")

**Document Schema**:

```typescript
interface Tool {
  id: string;                    // UUID v4
  partitionKey: "tool";          // Static for partition efficiency
  name: string;                  // Display name (unique constraint)
  slug: string;                  // URL-safe identifier (auto-generated)
  vendor: string;                // Company/organization name
  category: ToolCategory;        // Enum: code-completion | chat | analysis
  description: string;           // Optional marketing description
  status: ToolStatus;            // Enum: active | deprecated | deleted
  metadata: {
    website?: string;            // Official website URL
    documentation?: string;      // Documentation URL
    pricing?: string;            // Pricing model (free, subscription, etc.)
  };
  created_at: string;            // ISO 8601 timestamp
  updated_at: string;            // ISO 8601 timestamp
}

type ToolCategory = "code-completion" | "chat" | "analysis";
type ToolStatus = "active" | "deprecated" | "deleted";
```

**Example Document**:

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "partitionKey": "tool",
  "name": "GitHub Copilot",
  "slug": "github-copilot",
  "vendor": "GitHub",
  "category": "code-completion",
  "description": "AI pair programmer that suggests code and entire functions",
  "status": "active",
  "metadata": {
    "website": "https://github.com/features/copilot",
    "documentation": "https://docs.github.com/copilot",
    "pricing": "subscription"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### ToolAliases Container

**Partition Key**: `/partitionKey` (static value "alias")

**Document Schema**:

```typescript
interface ToolAlias {
  id: string;                    // UUID v4
  partitionKey: "alias";         // Static for partition efficiency
  alias_tool_id: string;         // FK to Tools.id (the alias)
  primary_tool_id: string;       // FK to Tools.id (the primary tool)
  created_at: string;            // ISO 8601 timestamp
  created_by: string;            // Admin user ID
}
```

**Example Document**:

```json
{
  "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "partitionKey": "alias",
  "alias_tool_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
  "primary_tool_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2025-01-15T12:00:00Z",
  "created_by": "admin-123"
}
```

**Constraints**:

- **No self-referencing**: `alias_tool_id != primary_tool_id`
- **No circular aliases**: Cannot have A→B and B→A
- **One primary per alias**: Each alias tool can only point to one primary
- **Multiple aliases allowed**: One primary tool can have many aliases

## API Models

### Request Models

**ToolCreateRequest**:

```typescript
interface ToolCreateRequest {
  name: string;                  // Required, 1-100 chars, unique
  vendor: string;                // Required, 1-100 chars
  category: ToolCategory;        // Required enum
  description?: string;          // Optional, max 500 chars
  metadata?: {
    website?: string;            // Optional URL
    documentation?: string;      // Optional URL
    pricing?: string;            // Optional text
  };
}
```

**ToolUpdateRequest**:

```typescript
interface ToolUpdateRequest {
  name?: string;                 // Optional, 1-100 chars
  vendor?: string;               // Optional, 1-100 chars
  category?: ToolCategory;       // Optional enum
  description?: string;          // Optional, max 500 chars
  status?: ToolStatus;           // Optional enum
  metadata?: {
    website?: string;
    documentation?: string;
    pricing?: string;
  };
}
```

**AliasLinkRequest**:

```typescript
interface AliasLinkRequest {
  primary_tool_id: string;       // Required UUID
}
```

### Response Models

**ToolResponse**:

```typescript
interface ToolResponse {
  id: string;
  name: string;
  slug: string;
  vendor: string;
  category: ToolCategory;
  description: string;
  status: ToolStatus;
  metadata: {
    website?: string;
    documentation?: string;
    pricing?: string;
  };
  aliases?: ToolAlias[];         // Include if tool is primary
  primary_tool?: ToolResponse;   // Include if tool is alias
  created_at: string;
  updated_at: string;
}
```

**ToolListResponse**:

```typescript
interface ToolListResponse {
  tools: ToolResponse[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}
```

**AliasLinkResponse**:

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

## Database Queries

### Create Tool

```sql
INSERT INTO Tools 
VALUES (
  @id,
  'tool',
  @name,
  LOWER(REPLACE(@name, ' ', '-')),
  @vendor,
  @category,
  @description,
  'active',
  @metadata,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
)
```

### Get Tool by ID (with aliases)

```sql
SELECT 
  t.*,
  (
    SELECT VALUE alias
    FROM alias IN ToolAliases
    WHERE alias.primary_tool_id = t.id
  ) as aliases
FROM Tools t
WHERE t.id = @tool_id AND t.status = 'active'
```

### List Tools (paginated)

```sql
SELECT * FROM Tools t
WHERE t.partitionKey = 'tool' 
  AND t.status = 'active'
  AND (IS_NULL(@search) OR CONTAINS(LOWER(t.name), LOWER(@search)))
  AND (IS_NULL(@category) OR t.category = @category)
ORDER BY t.name
OFFSET @offset LIMIT @limit
```

### Create Alias Link

```sql
INSERT INTO ToolAliases
VALUES (
  @id,
  'alias',
  @alias_tool_id,
  @primary_tool_id,
  CURRENT_TIMESTAMP(),
  @created_by
)
```

### Resolve Tool with Alias

```sql
SELECT 
  COALESCE(ta.primary_tool_id, @tool_id) as resolved_tool_id
FROM Tools t
LEFT JOIN ToolAliases ta ON t.id = ta.alias_tool_id
WHERE t.id = @tool_id
```

### Get Sentiment with Resolved Tools

```sql
SELECT 
  COALESCE(ta.primary_tool_id, s.tool_id) as tool_id,
  t.name as tool_name,
  AVG(s.sentiment_score) as avg_sentiment,
  COUNT(*) as mention_count
FROM Sentiments s
LEFT JOIN ToolAliases ta ON s.tool_id = ta.alias_tool_id
JOIN Tools t ON COALESCE(ta.primary_tool_id, s.tool_id) = t.id
WHERE s.timestamp >= @start_date 
  AND s.timestamp <= @end_date
GROUP BY COALESCE(ta.primary_tool_id, s.tool_id), t.name
ORDER BY avg_sentiment DESC
```

## Validation Rules

### Tool Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| name | Required, 1-100 chars, unique | "Tool name is required and must be unique" |
| name | Alphanumeric + spaces/hyphens only | "Tool name contains invalid characters" |
| vendor | Required, 1-100 chars | "Vendor name is required" |
| category | Must be code-completion, chat, or analysis | "Invalid category" |
| description | Max 500 chars | "Description too long (max 500 characters)" |
| metadata.website | Valid URL or empty | "Invalid website URL" |
| metadata.documentation | Valid URL or empty | "Invalid documentation URL" |

### Alias Validation

| Field | Rule | Error Message |
|-------|------|---------------|
| alias_tool_id | Must exist in Tools | "Alias tool not found" |
| primary_tool_id | Must exist in Tools | "Primary tool not found" |
| alias_tool_id | Cannot equal primary_tool_id | "Tool cannot be alias of itself" |
| relationship | No circular aliases | "Circular alias detected" |
| relationship | Alias tool cannot already be primary | "Alias tool is already primary for other aliases" |

## Migration Strategy

### Seed Data

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "partitionKey": "tool",
    "name": "GitHub Copilot",
    "slug": "github-copilot",
    "vendor": "GitHub",
    "category": "code-completion",
    "description": "AI pair programmer",
    "status": "active",
    "metadata": {},
    "created_at": "2025-01-15T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
  },
  {
    "id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
    "partitionKey": "tool",
    "name": "Jules AI",
    "slug": "jules-ai",
    "vendor": "Jules",
    "category": "code-completion",
    "description": "AI coding assistant",
    "status": "active",
    "metadata": {},
    "created_at": "2025-01-15T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
  }
]
```

### Update Existing Sentiment Data

```sql
-- Update tool_id references (if currently storing tool names as strings)
UPDATE Sentiments s
SET s.tool_id = (
  SELECT t.id 
  FROM Tools t 
  WHERE LOWER(t.name) = LOWER(s.tool_name)
)
WHERE s.tool_name IS NOT NULL
```

## Performance Considerations

### Indexing

**Tools Container**:

- Composite index on `(partitionKey, status, name)` for list queries
- Index on `slug` for URL routing
- Index on `category` for filtering

**ToolAliases Container**:

- Composite index on `(alias_tool_id, primary_tool_id)` for alias resolution
- Index on `primary_tool_id` for reverse lookups

### Caching

**Tool List Cache**:

```typescript
interface ToolCache {
  key: "tools:all";
  ttl: 300; // 5 minutes
  data: ToolResponse[];
}
```

**Alias Map Cache**:

```typescript
interface AliasMapCache {
  key: "aliases:map";
  ttl: 600; // 10 minutes
  data: Record<string, string>; // alias_id → primary_id
}
```

## Error Handling

### HTTP Status Codes

| Code | Scenario | Response |
|------|----------|----------|
| 200 | Tool created/updated/deleted | `{ message: "Success" }` |
| 400 | Validation error | `{ error: "Validation failed", details: [...] }` |
| 404 | Tool not found | `{ error: "Tool not found" }` |
| 409 | Duplicate tool name | `{ error: "Tool name already exists" }` |
| 500 | Database error | `{ error: "Internal server error" }` |

### Example Error Response

```json
{
  "error": "Validation failed",
  "details": [
    {
      "field": "name",
      "message": "Tool name is required"
    },
    {
      "field": "category",
      "message": "Invalid category"
    }
  ]
}
```
