"""API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime
from pydantic import BaseModel

from ..services import db, ai_agent
from ..models import RedditPost, SentimentScore, TrendingTopic

router = APIRouter()


class QueryRequest(BaseModel):
    """AI agent query request."""
    question: str


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/sentiment/stats")
async def get_sentiment_stats(
    subreddit: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get aggregated sentiment statistics.
    
    Args:
        subreddit: Filter by specific subreddit (optional)
        hours: Time window in hours (default: 24)
    """
    try:
        stats = db.get_sentiment_stats(subreddit=subreddit, hours=hours)
        return {
            "subreddit": subreddit or "all",
            "time_window_hours": hours,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/trends")
async def get_sentiment_trends(
    subreddit: Optional[str] = None,
    hours: int = Query(default=168, ge=1, le=720)
):
    """
    Get sentiment trends over time.
    
    Args:
        subreddit: Filter by specific subreddit (optional)
        hours: Time window in hours (default: 168 = 1 week)
    """
    try:
        # This would need a more sophisticated query to get time-series data
        # For now, return basic stats
        stats = db.get_sentiment_stats(subreddit=subreddit, hours=hours)
        
        return {
            "subreddit": subreddit or "all",
            "time_window_hours": hours,
            "trend_data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/recent", response_model=List[RedditPost])
async def get_recent_posts(
    subreddit: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Get recent Reddit posts.
    
    Args:
        subreddit: Filter by specific subreddit (optional)
        hours: Time window in hours (default: 24)
        limit: Maximum number of posts (default: 100)
    """
    try:
        posts = db.get_recent_posts(subreddit=subreddit, hours=hours, limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{post_id}")
async def get_post(post_id: str, subreddit: str):
    """
    Get a specific post by ID.
    
    Args:
        post_id: Reddit post ID
        subreddit: Subreddit name (required for partition key)
    """
    try:
        post = db.get_post(post_id, subreddit)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=List[TrendingTopic])
async def get_trending_topics(
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Get trending topics.
    
    Args:
        limit: Maximum number of trending topics (default: 20)
    """
    try:
        topics = db.get_trending_topics(limit=limit)
        return topics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subreddits")
async def get_monitored_subreddits():
    """Get list of monitored subreddits."""
    from ..config import settings
    return {
        "subreddits": settings.subreddit_list,
        "count": len(settings.subreddit_list)
    }


@router.post("/admin/collect")
async def trigger_collection():
    """
    Manually trigger data collection.
    
    This endpoint triggers an immediate data collection cycle.
    Useful for testing or forcing a data refresh.
    """
    try:
        from ..services import scheduler
        # Trigger collection asynchronously
        scheduler.scheduler.add_job(
            scheduler.collect_and_analyze,
            id='manual_collection',
            name='Manual data collection',
            replace_existing=True
        )
        return {
            "status": "triggered",
            "message": "Data collection started",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai/query")
async def ai_query(request: QueryRequest = Body(...)):
    """
    Query the AI agent with natural language questions.
    
    Example questions:
    - "What is driving sentiment change in Cursor?"
    - "Compare sentiment between GitHub Copilot and Claude"
    - "What are the trending topics in programming subreddits?"
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        result = await ai_agent.query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
