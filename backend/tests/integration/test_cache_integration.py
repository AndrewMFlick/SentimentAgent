"""Integration tests for cache service (Feature 017 - Pre-Cached Sentiment Analysis).

Test Coverage:
- T014: End-to-end cache lookup and fallback

These tests verify the complete cache flow with real (mocked) container interactions.

Reference: specs/017-pre-cached-sentiment/tasks.md Phase 3
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.models.cache import CachePeriod, SentimentCacheEntry
from src.services.cache_service import CacheService


class TestCacheIntegration:
    """Integration tests for end-to-end cache functionality."""

    @pytest.fixture
    def cache_service_integrated(self):
        """Create cache service with integrated mock containers."""
        # Create mock containers with more realistic behavior
        cache_container = MagicMock()
        sentiment_container = MagicMock()
        tools_container = MagicMock()
        
        service = CacheService(
            cache_container=cache_container,
            sentiment_container=sentiment_container,
            tools_container=tools_container,
        )
        
        return service, cache_container, sentiment_container

    @pytest.mark.asyncio
    async def test_end_to_end_cache_hit_flow(self, cache_service_integrated):
        """Test complete flow: cache exists and is fresh -> return cached data."""
        service, cache_container, _ = cache_service_integrated
        
        tool_id = "test-tool-123"
        hours = 24
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Cache exists and is fresh
        cached_data = {
            "id": f"{tool_id}:HOUR_24",
            "tool_id": tool_id,
            "period": "HOUR_24",
            "total_mentions": 200,
            "positive_count": 150,
            "negative_count": 30,
            "neutral_count": 20,
            "positive_percentage": 75.0,
            "negative_percentage": 15.0,
            "neutral_percentage": 10.0,
            "average_sentiment": 0.6,
            "period_start_ts": now_ts - 86400,
            "period_end_ts": now_ts,
            "last_updated_ts": now_ts - 600,  # 10 minutes ago (fresh)
        }
        cache_container.read_item = AsyncMock(return_value=cached_data)
        
        # Execute
        result = await service.get_cached_sentiment(tool_id, hours)
        
        # Verify
        assert result["is_cached"] is True
        assert result["total_mentions"] == 200
        assert result["positive_count"] == 150
        assert result["cached_at"] == cached_data["last_updated_ts"]
        
        # Verify cache was read but not written
        cache_container.read_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_cache_miss_flow(self, cache_service_integrated):
        """Test complete flow: cache miss -> calculate -> save to cache -> return data."""
        service, cache_container, sentiment_container = cache_service_integrated
        
        tool_id = "test-tool-456"
        hours = 24
        
        # Setup: Cache miss
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        cache_container.read_item = AsyncMock(
            side_effect=CosmosResourceNotFoundError(status_code=404, message="Not found")
        )
        
        # Setup: Sentiment data available
        sentiment_data = [
            {"sentiment_score": 0.8, "detected_tool_ids": [tool_id], "_ts": 1698451200},
            {"sentiment_score": -0.3, "detected_tool_ids": [tool_id], "_ts": 1698451300},
            {"sentiment_score": 0.1, "detected_tool_ids": [tool_id], "_ts": 1698451400},
        ]
        
        async def mock_query(query, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        cache_container.upsert_item = AsyncMock()
        
        # Execute
        result = await service.get_cached_sentiment(tool_id, hours)
        
        # Verify result
        assert result["is_cached"] is False  # First request not cached
        assert result["total_mentions"] == 3
        assert result["positive_count"] == 2
        assert result["negative_count"] == 1
        assert result["neutral_count"] == 0
        
        # Verify cache was populated for next request
        cache_container.upsert_item.assert_called_once()
        saved_entry = cache_container.upsert_item.call_args[0][0]
        assert saved_entry["tool_id"] == tool_id
        assert saved_entry["total_mentions"] == 3

    @pytest.mark.asyncio
    async def test_end_to_end_stale_cache_refresh(self, cache_service_integrated):
        """Test complete flow: stale cache -> recalculate -> update cache -> return fresh data."""
        service, cache_container, sentiment_container = cache_service_integrated
        
        tool_id = "test-tool-789"
        hours = 24
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Stale cache (40 minutes old, TTL is 30)
        stale_data = {
            "id": f"{tool_id}:HOUR_24",
            "tool_id": tool_id,
            "period": "HOUR_24",
            "total_mentions": 50,
            "positive_count": 30,
            "negative_count": 10,
            "neutral_count": 10,
            "positive_percentage": 60.0,
            "negative_percentage": 20.0,
            "neutral_percentage": 20.0,
            "average_sentiment": 0.4,
            "period_start_ts": now_ts - 86400,
            "period_end_ts": now_ts,
            "last_updated_ts": now_ts - 2400,  # 40 minutes ago (stale)
        }
        cache_container.read_item = AsyncMock(return_value=stale_data)
        
        # Setup: Fresh sentiment data (more data now)
        fresh_sentiment_data = [
            {"sentiment_score": 0.9, "detected_tool_ids": [tool_id], "_ts": now_ts - 3600},
            {"sentiment_score": 0.7, "detected_tool_ids": [tool_id], "_ts": now_ts - 1800},
            {"sentiment_score": 0.5, "detected_tool_ids": [tool_id], "_ts": now_ts - 900},
        ]
        
        async def mock_query(query, **kwargs):
            for item in fresh_sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        cache_container.upsert_item = AsyncMock()
        
        # Execute
        result = await service.get_cached_sentiment(tool_id, hours)
        
        # Verify fresh data was calculated
        assert result["total_mentions"] == 3  # Updated count
        assert result["positive_count"] == 3  # All positive now
        
        # Verify cache was updated
        cache_container.upsert_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_non_standard_period(self, cache_service_integrated):
        """Test complete flow: non-standard period -> always calculate on-demand, no cache."""
        service, cache_container, sentiment_container = cache_service_integrated
        
        tool_id = "test-tool-abc"
        hours = 48  # Non-standard period (not 1, 24, 168, or 720)
        
        # Setup: Sentiment data
        sentiment_data = [
            {"sentiment_score": 0.6, "detected_tool_ids": [tool_id], "_ts": 1698451200},
        ]
        
        async def mock_query(query, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        
        # Execute
        result = await service.get_cached_sentiment(tool_id, hours)
        
        # Verify on-demand calculation without caching
        assert result["is_cached"] is False
        assert result["total_mentions"] == 1
        
        # Verify cache was NOT accessed or written
        cache_container.read_item.assert_not_called()
        cache_container.upsert_item.assert_not_called()

    @pytest.mark.asyncio
    async def test_end_to_end_error_handling(self, cache_service_integrated):
        """Test that cache errors don't break the service - graceful fallback."""
        service, cache_container, sentiment_container = cache_service_integrated
        
        tool_id = "test-tool-error"
        hours = 24
        
        # Setup: Cache container raises unexpected error
        cache_container.read_item = AsyncMock(
            side_effect=Exception("Unexpected cache error")
        )
        
        # Setup: Sentiment data still works
        sentiment_data = [
            {"sentiment_score": 0.5, "detected_tool_ids": [tool_id], "_ts": 1698451200},
        ]
        
        async def mock_query(query, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        cache_container.upsert_item = AsyncMock()
        
        # Execute - should not raise, should fallback
        result = await service.get_cached_sentiment(tool_id, hours)
        
        # Verify fallback worked
        assert result["total_mentions"] == 1
        assert result["is_cached"] is False
