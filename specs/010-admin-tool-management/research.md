# Research: Admin Tool Management & Aliasing

## Database Schema Design

### Tool Table Structure

**Azure Cosmos DB SQL API** requires partition key strategy:

```sql

-- Tool Container (primary collection)
{
  "id": "uuid-v4",                    -- Unique identifier
  "partitionKey": "tool",             -- Static partition for tool queries
  "name": "GitHub Copilot",           -- Display name (unique)
  "slug": "github-copilot",           -- URL-friendly identifier
  "description": "AI pair programmer",
  "vendor": "GitHub",                 -- Company/organization
  "category": "code-completion",      -- code-completion, chat, analysis
  "status": "active",                 -- active, deprecated, deleted
  "metadata": {
    "website": "https://github.com/features/copilot",
    "documentation": "https://docs.github.com/copilot",
    "pricing": "subscription"
  },
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

**Key Design Decisions**:

- `partitionKey: "tool"` groups all tools in same partition (small dataset, efficient queries)
- `slug` for URL routing (e.g., `/tools/github-copilot`)
- `status` enables soft delete (preserve historical data)
- `metadata` for extensible fields without schema changes

### Tool Alias Table Structure

```sql

-- ToolAlias Container
{
  "id": "uuid-v4",
  "partitionKey": "alias",
  "alias_tool_id": "uuid-of-codex",      -- Tool that is an alias
  "primary_tool_id": "uuid-of-openai",   -- Tool that aliases resolve to
  "created_at": "2025-01-15T12:00:00Z",
  "created_by": "admin-user-id"
}

```

**Key Design Decisions**:

- Separate container for alias relationships (cleaner data model)
- One-to-one alias relationship (one alias → one primary)
- No circular aliases (validation in backend)
- Supports multiple aliases per primary (e.g., "Codex", "ChatGPT" → "OpenAI")

### Sentiment Data Resolution

**Before Aliasing** (duplicate tools):

```json

[
  {"tool": "Codex", "sentiment": 0.7, "count": 150},
  {"tool": "OpenAI", "sentiment": 0.6, "count": 200}
]

```

**After Aliasing** (consolidated):

```json

[
  {"tool": "OpenAI", "sentiment": 0.65, "count": 350}  // Weighted average
]

```

**Query Strategy**:

```sql

-- Resolve aliases in sentiment aggregation
SELECT 
  COALESCE(ta.primary_tool_id, s.tool_id) as resolved_tool_id,
  t.name as tool_name,
  AVG(s.sentiment_score) as avg_sentiment,
  COUNT(*) as mention_count
FROM Sentiments s
LEFT JOIN ToolAlias ta ON s.tool_id = ta.alias_tool_id
JOIN Tools t ON COALESCE(ta.primary_tool_id, s.tool_id) = t.id
GROUP BY COALESCE(ta.primary_tool_id, s.tool_id), t.name

```

## Admin UI Patterns

### Form Design (Glass Theme)

**"Add New Tool" Form**:

```tsx

<div className="glass-card p-6">
  <h2 className="text-2xl font-bold text-gray-100 mb-6">Add New Tool</h2>
  
  <form className="space-y-4">
    <div>
      <label className="block text-sm font-medium text-gray-200 mb-2">Tool Name</label>
      <input 
        type="text" 
        className="glass-input w-full"
        placeholder="e.g., Cursor IDE"
        required
      />
    </div>
    
    <div>
      <label className="block text-sm font-medium text-gray-200 mb-2">Vendor</label>
      <input 
        type="text" 
        className="glass-input w-full"
        placeholder="e.g., Anysphere"
      />
    </div>
    
    <div>
      <label className="block text-sm font-medium text-gray-200 mb-2">Category</label>
      <select className="glass-input w-full">
        <option value="code-completion">Code Completion</option>
        <option value="chat">Chat Assistant</option>
        <option value="analysis">Code Analysis</option>
      </select>
    </div>
    
    <div>
      <label className="block text-sm font-medium text-gray-200 mb-2">Description</label>
      <textarea 
        className="glass-input w-full h-24"
        placeholder="Brief description of the tool"
      />
    </div>
    
    <button 
      type="submit" 
      className="glass-button bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 px-6 py-2"
    >
      Add Tool
    </button>
  </form>
