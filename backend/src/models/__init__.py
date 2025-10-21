"""Data models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    """Reddit post model."""
    
    id: str = Field(..., description="Reddit post ID")
    subreddit: str = Field(..., description="Subreddit name")
    author: str = Field(..., description="Post author username")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content/selftext")
    url: str = Field(..., description="Post URL")
    created_utc: datetime = Field(..., description="Post creation timestamp")
    upvotes: int = Field(default=0, description="Number of upvotes")
    comment_count: int = Field(default=0, description="Number of comments")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")


class RedditComment(BaseModel):
    """Reddit comment model."""
    
    id: str = Field(..., description="Reddit comment ID")
    post_id: str = Field(..., description="Parent post ID")
    parent_id: Optional[str] = Field(None, description="Parent comment ID for threading")
    author: str = Field(..., description="Comment author username")
    content: str = Field(..., description="Comment text")
    created_utc: datetime = Field(..., description="Comment creation timestamp")
    upvotes: int = Field(default=0, description="Number of upvotes")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")


class SentimentScore(BaseModel):
    """Sentiment analysis result."""
    
    content_id: str = Field(..., description="Reddit post or comment ID")
    content_type: str = Field(..., description="Type: 'post' or 'comment'")
    subreddit: str = Field(..., description="Source subreddit")
    sentiment: str = Field(..., description="Sentiment classification: positive, negative, or neutral")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    compound_score: float = Field(..., ge=-1.0, le=1.0, description="Compound sentiment score")
    positive_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Positive sentiment component")
    negative_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Negative sentiment component")
    neutral_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Neutral sentiment component")
    analysis_method: str = Field(..., description="Analysis method: VADER or LLM")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    detected_tool_ids: list[str] = Field(
        default_factory=list,
        description="AI tool IDs detected in content"
    )


class AITool(BaseModel):
    """AI developer tool entity."""
    
    name: str = Field(..., description="Tool name")
    associated_subreddits: list[str] = Field(..., description="Related subreddits")
    current_sentiment: float = Field(default=0.0, description="Current average sentiment score")
    trend_direction: str = Field(default="neutral", description="Trend: positive, negative, or neutral")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class TrendingTopic(BaseModel):
    """Trending discussion topic."""
    
    id: str = Field(..., description="Trending topic ID")
    post_ids: list[str] = Field(..., description="Related post IDs")
    theme: str = Field(..., description="Topic theme/category")
    keywords: list[str] = Field(default_factory=list, description="Related keywords")
    engagement_velocity: float = Field(..., description="Engagement rate score")
    sentiment_distribution: dict[str, int] = Field(..., description="Sentiment breakdown")
    peak_time: datetime = Field(..., description="Peak engagement timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")


class DataCollectionCycle(BaseModel):
    """Data collection run metadata."""
    
    id: str = Field(..., description="Cycle ID")
    start_time: datetime = Field(..., description="Cycle start time")
    end_time: Optional[datetime] = Field(None, description="Cycle end time")
    subreddits_processed: list[str] = Field(default_factory=list, description="Processed subreddits")
    posts_collected: int = Field(default=0, description="Number of posts collected")
    comments_collected: int = Field(default=0, description="Number of comments collected")
    errors: list[str] = Field(default_factory=list, description="Errors encountered")
    status: str = Field(default="running", description="Status: running, completed, or failed")
