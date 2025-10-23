# Data Model: Enhanced Hot Topics with Tool Insights

**Feature**: 012-hot-topics-isn  
**Date**: 2025-10-23

## Overview

This feature introduces **calculated/derived entities** rather than new database tables. Hot Topics and Related Posts are **query results** aggregated from existing data (Tools, reddit_posts, reddit_comments, sentiment_scores).

## Existing Entities (Used, Not Modified)

### Tool (Existing Container: `Tools`)

```python
{
  "id": str,                    # Unique tool identifier
  "name": str,                  # Display name (e.g., "GitHub Copilot")
  "slug": str,                  # URL-safe identifier
  "vendor": str,                # Tool vendor/creator
  "categories": List[str],      # Tool categories
  "status": str,                # "active" | "archived" | "pending"
  # ... other admin fields
}
```

**Usage**: Source of truth for tools, queried to build hot topics list.

---

### RedditPost (Existing Container: `reddit_posts`)

```python
{
  "id": str,                           # Reddit post ID
  "subreddit": str,                    # Subreddit name
  "author": str,                       # Post author username
  "title": str,                        # Post title
  "content": str,                      # Post content/selftext
  "url": str,                          # Post URL (Reddit link)
  "created_utc": datetime,             # Post creation timestamp
  "upvotes": int,                      # Number of upvotes
  "comment_count": int,                # Number of comments
  "collected_at": datetime,            # Collection timestamp
  "_ts": int                           # CosmosDB system timestamp (Unix)
}
```

**Usage**: Source of related posts, filtered by time range and sorted by engagement.

---

### RedditComment (Existing Container: `reddit_comments`)

```python
{
  "id": str,                    # Reddit comment ID
  "post_id": str,               # Parent post ID
  "author": str,                # Comment author username
  "content": str,               # Comment text
  "created_utc": datetime,      # Comment creation timestamp
  "upvotes": int,               # Number of upvotes
  "_ts": int                    # CosmosDB system timestamp (Unix)
}
```

**Usage**: Used to detect "engagement activity" - posts with recent comments are considered "engaged".

---

### SentimentScore (Existing Container: `sentiment_scores`)

```python
{
  "content_id": str,                   # Reddit post or comment ID
  "content_type": str,                 # "post" | "comment"
  "subreddit": str,                    # Source subreddit
  "sentiment": str,                    # "positive" | "negative" | "neutral"
  "confidence": float,                 # 0.0-1.0
  "compound_score": float,             # -1.0 to 1.0
  "detected_tool_ids": List[str],      # AI tool IDs detected in content
  "analyzed_at": datetime,             # Analysis timestamp
  "_ts": int                           # CosmosDB system timestamp (Unix)
}
```

**Usage**: 
- Join with posts via `content_id`
- Filter by `detected_tool_ids` to find mentions of specific tools
- Aggregate `sentiment` for sentiment distribution percentages

---

## Derived Entities (Calculated at Query Time)

### HotTopic (API Response Model)

**Not stored in database** - calculated on-demand from aggregated queries.

```python
class HotTopic(BaseModel):
    """Hot topic with engagement metrics."""
    
    tool_id: str                           # Tool.id
    tool_name: str                         # Tool.name
    tool_slug: str                         # Tool.slug for URL routing
    engagement_score: int                  # Calculated: (mentions × 10) + (comments × 2) + upvotes
    total_mentions: int                    # Count of posts/comments with tool in detected_tool_ids
    total_comments: int                    # Sum of comment_count for related posts
    total_upvotes: int                     # Sum of upvotes for related posts
    sentiment_distribution: SentimentDist  # Nested object
    time_range: str                        # Filter applied: "24h" | "7d" | "30d"
    generated_at: datetime                 # Timestamp when calculated

class SentimentDist(BaseModel):
    """Sentiment distribution breakdown."""
    
    positive_count: int                    # Count of positive sentiment mentions
    negative_count: int                    # Count of negative sentiment mentions
    neutral_count: int                     # Count of neutral sentiment mentions
    positive_percent: float                # positive_count / total_mentions × 100
    negative_percent: float                # negative_count / total_mentions × 100
    neutral_percent: float                 # neutral_count / total_mentions × 100
```

**Calculation Logic** (Backend Service):
```python
async def get_hot_topics(time_range: str) -> List[HotTopic]:
    """
    1. Calculate cutoff timestamp from time_range
    2. Query Tools container for active tools
    3. For each tool:
       a. COUNT posts/comments where tool_id in detected_tool_ids AND _ts >= cutoff
       b. SUM comment_count and upvotes from related posts
       c. COUNT sentiment by type (positive/negative/neutral)
       d. Calculate engagement_score
    4. Sort by engagement_score DESC
    5. Return top N tools
    """
```

**Query Performance**: 
- Multiple tools queried in parallel using `asyncio.gather()`
- Each tool query uses indexed `detected_tool_ids` field
- Time range filter uses `_ts` field (system-indexed)
- Target: <5 seconds for top 10 tools (SC-001)

---

### RelatedPost (API Response Model)

**Not stored in database** - filtered and sorted view of reddit_posts.

