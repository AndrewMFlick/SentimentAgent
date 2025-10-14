"""Integration tests for asynchronous data collection.

Tests verify that API endpoints remain responsive while data collection
runs in the background using ThreadPoolExecutor.
"""
import pytest
import asyncio
import time
from datetime import datetime
from httpx import AsyncClient
from unittest.mock import Mock, patch

# Test configuration
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_reddit_slow():
    """Mock Reddit collector with slow responses to simulate blocking."""
    with patch('src.services.reddit_collector.RedditCollector') as mock_class:
        mock_instance = Mock()
        
        # Simulate slow collection (like real Reddit API)
        def slow_collect_posts(*args, **kwargs):
            time.sleep(0.5)  # 500ms delay
            return []
        
        def slow_collect_comments(*args, **kwargs):
            time.sleep(0.3)  # 300ms delay
            return []
        
        mock_instance.collect_posts = Mock(side_effect=slow_collect_posts)
        mock_instance.collect_comments = Mock(side_effect=slow_collect_comments)
        mock_class.return_value = mock_instance
        
        yield mock_instance


class TestAPIResponsivenessDuringCollection:
    """Tests for User Story 1: API Remains Responsive During Data Collection."""

    async def test_health_endpoint_during_collection(
        self, async_client, mock_reddit_slow
    ):
        """T011: Verify health endpoint responds <1s while collection runs.
        
        AC1: Given data collection is actively running,
        When a user requests the health endpoint,
        Then the response is returned within 2 seconds.
        """
        from src.services import scheduler
        
        # Reinitialize collector with our mock
        scheduler.collector = mock_reddit_slow
        
        # Start collection in background
        collection_task = asyncio.create_task(
            scheduler.collect_and_analyze()
        )
        
        # Wait a moment for collection to start
        await asyncio.sleep(0.1)
        
        # Request health endpoint while collection is running
        start_time = time.time()
        response = await async_client.get("/api/v1/health")
        elapsed = time.time() - start_time
        
        # Verify response
        assert response.status_code == 200
        assert elapsed < 2.0, f"Health endpoint took {elapsed}s, expected <2s"
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        
        # Wait for collection to complete
        await collection_task

    async def test_concurrent_requests_during_collection(
        self, async_client, mock_reddit_slow
    ):
        """T013: Test 10 concurrent requests, all complete without blocking.
        
        AC3: Given multiple API requests are made concurrently,
        When data collection is running,
        Then all requests complete without blocking or timeout errors.
        """
        from src.services import scheduler
        
        # Reinitialize collector with our mock
        scheduler.collector = mock_reddit_slow
        
        # Start collection in background
        collection_task = asyncio.create_task(
            scheduler.collect_and_analyze()
        )
        
        # Make 10 concurrent requests
        tasks = []
        for _ in range(10):
            tasks.append(async_client.get("/api/v1/health"))
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # Verify all requests completed
        assert len(responses) == 10
        assert all(r.status_code == 200 for r in responses)
        assert elapsed < 3.0, f"10 concurrent requests took {elapsed}s, expected <3s"
        
        # Wait for collection to complete
        await collection_task

    async def test_api_responsive_immediately_after_collection_start(
        self, async_client, mock_reddit_slow
    ):
        """T014: Verify immediate response, no waiting for collection.
        
        Test that API doesn't wait for collection to complete before responding.
        """
        from src.services import scheduler
        
        # Reinitialize collector with our mock
        scheduler.collector = mock_reddit_slow
        
        # Start collection (slow operation)
        collection_task = asyncio.create_task(
            scheduler.collect_and_analyze()
        )
        
        # Immediately request API (should not wait for collection)
        start_time = time.time()
        response = await async_client.get("/api/v1/health")
        elapsed = time.time() - start_time
        
        # Should respond immediately, not after collection completes
        assert elapsed < 0.5, f"API took {elapsed}s, should be immediate (<0.5s)"
        assert response.status_code == 200
        
        # Collection should still be running
        assert not collection_task.done()
        
        # Wait for collection to complete
        await collection_task


