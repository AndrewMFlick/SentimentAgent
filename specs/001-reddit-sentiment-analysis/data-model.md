# Data Model: Reddit Sentiment Analysis

**Feature**: 001-reddit-sentiment-analysis  
**Date**: 2025-10-13  
**Phase**: Phase 1 - Design  
**Database**: Azure CosmosDB (SQL API)

## Overview

This document defines the data models for the Reddit Sentiment Analysis platform. All models are designed for CosmosDB with 90-day TTL and optimized partitioning for time-series queries.

## CosmosDB Container Strategy

### Containers

1. **posts** - Reddit posts
   - Partition Key: `/subreddit_date` (e.g., "Cursor_2025-10-13")
   - TTL: 90 days
   - Indexing: Composite index on `timestamp` + `upvotes`

2. **comments** - Reddit comments
   - Partition Key: `/post_id_date` (first 8 chars of post_id + date)
   - TTL: 90 days
   - Indexing: Composite index on `timestamp` + `upvotes`

3. **sentiment_scores** - Sentiment analysis results
   - Partition Key: `/ai_tool_date` (e.g., "Cursor_2025-10-13")
   - TTL: 90 days
   - Indexing: Composite index on `timestamp` + `sentiment_class`

4. **trending_topics** - Trending discussions
   - Partition Key: `/date` (e.g., "2025-10-13")
   - TTL: 90 days
   - Indexing: Composite index on `engagement_velocity` + `timestamp`

5. **ai_tools** - Monitored AI developer tools
   - Partition Key: `/tool_name`
   - TTL: None (reference data)
   - Small container (~14 documents)

6. **analysis_queries** - AI agent query history
   - Partition Key: `/query_date` (e.g., "2025-10-13")
   - TTL: 30 days
   - Indexing: `timestamp`

7. **collection_cycles** - Data collection run metadata
   - Partition Key: `/cycle_date` (e.g., "2025-10-13")
   - TTL: 30 days
   - Indexing: `start_time`

## Entity Definitions

### RedditPost

Represents a Reddit post from monitored subreddits.

```python
{
    "id": "abc123def",                    # Reddit post ID (unique)
    "subreddit": "Cursor",                # Subreddit name
    "subreddit_date": "Cursor_2025-10-13", # Partition key
    "author": "username",                 # Reddit username
    "title": "New feature in Cursor...",  # Post title
    "content": "Full post text...",       # Self-text content (may be empty for links)
    "url": "https://reddit.com/...",      # Permalink to post
    "post_type": "text",                  # "text", "link", "image", "video"
    "link_url": "https://...",            # External link (if post_type != "text")
    "timestamp": "2025-10-13T10:30:00Z",  # ISO 8601 timestamp
    "upvotes": 42,                        # Upvote count at collection time
    "upvote_ratio": 0.95,                 # Upvote ratio (0.0-1.0)
    "comment_count": 12,                  # Number of comments
    "is_edited": false,                   # Whether post was edited
    "flair_text": "Discussion",           # Post flair (may be null)
    "is_nsfw": false,                     # NSFW flag
    "is_locked": false,                   # Locked for comments
    "is_archived": false,                 # Archived (>6 months old)
    "collected_at": "2025-10-13T10:35:00Z", # When we collected this data
    "collection_cycle_id": "cycle_20251013_1030", # Reference to collection cycle
    "_ts": 1697196900,                    # CosmosDB timestamp
    "ttl": 7776000                        # 90 days in seconds
}
```

**Validation Rules**:
- `id`: Required, unique, alphanumeric
- `subreddit`: Required, must be in monitored list
- `timestamp`: Required, ISO 8601 format
- `upvotes`: Required, >= 0
- `upvote_ratio`: Required, 0.0 to 1.0
- `comment_count`: Required, >= 0

**Relationships**:
- Has many `RedditComment` (via `post_id`)
- Has many `SentimentScore` (via `content_id`)
- Belongs to `AITool` (via `subreddit` mapping)

---

### RedditComment

Represents a comment on a Reddit post.

```python
{
    "id": "xyz789abc",                    # Reddit comment ID (unique)
    "post_id": "abc123def",               # Parent post ID
    "post_id_date": "abc123de_2025-10-13", # Partition key
    "parent_comment_id": null,            # Parent comment ID (null if top-level)
    "author": "commenter",                # Reddit username
    "content": "Comment text...",         # Comment body
    "timestamp": "2025-10-13T10:45:00Z",  # ISO 8601 timestamp
    "upvotes": 5,                         # Upvote count
    "is_edited": false,                   # Whether comment was edited
    "depth": 0,                           # Comment nesting level (0 = top-level)
    "is_submitter": false,                # Whether author is post author (OP)
    "collected_at": "2025-10-13T10:50:00Z", # When we collected this data
    "collection_cycle_id": "cycle_20251013_1030",
    "_ts": 1697197800,
    "ttl": 7776000                        # 90 days
}
```

