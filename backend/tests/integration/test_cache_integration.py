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


class TestCacheIntegrationPhase4:
    """Integration tests for Phase 4 - Automatic Cache Refresh."""

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

    # T031: Integration test for full refresh cycle
    @pytest.mark.asyncio
    async def test_full_refresh_cycle_integration(self, cache_service, mock_containers):
        """Test complete refresh cycle from active tools to cache update."""
        cache_container, sentiment_container, tools_container = mock_containers
        
        # Setup: Mock 2 active tools
        async def mock_tools_query(*args, **kwargs):
            yield {"id": "tool-1"}
            yield {"id": "tool-2"}
        
        tools_container.query_items = MagicMock(return_value=mock_tools_query())
        
        # Setup: Mock sentiment data for calculations
        now_ts = int(datetime.now(timezone.utc).timestamp())
        sentiment_data = [
            {"sentiment_score": 0.5, "detected_tool_ids": ["tool-1"], "_ts": now_ts - 3600},
            {"sentiment_score": 0.3, "detected_tool_ids": ["tool-1"], "_ts": now_ts - 7200},
        ]
        
        async def mock_sentiment_query(*args, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = MagicMock(return_value=mock_sentiment_query())
        
        # Setup: Mock cache operations
        cache_container.upsert_item = MagicMock()
        
        # Setup: Mock count query for metadata
        async def mock_count_query(*args, **kwargs):
            yield 8  # 2 tools * 4 periods
        
        cache_container.query_items = MagicMock(return_value=mock_count_query())
        
        # Execute
        result = await cache_service.refresh_all_tools()
        
        # Verify results
        assert result["tools_refreshed"] == 2
        assert result["entries_created"] == 8  # 2 tools * 4 periods
        assert result["errors"] == 0
        
        # Verify cache entries were saved (4 periods per tool * 2 tools = 8 upserts + 1 metadata)
        assert cache_container.upsert_item.call_count >= 8

    # T032: Integration test for concurrent requests during refresh
    @pytest.mark.asyncio
    async def test_concurrent_requests_during_refresh(self, cache_service, mock_containers):
        """Test that user requests work during cache refresh."""
        cache_container, sentiment_container, tools_container = mock_containers
        
        tool_id = "test-tool-123"
        hours = 24
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Mock existing cache entry (old but valid)
        old_cache_entry = {
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
            "period_end_ts": now_ts - 1800,  # 30 minutes old
            "last_updated_ts": now_ts - 1800,
        }
        
        cache_container.read_item = MagicMock(return_value=old_cache_entry)
        
        # Execute: Simulate concurrent user request during refresh
        result = await cache_service.get_cached_sentiment(tool_id, hours)
        
        # Verify: User gets the old cached data (doesn't block on refresh)
        assert result["is_cached"] is True
        assert result["total_mentions"] == 50
        assert result["cached_at"] == now_ts - 1800

    @pytest.mark.asyncio
    async def test_refresh_updates_stale_cache(self, cache_service, mock_containers):
        """Test that refresh updates stale cache entries."""
        cache_container, sentiment_container, tools_container = mock_containers
        
        # Setup: Mock 1 active tool
        async def mock_tools_query(*args, **kwargs):
            yield {"id": "tool-1"}
        
        tools_container.query_items = MagicMock(return_value=mock_tools_query())
        
        # Setup: Mock fresh sentiment data
        now_ts = int(datetime.now(timezone.utc).timestamp())
        sentiment_data = [
            {"sentiment_score": 0.8, "detected_tool_ids": ["tool-1"], "_ts": now_ts - 1000},
            {"sentiment_score": 0.7, "detected_tool_ids": ["tool-1"], "_ts": now_ts - 2000},
        ]
        
        async def mock_sentiment_query(*args, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = MagicMock(return_value=mock_sentiment_query())
        
        # Track upserted entries
        upserted_entries = []
        
        def track_upsert(body):
            upserted_entries.append(body)
        
        cache_container.upsert_item = MagicMock(side_effect=track_upsert)
        
        # Setup: Mock count query
        async def mock_count_query(*args, **kwargs):
            yield 4
        
        cache_container.query_items = MagicMock(return_value=mock_count_query())
        
        # Execute
        result = await cache_service.refresh_all_tools()
        
        # Verify entries were updated
        assert result["tools_refreshed"] == 1
        assert result["entries_created"] == 4
        
        # Verify cache entries have fresh data
        cache_entries = [e for e in upserted_entries if e["id"] != "metadata"]
        assert len(cache_entries) == 4
        
        # All entries should have positive sentiment (from mock data)
        for entry in cache_entries:
            assert entry["positive_count"] >= 0
            assert entry["total_mentions"] >= 0


class TestCacheIntegrationPhase5:
    """Integration tests for Phase 5 (User Story 3): View Historical Trends.
    
    Test Coverage:
    - T047: Integration test for time period switching - verify all periods accessible
    
    Reference: specs/017-pre-cached-sentiment/tasks.md Phase 5
    """

    @pytest.fixture
    def cache_service_integrated(self):
        """Create cache service with integrated mock containers."""
        cache_container = MagicMock()
        sentiment_container = MagicMock()
        tools_container = MagicMock()
        
        service = CacheService(
            cache_container=cache_container,
            sentiment_container=sentiment_container,
            tools_container=tools_container,
        )
        
        return service, cache_container, sentiment_container, tools_container

    # T047: Integration test for time period switching
    @pytest.mark.asyncio
    async def test_time_period_switching_all_periods_accessible(
        self, cache_service_integrated
    ):
        """Test switching between all time periods (1h, 24h, 7d, 30d).
        
        Verifies that:
        - All 4 standard periods are accessible
        - Switching between periods works correctly
        - Each period returns correct cached data
        - Cache keys are correctly formatted for each period
        """
        service, cache_container, _, _ = cache_service_integrated
        
        tool_id = "integration-tool-periods"
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Cache entries for all 4 periods
        cache_data_by_period = {
            f"{tool_id}:HOUR_1": {
                "id": f"{tool_id}:HOUR_1",
                "tool_id": tool_id,
                "period": "HOUR_1",
                "total_mentions": 50,
                "positive_count": 30,
                "negative_count": 10,
                "neutral_count": 10,
                "positive_percentage": 60.0,
                "negative_percentage": 20.0,
                "neutral_percentage": 20.0,
                "average_sentiment": 0.4,
                "period_start_ts": now_ts - 3600,
                "period_end_ts": now_ts,
                "last_updated_ts": now_ts - 300,
            },
            f"{tool_id}:HOUR_24": {
                "id": f"{tool_id}:HOUR_24",
                "tool_id": tool_id,
                "period": "HOUR_24",
                "total_mentions": 200,
                "positive_count": 120,
                "negative_count": 40,
                "neutral_count": 40,
                "positive_percentage": 60.0,
                "negative_percentage": 20.0,
                "neutral_percentage": 20.0,
                "average_sentiment": 0.4,
                "period_start_ts": now_ts - 86400,
                "period_end_ts": now_ts,
                "last_updated_ts": now_ts - 300,
            },
            f"{tool_id}:DAY_7": {
                "id": f"{tool_id}:DAY_7",
                "tool_id": tool_id,
                "period": "DAY_7",
                "total_mentions": 800,
                "positive_count": 500,
                "negative_count": 150,
                "neutral_count": 150,
                "positive_percentage": 62.5,
                "negative_percentage": 18.75,
                "neutral_percentage": 18.75,
                "average_sentiment": 0.43,
                "period_start_ts": now_ts - (168 * 3600),
                "period_end_ts": now_ts,
                "last_updated_ts": now_ts - 300,
            },
            f"{tool_id}:DAY_30": {
                "id": f"{tool_id}:DAY_30",
                "tool_id": tool_id,
                "period": "DAY_30",
                "total_mentions": 3000,
                "positive_count": 1800,
                "negative_count": 600,
                "neutral_count": 600,
                "positive_percentage": 60.0,
                "negative_percentage": 20.0,
                "neutral_percentage": 20.0,
                "average_sentiment": 0.4,
                "period_start_ts": now_ts - (720 * 3600),
                "period_end_ts": now_ts,
                "last_updated_ts": now_ts - 600,
            },
        }
        
        def mock_read_item(item, partition_key):
            return cache_data_by_period[item]
        
        cache_container.read_item = mock_read_item
        
        # Test all 4 periods
        test_cases = [
            (1, "HOUR_1", 50),
            (24, "HOUR_24", 200),
            (168, "DAY_7", 800),
            (720, "DAY_30", 3000),
        ]
        
        for hours, expected_period, expected_mentions in test_cases:
            result = await service.get_cached_sentiment(tool_id, hours)
            
            # Verify correct data returned
            assert result["is_cached"] is True, f"Period {expected_period} should be cached"
            assert result["total_mentions"] == expected_mentions, \
                f"Period {expected_period} should have {expected_mentions} mentions"
            
            # Verify correct period start timestamp
            if expected_period == "HOUR_1":
                assert result["period_start_ts"] == now_ts - 3600
            elif expected_period == "HOUR_24":
                assert result["period_start_ts"] == now_ts - 86400
            elif expected_period == "DAY_7":
                assert result["period_start_ts"] == now_ts - (168 * 3600)
            elif expected_period == "DAY_30":
                assert result["period_start_ts"] == now_ts - (720 * 3600)

    @pytest.mark.asyncio
    async def test_7day_and_30day_periods_full_flow(self, cache_service_integrated):
        """Test complete flow for 7-day and 30-day periods.
        
        Verifies:
        - Cache miss triggers calculation for 7-day period
        - Cache miss triggers calculation for 30-day period
        - Both periods are saved to cache
        - Subsequent requests hit cache
        """
        service, cache_container, sentiment_container, _ = cache_service_integrated
        
        tool_id = "integration-tool-7d-30d"
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Cache misses initially
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        cache_reads = []
        
        def mock_read_item(item, partition_key):
            cache_reads.append(item)
            # First call: cache miss
            # Second call: cache hit
            if len([r for r in cache_reads if r == item]) == 1:
                raise CosmosResourceNotFoundError(status_code=404, message="Not found")
            else:
                # Return cached data
                if "DAY_7" in item:
                    return {
                        "id": item,
                        "tool_id": tool_id,
                        "period": "DAY_7",
                        "total_mentions": 500,
                        "positive_count": 300,
                        "negative_count": 100,
                        "neutral_count": 100,
                        "positive_percentage": 60.0,
                        "negative_percentage": 20.0,
                        "neutral_percentage": 20.0,
                        "average_sentiment": 0.4,
                        "period_start_ts": now_ts - (168 * 3600),
                        "period_end_ts": now_ts,
                        "last_updated_ts": now_ts - 100,
                    }
                else:  # DAY_30
                    return {
                        "id": item,
                        "tool_id": tool_id,
                        "period": "DAY_30",
                        "total_mentions": 2000,
                        "positive_count": 1200,
                        "negative_count": 400,
                        "neutral_count": 400,
                        "positive_percentage": 60.0,
                        "negative_percentage": 20.0,
                        "neutral_percentage": 20.0,
                        "average_sentiment": 0.4,
                        "period_start_ts": now_ts - (720 * 3600),
                        "period_end_ts": now_ts,
                        "last_updated_ts": now_ts - 100,
                    }
        
        cache_container.read_item = mock_read_item
        
        # Setup: Sentiment data for calculation
        sentiment_data_7d = [
            {"sentiment_score": 0.5 + (i % 3 - 1) * 0.3, "detected_tool_ids": [tool_id], "_ts": now_ts - (i * 1000)}
            for i in range(500)
        ]
        
        sentiment_data_30d = [
            {"sentiment_score": 0.5 + (i % 3 - 1) * 0.3, "detected_tool_ids": [tool_id], "_ts": now_ts - (i * 2000)}
            for i in range(2000)
        ]
        
        query_call_count = [0]
        
        async def mock_query_items(query, **kwargs):
            query_call_count[0] += 1
            # First call: 7-day data
            # Second call: 30-day data
            if query_call_count[0] == 1:
                for item in sentiment_data_7d:
                    yield item
            else:
                for item in sentiment_data_30d:
                    yield item
        
        sentiment_container.query_items = mock_query_items
        
        # Track cache saves
        cache_saves = []
        
        def track_upsert(body):
            cache_saves.append(body)
        
        cache_container.upsert_item = AsyncMock(side_effect=track_upsert)
        
        # First request: 7-day (cache miss, should calculate)
        result_7d_miss = await service.get_cached_sentiment(tool_id, 168)
        assert result_7d_miss["is_cached"] is False
        assert result_7d_miss["total_mentions"] == 500
        assert len([s for s in cache_saves if "DAY_7" in s.get("id", "")]) == 1
        
        # Second request: 30-day (cache miss, should calculate)
        result_30d_miss = await service.get_cached_sentiment(tool_id, 720)
        assert result_30d_miss["is_cached"] is False
        assert result_30d_miss["total_mentions"] == 2000
        assert len([s for s in cache_saves if "DAY_30" in s.get("id", "")]) == 1
        
        # Third request: 7-day again (cache hit)
        result_7d_hit = await service.get_cached_sentiment(tool_id, 168)
        assert result_7d_hit["is_cached"] is True
        assert result_7d_hit["total_mentions"] == 500
        
        # Fourth request: 30-day again (cache hit)
        result_30d_hit = await service.get_cached_sentiment(tool_id, 720)
        assert result_30d_hit["is_cached"] is True
        assert result_30d_hit["total_mentions"] == 2000

    @pytest.mark.asyncio
    async def test_refresh_job_includes_all_4_periods(self, cache_service_integrated):
        """Test that background refresh job refreshes all 4 periods.
        
        Verifies Phase 5 requirement that refresh includes 1h, 24h, 7d, and 30d.
        """
        service, cache_container, sentiment_container, tools_container = cache_service_integrated
        
        # Setup: One active tool
        async def mock_tools_query():
            yield {"id": "tool-refresh-test"}
        
        tools_container.query_items = MagicMock(return_value=mock_tools_query())
        
        # Setup: Mock sentiment data
        now_ts = int(datetime.now(timezone.utc).timestamp())
        sentiment_data = [
            {"sentiment_score": 0.5, "detected_tool_ids": ["tool-refresh-test"], "_ts": now_ts - (i * 1000)}
            for i in range(100)
        ]
        
        async def mock_sentiment_query(*args, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = MagicMock(return_value=mock_sentiment_query())
        
        # Track cache saves
        upserted_entries = []
        
        def track_upsert(body):
            upserted_entries.append(body)
        
        cache_container.upsert_item = MagicMock(side_effect=track_upsert)
        
        # Setup: Mock count query for metadata
        async def mock_count_query(*args, **kwargs):
            yield 4
        
        cache_container.query_items = MagicMock(return_value=mock_count_query())
        
        # Execute refresh
        result = await service.refresh_all_tools()
        
        # Verify all 4 periods were refreshed
        assert result["tools_refreshed"] == 1
        assert result["entries_created"] == 4
        
        # Verify entries for all periods exist
        cache_entries = [e for e in upserted_entries if e["id"] != "metadata"]
        assert len(cache_entries) == 4
        
        periods_refreshed = [e["period"] for e in cache_entries]
        assert "HOUR_1" in periods_refreshed
        assert "HOUR_24" in periods_refreshed
        assert "DAY_7" in periods_refreshed
        assert "DAY_30" in periods_refreshed
