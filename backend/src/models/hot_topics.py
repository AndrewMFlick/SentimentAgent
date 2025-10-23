"""Hot Topics data models.

This module defines Pydantic models for the Hot Topics feature,
which displays trending developer tools with engagement metrics
and related Reddit posts.

Models are derived/calculated entities - not stored in database.
Data is aggregated on-demand from existing containers:
- Tools (tool metadata)
- sentiment_scores (detected_tool_ids, sentiment)
- reddit_posts (post data, engagement metrics)
- reddit_comments (engagement activity)
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class SentimentDistribution(BaseModel):
    """Sentiment distribution breakdown for a tool.
    
    Represents aggregated sentiment analysis across all mentions
    of a specific tool within a time range.
    """

    positive_count: int = Field(
        ...,
        ge=0,
        description="Number of positive sentiment mentions"
    )
    negative_count: int = Field(
        ...,
        ge=0,
        description="Number of negative sentiment mentions"
    )
    neutral_count: int = Field(
        ...,
        ge=0,
        description="Number of neutral sentiment mentions"
    )
    positive_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of positive mentions (0-100)"
    )
    negative_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of negative mentions (0-100)"
    )
    neutral_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of neutral mentions (0-100)"
    )


class HotTopic(BaseModel):
    """Hot topic representing a trending developer tool.
    
    Calculated entity aggregated from:
    - Tools container (tool metadata)
    - sentiment_scores (mentions via detected_tool_ids)
    - reddit_posts (comment counts, upvotes)
    
    Not stored in database - generated on-demand per request.
    """

    tool_id: str = Field(
        ...,
        description="Unique tool identifier from Tools container"
    )
    tool_name: str = Field(
        ...,
        description="Display name of the tool (e.g., 'GitHub Copilot')"
    )
    tool_slug: str = Field(
        ...,
        description="URL-safe identifier for routing"
    )
    engagement_score: int = Field(
        ...,
        ge=0,
        description="Calculated engagement: (mentions × 10) + (comments × 2) + upvotes"
    )
    total_mentions: int = Field(
        ...,
        ge=0,
        description="Number of posts/comments mentioning this tool"
    )
    total_comments: int = Field(
        ...,
        ge=0,
        description="Sum of comment counts on related posts"
    )
    total_upvotes: int = Field(
        ...,
        ge=0,
        description="Sum of upvotes on related posts"
    )
    sentiment_distribution: SentimentDistribution = Field(
        ...,
        description="Sentiment breakdown (positive/negative/neutral)"
    )


class RelatedPost(BaseModel):
    """Reddit post related to a specific tool.
    
    Filtered and sorted view of reddit_posts container:
    - Posts mentioning the tool (via sentiment_scores.detected_tool_ids)
    - Within selected time range
    - Sorted by engagement (comment_count + upvotes)
    
    Not stored in database - generated on-demand with pagination.
    """

    post_id: str = Field(
        ...,
        description="Reddit post ID (from reddit_posts.id)"
    )
    title: str = Field(
        ...,
        description="Post title"
    )
    excerpt: str = Field(
        ...,
        min_length=0,
        max_length=200,
        description="First 100-150 characters of post content for preview"
    )
    author: str = Field(
        ...,
        description="Reddit username of post author"
    )
    subreddit: str = Field(
        ...,
        description="Subreddit where post was made"
    )
    created_utc: datetime = Field(
        ...,
        description="When post was created (UTC)"
    )
    reddit_url: str = Field(
        ...,
        description="Direct link to Reddit post (opens in new tab)"
    )
    comment_count: int = Field(
        ...,
        ge=0,
        description="Number of comments on the post"
    )
    upvotes: int = Field(
        ...,
        ge=0,
        description="Number of upvotes"
    )
    sentiment: str = Field(
        ...,
        description="Overall sentiment: 'positive', 'negative', or 'neutral'"
    )
    engagement_score: int = Field(
        ...,
        ge=0,
        description="Calculated engagement for sorting: comment_count + upvotes"
    )


class HotTopicsResponse(BaseModel):
    """API response for GET /api/hot-topics endpoint."""

    hot_topics: List[HotTopic] = Field(
        ...,
        description="Ranked list of hot topics, sorted by engagement_score DESC"
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when results were calculated"
    )
    time_range: str = Field(
        ...,
        description="Applied time range filter: '24h', '7d', or '30d'"
    )


class RelatedPostsResponse(BaseModel):
    """API response for GET /api/hot-topics/{tool_id}/posts endpoint."""

    posts: List[RelatedPost] = Field(
        ...,
        description="Paginated list of related posts, sorted by engagement"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of posts matching criteria (not paginated)"
    )
    has_more: bool = Field(
        ...,
        description="True if more posts available beyond current offset+limit"
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Current offset value (echoed from request)"
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Current limit value (echoed from request)"
    )