**Validation Rules**:
- `id`: Required, unique, alphanumeric
- `post_id`: Required, must reference existing RedditPost
- `parent_comment_id`: Optional, must reference existing RedditComment if provided
- `content`: Required, max 10,000 characters
- `depth`: Required, >= 0, <= 10 (Reddit max depth)

**Relationships**:
- Belongs to `RedditPost` (via `post_id`)
- Belongs to `RedditComment` (parent, via `parent_comment_id`)
- Has many `RedditComment` (children, via `parent_comment_id`)
- Has one `SentimentScore` (via `content_id`)

---

### SentimentScore

Represents sentiment analysis results for a post or comment.

```python
{
    "id": "sent_abc123def",               # Generated ID
    "content_id": "abc123def",            # Reddit post or comment ID
    "content_type": "post",               # "post" or "comment"
    "ai_tool": "Cursor",                  # Associated AI tool
    "ai_tool_date": "Cursor_2025-10-13",  # Partition key
    "subreddit": "Cursor",                # Source subreddit
    "sentiment_class": "positive",        # "positive", "negative", "neutral"
    "confidence_score": 0.92,             # Model confidence (0.0-1.0)
    "positive_score": 0.92,               # Positive class probability
    "negative_score": 0.05,               # Negative class probability
    "neutral_score": 0.03,                # Neutral class probability
    "analysis_method": "distilbert",      # "distilbert" or "llm"
    "model_version": "distilbert-base-uncased-finetuned-sst-2-english",
    "analyzed_at": "2025-10-13T10:55:00Z", # Analysis timestamp
    "analysis_duration_ms": 45,           # Processing time
    "content_preview": "First 200 chars...", # Text snippet for reference
    "emotion_dimensions": {               # Optional: LLM-based analysis
        "joy": 0.8,
        "anger": 0.1,
        "sadness": 0.05,
        "surprise": 0.05
    },
    "collection_cycle_id": "cycle_20251013_1030",
    "_ts": 1697198100,
    "ttl": 7776000                        # 90 days
}
```

**Validation Rules**:
- `content_id`: Required, must reference existing RedditPost or RedditComment
- `sentiment_class`: Required, enum ["positive", "negative", "neutral"]
- `confidence_score`: Required, 0.0 to 1.0
- `positive_score` + `negative_score` + `neutral_score` ≈ 1.0
- `analysis_method`: Required, enum ["distilbert", "llm", "vader"]

**Relationships**:
- Belongs to `RedditPost` or `RedditComment` (via `content_id`)
- Belongs to `AITool` (via `ai_tool`)

---

### AITool

Represents a monitored AI developer tool.

```python
{
    "id": "Cursor",                       # Tool name (also partition key)
    "tool_name": "Cursor",                # Display name
    "associated_subreddits": [            # Monitored subreddits
        "Cursor"
    ],
    "current_sentiment_score": 0.72,      # Latest aggregated sentiment (0-1)
    "sentiment_trend": "up",              # "up", "down", "stable"
    "trend_change_percent": 5.2,          # Percent change (7-day avg)
    "total_posts_analyzed": 1247,         # Lifetime count
    "total_comments_analyzed": 5832,      # Lifetime count
    "last_updated": "2025-10-13T11:00:00Z", # Last sentiment calculation
    "description": "AI-powered code editor", # Tool description
    "website_url": "https://cursor.sh",   # Official website
    "is_active": true,                    # Whether currently monitoring
    "_ts": 1697198400,
    "ttl": -1                             # No expiration (reference data)
}
```

**Validation Rules**:
- `id` / `tool_name`: Required, unique, matches subreddit name
- `associated_subreddits`: Required, array of valid subreddit names
- `current_sentiment_score`: Optional, 0.0 to 1.0
- `sentiment_trend`: Optional, enum ["up", "down", "stable"]

**Relationships**:
- Has many `RedditPost` (via `subreddit` mapping)
- Has many `SentimentScore` (via `ai_tool`)
- Has many `TrendingTopic` (via `ai_tool`)

