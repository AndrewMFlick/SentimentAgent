# Research: Admin Tool List Management

**Date**: October 21, 2025  
**Feature**: 011-the-admin-section  
**Purpose**: Resolve technical clarifications and establish best practices for implementation

## Research Tasks

### 1. Multi-Category Support in Cosmos DB

**Decision**: Use array field in Tool model to store multiple categories

**Rationale**:
- Cosmos DB SQL API supports array fields natively
- Allows efficient querying with ARRAY_CONTAINS for filtering by category
- Maintains simplicity - no need for separate CategoryMapping container
- Aligns with existing Pydantic model patterns in the codebase

**Alternatives Considered**:
- **Separate CategoryMapping container**: Rejected - adds complexity for marginal benefit. Requires joins and increases query complexity.
- **Comma-separated string**: Rejected - difficult to query, not type-safe, requires parsing
- **Single category only**: Rejected - doesn't meet requirement for multi-category after acquisitions

**Implementation Notes**:
```python
# Pydantic model update
class Tool(BaseModel):
    id: str
    name: str
    vendor: str
    categories: List[str]  # Changed from single 'category' to array
    status: Literal["active", "archived"] = "active"
    # ... other fields
```

**Query Pattern**:
```sql
-- Filter by category
SELECT * FROM Tools t 
WHERE ARRAY_CONTAINS(t.categories, "code_assistant") 
AND t.status = "active"
```

---

### 2. Maximum Categories Per Tool

**Decision**: Limit to 5 categories per tool

**Rationale**:
- Covers 99% of real-world cases (most tools have 1-3 categories)
- Prevents data quality issues from over-categorization
- Maintains UI/UX readability (too many categories create visual clutter)
- Aligns with UX best practice: 5±2 items for optimal cognitive load

**Alternatives Considered**:
- **No limit**: Rejected - could lead to abuse, UI challenges, and reduced data quality
- **Limit to 3**: Rejected - too restrictive for complex tools or post-acquisition scenarios
- **Limit to 10**: Rejected - excessive, creates UI challenges

**Implementation Notes**:
- Add validation in Pydantic model: `@field_validator('categories')`
- Provide clear error message when limit exceeded
- UI should show warning when approaching limit (4-5 categories)

---

### 3. Merge Operation Data Integrity

**Decision**: Implement transactional merge with rollback capability

**Rationale**:
- Cosmos DB supports transactions within a single partition
- Critical operation - must be atomic to prevent data corruption
- Rollback allows recovery from partial failures
- Audit trail required for compliance and debugging

**Alternatives Considered**:
- **Simple data copy**: Rejected - no atomicity guarantee, risk of partial failure
- **Manual merge**: Rejected - error-prone, no audit trail
- **External transaction coordinator**: Rejected - over-engineered for current scale

**Implementation Pattern**:
```python
async def merge_tools(source_tool_ids: List[str], target_tool_id: str):
    # 1. Begin transaction (if supported) or implement compensating logic
    # 2. Validate all tools exist and are mergeable
    # 3. Copy sentiment data with source attribution
    # 4. Update source tools: status="archived", merged_into=target_tool_id
    # 5. Log merge operation to audit log
    # 6. Commit or rollback on error
```

