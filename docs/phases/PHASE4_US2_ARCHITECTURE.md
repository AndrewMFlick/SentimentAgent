# Phase 4: User Story 2 - Alias Linking Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Admin Tool Approval Page                     │
│                  (AdminToolApproval.tsx)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            Pending Tools Section (Existing)             │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  Tool 1  │  Vendor  │  Mentions  │  ✓ ✗         │  │    │
│  │  │  Tool 2  │  Vendor  │  Mentions  │  ✓ ✗         │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Tool Alias Management Section (NEW)             │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  Tool    │  Vendor  │  Category  │  Status  │ 🔗  │  │    │
│  │  │  OpenAI  │  OpenAI  │  chat      │  active  │ 🔗  │  │    │
│  │  │  Codex   │  OpenAI  │  code      │  active  │ 🔗  │  │    │
│  │  │  Jules   │  Anthropic│  code     │  active  │ 🔗  │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │                                                          │    │
│  │  [Click 🔗 on "Codex" opens modal]                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ (showAliasModal = true)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AliasLinkModal Component                      │
│                  (AliasLinkModal.tsx)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Link Tool Alias                                      ✕   │ │
│  │  ─────────────────────────────────────────────────────────│ │
│  │                                                             │ │
│  │  Set "Codex" as an alias of another primary tool.         │ │
│  │  Sentiment data will be consolidated under the primary.   │ │
│  │                                                             │ │
│  │  Primary Tool:                                             │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │ OpenAI (OpenAI)                              ▼      │  │ │
│  │  │ Jules AI (Anthropic)                                │  │ │
│  │  │ Cursor (Anysphere)                                  │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │                                 [Cancel] [Link Alias]      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ (onClick Link Alias)
                               ▼
                    PUT /api/admin/tools/{codex_id}/alias
                    Body: { primary_tool_id: openai_id }
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend API Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. verify_admin(x_admin_token)                                 │
│     ├─ Check token exists                                       │
│     └─ Return admin_user                                        │
│                                                                   │
│  2. get_tool_service() [Dependency Injection]                   │
│     ├─ tools_container: ContainerProxy                          │
│     └─ aliases_container: ContainerProxy                        │
│                                                                   │
│  3. Validation                                                   │
│     ├─ get_tool(codex_id) → exists?                            │
│     ├─ get_tool(openai_id) → exists?                           │
│     ├─ codex_id != openai_id? (self-reference check)           │
│     ├─ has_circular_alias(codex_id, openai_id)? (circular)     │
│     └─ get_aliases(codex_id) → empty? (not already primary)    │
│                                                                   │
│  4. Create Alias                                                 │
│     ├─ alias_id = uuid.uuid4()                                  │
│     ├─ alias = {                                                │
│     │     id: alias_id,                                         │
│     │     partitionKey: "alias",                                │
│     │     alias_tool_id: codex_id,                              │
│     │     primary_tool_id: openai_id,                           │
│     │     created_at: now(),                                    │
│     │     created_by: admin_user                                │
│     │   }                                                        │
│     └─ aliases_container.create_item(alias)                     │
│                                                                   │
│  5. Audit Log                                                    │
│     └─ logger.warning("AUDIT: Alias linked", ...)               │
│                                                                   │
│  6. Response                                                     │
│     └─ { message, alias_tool: {...}, primary_tool: {...} }     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Sentiment Query with Alias Resolution

