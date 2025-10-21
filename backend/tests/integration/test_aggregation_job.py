"""Integration tests for daily aggregation job."""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_compute_daily_aggregates_success():
    """Test daily aggregation computes correctly for all tools."""
    from src.services.sentiment_aggregator import SentimentAggregator
    
    # Mock database service
    mock_db = AsyncMock()
    
    # Mock approved tools
    mock_db.get_approved_tools = AsyncMock(return_value=[
        {
            "id": "github-copilot",
            "name": "GitHub Copilot",
            "status": "approved"
        },
        {
            "id": "cursor",
            "name": "Cursor",
            "status": "approved"
        }
    ])
    
    # Mock query results for tool mentions + sentiment
    mock_db.query_items = AsyncMock(return_value=[
        {
            "tool_id": "github-copilot",
            "total_mentions": 150,
            "positive_count": 90,
            "negative_count": 40,
            "neutral_count": 20,
            "avg_sentiment": 0.35
        }
    ])
    
    # Mock upsert
    mock_db.upsert_item = AsyncMock(return_value={})
    
    # Create aggregator
    aggregator = SentimentAggregator(mock_db)
    
    # Compute for specific date
    date = "2025-01-15"
    aggregates = await aggregator.compute_daily_aggregates(date)
    
    # Verify results
    assert len(aggregates) == 2  # Should process both tools
    assert mock_db.get_approved_tools.called
    assert mock_db.upsert_item.call_count == 2


@pytest.mark.asyncio
async def test_compute_aggregate_for_date_with_data():
    """Test computing aggregate for single tool with data."""
    from src.services.sentiment_aggregator import SentimentAggregator
    
    mock_db = AsyncMock()
    
    # Mock query result
    mock_db.query_items = AsyncMock(return_value=[
        {
            "tool_id": "github-copilot",
            "total_mentions": 100,
            "positive_count": 60,
            "negative_count": 30,
            "neutral_count": 10,
            "avg_sentiment": 0.30
        }
    ])
    
    mock_db.upsert_item = AsyncMock(return_value={})
    
    aggregator = SentimentAggregator(mock_db)
    
    result = await aggregator.compute_aggregate_for_date(
        "github-copilot",
        "2025-01-15"
    )
    
    # Verify result structure
    assert result is not None
    assert result["tool_id"] == "github-copilot"
    assert result["date"] == "2025-01-15"
    assert result["total_mentions"] == 100
    assert result["positive_count"] == 60
    assert result["negative_count"] == 30
    assert result["neutral_count"] == 10
    assert result["avg_sentiment"] == 0.30
    assert "computed_at" in result
    assert result["deleted_at"] is None
    
    # Verify upsert was called
    assert mock_db.upsert_item.called


@pytest.mark.asyncio
async def test_compute_aggregate_for_date_no_data():
    """Test computing aggregate when no mentions exist."""
    from src.services.sentiment_aggregator import SentimentAggregator
    
    mock_db = AsyncMock()
    
    # Mock empty query result
    mock_db.query_items = AsyncMock(return_value=[])
    
    aggregator = SentimentAggregator(mock_db)
    
    result = await aggregator.compute_aggregate_for_date(
        "unknown-tool",
        "2025-01-15"
    )
    
    # Should return None when no data
    assert result is None
    
    # Upsert should not be called
    assert not mock_db.upsert_item.called


@pytest.mark.asyncio
async def test_compute_daily_aggregates_defaults_to_yesterday():
    """Test that compute_daily_aggregates defaults to yesterday."""
    from src.services.sentiment_aggregator import SentimentAggregator
    
    mock_db = AsyncMock()
    mock_db.get_approved_tools = AsyncMock(return_value=[])
    
    aggregator = SentimentAggregator(mock_db)
    
    # Call without date parameter
    await aggregator.compute_daily_aggregates()
    
    # Verify it was called (no error)
    assert mock_db.get_approved_tools.called


@pytest.mark.asyncio
async def test_aggregation_handles_missing_sentiment_fields():
    """Test aggregation handles missing sentiment data gracefully."""
    from src.services.sentiment_aggregator import SentimentAggregator
    
    mock_db = AsyncMock()
    
    # Mock query with missing fields
    mock_db.query_items = AsyncMock(return_value=[
        {
            "tool_id": "new-tool"
            # Missing all count fields
        }
    ])
    
    mock_db.upsert_item = AsyncMock(return_value={})
    
    aggregator = SentimentAggregator(mock_db)
    
    result = await aggregator.compute_aggregate_for_date(
        "new-tool",
        "2025-01-15"
    )
    
    # Should handle missing fields with defaults
    assert result is not None
    assert result["total_mentions"] == 0
    assert result["positive_count"] == 0
    assert result["negative_count"] == 0
    assert result["neutral_count"] == 0
    assert result["avg_sentiment"] == 0.0
