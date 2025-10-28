"""Performance tests for cache service (Feature 017 - Pre-Cached Sentiment Analysis).

Test Coverage:
- T015: Verify <1s response time for cache hit

These tests validate that the caching system meets performance targets.

Reference: specs/017-pre-cached-sentiment/tasks.md Phase 3
Success Criteria: 24-hour queries should return in <1 second from cache
"""

import pytest
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.services.cache_service import CacheService


class TestCachePerformance:
    """Performance tests for cache service."""

    @pytest.fixture
    def cache_service_perf(self):
        """Create cache service for performance testing."""
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
    async def test_cache_hit_response_time(self, cache_service_perf):
        """Test that cache hit returns in <1 second (should be <50ms typically)."""
        service, cache_container, _ = cache_service_perf
        
        tool_id = "perf-tool-123"
        hours = 24
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Fresh cache entry
        cached_data = {
            "id": f"{tool_id}:HOUR_24",
            "tool_id": tool_id,
            "period": "HOUR_24",
            "total_mentions": 1000,
            "positive_count": 600,
            "negative_count": 300,
            "neutral_count": 100,
            "positive_percentage": 60.0,
            "negative_percentage": 30.0,
            "neutral_percentage": 10.0,
            "average_sentiment": 0.3,
            "period_start_ts": now_ts - 86400,
            "period_end_ts": now_ts,
            "last_updated_ts": now_ts - 300,  # 5 minutes ago
        }
        
        # Simulate very fast cache read (realistic for in-memory/fast storage)
        async def fast_cache_read(*args, **kwargs):
            await AsyncMock(return_value=cached_data)()
            return cached_data
        
        cache_container.read_item = fast_cache_read
        
        # Execute and measure
        start_time = time.time()
        result = await service.get_cached_sentiment(tool_id, hours)
        duration = time.time() - start_time
        
        # Verify performance target met
        assert duration < 1.0, f"Cache hit took {duration:.3f}s, expected <1s"
        
        # Typically should be much faster (<50ms), but allowing 1s for CI/test overhead
        assert result["is_cached"] is True
        assert result["total_mentions"] == 1000

    @pytest.mark.asyncio
    async def test_cache_miss_fallback_performance(self, cache_service_perf):
        """Test that cache miss with fallback calculation completes in reasonable time."""
        service, cache_container, sentiment_container = cache_service_perf
        
        tool_id = "perf-tool-456"
        hours = 24
        
        # Setup: Cache miss
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        
        async def cache_miss(*args, **kwargs):
            raise CosmosResourceNotFoundError(status_code=404, message="Not found")
        
        cache_container.read_item = cache_miss
        
        # Setup: Moderate amount of sentiment data (similar to real-world scenario)
        # 100 documents to aggregate
        sentiment_data = [
            {"sentiment_score": 0.5 + (i % 3 - 1) * 0.3, "detected_tool_ids": [tool_id], "_ts": 1698451200 + i}
            for i in range(100)
        ]
        
        async def mock_query(query, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        cache_container.upsert_item = AsyncMock()
        
        # Execute and measure
        start_time = time.time()
        result = await service.get_cached_sentiment(tool_id, hours)
        duration = time.time() - start_time
        
        # Cache miss with calculation should still be fast (<2s acceptable, <1s ideal)
        assert duration < 2.0, f"Cache miss fallback took {duration:.3f}s, expected <2s"
        
        # Verify result
        assert result["total_mentions"] == 100
        assert result["is_cached"] is False

    @pytest.mark.asyncio
    async def test_cache_lookup_overhead(self, cache_service_perf):
        """Test that cache lookup overhead is minimal (<50ms)."""
        service, cache_container, _ = cache_service_perf
        
        tool_id = "perf-tool-789"
        hours = 24
        now_ts = int(datetime.now(timezone.utc).timestamp())
        
        # Setup: Instant cache response
        cached_data = {
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
            "last_updated_ts": now_ts - 100,
        }
        
        cache_container.read_item = AsyncMock(return_value=cached_data)
        
        # Execute multiple times and measure average
        durations = []
        for _ in range(5):
            start_time = time.time()
            await service.get_cached_sentiment(tool_id, hours)
            durations.append(time.time() - start_time)
        
        avg_duration = sum(durations) / len(durations)
        
        # Average overhead should be minimal
        # In production with real CosmosDB, this might be 10-50ms
        # In tests with mocks, should be <10ms
        assert avg_duration < 0.1, f"Average cache lookup: {avg_duration*1000:.1f}ms, expected <100ms"

    @pytest.mark.asyncio
    async def test_large_dataset_aggregation(self, cache_service_perf):
        """Test performance with large dataset (1000+ documents)."""
        service, cache_container, sentiment_container = cache_service_perf
        
        tool_id = "perf-tool-large"
        hours = 24
        
        # Setup: Cache miss
        from azure.cosmos.exceptions import CosmosResourceNotFoundError
        cache_container.read_item = AsyncMock(
            side_effect=CosmosResourceNotFoundError(status_code=404, message="Not found")
        )
        
        # Setup: Large dataset (1000 documents)
        import random
        sentiment_data = [
            {
                "sentiment_score": random.uniform(-1, 1),
                "detected_tool_ids": [tool_id],
                "_ts": 1698451200 + i
            }
            for i in range(1000)
        ]
        
        async def mock_query(query, **kwargs):
            for item in sentiment_data:
                yield item
        
        sentiment_container.query_items = AsyncMock(return_value=mock_query(None))
        cache_container.upsert_item = AsyncMock()
        
        # Execute and measure
        start_time = time.time()
        result = await service.get_cached_sentiment(tool_id, hours)
        duration = time.time() - start_time
        
        # Even with 1000 documents, should complete in reasonable time
        # Real-world scenario: this would be slow without caching (10+ seconds)
        # With our on-demand calculation: should be <2-3 seconds
        assert duration < 3.0, f"Large dataset aggregation took {duration:.3f}s, expected <3s"
        
        # Verify calculation
        assert result["total_mentions"] == 1000
        
        # Verify cache was populated for next request
        cache_container.upsert_item.assert_called_once()
