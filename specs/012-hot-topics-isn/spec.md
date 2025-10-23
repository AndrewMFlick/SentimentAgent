# Feature Specification: Enhanced Hot Topics with Tool Insights

**Feature Branch**: `012-hot-topics-isn`  
**Created**: 2025-10-23  
**Status**: Draft  
**Input**: User description: "Hot Topics isn't implemented in a useful fashion. More insight should be given to hot topics related to tools. This should give an engagement score, sentiment, and the related posts. The posts should include a link so that a deeper inspection can be made."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Hot Topics Dashboard with Engagement Metrics (Priority: P1)

Users need to quickly identify which developer tools are generating the most discussion and engagement in the community, along with the overall sentiment toward each tool.

**Why this priority**: This is the core value proposition - giving users immediate visibility into trending tools and community sentiment. Without this, users cannot make informed decisions about tool adoption or monitor tool reputation.

**Independent Test**: Can be fully tested by navigating to the Hot Topics page and verifying that it displays a ranked list of tools with engagement scores and sentiment indicators, delivering immediate value to users monitoring tool trends.

**Acceptance Scenarios**:

1. **Given** a user visits the Hot Topics page, **When** the page loads, **Then** they see a ranked list of developer tools ordered by engagement score (most engaged first)
2. **Given** a user views a hot topic entry, **When** examining the metrics, **Then** they see an engagement score (number of mentions/discussions), overall sentiment (positive/negative/neutral percentage), and total post count
3. **Given** multiple tools are being discussed, **When** viewing the list, **Then** tools with higher engagement appear at the top of the list
4. **Given** a tool has sentiment data, **When** viewing its hot topic card, **Then** the sentiment is visually indicated (color-coded or with icons for positive/negative/neutral)

---

### User Story 2 - Access Related Posts with Deep Links (Priority: P2)

Users need to investigate why a tool is trending by reading the actual Reddit posts and comments that mention the tool, with direct links to the original discussions.

**Why this priority**: Provides context and evidence for the metrics shown. Users can validate trends and understand the "why" behind sentiment scores by reading source material.

**Independent Test**: Can be tested independently by clicking on any hot topic to view its related posts, with each post showing preview content and a working link to Reddit that opens the original discussion.

**Acceptance Scenarios**:

1. **Given** a user selects a hot topic, **When** they view its details, **Then** they see a list of related Reddit posts that mention the tool
2. **Given** a user views related posts, **When** examining each post, **Then** they see the post title, excerpt/preview text, post author, subreddit source, and timestamp
3. **Given** a user wants to read more, **When** they click on a post link, **Then** they are directed to the original Reddit thread in a new browser tab
4. **Given** a post has associated comments, **When** viewing the post preview, **Then** the comment count is displayed
5. **Given** multiple posts mention the same tool, **When** viewing related posts, **Then** posts are ordered by engagement (most comments/upvotes first), with only posts that have engagement within the selected time range displayed

---

### User Story 3 - Filter and Time-Range Selection (Priority: P3)

Users need to focus on specific time periods or sentiment types to understand trends over time and filter out noise.

**Why this priority**: Enhances analysis capabilities but is not essential for basic hot topic viewing. Users can still get value without filtering.

**Independent Test**: Can be tested by applying different time range filters (24 hours, 7 days, 30 days) and verifying that engagement scores and post lists update accordingly.

**Acceptance Scenarios**:

1. **Given** a user is viewing hot topics, **When** they select a time range filter (e.g., "Last 24 hours", "Last 7 days", "Last 30 days"), **Then** the hot topics list and metrics update to reflect only posts from that time period
2. **Given** a user wants to focus on positive or negative sentiment, **When** they apply a sentiment filter, **Then** only topics matching that sentiment criteria are shown
3. **Given** filters are applied, **When** viewing related posts, **Then** only posts matching the filter criteria are included in the list

---

### Edge Cases

