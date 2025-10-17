# Feature Specification: Fix CosmosDB DateTime Query Format

**Feature Branch**: `004-fix-the-cosmosdb`  
**Created**: 2025-10-17  
**Status**: Draft  
**Input**: User description: "Fix the CosmosDB DateTime Query Format"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Startup Data Loading (Priority: P1)

When the backend application starts up, it needs to load recent data from CosmosDB to warm up caches and provide immediate data availability to API consumers. Currently, this data loading fails due to datetime format incompatibility between the Python application and CosmosDB's PostgreSQL mode emulator.

**Why this priority**: This is blocking a critical P1 user story (#003) for startup data loading. Without this fix, the backend starts with empty caches, causing slow initial response times and degraded user experience.

**Independent Test**: Can be fully tested by starting the backend application and verifying that the `load_recent_data()` method successfully queries and loads posts, comments, and sentiment data from the last 24 hours without errors.

**Acceptance Scenarios**:

1. **Given** the backend is starting up and CosmosDB contains data from the past 24 hours, **When** the `load_recent_data()` method executes, **Then** it successfully queries and loads all recent posts, comments, and sentiment data without throwing InternalServerError exceptions
2. **Given** a database query includes a datetime filter parameter, **When** the query is executed against CosmosDB PostgreSQL mode, **Then** the datetime parameter is properly formatted and accepted by the database engine
3. **Given** the application logs startup events, **When** data loading completes successfully, **Then** the logs show actual counts of loaded data (e.g., "100 posts, 250 comments") instead of "Data loading temporarily disabled"

---

### User Story 2 - Historical Data Queries (Priority: P2)

Users and background jobs need to query historical data based on time ranges (e.g., "get posts from the last 24 hours", "get sentiment stats from last week"). These queries currently fail when datetime parameters are used.

**Why this priority**: This affects multiple API endpoints and scheduled jobs that rely on time-based queries, including trending topic analysis, data cleanup jobs, and historical sentiment reporting.

**Independent Test**: Can be fully tested by calling any API endpoint that accepts time range parameters (e.g., `/api/v1/posts?hours=24`) and verifying that results are returned without database errors.

**Acceptance Scenarios**:

1. **Given** a request to get posts from the last N hours, **When** `get_recent_posts(hours=24)` is called, **Then** it returns all posts collected within that timeframe without query errors
2. **Given** a request to get sentiment statistics for a time range, **When** `get_sentiment_stats(hours=168)` is called, **Then** it returns aggregated statistics for the past week without InternalServerError
3. **Given** the cleanup job runs on schedule, **When** `cleanup_old_data()` executes to remove data older than the retention period, **Then** it successfully queries and deletes old records without datetime format errors

---

### User Story 3 - Data Collection and Analysis Jobs (Priority: P2)

Scheduled background jobs collect Reddit data, analyze sentiment, and identify trending topics. These jobs need to check for existing data and avoid duplicates by querying based on timestamps.

**Why this priority**: While jobs can still collect new data, they cannot efficiently check for duplicates or incremental updates, leading to potential data duplication and wasted API quota.

**Independent Test**: Can be fully tested by triggering a data collection job manually and verifying that it can query existing posts by timestamp to avoid re-collecting the same data.

**Acceptance Scenarios**:

1. **Given** a scheduled collection job is about to collect new posts, **When** it queries for existing posts from the same time period, **Then** it successfully retrieves existing posts to check for duplicates
2. **Given** the trending topics analyzer needs recent data, **When** it queries for posts and comments from the analysis window, **Then** it receives all relevant data without query failures

---

### Edge Cases

- What happens when datetime values include microseconds vs. without microseconds?
- How does the system handle timezone-aware vs. naive datetime objects?
- What happens when datetime values are stored in ISO 8601 format but queried in a different format?
- How does the system handle datetime comparison operators (>=, <=, BETWEEN) with the correct format?
- What happens when the CosmosDB emulator version is upgraded and datetime format requirements change?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST successfully execute datetime-filtered queries against CosmosDB PostgreSQL mode emulator without InternalServerError exceptions
- **FR-002**: System MUST support datetime comparison operators (>=, <=, =, BETWEEN) in query parameters for all time-based filtering
- **FR-003**: System MUST format datetime parameters consistently across all database query methods (`get_recent_posts`, `get_sentiment_stats`, `cleanup_old_data`, `load_recent_data`)
- **FR-004**: System MUST handle datetime values stored in ISO 8601 format (with or without microseconds) when querying
- **FR-005**: System MUST preserve backward compatibility with existing data already stored in the database
- **FR-006**: System MUST log clear error messages when datetime format issues occur, including the attempted format and the database error response
- **FR-007**: Data loading on startup MUST complete successfully and load actual data counts instead of being disabled
- **FR-008**: System MUST validate datetime format compatibility during database initialization to detect format issues early

### Key Entities

- **DateTime Query Parameter**: Represents a datetime value passed as a query parameter to CosmosDB, requiring specific formatting to be accepted by PostgreSQL mode
- **Database Query**: SQL queries with parameterized datetime filters (e.g., `WHERE c.collected_at >= @cutoff`)
- **Stored DateTime Fields**: Datetime values persisted in CosmosDB documents (created_utc, collected_at, analyzed_at, peak_time) that may use different formats

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Backend startup completes data loading within 5 seconds and logs actual counts of loaded records (posts, comments, sentiment data)
- **SC-002**: All datetime-filtered database queries execute successfully with 100% success rate (zero InternalServerError exceptions)
- **SC-003**: Historical data queries (last 24 hours, last 7 days, last 30 days) return results in under 2 seconds
- **SC-004**: Scheduled cleanup jobs successfully delete old data without datetime query errors, maintaining system performance
- **SC-005**: Data collection jobs can query for existing posts by timestamp to avoid duplicates, reducing duplicate data by 100%

## Context *(mandatory)*

### Problem Statement

The backend application currently cannot execute datetime-filtered queries against CosmosDB when running in PostgreSQL mode emulation. When attempting to query data using datetime parameters (e.g., filtering posts collected in the last 24 hours), the database returns HTTP 500 InternalServerError with the message: `'/' is invalid after a value. Expected either ',', '}', or ']'`. 

This error occurs at byte position 18 of the datetime parameter string, indicating a JSON serialization issue in how CosmosDB PostgreSQL mode parses the datetime values passed from the Python application.

The current implementation:
1. Stores datetime values using Python's `.isoformat()` method (e.g., `"2025-10-17T14:53:28.639801Z"`)
2. Queries using `.strftime("%Y-%m-%dT%H:%M:%SZ")` format (e.g., `"2025-10-17T14:53:28Z"`)
3. Passes datetime strings as query parameters like `{"name": "@cutoff", "value": "2025-10-17T14:53:28Z"}`

The mismatch between storage format (with microseconds) and query format (without microseconds), or a fundamental incompatibility with how CosmosDB PostgreSQL mode expects datetime parameters, causes all time-based queries to fail.

As a temporary workaround, the `load_recent_data()` method has been disabled, preventing startup data loading and leaving the application with cold caches on startup.

### Current Behavior

- Backend starts successfully but skips data loading with warning: "Data loading temporarily disabled - datetime format issue with CosmosDB"
- Any API call or background job that queries data by datetime fails with InternalServerError
- Logs show repeated retry attempts with exponential backoff (4 retries) before giving up
- No data is loaded into memory on startup, causing slow initial API responses
- Cleanup jobs cannot run, risking database bloat over time
- Data collection jobs cannot check for duplicates efficiently

### Desired Behavior

- Backend starts and successfully loads recent data (posts, comments, sentiment stats) into memory
- All datetime-filtered queries execute without errors
- Logs show successful data loading: "Data loading complete: 100 posts, 250 comments, 75 sentiment scores loaded in 2.35s"
- API endpoints respond quickly even immediately after startup
- Scheduled jobs run successfully with time-based queries
- Data cleanup maintains database size within retention policies

## Assumptions *(mandatory)*

- CosmosDB PostgreSQL mode emulator expects datetime values in a specific format (to be determined through research/testing)
- The Azure Cosmos SDK for Python (version 4.5.1) correctly serializes query parameters when given the proper format
- Datetime values already stored in the database can be queried regardless of their stored format
- The system uses UTC timezone consistently for all datetime operations
- Performance impact of datetime formatting changes is negligible (< 1ms per query)
- The solution should work with both the local CosmosDB emulator and Azure-hosted CosmosDB

## Dependencies *(optional)*

- Azure Cosmos SDK for Python (version 4.5.1) - already installed
- CosmosDB Emulator running in PostgreSQL mode on localhost:8081
- Python 3.13.3 datetime handling capabilities
- Existing database schema with datetime fields (created_utc, collected_at, analyzed_at, peak_time)

## Out of Scope *(optional)*

- Migrating existing data to a new datetime format (backward compatibility must be maintained)
- Changing the database engine or moving away from CosmosDB PostgreSQL mode
- Implementing timezone conversion or multi-timezone support (system remains UTC-only)
- Optimizing query performance beyond fixing the datetime format issue
- Adding new datetime-based query features or capabilities

## Constraints *(optional)*

- Must maintain backward compatibility with data already stored in the database
- Cannot introduce breaking changes to the public API
- Must work with the current CosmosDB emulator version without requiring upgrades
- Changes should be localized to the database service layer without affecting other components
- Solution must work consistently across development (emulator) and production (Azure CosmosDB) environments

## Security & Privacy Considerations *(optional)*

- No user-provided datetime values are used in queries (all datetimes are system-generated), mitigating SQL injection risks
- Datetime format changes should not expose system internals through error messages
- Query parameter logging should not reveal sensitive timestamp information that could be used for timing attacks

## References *(optional)*

- Azure Cosmos DB SQL Query documentation: https://learn.microsoft.com/en-us/azure/cosmos-db/sql/sql-query-getting-started
- Azure Cosmos DB PostgreSQL mode documentation: https://learn.microsoft.com/en-us/azure/cosmos-db/postgresql/
- Python datetime.isoformat() documentation: https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat
- Current implementation: `/Users/andrewflick/Documents/SentimentAgent/backend/src/services/database.py`
- Feature #003 spec (blocked by this issue): `/Users/andrewflick/Documents/SentimentAgent/specs/003-backend-stability-and-data-loading/spec.md`


- **SC-001**: [Measurable metric, e.g., "Users can complete account creation in under 2 minutes"]
- **SC-002**: [Measurable metric, e.g., "System handles 1000 concurrent users without degradation"]
- **SC-003**: [User satisfaction metric, e.g., "90% of users successfully complete primary task on first attempt"]
- **SC-004**: [Business metric, e.g., "Reduce support tickets related to [X] by 50%"]