</div>

```

### Alias Linking Modal

**"Link Alias" Modal**:

```tsx

<div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
  <div className="glass-card-strong p-6 max-w-md w-full">
    <h3 className="text-xl font-bold text-gray-100 mb-4">Link Tool Alias</h3>
    
    <p className="text-gray-300 mb-4">
      Set <span className="text-emerald-400 font-semibold">Codex</span> as an alias for:
    </p>
    
    <select className="glass-input w-full mb-6">
      <option value="">Select primary tool...</option>
      <option value="uuid-openai">OpenAI</option>
      <option value="uuid-github-copilot">GitHub Copilot</option>
    </select>
    
    <div className="flex gap-3">
      <button className="glass-button bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 px-4 py-2">
        Link Alias
      </button>
      <button className="glass-button text-gray-400 px-4 py-2">
        Cancel
      </button>
    </div>
  </div>
</div>

```

### Tool Management Table

**Table with Glass Styling**:

```tsx

<div className="glass-card overflow-hidden">
  <table className="w-full">
    <thead>
      <tr className="border-b border-white/10">
        <th className="text-left py-3 px-4 text-gray-200">Tool Name</th>
        <th className="text-left py-3 px-4 text-gray-200">Vendor</th>
        <th className="text-left py-3 px-4 text-gray-200">Category</th>
        <th className="text-left py-3 px-4 text-gray-200">Alias Status</th>
        <th className="text-right py-3 px-4 text-gray-200">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr className="border-b border-white/5 hover:bg-white/5 transition-colors">
        <td className="py-3 px-4 text-gray-100">GitHub Copilot</td>
        <td className="py-3 px-4 text-gray-300">GitHub</td>
        <td className="py-3 px-4 text-gray-300">Code Completion</td>
        <td className="py-3 px-4">
          <span className="text-gray-400 text-sm">No aliases</span>
        </td>
        <td className="py-3 px-4 text-right">
          <button className="text-emerald-400 hover:text-emerald-300 text-sm">Edit</button>
          <button className="text-red-400 hover:text-red-300 text-sm ml-3">Delete</button>
        </td>
      </tr>
      
      <tr className="border-b border-white/5 hover:bg-white/5 transition-colors">
        <td className="py-3 px-4 text-gray-100">OpenAI</td>
        <td className="py-3 px-4 text-gray-300">OpenAI</td>
        <td className="py-3 px-4 text-gray-300">Chat</td>
        <td className="py-3 px-4">
          <div className="flex items-center gap-2">
            <span className="text-emerald-400 text-sm">Primary for:</span>
            <span className="text-gray-300 text-sm">Codex, ChatGPT</span>
          </div>
        </td>
        <td className="py-3 px-4 text-right">
          <button className="text-emerald-400 hover:text-emerald-300 text-sm">Edit</button>
          <button className="text-red-400 hover:text-red-300 text-sm ml-3">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>

```

## Backend API Design

### Endpoints

**POST /api/admin/tools** - Create new tool

```python

from pydantic import BaseModel, Field

class ToolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vendor: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., regex="^(code-completion|chat|analysis)$")
    description: str = Field(default="", max_length=500)