**Initial Data** (14 AI Tools):
```python
tools = [
    {"id": "Cursor", "tool_name": "Cursor", "associated_subreddits": ["Cursor"], ...},
    {"id": "Bard", "tool_name": "Google Bard", "associated_subreddits": ["Bard"], ...},
    {"id": "GithubCopilot", "tool_name": "GitHub Copilot", "associated_subreddits": ["GithubCopilot", "programming"], ...},
    {"id": "Claude", "tool_name": "Anthropic Claude", "associated_subreddits": ["claude"], ...},
    {"id": "Windsurf", "tool_name": "Windsurf", "associated_subreddits": ["windsurf"], ...},
    {"id": "ChatGPT", "tool_name": "ChatGPT", "associated_subreddits": ["ChatGPTCoding", "OpenAI"], ...},
    {"id": "Vibe", "tool_name": "Vibe Coding", "associated_subreddits": ["vibecoding"], ...},
    {"id": "AWS", "tool_name": "AWS AI Tools", "associated_subreddits": ["aws"], ...},
    {"id": "General", "tool_name": "General AI/ML", "associated_subreddits": ["MachineLearning", "artificial"], ...},
    {"id": "Kiro", "tool_name": "Kiro IDE", "associated_subreddits": ["kiroIDE"], ...},
    {"id": "Jules", "tool_name": "Jules Agent", "associated_subreddits": ["JulesAgent"], ...},
]
```

---

### TrendingTopic

Represents a trending discussion identified by engagement velocity.

```python
{
    "id": "trend_20251013_001",           # Generated ID
    "date": "2025-10-13",                 # Partition key
    "primary_post_id": "abc123def",       # Main post ID
    "related_post_ids": [                 # Related discussion posts
        "def456ghi",
        "ghi789jkl"
    ],
    "ai_tool": "Cursor",                  # Associated AI tool (may be null for cross-tool)
    "theme": "New AI feature release",    # Detected theme/category
    "keywords": [                         # Extracted keywords
        "inline editing",
        "AI completion",
        "performance"
    ],
    "engagement_velocity_score": 8.7,     # Calculated velocity metric
    "total_upvotes": 342,                 # Combined upvotes
    "total_comments": 127,                # Combined comments
    "sentiment_distribution": {           # Aggregated sentiment
        "positive": 0.65,
        "negative": 0.20,
        "neutral": 0.15
    },
    "peak_engagement_time": "2025-10-13T14:00:00Z", # When activity peaked
    "first_detected_at": "2025-10-13T12:00:00Z", # When trending started
    "last_updated_at": "2025-10-13T15:00:00Z", # Last recalculation
    "is_active": true,                    # Still trending
    "summary": "Discussion about new inline editing feature...", # Auto-generated summary
    "collection_cycle_id": "cycle_20251013_1400",
    "_ts": 1697205600,
    "ttl": 7776000                        # 90 days
}
```

**Validation Rules**:
- `primary_post_id`: Required, must reference existing RedditPost
- `theme`: Required, max 200 characters
- `engagement_velocity_score`: Required, >= 0
- `sentiment_distribution`: Required, positive + negative + neutral ≈ 1.0

**Relationships**:
- Belongs to `RedditPost` (primary, via `primary_post_id`)
- Has many `RedditPost` (related, via `related_post_ids`)
- Belongs to `AITool` (via `ai_tool`, optional)

**Engagement Velocity Calculation**:
```python
velocity_score = (
    (upvotes_per_hour * 0.6) +
    (comments_per_hour * 0.4) +
    (upvote_ratio * 2.0)
)
```

---

### AnalysisQuery

Represents a user query to the AI agent.

```python
{
    "id": "query_1697205000_abc",         # Generated ID
    "query_date": "2025-10-13",           # Partition key
    "query_text": "What is driving negative sentiment for Cursor?",
    "query_intent": "sentiment_driver",   # "sentiment_driver", "comparison", "trend_analysis"
    "mentioned_tools": ["Cursor"],        # Extracted AI tools from query
    "user_id": "user_123",                # Optional: user identifier
    "timestamp": "2025-10-13T15:30:00Z",  # Query timestamp
    "response_text": "Analysis shows...", # AI agent response
    "data_sources": [                     # Referenced data
        {
            "type": "sentiment_score",
            "count": 150,
            "date_range": {"start": "2025-10-06", "end": "2025-10-13"}
        },
        {
            "type": "trending_topic",
            "topic_ids": ["trend_20251013_001"],
            "themes": ["performance issues"]
        }
    ],
    "processing_time_ms": 3420,           # Response time
    "llm_model": "gpt-4",                 # LLM used for response
    "token_usage": {                      # Cost tracking
        "prompt_tokens": 1200,
        "completion_tokens": 450,
        "total_tokens": 1650
    },
    "_ts": 1697210400,
    "ttl": 2592000                        # 30 days
}
```

**Validation Rules**:
- `query_text`: Required, max 500 characters
- `query_intent`: Optional, enum ["sentiment_driver", "comparison", "trend_analysis", "general"]
- `response_text`: Required, max 5000 characters
- `processing_time_ms`: Required, >= 0

**Relationships**:
- References `AITool` (via `mentioned_tools`)
- References `SentimentScore` and `TrendingTopic` (via `data_sources`)

---

### DataCollectionCycle

Represents a scheduled 30-minute data collection run.

