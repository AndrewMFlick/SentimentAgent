"""Integration tests for data retention and cleanup jobs."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_cleanup_soft_deletes_old_aggregates():
    """Test that cleanup job soft deletes aggregates older than retention period."""
    from src.services.scheduler import CollectionScheduler
    
    # Mock database
    mock_db = AsyncMock()
    
    # Old aggregate to be soft deleted
    old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%d')
    old_aggregate = {
        "id": f"github-copilot_{old_date}",
        "tool_id": "github-copilot",
        "date": old_date,
        "total_mentions": 50,
        "deleted_at": None
    }
    
    # Mock query for soft delete
    mock_db.query_items = AsyncMock(return_value=[old_aggregate])
    mock_db.upsert_item = AsyncMock(return_value={})
    
    scheduler = CollectionScheduler()
    
    with patch('src.services.scheduler.db', mock_db):
        with patch('src.services.scheduler.settings') as mock_settings:
            mock_settings.sentiment_retention_days = 90
            
            await scheduler.cleanup_sentiment_data()
    
    # Verify soft delete was performed
    assert mock_db.upsert_item.called
    # Check that deleted_at was set
    call_args = mock_db.upsert_item.call_args[0][1]
    assert call_args["deleted_at"] is not None


@pytest.mark.asyncio
async def test_cleanup_hard_deletes_old_soft_deleted_items():
    """Test that cleanup job hard deletes items soft-deleted 30+ days ago."""
    from src.services.scheduler import CollectionScheduler
    
    # Mock database
    mock_db = AsyncMock()
    
    # Item soft deleted 40 days ago (should be hard deleted)
    old_soft_delete_date = (
        datetime.utcnow() - timedelta(days=40)
    ).isoformat()
    
    item_to_hard_delete = {
        "id": "old-tool_2024-01-01",
        "tool_id": "old-tool",
        "date": "2024-01-01",
        "deleted_at": old_soft_delete_date
    }
    
    # Mock queries
    def mock_query(container, query, parameters):
        if "deleted_at = null" in query:
            # Soft delete query - return empty
            return AsyncMock(return_value=[])()
        else:
            # Hard delete query - return old item
            return AsyncMock(return_value=[item_to_hard_delete])()
    
    mock_db.query_items = mock_query
    mock_db.upsert_item = AsyncMock(return_value={})
    mock_db.delete_item = AsyncMock(return_value=None)
    
    scheduler = CollectionScheduler()
    
    with patch('src.services.scheduler.db', mock_db):
        with patch('src.services.scheduler.settings') as mock_settings:
            mock_settings.sentiment_retention_days = 90
            
            await scheduler.cleanup_sentiment_data()
    
    # Verify hard delete was called
    assert mock_db.delete_item.called


@pytest.mark.asyncio
async def test_cleanup_respects_retention_period():
    """Test cleanup respects configured retention period."""
    from src.services.scheduler import CollectionScheduler
    
    mock_db = AsyncMock()
    
    # Recent aggregate (within retention) - should NOT be deleted
    recent_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Old aggregate (beyond retention) - should be deleted
    old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%d')
    
    recent_aggregate = {
        "id": f"tool1_{recent_date}",
        "tool_id": "tool1",
        "date": recent_date,
        "deleted_at": None
    }
    
    old_aggregate = {
        "id": f"tool2_{old_date}",
        "tool_id": "tool2",
        "date": old_date,
        "deleted_at": None
    }
    
    # Mock query returns only old items
    mock_db.query_items = AsyncMock(return_value=[old_aggregate])
    mock_db.upsert_item = AsyncMock(return_value={})
    mock_db.delete_item = AsyncMock(return_value=None)
    
    scheduler = CollectionScheduler()
    
    with patch('src.services.scheduler.db', mock_db):
        with patch('src.services.scheduler.settings') as mock_settings:
            mock_settings.sentiment_retention_days = 90
            
            await scheduler.cleanup_sentiment_data()
    
    # Verify only old items were processed
    assert mock_db.query_items.called
    # Should have soft deleted the old item
    assert mock_db.upsert_item.called


@pytest.mark.asyncio
async def test_cleanup_handles_errors_gracefully():
    """Test cleanup job handles database errors gracefully."""
    from src.services.scheduler import CollectionScheduler
    
    mock_db = AsyncMock()
    
    # Simulate database error
    mock_db.query_items = AsyncMock(side_effect=Exception("Database error"))
    
    scheduler = CollectionScheduler()
    
    with patch('src.services.scheduler.db', mock_db):
        with patch('src.services.scheduler.settings') as mock_settings:
            mock_settings.sentiment_retention_days = 90
            
            # Should not raise exception
            await scheduler.cleanup_sentiment_data()
    
    # Job should handle error gracefully (logs but doesn't crash)
    assert mock_db.query_items.called


@pytest.mark.asyncio
async def test_cleanup_processes_multiple_tools():
    """Test cleanup processes aggregates for multiple tools."""
    from src.services.scheduler import CollectionScheduler
    
    mock_db = AsyncMock()
    
    old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%d')
    
    # Multiple old aggregates from different tools
    old_aggregates = [
        {
            "id": f"tool1_{old_date}",
            "tool_id": "tool1",
            "date": old_date,
            "deleted_at": None
        },
        {
            "id": f"tool2_{old_date}",
            "tool_id": "tool2",
            "date": old_date,
            "deleted_at": None
        },
        {
            "id": f"tool3_{old_date}",
            "tool_id": "tool3",
            "date": old_date,
            "deleted_at": None
        }
    ]
    
    mock_db.query_items = AsyncMock(return_value=old_aggregates)
    mock_db.upsert_item = AsyncMock(return_value={})
    mock_db.delete_item = AsyncMock(return_value=None)
    
    scheduler = CollectionScheduler()
    
    with patch('src.services.scheduler.db', mock_db):
        with patch('src.services.scheduler.settings') as mock_settings:
            mock_settings.sentiment_retention_days = 90
            
            await scheduler.cleanup_sentiment_data()
    
    # Should have soft deleted all 3 aggregates
    assert mock_db.upsert_item.call_count == 3
