"""Hot Topics API endpoints.

This module provides REST API endpoints for the Hot Topics feature,
allowing users to view trending developer tools with engagement metrics
and related Reddit posts.

Endpoints:
- GET /api/hot-topics - Get ranked list of hot topics
- GET /api/hot-topics/{tool_id}/posts - Get related posts for a tool (US2)
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.hot_topics import HotTopicsResponse, RelatedPostsResponse
from ..services.database import DatabaseService, get_db
from ..services.hot_topics_service import HotTopicsService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api", tags=["hot-topics"])


def get_hot_topics_service(db: DatabaseService = Depends(get_db)) -> HotTopicsService:
    """Dependency injection for HotTopicsService.

    Args:
        db: DatabaseService instance from dependency injection

    Returns:
        Initialized HotTopicsService with database containers
    """
    sentiment_scores_container = db.database.get_container_client("sentiment_scores")
    reddit_posts_container = db.database.get_container_client("reddit_posts")
    reddit_comments_container = db.database.get_container_client("reddit_comments")
    tools_container = db.database.get_container_client("Tools")

    return HotTopicsService(
        sentiment_scores_container=sentiment_scores_container,
        reddit_posts_container=reddit_posts_container,
        reddit_comments_container=reddit_comments_container,
        tools_container=tools_container,
    )


@router.get("/hot-topics", response_model=HotTopicsResponse)
async def get_hot_topics(
    time_range: str = Query(
        default="7d",
        regex="^(24h|7d|30d)$",
        description="Time range filter: 24h, 7d, or 30d",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of hot topics to return (1-50)",
    ),
    service: HotTopicsService = Depends(get_hot_topics_service),
) -> HotTopicsResponse:
    """Get hot topics ranked by engagement.

    Returns a ranked list of developer tools based on engagement score
    (calculated from mentions, comments, and upvotes) within the specified
    time range. Includes sentiment distribution for each tool.

    Args:
        time_range: Filter by time period (24h, 7d, 30d)
        limit: Maximum number of results (1-50)
        service: HotTopicsService dependency

    Returns:
        HotTopicsResponse with ranked hot topics list

    Raises:
        HTTPException 400: Invalid parameters
        HTTPException 500: Server error during calculation

    Example:
        GET /api/hot-topics?time_range=7d&limit=10
    """
    try:
        logger.info(
            "Hot topics request received",
            time_range=time_range,
            limit=limit,
        )

        result = await service.get_hot_topics(
            time_range=time_range,
            limit=limit,
        )

        logger.info(
            "Hot topics calculated successfully",
            count=len(result.hot_topics),
            time_range=time_range,
        )

        return result

    except ValueError as e:
        logger.warning(
            "Invalid hot topics request parameters",
            error=str(e),
            time_range=time_range,
            limit=limit,
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "Failed to calculate hot topics",
            error=str(e),
            time_range=time_range,
            limit=limit,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate hot topics. Please try again later.",
        )


@router.get("/hot-topics/{tool_id}/posts", response_model=RelatedPostsResponse)
async def get_related_posts(
    tool_id: str,
    time_range: str = Query(
        default="7d",
        regex="^(24h|7d|30d)$",
        description="Time range filter: 24h, 7d, or 30d",
    ),
    offset: int = Query(
        default=0, ge=0, description="Number of posts to skip (pagination)"
    ),
    limit: int = Query(
        default=20, ge=1, le=100, description="Maximum posts to return (1-100)"
    ),
    service: HotTopicsService = Depends(get_hot_topics_service),
    db: DatabaseService = Depends(get_db),
) -> RelatedPostsResponse:
    """Get related posts for a specific tool.

    Returns paginated list of Reddit posts mentioning the specified tool,
    sorted by engagement (comment_count + upvotes). Only includes posts
    that have engagement activity (created or commented on) within the
    selected time range.

    Args:
        tool_id: Tool identifier
        time_range: Filter by time period (24h, 7d, 30d)
        offset: Pagination offset
        limit: Maximum results per page (1-100)
        service: HotTopicsService dependency
        db: DatabaseService dependency for tool validation

    Returns:
        RelatedPostsResponse with paginated posts

    Raises:
        HTTPException 404: Tool not found
        HTTPException 400: Invalid parameters
        HTTPException 500: Server error

    Example:
        GET /api/hot-topics/{tool_id}/posts?time_range=7d&offset=0&limit=20
    """
    try:
        logger.info(
            "Related posts request received",
            tool_id=tool_id,
            time_range=time_range,
            offset=offset,
            limit=limit,
        )

        # Validate tool exists in Tools container
        tools_container = db.database.get_container_client("Tools")
        tool_query = "SELECT * FROM c WHERE c.id = @tool_id AND c.partitionKey = 'tool'"
        tool_results = list(
            tools_container.query_items(
                query=tool_query,
                parameters=[{"name": "@tool_id", "value": tool_id}],
                enable_cross_partition_query=False,
            )
        )

        if not tool_results:
            logger.warning(
                "Tool not found",
                tool_id=tool_id,
            )
            raise HTTPException(
                status_code=404, detail=f"Tool with ID '{tool_id}' not found"
            )

        # Call service to get related posts
        result = await service.get_related_posts(
            tool_id=tool_id,
            time_range=time_range,
            offset=offset,
            limit=limit,
        )

        logger.info(
            "Related posts retrieved successfully",
            tool_id=tool_id,
            total=result.total,
            returned=len(result.posts),
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        logger.warning(
            "Invalid related posts request parameters",
            error=str(e),
            tool_id=tool_id,
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(
            "Failed to get related posts",
            error=str(e),
            tool_id=tool_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to get related posts. Please try again later.",
        )