```python
class RelatedPost(BaseModel):
    """Reddit post related to a tool."""
    
    post_id: str                           # RedditPost.id
    title: str                             # RedditPost.title
    excerpt: str                           # First 150 chars of content
    author: str                            # RedditPost.author
    subreddit: str                         # RedditPost.subreddit
    created_utc: datetime                  # RedditPost.created_utc
    reddit_url: str                        # RedditPost.url (direct link)
    comment_count: int                     # RedditPost.comment_count
    upvotes: int                           # RedditPost.upvotes
    sentiment: str                         # From SentimentScore (joined)
    engagement_score: int                  # comment_count + upvotes (for sorting)
```

**Calculation Logic** (Backend Service):
```python
async def get_related_posts(
    tool_id: str, 
    time_range: str, 
    offset: int = 0, 
    limit: int = 20
) -> List[RelatedPost]:
    """
    1. Calculate cutoff timestamp from time_range
    2. Query posts WHERE:
       - tool_id IN detected_tool_ids (via sentiment_scores join)
       - _ts >= cutoff OR EXISTS recent comment
    3. LEFT JOIN sentiment_scores ON post_id = content_id
    4. ORDER BY (comment_count + upvotes) DESC
    5. OFFSET/LIMIT for pagination
    6. Return posts with excerpt (first 150 chars)
    """
```

**Engagement Filtering**:
```sql
-- Post engaged if created recently OR has recent comments
WHERE (post._ts >= @cutoff) 
   OR EXISTS (
     SELECT VALUE 1 FROM comments c 
     WHERE c.post_id = post.id AND c._ts >= @cutoff
   )
```

**Query Performance**:
- Composite index: `[detected_tool_ids[], _ts]` on sentiment_scores
- Index: `[post_id, _ts]` on reddit_comments
- Server-side caching: 5-minute TTL for full result set
- Target: <2 seconds for initial 20 posts (SC-005)

---

## State Transitions

### HotTopic Lifecycle

```
User selects time range → Calculate engagement scores → Rank tools → Display list
                ↓
User changes time range → Invalidate cache → Recalculate → Update display
```

**No persistence** - recalculated on each request, cached for 5 minutes.

---

### RelatedPost Pagination State

```
Initial Request (offset=0, limit=20)
    ↓
Calculate full result set → Cache (5 min TTL) → Return first 20
    ↓
Load More Request (offset=20, limit=20)
    ↓
Check cache → Return next 20 (if exists) OR Recalculate (if cache expired)
    ↓
Repeat until hasNextPage = false (returned < 20 posts)
```

---

## Validation Rules

### HotTopic
- **Minimum mentions threshold**: 3 (assumption from spec)
- **Time range values**: "24h" | "7d" | "30d" (from FR-008)
- **Sentiment percentages**: Must sum to 100% ± 0.1% (floating point tolerance)

### RelatedPost
- **Excerpt length**: 100-150 characters (SC-008 requires minimum 100)
- **Reddit URL format**: Must start with `https://reddit.com/` or `https://www.reddit.com/`
- **Engagement score**: `>= 0` (comment_count and upvotes non-negative)

---

## Data Flow Diagram

```
┌──────────────┐
│ User Request │
│ (time_range) │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ GET /api/hot-topics │
│ ?time_range=7d      │
└──────┬──────────────┘
       │
       ▼
┌────────────────────────────┐
│ HotTopicsService           │
│ ├─ Calculate cutoff (_ts)  │
│ ├─ Query active tools      │
│ ├─ Parallel aggregation:   │
│ │   ├─ Count mentions      │
│ │   ├─ Sum engagement      │
│ │   └─ Group sentiment     │
│ ├─ Calculate scores        │
│ └─ Sort by engagement DESC │
└──────┬─────────────────────┘
       │
       ▼
┌────────────────────────┐
│ Return HotTopic[] JSON │
└────────────────────────┘

User clicks tool → GET /api/hot-topics/{tool_id}/posts

┌──────────────────────────────┐
│ RelatedPostsService          │
│ ├─ Check cache (5 min TTL)   │
│ ├─ If miss:                  │
│ │   ├─ Query posts by tool   │
│ │   ├─ Filter by engagement  │
│ │   ├─ Join sentiment        │
│ │   ├─ Sort by engagement    │
│ │   └─ Cache result set      │
│ ├─ Apply offset/limit        │
│ └─ Return RelatedPost[] JSON │
└──────────────────────────────┘
```

---

## Indexing Strategy

### Required Indexes (CosmosDB)

**sentiment_scores container**:
```json
{
  "indexingPolicy": {
    "compositeIndexes": [
      [
        {"path": "/detected_tool_ids/*", "order": "ascending"},
        {"path": "/_ts", "order": "descending"}
      ]
    ],
    "includedPaths": [
      {"path": "/sentiment/?"},
      {"path": "/content_id/?"}
    ]
  }
}
```

**reddit_comments container**:
```json
{
  "indexingPolicy": {
    "compositeIndexes": [
      [
        {"path": "/post_id", "order": "ascending"},
        {"path": "/_ts", "order": "descending"}
      ]
    ]
  }
}
```

**reddit_posts container**:
- Existing indexes sufficient (id, _ts auto-indexed)
- comment_count and upvotes fields auto-indexed by CosmosDB

---

## Migration Plan

**No database migrations required** - all existing containers have necessary fields.

**Index additions**:
1. Add composite indexes via Azure Portal or Azure CLI
2. Indexing operation is online, no downtime
3. Monitor index progress via portal metrics
4. Estimated time: 5-10 minutes for current dataset size

**Backward compatibility**: ✅ No breaking changes to existing data structures
