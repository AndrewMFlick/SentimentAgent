"""API endpoints."""

import os
from datetime import datetime
from typing import List, Optional

import psutil
from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from ..models import RedditPost, TrendingTopic
from ..services import ai_agent, db
from ..services.health import app_state
from .tools import router as tools_router

router = APIRouter()

# Include AI Tools router
router.include_router(tools_router)


class QueryRequest(BaseModel):
    """AI agent query request."""

    question: str


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns process metrics, application state, and database health.
    Returns 503 status code when the application is unhealthy.
    """
    try:
        # Get process metrics using psutil
        process = psutil.Process(os.getpid())

        # Calculate uptime
        uptime_seconds = app_state.get_uptime_seconds()

        # Calculate memory usage in MB
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # Calculate CPU percentage
        cpu_percent = process.cpu_percent(interval=0.1)

        # Check database connection
        db_connected = await db.is_connected()

        # Calculate data freshness
        data_freshness_minutes = app_state.get_data_freshness_minutes()

        # Determine overall health status
        status = "healthy"

        if not db_connected:
            status = "unhealthy"
        elif memory_mb > 512:  # Memory threshold: 512MB
            status = "degraded"
        elif (
            data_freshness_minutes and data_freshness_minutes > 60
        ):  # Data older than 1 hour
            status = "degraded"

        health_data = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "process": {
                "uptime_seconds": uptime_seconds,
                "memory_mb": round(memory_mb, 2),
                "cpu_percent": round(cpu_percent, 2),
                "pid": process.pid,
            },
            "application": {
                "last_collection_at": (
                    app_state.last_collection_time.isoformat()
                    if app_state.last_collection_time
                    else None
                ),
                "collections_succeeded": app_state.collections_succeeded,
                "collections_failed": app_state.collections_failed,
                "data_freshness_minutes": (
                    round(data_freshness_minutes, 2) if data_freshness_minutes else None
                ),
            },
            "database": {"connected": db_connected},
        }

        # Return 503 if unhealthy
        if status == "unhealthy":
            raise HTTPException(status_code=503, detail=health_data)

        return health_data

    except HTTPException:
        raise
    except Exception as e:
        # If health check itself fails, return unhealthy status
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/sentiment/stats")
async def get_sentiment_stats(
    subreddit: Optional[str] = None, hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get aggregated sentiment statistics.

    Args:
        subreddit: Filter by specific subreddit (optional)
        hours: Time window in hours (default: 24)
    """
    try:
        stats = await db.get_sentiment_stats(subreddit=subreddit, hours=hours)
        return {
            "subreddit": subreddit or "all",
            "time_window_hours": hours,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/trends")
async def get_sentiment_trends(
    subreddit: Optional[str] = None, hours: int = Query(default=168, ge=1, le=720)
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
        stats = await db.get_sentiment_stats(subreddit=subreddit, hours=hours)

        return {
            "subreddit": subreddit or "all",
            "time_window_hours": hours,
            "trend_data": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/recent", response_model=List[RedditPost])
async def get_recent_posts(
    subreddit: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=500),
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
async def get_trending_topics(limit: int = Query(default=20, ge=1, le=100)):
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
        "count": len(settings.subreddit_list),
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
            id="manual_collection",
            name="Manual data collection",
            replace_existing=True,
        )
        return {
            "status": "triggered",
            "message": "Data collection started",
            "timestamp": datetime.utcnow().isoformat(),
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