```
┌─────────────────────────────────────────────────────────────────┐
│              User requests sentiment for "Codex"                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    GET /api/tools/codex-id/sentiment
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              get_tool_sentiment(tool_id="codex-id")              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Step 1: Resolve Alias                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ _resolve_tool_alias("codex-id")                            │ │
│  │   Query: SELECT * FROM ToolAliases ta                      │ │
│  │          WHERE ta.alias_tool_id = "codex-id"               │ │
│  │   Result: { primary_tool_id: "openai-id" }                │ │
│  │   Return: "openai-id"                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Step 2: Get All Tool IDs for Aggregation                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ _get_tool_ids_for_aggregation("openai-id")                │ │
│  │   Query: SELECT * FROM ToolAliases ta                      │ │
│  │          WHERE ta.primary_tool_id = "openai-id"            │ │
│  │   Result: [{ alias_tool_id: "codex-id" },                 │ │
│  │            { alias_tool_id: "chatgpt-id" }]                │ │
│  │   Return: ["openai-id", "codex-id", "chatgpt-id"]         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Step 3: Query Sentiment Data                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Query: SELECT SUM(total_mentions), SUM(positive_count),   │ │
│  │               SUM(negative_count), AVG(avg_sentiment)      │ │
│  │        FROM time_period_aggregates c                       │ │
│  │        WHERE ARRAY_CONTAINS(@tool_ids, c.tool_id)          │ │
│  │          AND c.date >= @cutoff                             │ │
│  │                                                             │ │
│  │ Parameters:                                                 │ │
│  │   @tool_ids: ["openai-id", "codex-id", "chatgpt-id"]      │ │
│  │                                                             │ │
│  │ Result:                                                     │ │
│  │   total_mentions: 1500  (OpenAI: 1000 + Codex: 300 +      │ │
│  │                          ChatGPT: 200)                     │ │
│  │   positive_count: 900                                      │ │
│  │   negative_count: 300                                      │ │
│  │   avg_sentiment: 0.65                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                  Return consolidated sentiment data
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                        Tools Container                           │
├─────────────────────────────────────────────────────────────────┤
│ {                                                                 │
│   "id": "openai-id",                                             │
│   "partitionKey": "tool",                                        │
│   "name": "OpenAI",                                              │
│   "slug": "openai",                                              │
│   "vendor": "OpenAI",                                            │
│   "category": "chat",                                            │
│   "description": "ChatGPT and GPT models",                       │
│   "status": "active",                                            │
│   "metadata": {},                                                │
│   "created_at": "2025-01-15T10:00:00Z",                         │
│   "updated_at": "2025-01-15T10:00:00Z"                          │
│ }                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ToolAliases Container                         │
├─────────────────────────────────────────────────────────────────┤
│ {                                                                 │
│   "id": "alias-1",                                               │
│   "partitionKey": "alias",                                       │
│   "alias_tool_id": "codex-id",         ◄── Tool to be aliased   │
│   "primary_tool_id": "openai-id",      ◄── Primary tool         │
│   "created_at": "2025-10-21T14:30:00Z",                         │
│   "created_by": "admin"                                          │
│ }                                                                 │
│                                                                   │
│ Indexes:                                                          │
│  - alias_tool_id (for _resolve_tool_alias)                      │
│  - primary_tool_id (for _get_tool_ids_for_aggregation)          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Alias Relationship Visualization                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│                       ┌─────────────┐                            │
│                       │   OpenAI    │ ◄── Primary Tool           │
│                       │  (primary)  │                            │
│                       └─────────────┘                            │
│                              ▲                                    │
│                              │                                    │
│                    ┌─────────┴─────────┐                         │
│                    │                   │                         │
│              ┌─────────┐         ┌─────────┐                     │
│              │  Codex  │         │ ChatGPT │                     │
│              │ (alias) │         │ (alias) │                     │
│              └─────────┘         └─────────┘                     │
│                                                                   │
│  When querying sentiment for any of these tools, all data is     │
│  consolidated under "OpenAI"                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## API Sequence Diagram

```
Admin UI          API Server        ToolService      DB (Cosmos)
   │                  │                  │                │
   │  PUT /alias      │                  │                │
   ├─────────────────>│                  │                │
   │                  │  create_alias()  │                │
   │                  ├─────────────────>│                │
   │                  │                  │  get_tool()    │
   │                  │                  ├───────────────>│
   │                  │                  │   alias tool   │
   │                  │                  │<───────────────┤
   │                  │                  │  get_tool()    │
   │                  │                  ├───────────────>│
   │                  │                  │  primary tool  │
   │                  │                  │<───────────────┤
   │                  │                  │                │
   │                  │                  │ has_circular() │
   │                  │                  ├───────────────>│
   │                  │                  │   false        │
   │                  │                  │<───────────────┤
   │                  │                  │                │
   │                  │                  │ create_item()  │
   │                  │                  ├───────────────>│
   │                  │                  │   alias obj    │
   │                  │                  │<───────────────┤
   │                  │    alias obj     │                │
   │                  │<─────────────────┤                │
   │  200 OK          │                  │                │
   │<─────────────────┤                  │                │
   │                  │                  │                │
   │                  │                  │                │
   │  GET sentiment   │                  │                │
   ├─────────────────>│                  │                │
   │                  │  get_tool_sent() │                │
   │                  ├─────────────────>│                │
   │                  │                  │ resolve_alias()│
   │                  │                  ├───────────────>│
   │                  │                  │  primary_id    │
   │                  │                  │<───────────────┤
   │                  │                  │                │
   │                  │                  │ get_tool_ids() │
   │                  │                  ├───────────────>│
   │                  │                  │  [pri, al1]    │
   │                  │                  │<───────────────┤
   │                  │                  │                │
   │                  │                  │ query_items()  │
   │                  │                  ├───────────────>│
   │                  │                  │  aggregated    │
   │                  │                  │<───────────────┤
   │                  │  sentiment data  │                │
   │                  │<─────────────────┤                │
   │  sentiment data  │                  │                │
   │<─────────────────┤                  │                │
   │                  │                  │                │
```

## Validation Flow

```
                    Link Alias Request
                           │
                           ▼
                  ┌─────────────────┐
                  │ Tool Existence  │
                  │    Check        │
                  └────────┬────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                Both exist?    One missing
                    │             │
                    ▼             ▼
              ┌──────────┐   [404 Error]
              │Self-ref  │   "Tool not found"
              │  Check   │
              └────┬─────┘
                   │
            ┌──────┴──────┐
            │             │
        Different?    Same tool
            │             │
            ▼             ▼
      ┌──────────┐   [400 Error]
      │ Circular │   "Cannot be
      │  Check   │    alias of itself"
      └────┬─────┘
           │
    ┌──────┴──────┐
    │             │
 No cycle?    Cycle detected
    │             │
    ▼             ▼
┌─────────┐   [400 Error]
│Already  │   "Circular alias
│Primary? │    detected"
└────┬────┘
     │
┌────┴────┐
│         │
Not      Already
primary   primary
│         │
▼         ▼
[Create]  [400 Error]
Alias     "Already primary
Success   for other aliases"
```
