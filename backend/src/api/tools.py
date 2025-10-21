"""AI Tools API endpoints."""

from collections import defaultdict
from datetime import datetime, timedelta
from time import time
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, Request

from ..services.database import db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tools", tags=["AI Tools"])

# Simple in-memory rate limiting (per-IP tracking)
# In production, use Redis or similar distributed cache
rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # requests per window


def check_rate_limit(request: Request, endpoint: str):
    """
    Simple rate limiting check.

    Limits: 30 requests per 60 seconds per IP per endpoint

    Args:
        request: FastAPI request object
        endpoint: Endpoint identifier

    Raises:
        HTTPException: If rate limit exceeded
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{endpoint}"
    current_time = time()

    # Clean old requests outside the window
    rate_limit_store[key] = [
        req_time
        for req_time in rate_limit_store[key]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if limit exceeded
    if len(rate_limit_store[key]) >= RATE_LIMIT_MAX_REQUESTS:
        logger.warning(
            "Rate limit exceeded",
            client_ip=client_ip,
            endpoint=endpoint,
            request_count=len(rate_limit_store[key]),
        )
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX_REQUESTS} "
            f"requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    # Add current request
    rate_limit_store[key].append(current_time)


@router.get("")
async def list_tools():
    """
    Get list of approved AI tools.

    Returns:
        List of approved tools with metadata
    """
    try:
        tools = await db.get_approved_tools()

        logger.info("Listed approved tools", tool_count=len(tools))

        return {"tools": tools}

    except Exception as e:
        logger.error("Failed to list tools", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve tools")


@router.get("/{tool_id}/sentiment")
async def get_tool_sentiment(
    tool_id: str,
    hours: Optional[int] = Query(
        default=None, description="Time window in hours (default: 24)"
    ),
    start_date: Optional[str] = Query(
        default=None, description="Start date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
):
    """
    Get sentiment breakdown for a specific tool.

    Args:
        tool_id: Tool identifier
        hours: Time window in hours (mutually exclusive with dates)
        start_date: Start date for range query
        end_date: End date for range query

    Returns:
        Sentiment breakdown with percentages
    """
    try:
        # Verify tool exists
        tool = await db.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Get sentiment data
        sentiment_data = await db.get_tool_sentiment(
            tool_id=tool_id, hours=hours, start_date=start_date, end_date=end_date
        )

        # Calculate percentages
        total = sentiment_data.get("total_mentions", 0)
        if total > 0:
            positive_pct = (sentiment_data.get("positive_count", 0) / total) * 100
            negative_pct = (sentiment_data.get("negative_count", 0) / total) * 100
            neutral_pct = (sentiment_data.get("neutral_count", 0) / total) * 100
        else:
            positive_pct = 0.0
            negative_pct = 0.0
            neutral_pct = 0.0

        # Determine time period
        if hours:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            end_time = datetime.utcnow()
        elif start_date and end_date:
            start_time = datetime.fromisoformat(start_date)
            end_time = datetime.fromisoformat(end_date)
        else:
            # Default to last 24 hours
            start_time = datetime.utcnow() - timedelta(hours=24)
            end_time = datetime.utcnow()

        response = {
            "tool_id": tool_id,
            "tool_name": tool.get("name"),
            "total_mentions": sentiment_data.get("total_mentions", 0),
            "positive_count": sentiment_data.get("positive_count", 0),
            "negative_count": sentiment_data.get("negative_count", 0),
            "neutral_count": sentiment_data.get("neutral_count", 0),
            "positive_percentage": round(positive_pct, 2),
            "negative_percentage": round(negative_pct, 2),
            "neutral_percentage": round(neutral_pct, 2),
            "avg_sentiment": sentiment_data.get("avg_sentiment", 0.0),
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
        }

        logger.info(
            "Retrieved tool sentiment",
            tool_id=tool_id,
            total_mentions=response["total_mentions"],
            time_period_hours=hours,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get tool sentiment", tool_id=tool_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve sentiment data")


@router.get("/compare")
async def compare_tools(
    request: Request,
    tool_ids: str = Query(..., description="Comma-separated tool IDs to compare"),
    hours: Optional[int] = Query(
        default=None, description="Time window in hours (default: 24)"
    ),
    start_date: Optional[str] = Query(
        default=None, description="Start date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
):
    """
    Compare sentiment data for multiple AI tools.

    Rate limited: 30 requests per 60 seconds per IP.

    Args:
        tool_ids: Comma-separated tool IDs (e.g., "github-copilot,
            jules-ai")
        hours: Time window in hours (mutually exclusive with dates)
        start_date: Start date for range query
        end_date: End date for range query

    Returns:
        {
            "tools": [ToolSentiment, ...],
            "deltas": [Delta, ...]
        }
    """
    # Check rate limit
    check_rate_limit(request, "compare_tools")

    try:
        # Parse tool IDs
        parsed_tool_ids = [tid.strip() for tid in tool_ids.split(",") if tid.strip()]

        if not parsed_tool_ids:
            raise HTTPException(
                status_code=400, detail="At least one tool_id is required"
            )

        # Verify all tools exist
        tools_lookup = {}
        for tool_id in parsed_tool_ids:
            tool = await db.get_tool(tool_id)
            if not tool:
                raise HTTPException(
                    status_code=404, detail=f"Tool '{tool_id}' not found"
                )
            tools_lookup[tool_id] = tool

        # Get sentiment data for all tools in parallel
        sentiment_data_list = await db.compare_tools(
            tool_ids=parsed_tool_ids,
            hours=hours,
            start_date=start_date,
            end_date=end_date,
        )

        # Build tool sentiment responses
        tools_response = []
        for tool_id, sentiment_data in zip(parsed_tool_ids, sentiment_data_list):
            tool = tools_lookup[tool_id]
            total = sentiment_data.get("total_mentions", 0)

            if total > 0:
                positive_pct = (sentiment_data.get("positive_count", 0) / total) * 100
                negative_pct = (sentiment_data.get("negative_count", 0) / total) * 100
                neutral_pct = (sentiment_data.get("neutral_count", 0) / total) * 100
            else:
                positive_pct = 0.0
                negative_pct = 0.0
                neutral_pct = 0.0

            tools_response.append(
                {
                    "tool_id": tool_id,
                    "tool_name": tool.get("name"),
                    "total_mentions": total,
                    "positive_count": sentiment_data.get("positive_count", 0),
                    "negative_count": sentiment_data.get("negative_count", 0),
                    "neutral_count": sentiment_data.get("neutral_count", 0),
                    "positive_percentage": round(positive_pct, 2),
                    "negative_percentage": round(negative_pct, 2),
                    "neutral_percentage": round(neutral_pct, 2),
                    "avg_sentiment": sentiment_data.get("avg_sentiment", 0.0),
                }
            )

        # Calculate deltas between all tool pairs
        deltas = []
        for i in range(len(tools_response)):
            for j in range(i + 1, len(tools_response)):
                tool_a = tools_response[i]
                tool_b = tools_response[j]

                # Calculate percentage point differences
                positive_delta = (
                    tool_a["positive_percentage"] - tool_b["positive_percentage"]
                )
                negative_delta = (
                    tool_a["negative_percentage"] - tool_b["negative_percentage"]
                )
                sentiment_delta = tool_a["avg_sentiment"] - tool_b["avg_sentiment"]

                deltas.append(
                    {
                        "tool_a_id": tool_a["tool_id"],
                        "tool_b_id": tool_b["tool_id"],
                        "positive_delta": round(positive_delta, 2),
                        "negative_delta": round(negative_delta, 2),
                        "sentiment_delta": round(sentiment_delta, 4),
                    }
                )

        logger.info(
            "Compared tools",
            tool_count=len(parsed_tool_ids),
            tool_ids=parsed_tool_ids,
            delta_count=len(deltas),
        )

        return {"tools": tools_response, "deltas": deltas}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to compare tools", tool_ids=tool_ids, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to compare tools")


@router.get("/{tool_id}/timeseries")
async def get_tool_timeseries(
    request: Request,
    tool_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: str = Query(
        default="daily", description="Time granularity (currently only 'daily')"
    ),
):
    """
    Get time series sentiment data for an AI tool.

    Rate limited: 30 requests per 60 seconds per IP.

    Args:
        tool_id: Tool identifier
        start_date: Start date for range query (YYYY-MM-DD)
        end_date: End date for range query (YYYY-MM-DD)
        granularity: Time granularity (default: 'daily')

    Returns:
        Time series data with daily sentiment aggregates
    """
    import time

    start_time = time.time()

    # Check rate limit
    check_rate_limit(request, "timeseries")

    try:
        # Verify tool exists
        tool = await db.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Validate date format and range
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        if start_dt > end_dt:
            raise HTTPException(
                status_code=400, detail="start_date must be before end_date"
            )

        # Validate max 90-day range
        max_days = 90
        date_range = (end_dt - start_dt).days
        if date_range > max_days:
            raise HTTPException(
                status_code=400, detail=f"Date range exceeds maximum of {max_days} days"
            )

        # Get time series data
        data_points = await db.get_tool_timeseries(
            tool_id=tool_id, start_date=start_date, end_date=end_date
        )

        # Calculate execution time
        execution_time = time.time() - start_time

        response = {
            "tool_id": tool_id,
            "tool_name": tool.get("name"),
            "time_period": {"start": start_date, "end": end_date},
            "granularity": granularity,
            "data_points": data_points,
        }

        logger.info(
            "Retrieved tool timeseries",
            tool_id=tool_id,
            start_date=start_date,
            end_date=end_date,
            data_point_count=len(data_points),
            execution_time_ms=round(execution_time * 1000, 2),
        )

        # Performance warning if > 3 seconds
        if execution_time > 3.0:
            logger.warning(
                "Slow timeseries query",
                tool_id=tool_id,
                execution_time_s=round(execution_time, 2),
                date_range_days=date_range,
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get tool timeseries",
            tool_id=tool_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve time series data"
        )


@router.get("/last_updated")
async def get_last_updated():
    """
    Get timestamp of last data update.

    Returns the most recent computed_at timestamp from time_period_aggregates,
    used by frontend to detect when new data is available.

    Returns:
        dict with last_aggregation and last_detection timestamps
    """
    try:
        # Get most recent aggregation timestamp
        query_agg = """
            SELECT VALUE MAX(c.computed_at)
            FROM c
            WHERE c.deleted_at = null
        """

        results_agg = await db.query_items(
            "time_period_aggregates", query_agg, parameters=[]
        )

        last_aggregation = results_agg[0] if results_agg else None

        # Get most recent tool detection timestamp
        query_detect = """
            SELECT VALUE MAX(c.detected_at)
            FROM c
        """

        results_detect = await db.query_items(
            "tool_mentions", query_detect, parameters=[]
        )

        last_detection = results_detect[0] if results_detect else None

        logger.debug(
            "Retrieved last updated timestamps",
            last_aggregation=last_aggregation,
            last_detection=last_detection,
        )

        return {"last_aggregation": last_aggregation, "last_detection": last_detection}

    except Exception as e:
        logger.error(
            "Failed to get last updated timestamps", error=str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve last updated information"
        )
