# Research: Fix CosmosDB DateTime Query Format

**Feature**: 004-fix-the-cosmosdb  
**Date**: 2025-10-17  
**Status**: Complete

## Research Questions

### Q1: What datetime format does CosmosDB PostgreSQL mode accept in query parameters?

**Decision**: Use Unix timestamp (seconds since epoch) as integer values instead of ISO 8601 strings

**Rationale**:
- CosmosDB PostgreSQL mode has JSON serialization issues with ISO 8601 datetime strings in query parameters
- The error `'/' is invalid after a value` suggests the JSON parser is interpreting forward slashes or special characters incorrectly
- Unix timestamps are simple integers that avoid JSON parsing issues entirely
- Azure Cosmos SDK documentation shows examples using `TimestampToDateTime()` function for datetime comparisons
- This approach is database-agnostic and commonly used in distributed systems

**Alternatives Considered**:
1. **ISO 8601 without microseconds** (`2025-10-17T14:53:28Z`) - Already tried, still fails with same error
2. **ISO 8601 with timezone offset** (`2025-10-17T14:53:28+00:00`) - Likely to have same JSON parsing issues
3. **Formatted string** (`2025-10-17 14:53:28`) - Not standard, poor timezone handling
4. **TimestampToDateTime() function** - Requires changing SQL queries to use functions, adds complexity
5. **Unix timestamp (chosen)** - Simple, widely supported, no JSON parsing issues

**Evidence**:
- Current error occurs at byte position 18 of datetime string, suggesting character-based parsing issue
- Azure Cosmos DB uses Cosmos SQL (not pure PostgreSQL), which has different datetime handling
- Stack Overflow and GitHub issues show similar problems with datetime parameters in CosmosDB queries
- Best practice: Store datetimes as Unix timestamps or use `_ts` system property for queries

### Q2: How to maintain backward compatibility with existing ISO 8601 stored dates?

**Decision**: Continue storing dates in ISO 8601 format, only change query parameter format to Unix timestamp

**Rationale**:
- Stored data format doesn't cause the query issue - the problem is with query **parameters**
- ISO 8601 is human-readable in database for debugging
- Cosmos DB can compare Unix timestamp parameters against ISO 8601 stored values using numeric conversion
- Alternatively, store both formats (ISO string + Unix int) for maximum compatibility

**Implementation Approach**:
1. Keep existing `isoformat()` calls for storing datetime values
2. Convert datetime to Unix timestamp when creating query parameters
3. Use numeric comparison in queries: `WHERE c._ts >= @cutoff` or `WHERE UNIX_TIMESTAMP(c.collected_at) >= @cutoff`
4. If needed, add `collected_at_ts` field as Unix timestamp for optimized queries

**Alternatives Considered**:
1. **Migrate all stored dates to Unix timestamps** - Breaking change, requires data migration, loses human readability
2. **Store dual formats** - Increases storage, but provides maximum compatibility
3. **Use Cosmos DB `_ts` system field** - Only tracks last modification, not original collection time

### Q3: What testing strategy validates datetime query compatibility?

**Decision**: Integration tests with real CosmosDB emulator testing all datetime query scenarios

**Testing Strategy**:
1. **Setup**: Start CosmosDB emulator, seed with test data containing various datetime formats
2. **Test Cases**:
   - Query with cutoff timestamp (>= operator)
   - Query with date range (BETWEEN)
   - Query with exact match (=)
   - Query with old data (verify cleanup)
   - Query with microsecond precision
   - Query with timezone variations
3. **Validation**: Verify query succeeds AND returns correct results
4. **Teardown**: Clean up test data

**Test Implementation**:
```python
# tests/integration/test_datetime_queries.py
def test_recent_posts_query_with_datetime_filter():
    # Insert posts with known timestamps
    # Query for posts from last 24 hours using Unix timestamp
    # Verify correct posts returned
    # Verify no InternalServerError exceptions
```

**Alternatives Considered**:
1. **Unit tests with mocked database** - Won't catch actual CosmosDB behavior
2. **Manual testing only** - Not repeatable, easy to miss edge cases
3. **End-to-end tests** - Too slow for datetime format validation

### Q4: How do other Python projects handle CosmosDB datetime queries?

**Best Practices Found**:
1. **Use `_ts` system property** when possible for modification time queries
2. **Store timestamps as integers** for custom datetime fields that need querying
3. **Use UDF (User Defined Functions)** for complex datetime operations
4. **Avoid parameterized datetime strings** - Known issue in multiple CosmosDB SDKs

**Example Pattern** (from Azure documentation):
```python
# Store as Unix timestamp
item['collected_at'] = int(datetime.utcnow().timestamp())

# Query with integer parameter
query = "SELECT * FROM c WHERE c.collected_at >= @cutoff"
parameters = [{"name": "@cutoff", "value": int((datetime.utcnow() - timedelta(hours=24)).timestamp())}]
```

**Resources**:
- Azure Cosmos DB Python SDK samples: https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/cosmos/azure-cosmos/samples
- Cosmos DB SQL query reference: https://learn.microsoft.com/en-us/azure/cosmos-db/sql/sql-query-getting-started
- Known issue tracker: https://github.com/Azure/azure-cosmos-python/issues (similar datetime problems reported)

## Key Decisions Summary

| Decision | Choice | Impact |
|----------|--------|--------|
| Query parameter format | Unix timestamp (integer) | Eliminates JSON parsing errors |
| Storage format | Keep ISO 8601 | Maintains human readability, no migration needed |
| Query comparison | Numeric comparison or _ts | Fast, reliable |
| Testing approach | Integration tests with emulator | Validates actual behavior |
| Backward compatibility | Parameter format only | No breaking changes |

## Implementation Notes

1. **Add utility function** to convert datetime to Unix timestamp for queries
2. **Update 4 query methods**: `get_recent_posts()`, `get_sentiment_stats()`, `cleanup_old_data()`, `load_recent_data()`
3. **Consider**: Add `_ts` based queries as alternative (system field, always available)
4. **Document**: Comment why Unix timestamps used in query parameters
5. **Verify**: Test with both emulator and Azure CosmosDB production

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Unix timestamp precision loss | Use float/double for sub-second precision if needed |
| Timezone confusion | Always use UTC, document in code comments |
| Query performance | Add index on datetime fields if needed |
| Production vs emulator differences | Test in both environments before merge |
