# Feature Specification: AI Tools Sentiment Analysis Dashboard

**Feature Branch**: `008-dashboard-ui-with`  
**Created**: 2025-10-20  
**Status**: Draft  
**Input**: User description: "Dashboard UI should show a breakdown based on AI tools (Copilot) from a sentiment analysis and show a comparison between different tools (Copilot vs. Jules). This should also track time series and show how sentiment changes over time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Tool-Specific Sentiment Breakdown (Priority: P1)

Users need to see sentiment analysis results segmented by AI tool to understand which tools are receiving positive or negative feedback from the community.

**Why this priority**: This is the core value proposition - understanding sentiment per tool is the primary reason users would access this dashboard. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by loading the dashboard and verifying that sentiment statistics (positive, negative, neutral percentages) are displayed for each AI tool, delivering immediate insight into tool-specific sentiment.

**Acceptance Scenarios**:

1. **Given** Reddit posts mentioning AI tools have been collected and analyzed, **When** user loads the dashboard, **Then** they see a breakdown showing percentage of positive, negative, and neutral sentiment for each AI tool (e.g., Copilot: 60% positive, 25% negative, 15% neutral)
2. **Given** multiple AI tools are mentioned in the dataset, **When** user views the sentiment breakdown, **Then** each tool (Copilot, Jules, etc.) is displayed with its own sentiment statistics
3. **Given** no data exists for a particular tool, **When** user views the dashboard, **Then** that tool shows zero or "No data available" message rather than an error

---

### User Story 2 - Compare Sentiment Between Tools (Priority: P2)

Users need to directly compare sentiment metrics between different AI tools to identify which tools have better community reception and by how much.

**Why this priority**: Comparison is the key differentiator of this feature versus simple statistics. It enables decision-making and competitive analysis but requires the base sentiment data (P1) to exist first.

**Independent Test**: Can be fully tested by viewing two or more tools side-by-side and verifying that comparative metrics (sentiment deltas, ranking, visual comparison) are clearly presented, allowing users to immediately identify which tool has better sentiment.

**Acceptance Scenarios**:

1. **Given** sentiment data exists for Copilot and Jules, **When** user selects comparison view, **Then** they see both tools displayed side-by-side with sentiment percentages and a clear indication of which has more positive sentiment
2. **Given** user is comparing tools, **When** viewing the comparison, **Then** the dashboard highlights the difference in sentiment scores (e.g., "Copilot has 15% more positive sentiment than Jules")
3. **Given** user wants to compare more than two tools, **When** selecting multiple tools, **Then** dashboard shows all selected tools with their sentiment breakdown in a comparable format (e.g., grouped bar chart)

---

### User Story 3 - Track Sentiment Over Time (Priority: P2)

Users need to see how sentiment trends change over time to identify improvements, degradations, or the impact of specific events (product releases, incidents, updates).

**Why this priority**: Time series analysis provides context and identifies trends, which is critical for actionable insights. However, users can still derive value from current snapshots (P1) before adding temporal analysis.

**Independent Test**: Can be fully tested by selecting a time range and verifying that sentiment metrics are plotted over time, showing clear trend lines that allow users to identify periods of sentiment change without needing comparison or breakdown features.

**Acceptance Scenarios**:

1. **Given** sentiment data has been collected over multiple time periods, **When** user views the time series chart, **Then** they see sentiment scores plotted over time with clear date labels on the x-axis
2. **Given** user wants to see how sentiment changed for a specific tool, **When** they filter by tool name, **Then** the time series shows only that tool's sentiment trend over time
3. **Given** user selects a specific time range (e.g., last 7 days, last 30 days), **When** viewing the time series, **Then** the chart displays data only for that selected period
4. **Given** sentiment changes significantly between time periods, **When** user hovers over or clicks a data point, **Then** they see detailed statistics for that specific time period

---

### User Story 4 - Filter and Drill Down by Time Period (Priority: P3)

Users need to select custom time ranges and drill into specific periods to investigate sentiment spikes or drops in detail.

**Why this priority**: This enhances the time series feature (P2) by adding interactivity and granular control, but basic time series visualization provides most of the value. This is a convenience enhancement.

**Independent Test**: Can be fully tested by selecting various time ranges (e.g., "Last 24 hours", "Last week", custom date range) and verifying that all dashboard metrics update to reflect only that period, independent of other features.

**Acceptance Scenarios**:

1. **Given** user wants to see recent sentiment, **When** they select "Last 24 hours" filter, **Then** all dashboard metrics update to show only posts from the last 24 hours
2. **Given** user wants to investigate a specific period, **When** they select a custom date range, **Then** dashboard updates to show sentiment data only for that date range
3. **Given** user has applied time filters, **When** they reset filters, **Then** dashboard returns to showing all available historical data

---

### Edge Cases

