# Feature Specification: Pre-Cached Sentiment Analysis

**Feature Branch**: `017-pre-cached-sentiment`  
**Created**: October 27, 2025  
**Status**: Draft  
**Input**: User description: "There are performance challenges with local cosmosdb for tool level sentiment analysis, but in general there should be a quicker way to get to analysis through pre-cached analysis. For example, 30 days of analysis won't have a significant shift of sentiment over an additional day vs. changes in shorter periods."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Current Tool Sentiment (Priority: P1)

Users need to quickly view sentiment analysis for AI development tools without waiting for slow database queries. The system should display pre-calculated sentiment metrics that update periodically rather than computing them on every request.

**Why this priority**: Core functionality - users cannot effectively use the dashboard if queries take 10+ seconds. This is the primary pain point that blocks all other sentiment analysis features.

**Independent Test**: Can be fully tested by navigating to the tool sentiment dashboard and verifying response time is under 1 second, delivering immediate visibility into tool sentiment without waiting.

**Acceptance Scenarios**:

1. **Given** a user opens the tool sentiment dashboard, **When** they select a 24-hour time period, **Then** sentiment data displays in under 1 second
2. **Given** sentiment data was cached 5 minutes ago, **When** a user requests the same data, **Then** the cached data is returned instantly
3. **Given** a user requests 30-day sentiment trends, **When** the data is retrieved, **Then** it loads in under 2 seconds from pre-calculated aggregates

---

### User Story 2 - Automatic Cache Refresh (Priority: P2)

The system automatically updates cached sentiment analysis at regular intervals, ensuring users see reasonably current data without manual intervention or performance degradation.

**Why this priority**: Essential for data accuracy, but users can tolerate slightly stale data (5-15 minutes old) in exchange for fast performance. Lower priority than initial display speed.

**Independent Test**: Can be tested by monitoring cache refresh jobs and verifying sentiment data updates every N minutes, delivering fresh data without user action.

**Acceptance Scenarios**:

1. **Given** the system is running, **When** 15 minutes have passed since last cache update, **Then** sentiment aggregates are automatically recalculated for all tools
2. **Given** new sentiment scores have been added, **When** the next cache refresh occurs, **Then** the updated metrics include the new data
3. **Given** a cache refresh is in progress, **When** a user requests sentiment data, **Then** they receive the previous cached version without waiting for the refresh to complete

---

### User Story 3 - View Historical Trends (Priority: P3)

Users can view pre-calculated sentiment trends over different time periods (1 day, 7 days, 30 days) with consistent fast performance regardless of the time range selected.

**Why this priority**: Nice-to-have for deeper analysis. Users primarily need current sentiment (P1) and automatic updates (P2). Historical trends add analytical value but are not critical for basic dashboard functionality.

**Independent Test**: Can be tested by selecting different time ranges and verifying all load in under 2 seconds, delivering historical insights without performance penalty.

**Acceptance Scenarios**:

1. **Given** a user selects a 7-day time range, **When** requesting sentiment data, **Then** pre-calculated 7-day aggregates are returned in under 1 second
2. **Given** a user switches between 1-day, 7-day, and 30-day views, **When** each selection is made, **Then** all periods load with similar performance (under 2 seconds)
3. **Given** multiple time periods are available, **When** a user requests a custom date range within cached periods, **Then** the system uses the nearest cached aggregate

---

### Edge Cases

- What happens when cache refresh fails due to database connectivity issues?
- How does the system handle requests during the initial cache population (cold start)?
- What happens if a user requests a time range that falls between cached aggregates?
- How does the system handle cache invalidation when sentiment data is manually corrected or reanalyzed?
- What happens when cache storage fills up or becomes corrupted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST pre-calculate sentiment aggregates for each AI tool at regular intervals (1-hour, 24-hour, 7-day, 30-day periods)
- **FR-002**: System MUST store cached sentiment aggregates including total mentions, positive/negative/neutral counts, percentages, and average sentiment scores
- **FR-003**: System MUST refresh cached aggregates on a configurable schedule (default: every 15 minutes)
- **FR-004**: System MUST serve sentiment data from cache when available, falling back to direct queries only when cache is unavailable
- **FR-005**: System MUST invalidate and recalculate cache when underlying sentiment data is modified (e.g., through reanalysis)
- **FR-006**: System MUST track cache metadata including last update timestamp, data freshness, and coverage period
- **FR-007**: System MUST handle cache misses gracefully by computing sentiment on-demand and populating cache for future requests
- **FR-008**: System MUST support multiple cache granularities (hourly, daily, weekly, monthly) to optimize for different query patterns
- **FR-009**: System MUST expose cache freshness information to users so they know how current the displayed data is
- **FR-010**: System MUST clean up expired cache entries to prevent unbounded storage growth

### Key Entities

- **Sentiment Cache Entry**: Represents pre-calculated sentiment aggregates for a specific tool and time period, including total mentions, sentiment breakdown (positive/negative/neutral counts and percentages), average sentiment score, time range covered, last update timestamp, and data freshness indicator

- **Cache Metadata**: Tracks cache health and performance including last successful refresh time, refresh frequency, cache hit rate, and error counts for monitoring cache effectiveness

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see sentiment data for 24-hour periods in under 1 second (down from current 10+ seconds)
- **SC-002**: System serves 95% of sentiment requests from cache without direct database queries
- **SC-003**: Cached data is refreshed every 15 minutes to ensure users see data no more than 15 minutes old
- **SC-004**: 30-day sentiment trends load in under 2 seconds regardless of total data volume
- **SC-005**: Cache hit rate exceeds 90% for standard time periods (1-hour, 24-hour, 7-day, 30-day)
- **SC-006**: Users can identify data freshness within 5 seconds of viewing any sentiment display
- **SC-007**: System maintains cache availability above 99% during normal operations

## Assumptions

- Sentiment data for longer periods (30 days) changes slowly enough that 15-minute cache refresh intervals provide acceptable accuracy
- Users can tolerate slightly stale data (up to 15 minutes old) in exchange for significantly faster performance
- Cache storage requirements are manageable within current infrastructure constraints
- Most users query standard time periods (1-hour, 24-hour, 7-day, 30-day) rather than arbitrary custom ranges
- Current database query performance issues are primarily due to querying large result sets, not database server capacity

## Dependencies

- Existing sentiment analysis pipeline must continue to populate sentiment_scores collection
- Scheduled job system (APScheduler or similar) for triggering cache refresh operations
- Database support for efficient time-range queries to calculate aggregates
- Storage capacity for cache entries (estimated: minimal - one entry per tool per time period)

## Scope

### In Scope

- Pre-calculating and caching sentiment aggregates for standard time periods
- Automatic cache refresh on a fixed schedule
- Cache invalidation when underlying sentiment data changes
- Serving sentiment data from cache with fallback to direct queries
- Exposing cache freshness information to users
- Cleaning up expired cache entries

### Out of Scope

- Real-time sentiment analysis updates (15-minute refresh interval is acceptable)
- Custom time range caching (only standard periods: 1-hour, 24-hour, 7-day, 30-day)
- Distributed caching across multiple servers
- Cache warming strategies for new tools
- Predictive cache pre-population based on user access patterns
- Cache compression or optimization techniques