@app.post("/api/admin/tools")
async def create_tool(tool: ToolCreate, db: DatabaseService):
    # Check for duplicate name
    existing = await db.query_tools(name=tool.name)
    if existing:
        raise HTTPException(400, "Tool name already exists")
    
    # Create tool record
    tool_id = str(uuid.uuid4())
    await db.create_tool({
        "id": tool_id,
        "partitionKey": "tool",
        "name": tool.name,
        "slug": tool.name.lower().replace(" ", "-"),
        "vendor": tool.vendor,
        "category": tool.category,
        "description": tool.description,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    return {"id": tool_id, "message": "Tool created successfully"}

```

**PUT /api/admin/tools/{tool_id}/alias** - Link alias to primary tool

```python

class AliasLink(BaseModel):
    primary_tool_id: str = Field(..., regex="^[a-f0-9-]{36}$")

@app.put("/api/admin/tools/{tool_id}/alias")
async def link_alias(tool_id: str, link: AliasLink, db: DatabaseService):
    # Validate both tools exist
    alias_tool = await db.get_tool(tool_id)
    primary_tool = await db.get_tool(link.primary_tool_id)
    
    if not alias_tool or not primary_tool:
        raise HTTPException(404, "Tool not found")
    
    # Prevent self-referencing alias
    if tool_id == link.primary_tool_id:
        raise HTTPException(400, "Tool cannot be alias of itself")
    
    # Check for circular aliases
    if await db.has_circular_alias(tool_id, link.primary_tool_id):
        raise HTTPException(400, "Circular alias detected")
    
    # Create alias relationship
    await db.create_alias({
        "id": str(uuid.uuid4()),
        "partitionKey": "alias",
        "alias_tool_id": tool_id,
        "primary_tool_id": link.primary_tool_id,
        "created_at": datetime.utcnow().isoformat()
    })
    
    return {"message": f"{alias_tool['name']} linked to {primary_tool['name']}"}

```

**GET /api/admin/tools** - List all tools with pagination

```python

@app.get("/api/admin/tools")
async def list_tools(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    category: str = None,
    db: DatabaseService = None
):
    offset = (page - 1) * limit
    
    query = "SELECT * FROM Tools t WHERE t.partitionKey = 'tool' AND t.status = 'active'"
    
    if search:
        query += f" AND CONTAINS(LOWER(t.name), LOWER('{search}'))"
    
    if category:
        query += f" AND t.category = '{category}'"
    
    query += f" ORDER BY t.name OFFSET {offset} LIMIT {limit}"
    
    tools = await db.query_items(query)
    total = await db.count_tools()
    
    return {
        "tools": tools,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

```

## Validation & Security

### Input Validation

- **Tool names**: 1-100 characters, alphanumeric + spaces/hyphens

- **Categories**: Predefined enum (code-completion, chat, analysis)

- **Descriptions**: Max 500 characters, sanitize HTML

- **UUIDs**: Regex validation for tool IDs

### Security Considerations

- **Authentication**: Require admin JWT token for all /api/admin/* routes

- **Rate limiting**: Max 10 tool creations per hour per admin

- **SQL injection**: Use parameterized queries for Cosmos DB

- **XSS prevention**: Sanitize all text inputs on frontend

## Performance Optimization

### Indexing Strategy

```json

{
  "indexingPolicy": {
    "includedPaths": [
      {"path": "/name/?"},
      {"path": "/category/?"},
      {"path": "/status/?"},
      {"path": "/created_at/?"}
    ],
    "excludedPaths": [
      {"path": "/metadata/*"}
    ]
  }
}

```

### Caching Strategy

- **Tool list**: Cache for 5 minutes (rarely changes)

- **Alias mappings**: Cache for 10 minutes (critical for sentiment queries)

- **Invalidation**: Clear cache on tool/alias creation/deletion

## Migration Plan

### Phase 1: Database Setup (Day 1)

1. Create `Tools` container in Cosmos DB
2. Create `ToolAliases` container
3. Migrate existing tool data (GitHub Copilot, Jules AI)
4. Create indexes

### Phase 2: Backend Implementation (Days 2-3)

1. Implement `ToolService` for CRUD operations
2. Add admin routes with authentication
3. Update sentiment aggregation to resolve aliases
4. Write unit tests for alias resolution

### Phase 3: Frontend Implementation (Days 4-5)

1. Build "Add New Tool" form
2. Build "Link Alias" modal
3. Build tool management table
4. Integrate with backend APIs

### Phase 4: Testing & Deployment (Days 6-7)

1. End-to-end testing of tool lifecycle
2. Test alias resolution in sentiment queries
3. Performance testing with 50+ tools
4. Deploy to production

## Open Questions to Resolve

1. **Soft vs. Hard Delete**: Recommendation is **soft delete** (set `status: "deleted"`) to preserve historical sentiment data
2. **Reversible Aliases**: **No** - keep relationships unidirectional (alias → primary only)
3. **Multiple Aliases**: **Yes** - allow N aliases per primary tool (e.g., "Codex", "ChatGPT" → "OpenAI")
4. **Category Management**: **Predefined enum** initially, consider admin-configurable in future