- What happens when no data exists for a selected time period? (Dashboard should show "No data available" message instead of empty charts)
- How does the system handle tools mentioned very rarely? (Tools with < 10 mentions should be flagged as "Low sample size" to indicate statistical unreliability)
- What happens when a new AI tool is detected that wasn't previously tracked? (Tool should automatically appear in the dashboard once minimum threshold of mentions is reached)
- How does the dashboard handle sentiment ties between tools? (Display both tools with equal rank and note the tie)
- What happens when data is still being collected/analyzed? (Show loading indicator or "Analysis in progress" for incomplete datasets)
- How does the system handle extreme sentiment shifts? (Highlight unusual changes with visual indicators and allow drill-down into the time period)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display sentiment breakdown (positive, negative, neutral percentages) for each AI tool tracked in the system
- **FR-002**: System MUST support comparison view between at least two AI tools, displaying their sentiment metrics side-by-side
- **FR-003**: System MUST display time series chart showing how sentiment changes over time for each tool
- **FR-004**: System MUST allow users to filter dashboard data by time period (e.g., last 24 hours, last 7 days, last 30 days, custom range)
- **FR-005**: System MUST track and display sentiment data for at minimum: GitHub Copilot and Jules AI
- **FR-006**: System MUST calculate and display the sentiment difference between compared tools (e.g., delta percentage)
- **FR-007**: System MUST handle cases where no data exists for a tool or time period by displaying appropriate "No data" messaging
- **FR-008**: System MUST support selection of specific time period on the time series chart to drill down into details
- **FR-009**: System MUST display total number of posts/mentions analyzed for each tool to provide context for sentiment percentages
- **FR-010**: System MUST automatically detect and categorize mentions of AI tools in Reddit posts through keyword matching or entity recognition
- **FR-011**: Dashboard MUST update sentiment displays when underlying data is refreshed without requiring page reload
- **FR-012**: System MUST support adding new AI tools through a hybrid approach: automatically detect frequently mentioned tools (50+ mentions in 7 days) and flag them for administrator approval before adding to tracking
- **FR-013**: System MUST retain historical sentiment data for at least 90 days with configurable retention periods to support future extension to indefinite retention with archival as storage budget allows
- **FR-014**: System MUST provide administrator interface to review, approve, or reject automatically detected AI tools before they appear in the dashboard

### Key Entities

- **AI Tool**: Represents a specific AI assistant or tool being tracked (e.g., GitHub Copilot, Jules). Attributes include: tool name, vendor/creator, category (code assistant, chat bot, etc.), and aliases/variations for detection
- **Sentiment Score**: Represents analyzed sentiment for a specific mention/post. Attributes include: compound score (-1 to +1), classification (positive/negative/neutral), confidence level, timestamp, source post reference
- **Tool Mention**: Represents a detected reference to an AI tool in a Reddit post. Attributes include: tool identifier, post content excerpt, subreddit, timestamp, sentiment score
- **Time Period Aggregate**: Represents sentiment statistics for a tool within a specific time window. Attributes include: tool identifier, start date, end date, positive count, negative count, neutral count, average sentiment score, total mentions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view sentiment breakdown for any tracked AI tool within 2 seconds of loading the dashboard
- **SC-002**: Users can identify which of two tools has better sentiment within 5 seconds of accessing the comparison view
- **SC-003**: Time series charts display sentiment trends for at least 30 days of historical data with daily granularity
- **SC-004**: Dashboard accurately categorizes at least 90% of tool mentions when compared to manual review
- **SC-005**: 85% of users successfully complete their primary task (viewing sentiment or making a comparison) on first visit without assistance
- **SC-006**: Dashboard supports displaying sentiment data for at least 5 different AI tools simultaneously
- **SC-007**: Time series charts render and display data for queries spanning up to 90 days within 3 seconds
- **SC-008**: Sentiment calculations update within 10 minutes of new Reddit posts being collected
- **SC-009**: Comparison view highlights sentiment differences of 10% or greater with clear visual indicators

### Assumptions

- Reddit posts are already being collected and stored by existing system infrastructure
- Sentiment analysis of post content is performed by existing sentiment analyzer service
- Dashboard has access to historical sentiment scores dating back at least 30 days at the time of feature launch
- Users access the dashboard through a web browser (desktop or mobile)
- AI tool names are relatively unambiguous in context (e.g., "Copilot" clearly refers to GitHub Copilot when discussed in developer communities)
- Initial deployment will retain 90 days of data with architecture designed to support future extension to longer retention periods
- Performance targets assume reasonable hardware (modern web browser, stable internet connection)
- The system will automatically detect common variations and misspellings of tool names (e.g., "copilot", "co-pilot", "GitHub Copilot")
- Administrator approval workflow exists or will be implemented to review automatically detected AI tools
- Storage capacity initially supports 90-day retention with ability to scale for longer retention periods based on business needs

### Known Constraints

- Sentiment analysis accuracy is limited by the underlying natural language processing model's capabilities
- Reddit API rate limits may affect how frequently new data can be collected
- Time series granularity may need to be reduced (e.g., weekly instead of daily) for very long time ranges to maintain performance
- Comparison view is most meaningful when tools have similar sample sizes; comparing a tool with 1000 mentions to one with 10 mentions has limited statistical validity
