"""Unit tests for CacheService (Feature 017 - Pre-Cached Sentiment Analysis).

Test Coverage:
- T010: get_cached_sentiment() - cache hit scenario
- T011: get_cached_sentiment() - cache miss with fallback
- T012: _calculate_sentiment_aggregate() - verify calculations
- T013: _map_hours_to_period() - verify time period mapping
- Additional: Helper methods (_calculate_cache_key, _is_cache_fresh, _save_to_cache)

Reference: specs/017-pre-cached-sentiment/tasks.md Phase 3
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from azure.cosmos import ContainerProxy

from src.models.cache import CachePeriod, SentimentCacheEntry
from src.services.cache_service import CacheService


class TestCacheService:
    """Test suite for CacheService core functionality."""

    @pytest.fixture
    def mock_containers(self):
        """Create mock containers for testing."""
        cache_container = MagicMock(spec=ContainerProxy)
        sentiment_container = MagicMock(spec=ContainerProxy)
        tools_container = MagicMock(spec=ContainerProxy)
        return cache_container, sentiment_container, tools_container

    @pytest.fixture
    def cache_service(self, mock_containers):
        """Create CacheService instance with mocked containers."""
        cache_container, sentiment_container, tools_container = mock_containers
        return CacheService(
            cache_container=cache_container,
            sentiment_container=sentiment_container,
            tools_container=tools_container,
        )

    # T013: Test _map_hours_to_period() - time period mapping
    @pytest.mark.parametrize(
        "hours,expected_period",
        [
            (1, CachePeriod.HOUR_1),
            (24, CachePeriod.HOUR_24),
            (168, CachePeriod.DAY_7),
            (720, CachePeriod.DAY_30),
        ],
    )
    def test_map_hours_to_period_standard_periods(
        self, cache_service, hours, expected_period
    ):
        """Test mapping of standard hours to cache periods."""
        result = cache_service._map_hours_to_period(hours)
        assert result == expected_period

    def test_map_hours_to_period_non_standard(self, cache_service):
        """Test that non-standard hours return None."""
        result = cache_service._map_hours_to_period(12)
        assert result is None

    # Test _calculate_cache_key() method
    def test_calculate_cache_key(self, cache_service):
        """Test cache key generation."""
        tool_id = "877eb2d8-1234-5678-9abc-def012345678"
        period = CachePeriod.HOUR_24
        
        result = cache_service._calculate_cache_key(tool_id, period)
        
        assert result == f"{tool_id}:{period.value}"
        assert ":" in result
        assert result.startswith(tool_id)

    # Test _is_cache_fresh() method
    def test_is_cache_fresh_within_ttl(self, cache_service):
        """Test cache freshness check for recent cache entry."""
        # Cache updated 5 minutes ago, TTL is 30 minutes
        now_ts = int(datetime.now(timezone.utc).timestamp())
        cache_entry = SentimentCacheEntry(
            id="tool:HOUR_24",
            tool_id="tool-id",
            period=CachePeriod.HOUR_24,
            total_mentions=100,
            positive_count=60,
            negative_count=20,
            neutral_count=20,
            positive_percentage=60.0,
            negative_percentage=20.0,
            neutral_percentage=20.0,
            average_sentiment=0.4,
            period_start_ts=now_ts - 86400,
            period_end_ts=now_ts,
            last_updated_ts=now_ts - 300,  # 5 minutes ago
        )
        
        result = cache_service._is_cache_fresh(cache_entry)
        
        assert result is True

    def test_is_cache_fresh_exceeds_ttl(self, cache_service):
        """Test cache freshness check for stale cache entry."""
        # Cache updated 45 minutes ago, TTL is 30 minutes
        now_ts = int(datetime.now(timezone.utc).timestamp())
        cache_entry = SentimentCacheEntry(
            id="tool:HOUR_24",
            tool_id="tool-id",
            period=CachePeriod.HOUR_24,
            total_mentions=100,
            positive_count=60,
            negative_count=20,
            neutral_count=20,
            positive_percentage=60.0,
            negative_percentage=20.0,
            neutral_percentage=20.0,
            average_sentiment=0.4,
            period_start_ts=now_ts - 86400,
            period_end_ts=now_ts,
            last_updated_ts=now_ts - 2700,  # 45 minutes ago
        )
        
        result = cache_service._is_cache_fresh(cache_entry)
        
        assert result is False

    # T012: Test _calculate_sentiment_aggregate() - verify calculations
    @pytest.mark.asyncio
    async def test_calculate_sentiment_aggregate_basic(self, cache_service, mock_containers):
        """Test sentiment aggregation calculation with basic data."""
        _, sentiment_container, _ = mock_containers
        tool_id = "tool-123"
        hours = 24
        
        # Mock sentiment scores data
        mock_scores = [
            {"sentiment_score": 0.8, "detected_tool_ids": [tool_id]},  # positive
            {"sentiment_score": 0.6, "detected_tool_ids": [tool_id]},  # positive
            {"sentiment_score": -0.5, "detected_tool_ids": [tool_id]},  # negative
            {"sentiment_score": 0.0, "detected_tool_ids": [tool_id]},  # neutral
        ]
        
        async def mock_query_items(query, **kwargs):
            """Mock async iterator for query results."""
            for item in mock_scores:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query_items(None))
        
        result = await cache_service._calculate_sentiment_aggregate(tool_id, hours)
        
        # Verify counts
        assert result["total_mentions"] == 4
        assert result["positive_count"] == 2
        assert result["negative_count"] == 1
        assert result["neutral_count"] == 1
        
        # Verify percentages (should sum to 100)
        assert abs(result["positive_percentage"] - 50.0) < 0.1
        assert abs(result["negative_percentage"] - 25.0) < 0.1
        assert abs(result["neutral_percentage"] - 25.0) < 0.1
        
        # Verify average
        expected_avg = (0.8 + 0.6 + (-0.5) + 0.0) / 4
        assert abs(result["average_sentiment"] - expected_avg) < 0.01

    @pytest.mark.asyncio
    async def test_calculate_sentiment_aggregate_empty(self, cache_service, mock_containers):
        """Test sentiment aggregation with no data."""
        _, sentiment_container, _ = mock_containers
        tool_id = "tool-123"
        hours = 24
        
        # Mock empty results
        async def mock_query_items(query, **kwargs):
            """Mock async iterator with no results."""
            return
            yield  # Make it a generator
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query_items(None))
        
        result = await cache_service._calculate_sentiment_aggregate(tool_id, hours)
        
        # Should return zeros for empty data
        assert result["total_mentions"] == 0
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["neutral_count"] == 0
        assert result["positive_percentage"] == 0.0
        assert result["negative_percentage"] == 0.0
        assert result["neutral_percentage"] == 0.0
        assert result["average_sentiment"] == 0.0

    # T010: Test get_cached_sentiment() - cache hit scenario
    @pytest.mark.asyncio
    async def test_get_cached_sentiment_cache_hit(self, cache_service, mock_containers):
        """Test cache hit scenario - returns cached data immediately."""
        cache_container, _, _ = mock_containers
        tool_id = "tool-123"
        hours = 24
        
        # Create mock cache entry
        now_ts = int(datetime.now(timezone.utc).timestamp())
        mock_cache_entry = {
            "id": f"{tool_id}:HOUR_24",
            "tool_id": tool_id,
            "period": "HOUR_24",
            "total_mentions": 150,
            "positive_count": 100,
            "negative_count": 30,
            "neutral_count": 20,
            "positive_percentage": 66.67,
            "negative_percentage": 20.0,
            "neutral_percentage": 13.33,
            "average_sentiment": 0.45,
            "period_start_ts": now_ts - 86400,
            "period_end_ts": now_ts,
            "last_updated_ts": now_ts - 300,  # 5 minutes ago
        }
        
        cache_container.read_item = AsyncMock(return_value=mock_cache_entry)
        
        result = await cache_service.get_cached_sentiment(tool_id, hours)
        
        # Verify cache hit
        assert result["is_cached"] is True
        assert result["total_mentions"] == 150
        assert result["positive_count"] == 100
        assert result["cached_at"] == mock_cache_entry["last_updated_ts"]

    # T011: Test get_cached_sentiment() - cache miss with fallback
    @pytest.mark.asyncio
    async def test_get_cached_sentiment_cache_miss_fallback(self, cache_service, mock_containers):
        """Test cache miss scenario - falls back to on-demand calculation."""
        cache_container, sentiment_container, _ = mock_containers
        tool_id = "tool-123"
        hours = 24
        
        # Mock cache miss
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        cache_container.read_item = AsyncMock(
            side_effect=CosmosResourceNotFoundError(status_code=404, message="Not found")
        )
        
        # Mock sentiment data for on-demand calculation
        mock_scores = [
            {"sentiment_score": 0.5, "detected_tool_ids": [tool_id]},
        ]
        
        async def mock_query_items(query, **kwargs):
            for item in mock_scores:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query_items(None))
        cache_container.upsert_item = AsyncMock()
        
        result = await cache_service.get_cached_sentiment(tool_id, hours)
        
        # Verify fallback to on-demand calculation
        assert result["is_cached"] is False
        assert result["total_mentions"] == 1
        
        # Verify cache was populated for next request
        cache_container.upsert_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_sentiment_stale_cache(self, cache_service, mock_containers):
        """Test stale cache scenario - recalculates even though cache exists."""
        cache_container, sentiment_container, _ = mock_containers
        tool_id = "tool-123"
        hours = 24
        
        # Create stale cache entry (45 minutes old, TTL is 30)
        now_ts = int(datetime.now(timezone.utc).timestamp())
        stale_cache_entry = {
            "id": f"{tool_id}:HOUR_24",
            "tool_id": tool_id,
            "period": "HOUR_24",
            "total_mentions": 100,
            "positive_count": 60,
            "negative_count": 20,
            "neutral_count": 20,
            "positive_percentage": 60.0,
            "negative_percentage": 20.0,
            "neutral_percentage": 20.0,
            "average_sentiment": 0.4,
            "period_start_ts": now_ts - 86400,
            "period_end_ts": now_ts,
            "last_updated_ts": now_ts - 2700,  # 45 minutes ago
        }
        
        cache_container.read_item = AsyncMock(return_value=stale_cache_entry)
        
        # Mock fresh sentiment data
        mock_scores = [
            {"sentiment_score": 0.7, "detected_tool_ids": [tool_id]},
            {"sentiment_score": 0.8, "detected_tool_ids": [tool_id]},
        ]
        
        async def mock_query_items(query, **kwargs):
            for item in mock_scores:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query_items(None))
        cache_container.upsert_item = AsyncMock()
        
        result = await cache_service.get_cached_sentiment(tool_id, hours)
        
        # Should recalculate with fresh data
        assert result["total_mentions"] == 2
        
        # Should update cache
        cache_container.upsert_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_sentiment_non_standard_period(self, cache_service, mock_containers):
        """Test non-standard time period - always calculates on-demand, no cache."""
        _, sentiment_container, _ = mock_containers
        tool_id = "tool-123"
        hours = 12  # Non-standard period
        
        # Mock sentiment data
        mock_scores = [
            {"sentiment_score": 0.5, "detected_tool_ids": [tool_id]},
        ]
        
        async def mock_query_items(query, **kwargs):
            for item in mock_scores:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query_items(None))
        
        result = await cache_service.get_cached_sentiment(tool_id, hours)
        
        # Should calculate on-demand
        assert result["is_cached"] is False
        assert result["total_mentions"] == 1

    # Test _save_to_cache() method
    @pytest.mark.asyncio
    async def test_save_to_cache(self, cache_service, mock_containers):
        """Test saving cache entry to container."""
        cache_container, _, _ = mock_containers
        
        now_ts = int(datetime.now(timezone.utc).timestamp())
        cache_entry = SentimentCacheEntry(
            id="tool:HOUR_24",
            tool_id="tool-id",
            period=CachePeriod.HOUR_24,
            total_mentions=100,
            positive_count=60,
            negative_count=20,
            neutral_count=20,
            positive_percentage=60.0,
            negative_percentage=20.0,
            neutral_percentage=20.0,
            average_sentiment=0.4,
            period_start_ts=now_ts - 86400,
            period_end_ts=now_ts,
            last_updated_ts=now_ts,
        )
        
        cache_container.upsert_item = AsyncMock()
        
        await cache_service._save_to_cache(cache_entry)
        
        cache_container.upsert_item.assert_called_once()
        call_args = cache_container.upsert_item.call_args[0][0]
        assert call_args["id"] == cache_entry.id
        assert call_args["tool_id"] == cache_entry.tool_id