**Data Migration Steps**:
1. Query all sentiment scores for source tools
2. Create new sentiment entries linked to target tool with metadata: `{original_tool_id, merge_date}`
3. Archive source tools (don't delete - preserve for audit)
4. Create ToolMergeRecord for traceability

---

### 4. Archive vs Delete Strategy

**Decision**: Soft delete (archive) as default, hard delete only for errors/duplicates

**Rationale**:
- Preserves historical data for analytics and auditing
- Allows unarchive if decision reversed
- Meets regulatory compliance requirements (data retention)
- Hard delete reserved for truly unwanted data (test entries, duplicates)

**Alternatives Considered**:
- **Always hard delete**: Rejected - loses valuable historical data, no undo
- **Always soft delete**: Rejected - clutters database with truly unwanted data
- **Time-based purge**: Considered for future - archive for N days then auto-purge

**Implementation Rules**:
- Archive: Default action, preserves all data, tool.status = "archived"
- Delete: Requires admin confirmation, shows impact (sentiment count), irreversible
- Unarchive: Simple status flip back to "active"

**UI Flow**:
- Archive button: Single confirmation, shows "will preserve data"
- Delete button: Strong warning dialog, shows sentiment count, requires typing tool name

---

### 5. Concurrent Administrator Actions

**Decision**: Optimistic locking with version field

**Rationale**:
- Cosmos DB supports ETag-based optimistic concurrency
- Prevents lost updates when multiple admins edit same tool
- User-friendly - rare conflicts, clear error messages
- No need for pessimistic locks (admin operations are infrequent)

**Alternatives Considered**:
- **No concurrency control**: Rejected - last write wins, data loss risk
- **Pessimistic locking**: Rejected - complex, overkill for admin frequency
- **Conflict-free replicated data types (CRDTs)**: Rejected - over-engineered

**Implementation**:
```python
# Cosmos DB provides _etag field automatically
async def update_tool(tool_id: str, updates: dict, etag: str):
    # Use etag in replace_item for optimistic concurrency
    container.replace_item(
        item=tool_id,
        body=updated_tool,
        match_condition=MatchConditions.IfNotModified,
        etag=etag
    )
    # Raises PreconditionFailedError if etag mismatch
```

**Error Handling**:
- Catch PreconditionFailedError
- Return 409 Conflict with message: "Tool was modified by another administrator. Please refresh and try again."
- Frontend: Refresh data and allow user to retry

---

### 6. Search and Filtering Performance

**Decision**: Use Cosmos DB composite indexes for common query patterns

**Rationale**:
- Composite indexes improve query performance for multi-field filters
- Supports common patterns: filter by status + category, search by name + vendor
- Minimal storage overhead
- Aligns with Azure Cosmos DB best practices

**Query Patterns to Optimize**:
1. Active tools by category: `status = "active" AND category`
2. Search by name: `status = "active" AND name LIKE "%search%"`
3. Filter by vendor: `status = "active" AND vendor = "X"`
4. Combined: `status + category + vendor`

**Index Configuration**:
```json
{
  "indexingPolicy": {
    "compositeIndexes": [
      [
        {"path": "/status", "order": "ascending"},
        {"path": "/name", "order": "ascending"}
      ],
      [
        {"path": "/status", "order": "ascending"},
        {"path": "/vendor", "order": "ascending"}
      ]
    ]
  }
}
```

**Search Strategy**:
- Server-side: Cosmos DB queries with STARTSWITH for name search (better than LIKE)
- Client-side: Additional filtering for 500+ tools if needed
- Pagination: Return max 100 results per page, use continuation tokens

---

### 7. Audit Logging Best Practices

**Decision**: Create AdminActionLog container with structured logging

**Rationale**:
- Separate container allows independent scaling and retention policies
- Structured data (JSON) enables powerful querying and analytics
- Complies with audit requirements (who, what, when, before/after state)
- Immutable append-only log

**Log Schema**:
```python
class AdminActionLog(BaseModel):
    id: str  # UUID
    partitionKey: str  # action_type or date-based for time-series queries
    timestamp: datetime
    admin_id: str  # From authentication
    action_type: Literal["create", "edit", "archive", "unarchive", "delete", "merge"]
    tool_id: str
    tool_name: str  # Denormalized for readability
    before_state: Optional[dict]  # Tool state before action
    after_state: Optional[dict]   # Tool state after action
    metadata: dict  # Additional context (e.g., merge sources, reason)
```

**Retention Policy**:
- Keep all logs for minimum 1 year (configurable)
- Consider archiving to cold storage after 1 year
- Never delete (unless legal requirement)

---

## Summary

All technical clarifications resolved:

1. ✅ Multi-category support: Array field with max 5 categories
2. ✅ Merge data integrity: Transactional pattern with audit trail
3. ✅ Archive vs delete: Soft delete default, hard delete for errors
4. ✅ Concurrency: Optimistic locking with ETags
5. ✅ Search performance: Composite indexes for common patterns
6. ✅ Audit logging: Separate container with structured data

**Ready for Phase 1**: Data model and API contracts design.