- What happens when a tool has no recent posts (no data for the selected time range)?
- How does the system handle tools mentioned in posts that are later deleted or removed by moderators?
- What if a tool name appears in a post but without clear positive/negative sentiment (neutral/ambiguous)?
- How are tools with very low engagement (1-2 mentions) displayed or filtered out to reduce noise?
- What happens when Reddit API is unavailable or rate-limited?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate an engagement score for each developer tool based on number of mentions across Reddit posts and comments
- **FR-002**: System MUST calculate overall sentiment distribution (percentage positive, negative, neutral) for each tool based on aggregated sentiment analysis of posts mentioning that tool
- **FR-003**: System MUST display hot topics in a ranked list ordered by engagement score (highest engagement first)
- **FR-004**: System MUST provide access to related posts for each hot topic, showing posts that mention the specific tool
- **FR-005**: System MUST include direct links to original Reddit posts that open in a new browser tab
- **FR-006**: System MUST display post metadata including title, author, subreddit, timestamp, and comment count
- **FR-007**: System MUST show post preview text (excerpt from post content) for context
- **FR-008**: System MUST support time range filtering (at minimum: 24 hours, 7 days, 30 days)
- **FR-009**: System MUST update hot topics and related posts when time range filter changes, excluding posts without engagement within the selected time range
- **FR-010**: System MUST sort related posts by engagement (most comments/upvotes first), filtering out posts with no engagement activity within the selected timeline
- **FR-011**: System MUST handle cases where tools have insufficient data (display "Not enough data" or similar message)
- **FR-012**: System MUST visually distinguish between positive, negative, and neutral sentiment using color coding or iconography
- **FR-013**: System MUST display up to 20 related posts initially with a "Load More" button to fetch additional posts in batches of 20 when more posts are available

### Key Entities

- **Hot Topic**: Represents a developer tool trending in discussions with associated metrics
  - Tool identifier (links to Tools table)
  - Engagement score (calculated metric)
  - Sentiment distribution (positive %, negative %, neutral %)
  - Time period (for time-based filtering)
  - Total post count mentioning the tool

- **Related Post**: A Reddit post that mentions a specific developer tool
  - Post ID (Reddit unique identifier)
  - Tool identifier (which tool it mentions)
  - Post title
  - Post excerpt/preview text
  - Author username
  - Subreddit source
  - Timestamp (when posted)
  - Comment count
  - Direct link to Reddit
  - Sentiment classification (positive/negative/neutral)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the top 10 trending developer tools within 5 seconds of viewing the Hot Topics page
- **SC-002**: Users can access original Reddit posts with a single click, with links opening correctly in 100% of cases
- **SC-003**: Engagement scores accurately reflect discussion volume, updating within 1 hour of new posts being collected
- **SC-004**: Sentiment percentages match the underlying sentiment analysis data with 95% accuracy
- **SC-005**: Time range filtering produces results within 2 seconds for any supported time period
- **SC-006**: At least 80% of hot topics have 5 or more related posts available for user review
- **SC-007**: Users can successfully complete the workflow "find trending tool → view related posts → click to Reddit" in under 30 seconds
- **SC-008**: Post previews contain sufficient context (minimum 100 characters or first 2 sentences) for users to decide whether to click through

## Assumptions

- Reddit API access is available and rate limits are sufficient for displaying post links
- Sentiment analysis has already been performed on posts (this feature displays existing analysis, doesn't perform new analysis)
- Tool detection has already identified which tools are mentioned in posts (existing `detected_tool_ids` field)
- Engagement score calculation method: Based on frequency of mentions (not upvotes/awards, which may not be accessible)
- Default time range if not specified: Last 7 days
- Minimum engagement threshold to appear as "hot topic": At least 3 mentions in the time period
- Post preview text: Extracted from post content or title if content is unavailable
- Related posts default sort order: If not clarified, assume recency (newest first)
- Maximum related posts: If not clarified, assume show top 20 with "load more" option

## Dependencies

- Existing sentiment analysis service must be operational and populated with data
- Tool detection integration must be working (from recent `detected_tool_ids` implementation)
- Database must have Tools container with active tools
- Reddit post and comment data must be available in database
- Frontend must support external link navigation (Reddit posts)

## Out of Scope

- Real-time streaming updates of hot topics (batch updates are sufficient)
- Sentiment analysis of individual Reddit comments (only post-level sentiment)
- User accounts or personalization (saved hot topics, alerts, etc.)
- Comparison tools (side-by-side tool sentiment comparison)
- Historical trending (showing how a tool's popularity changed over months)
- Integration with other platforms beyond Reddit (Twitter, HackerNews, etc.)
- Moderation or filtering of inappropriate content (assumes Reddit moderation is sufficient)
