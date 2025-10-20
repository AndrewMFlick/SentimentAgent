# Feature Specification: Fix CosmosDB SQL Aggregation for Sentiment Statistics

**Feature Branch**: `005-fix-cosmosdb-sql`  
**Created**: October 20, 2025  
**Status**: Draft  
**Input**: User description: "Fix CosmosDB SQL syntax error in get_sentiment_stats() CASE WHEN statement"
**Related Issue**: [#15](https://github.com/AndrewMFlick/SentimentAgent/issues/15)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - API Returns Accurate Sentiment Statistics (Priority: P1 - MVP)

API consumers request sentiment statistics for a time period and receive accurate aggregated counts of positive, negative, and neutral sentiments along with the average sentiment score.

**Why this priority**: This is the core functionality that must work correctly. Without accurate statistics, the entire sentiment analysis feature provides misleading data to users, making decisions based on incorrect information.

**Independent Test**: Can be fully tested by making API calls to `/api/v1/sentiment/stats?hours=168` and validating that returned counts match the actual sentiment distribution in the database for that time period. Delivers immediate value by providing accurate analytics.

**Acceptance Scenarios**:

1. **Given** the database contains 100 posts with sentiments (60 positive, 25 negative, 15 neutral), **When** a user requests sentiment statistics for the time period covering these posts, **Then** the response shows total=100, positive=60, negative=25, neutral=15
2. **Given** the database contains posts with compound scores (0.5, 0.3, -0.2, -0.4, 0.1), **When** a user requests sentiment statistics for the time period covering these posts, **Then** the response includes avg_sentiment calculated as the average of these scores (0.06)
3. **Given** the database contains no posts in the requested time window, **When** a user requests sentiment statistics, **Then** the response shows total=0, positive=0, negative=0, neutral=0, avg_sentiment=0.0

---

### User Story 2 - Dashboard Displays Real-Time Sentiment Trends (Priority: P2)

Dashboard users view sentiment statistics visualizations that accurately reflect current sentiment distribution across monitored subreddits.

**Why this priority**: While accurate API data is critical, users need to see this data in the UI. This builds upon US1 and provides the visual interface for decision-making.

**Independent Test**: Can be tested by opening the dashboard and verifying that sentiment charts display data matching the database contents. Confirms end-to-end data flow from database through API to UI.

**Acceptance Scenarios**:

1. **Given** the API returns accurate sentiment statistics, **When** a user opens the dashboard, **Then** the sentiment distribution pie chart displays the correct proportions
2. **Given** new posts are collected with different sentiment distributions, **When** the dashboard auto-refreshes after 5 minutes, **Then** the updated statistics reflect the new data
3. **Given** a user filters by specific subreddit, **When** viewing sentiment stats, **Then** only statistics for that subreddit are displayed

---

### User Story 3 - Historical Trend Analysis Works Correctly (Priority: P3)

Users can view sentiment trends over different time periods (1 hour, 24 hours, 1 week) and the statistics accurately reflect sentiment changes over time.

**Why this priority**: Time-based filtering extends the core statistics functionality. Users can identify sentiment trends and patterns over time, valuable for deeper analysis but not required for basic functionality.

**Independent Test**: Can be tested by requesting statistics with different time windows and comparing results to database records within those windows. Validates time-based filtering works correctly with the aggregation fix.

**Acceptance Scenarios**:

1. **Given** the database contains posts from the last 7 days, **When** a user requests statistics for the last 24 hours, **Then** only posts from the last 24 hours are included in the aggregation
2. **Given** sentiment distribution changes significantly between day 1 and day 7, **When** comparing 1-day vs 7-day statistics, **Then** the different time windows show distinct sentiment distributions
3. **Given** a user requests statistics with hours=0 (invalid), **When** the API processes the request, **Then** the system uses a default time window (24 hours) and returns statistics

---

### Edge Cases

- What happens when the database contains posts without sentiment analysis (null sentiment field)?
- How does the system handle requests for subreddits with zero posts in the time window?
- What happens if the compound_score field is missing or null for some posts?
- How does the system behave when requesting statistics for an invalid time range (negative hours, extremely large hours)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST aggregate sentiment counts (positive, negative, neutral) from posts within the specified time window without SQL syntax errors
- **FR-002**: System MUST calculate the average compound sentiment score across all posts in the time window
- **FR-003**: System MUST use CosmosDB-compatible SQL syntax for all aggregation queries
- **FR-004**: System MUST return accurate statistics that match the actual sentiment distribution in the database
- **FR-005**: System MUST handle cases where no posts exist in the time window by returning zero values
- **FR-006**: System MUST filter results by subreddit when a specific subreddit is requested
- **FR-007**: System MUST use Unix timestamp format for datetime filtering (consistent with Feature #004)
- **FR-008**: System MUST return statistics in JSON format with fields: total, positive, negative, neutral, avg_sentiment
- **FR-009**: System MUST handle missing or null sentiment values gracefully without failing the aggregation
- **FR-010**: System MUST complete statistics queries within 2 seconds for time windows up to 1 week

### Key Entities *(include if feature involves data)*

- **SentimentStatistics**: Aggregated view of sentiment data containing total count, positive count, negative count, neutral count, and average compound score for a given time window
- **Post**: Existing entity with sentiment field (values: "positive", "negative", "neutral") and compound_score field (float between -1.0 and 1.0)
- **TimeWindow**: Parameter defining the time range for aggregation (in hours)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: API endpoint `/api/v1/sentiment/stats` returns non-zero statistics when posts exist in the time window (verified by comparing API response to database query results with 100% accuracy)
- **SC-002**: Sentiment statistics calculations complete within 2 seconds for time windows up to 1 week (measured via API response time)
- **SC-003**: Dashboard displays accurate sentiment distribution that matches the database contents (verified by manual spot-checks and automated UI tests)
- **SC-004**: All sentiment aggregation queries execute successfully without SQL syntax errors (verified by integration tests covering all query paths)
- **SC-005**: System correctly handles edge cases (no data, null values, invalid parameters) without crashes or incorrect results (verified by edge case test suite)