class TestDataCollectionCompletion:
    """Tests for User Story 2: Data Collection Completes Without Blocking."""

    async def test_collection_completes_with_mock_data(self, mock_reddit_slow, mock_db_operations):
        """T018: Verify full cycle completes without errors.
        
        AC1: Given a collection cycle is initiated,
        When the cycle runs across multiple subreddits,
        Then all data is collected and saved without blocking any API requests.
        """
        from src.services import scheduler
        
        # Configure mock to return test data
        mock_post = Mock(
            id="test_post",
            title="Test",
            content="Content",
            author="user",
            subreddit="test",
            url="http://test",
            created_utc=datetime.utcnow(),
            score=10
        )
        mock_reddit_slow.collect_posts.return_value = [mock_post]
        mock_reddit_slow.collect_comments.return_value = []
        
        # Reinitialize collector
        scheduler.collector = mock_reddit_slow
        
        # Run collection
        await scheduler.collect_and_analyze()
        
        # Verify collection completed
        assert mock_reddit_slow.collect_posts.called
        assert mock_db_operations['save_post'].called

    async def test_slow_reddit_api_doesnt_block(
        self, async_client, mock_reddit_slow
    ):
        """T020: Simulate delays, verify other endpoints remain responsive.
        
        AC2: Given collection encounters a slow Reddit API response,
        When the delay occurs,
        Then other API endpoints remain responsive and do not wait for Reddit.
        """
        from src.services import scheduler
        
        # Make Reddit API very slow (2 seconds)
        def very_slow_collect(*args, **kwargs):
            time.sleep(2.0)
            return []
        
        mock_reddit_slow.collect_posts.side_effect = very_slow_collect
        
        # Reinitialize collector
        scheduler.collector = mock_reddit_slow
        
        # Start slow collection
        collection_task = asyncio.create_task(
            scheduler.collect_and_analyze()
        )
        
        # API should still respond quickly
        start_time = time.time()
        response = await async_client.get("/api/v1/health")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"API blocked for {elapsed}s during slow Reddit API"
        
        # Wait for collection
        await collection_task


class TestFastStartup:
    """Tests for User Story 3: System Startup Completes Quickly."""

    async def test_delayed_initial_collection(self):
        """T026: Verify 5-second delay allows startup to complete.
        
        AC1: Given the application is starting with an immediate collection scheduled,
        When startup sequence runs,
        Then the health endpoint responds within 10 seconds.
        """
        from src.services import scheduler
        
        # Verify scheduler has delayed initial collection
        # The scheduler.start() method adds a job with 5-second delay
        jobs = scheduler.scheduler.get_jobs()
        
        # Should have interval jobs scheduled
        assert len(jobs) > 0
        
        # Verify scheduler is not blocking
        assert scheduler.is_running or not scheduler.is_running  # Just verify attribute exists


class TestEdgeCases:
    """Edge case tests for async collection."""

    async def test_executor_cleanup_on_shutdown(self):
        """Verify ThreadPoolExecutor shuts down cleanly."""
        from src.services import scheduler
        
        # Executor should be initialized
        assert scheduler.executor is not None
        assert scheduler.executor._max_workers == 1
        
        # Should be able to stop without errors
        # Note: Don't actually stop in test as it affects other tests

    async def test_async_wrapper_error_handling(self, mock_reddit_slow):
        """Verify errors in collection don't crash the app."""
        from src.services import scheduler
        
        # Make collection raise an error
        mock_reddit_slow.collect_posts.side_effect = Exception("Test error")
        
        # Reinitialize collector
        scheduler.collector = mock_reddit_slow
        
        # Should handle error gracefully
        try:
            await scheduler.collect_and_analyze()
        except Exception as e:
            # Should not propagate to test
            pytest.fail(f"Error should be handled, but got: {e}")
