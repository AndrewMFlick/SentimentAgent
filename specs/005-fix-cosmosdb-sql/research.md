# Phase 0: Research

**Feature**: 005-fix-cosmosdb-sql  
**Created**: 2025-01-15  
**Status**: Complete ✅

## Research Questions

### 1. CosmosDB SQL Syntax Compatibility

**Question**: What SQL aggregation patterns are supported in Azure CosmosDB PostgreSQL mode?

**Findings**:

- CosmosDB PostgreSQL mode does **NOT support** `CASE WHEN` inside aggregate functions
- Error observed: SQL query returns zero values for all aggregations when using `SUM(CASE WHEN...)`
- **Supported pattern**: Separate `COUNT` queries with `WHERE` clauses

**Source**: GitHub Issue #15, production error logs

**Impact**: Must replace single query with multiple queries

### 2. Query Performance with Multiple Database Calls

**Question**: What is the performance impact of 4 separate queries vs 1 combined query?

**Analysis**:

- Current (broken): 1 query with CASE WHEN → ~1-2 seconds (but returns incorrect data)
- Proposed: 4 separate COUNT queries → estimated ~1-2 seconds per query = 4-8 seconds total
- Risk: May exceed 2-second performance target for time-sensitive dashboard

**Mitigation Options**:

1. **Run queries in parallel** using `asyncio.gather()` (recommended)
   - Expected: ~1-2 seconds total (limited by slowest query)
   - Benefit: Maintains performance target
   - Trade-off: 4x database connections simultaneously

2. Run queries sequentially
   - Expected: 4-8 seconds total
   - Risk: Exceeds performance target, poor user experience

**Decision**: Use parallel query execution with `asyncio.gather()`

### 3. CosmosDB SELECT VALUE Syntax

**Question**: Should we use `SELECT VALUE COUNT(1)` or `SELECT COUNT(1) AS count`?

**Findings**:

- `SELECT VALUE COUNT(1)` returns a single integer: `[42]`
- `SELECT COUNT(1) AS count` returns an object: `[{"count": 42}]`

**Recommendation**: Use `SELECT VALUE COUNT(1)` for cleaner result extraction

**Code Pattern**:

```python
query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff AND c.sentiment = 'positive'"
result = container.query_items(query, parameters=[{"name": "@cutoff", "value": cutoff}])
positive_count = list(result)[0]  # Single integer
```

### 4. Backward Compatibility with Feature #004

**Question**: Does this fix maintain compatibility with Feature #004 datetime filtering?

**Analysis**:

- Feature #004 changed datetime filtering from `datetime.utcnow()` to Unix timestamp `int(time.time())`
- Current code: `c._ts >= @cutoff` where cutoff is Unix timestamp
- **Requirement**: New queries must continue using `c._ts` (Unix timestamp) filtering

**Validation**: ✅ All new queries will use `c._ts >= @cutoff` parameter

### 5. Error Handling for Query Failures

**Question**: What happens if one of the 4 queries fails?

**Current Behavior**: Silent failure, returns zeros

**Proposed Behavior**:

- If any query fails, log error and raise exception
- Do NOT return partial/zero data (misleading)
- Let FastAPI return 500 error to client

**Pattern** (from copilot-instructions.md):

```python
try:
    results = await asyncio.gather(
        query_positive(),
        query_negative(),
        query_neutral(),
        query_avg()
    )
except Exception as e:
    logger.error(f"Failed to query sentiment stats: {e}", exc_info=True)
    raise  # Fail-fast, don't return zeros
```

### 6. Test Coverage Requirements

**Question**: What tests are needed to validate the fix?

**Existing Tests**:

- `backend/tests/integration/test_datetime_queries.py` - tests datetime filtering (Feature #004)

**New Tests Required**:

1. **Unit tests** (`test_database.py`):
   - Test each individual COUNT query
   - Test parallel execution with `asyncio.gather()`
   - Test error handling (database connection failure)

2. **Integration tests** (`test_datetime_queries.py` updates):
   - Test actual sentiment counts match database contents
   - Test with real data: insert posts with known sentiments, verify counts
   - Test subreddit filtering
   - Test time window filtering (24h, 7 days, 30 days)

**Success Criteria**: All existing tests pass + new tests verify accurate counts

## Research Summary

### Key Decisions

1. ✅ Use separate COUNT queries with WHERE clauses (CosmosDB compatible)
2. ✅ Execute queries in parallel with `asyncio.gather()` (maintains <2s performance)
3. ✅ Use `SELECT VALUE COUNT(1)` syntax (cleaner result extraction)
4. ✅ Maintain Unix timestamp filtering from Feature #004 (backward compatible)
5. ✅ Fail-fast error handling (no silent zeros)
6. ✅ Add unit + integration tests (validate accuracy)

### Unknowns Resolved

- ✅ CosmosDB SQL syntax limitations confirmed
- ✅ Performance impact mitigated with parallel execution
- ✅ Backward compatibility validated
- ✅ Error handling pattern defined
- ✅ Test coverage requirements documented

### Risks Identified

1. **Performance**: 4 parallel queries may still exceed 2s on large datasets
   - Mitigation: Monitor query times, add query optimization if needed
   - Fallback: Add caching layer if performance degrades

2. **Database Connection Limits**: 4 simultaneous connections per request
   - Mitigation: Monitor connection pool usage
   - Note: Low traffic application, unlikely to hit limits

### Ready for Phase 1

All research questions resolved. No blockers for design phase.

**Next Step**: Create `data-model.md` in Phase 1