```python
{
    "id": "cycle_20251013_1030",          # Generated ID (includes timestamp)
    "cycle_date": "2025-10-13",           # Partition key
    "start_time": "2025-10-13T10:30:00Z", # Cycle start
    "end_time": "2025-10-13T10:35:00Z",   # Cycle end
    "duration_seconds": 300,              # Total duration
    "status": "completed",                # "running", "completed", "failed", "partial"
    "subreddits_processed": [             # Successfully processed subreddits
        {"name": "Cursor", "posts": 12, "comments": 45, "duration_ms": 1200},
        {"name": "claude", "posts": 8, "comments": 32, "duration_ms": 980},
        # ... 14 subreddits total
    ],
    "total_posts_collected": 147,         # Total across all subreddits
    "total_comments_collected": 683,      # Total comments
    "total_sentiments_analyzed": 830,     # Posts + comments analyzed
    "errors_encountered": [               # Errors during collection
        {
            "subreddit": "Bard",
            "error_type": "RateLimitError",
            "message": "Rate limit exceeded",
            "timestamp": "2025-10-13T10:33:00Z",
            "retry_count": 3
        }
    ],
    "reddit_api_calls": 142,              # Total API requests
    "rate_limit_hits": 1,                 # Times rate limited
    "sentiment_analysis_duration_ms": 8500, # Time for all sentiment analysis
    "_ts": 1697197500,
    "ttl": 2592000                        # 30 days
}
```

**Validation Rules**:
- `id`: Required, unique, format "cycle_YYYYMMDD_HHMM"
- `status`: Required, enum ["running", "completed", "failed", "partial"]
- `duration_seconds`: Required, >= 0
- `subreddits_processed`: Required, array of 0-14 items

**Relationships**:
- Has many `RedditPost` (via `collection_cycle_id`)
- Has many `RedditComment` (via `collection_cycle_id`)
- Has many `SentimentScore` (via `collection_cycle_id`)

---

## Aggregation Queries

### Dashboard Sentiment Over Time

```sql
-- Get hourly sentiment for last 7 days
SELECT
    ai_tool,
    DATE_TRUNC('hour', analyzed_at) as hour,
    AVG(CASE WHEN sentiment_class = 'positive' THEN 1.0 ELSE 0.0 END) as positive_pct,
    AVG(CASE WHEN sentiment_class = 'negative' THEN 1.0 ELSE 0.0 END) as negative_pct,
    COUNT(*) as total_analyzed
FROM sentiment_scores
WHERE analyzed_at >= DATE_SUB(NOW(), 7, 'day')
GROUP BY ai_tool, hour
ORDER BY hour DESC
```

### Trending Topics (Top 20)

```sql
-- Get current trending topics
SELECT TOP 20 *
FROM trending_topics
WHERE date = TODAY()
  AND is_active = true
ORDER BY engagement_velocity_score DESC
```

### AI Agent Data Retrieval

```sql
-- Get recent sentiment for specific tool
SELECT *
FROM sentiment_scores
WHERE ai_tool = @tool_name
  AND analyzed_at >= DATE_SUB(NOW(), 30, 'day')
ORDER BY analyzed_at DESC
LIMIT 1000
```

## Migration Strategy

### Phase 1: Initial Setup
1. Create CosmosDB account and database
2. Create 7 containers with specified partition keys
3. Configure TTL policies (90 days for data, 30 days for queries/cycles)
4. Set up composite indexes for time-series queries
5. Seed `ai_tools` container with 14 tool definitions

### Phase 2: Local Development
1. Install CosmosDB emulator
2. Run initialization script to create local containers
3. Load sample data for testing (10-20 posts per subreddit)

### Phase 3: Production Deployment
1. Provision CosmosDB with 400 RU/s (auto-scale to 4000 RU/s)
2. Configure backup policy (continuous, 7-day retention)
3. Set up Azure Monitor alerts for RU consumption
4. Enable diagnostic logging

## Data Retention & Cleanup

- **Automatic TTL**: CosmosDB automatically deletes documents after TTL expires
- **Manual cleanup**: Not required, TTL handles expiration
- **Archival (future)**: Export to Azure Blob Storage before TTL expiration if long-term storage needed

## Performance Considerations

- **Partition strategy**: Date-based partitioning distributes load evenly
- **Hot partitions**: Current day's data may be hot, but queries spread across tools/subreddits
- **Read-heavy workload**: Dashboard queries cached for 5 minutes
- **Write pattern**: Burst writes during 30-minute collection cycles, otherwise idle
- **Query optimization**: Use composite indexes for dashboard time-series queries

## Security

- **Access control**: Azure AD authentication for production
- **Encryption**: At-rest encryption enabled by default
- **Network**: Virtual network service endpoints for production
- **Keys**: Stored in Azure Key Vault, rotated every 90 days
