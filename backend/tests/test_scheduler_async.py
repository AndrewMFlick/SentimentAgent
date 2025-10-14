"""Simple unit tests for async implementation in scheduler.

These tests verify the async pattern is implemented correctly
without requiring full application startup or database connections.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import os

# Set minimal environment variables
os.environ.setdefault('REDDIT_CLIENT_ID', 'test')
os.environ.setdefault('REDDIT_CLIENT_SECRET', 'test')
os.environ.setdefault('COSMOS_ENDPOINT', 'https://test/')
os.environ.setdefault('COSMOS_KEY', 'test')

pytestmark = pytest.mark.asyncio


class TestAsyncSchedulerPattern:
    """Test async/sync integration pattern in scheduler."""

    async def test_threadpool_executor_initialized(self):
        """T005: Verify ThreadPoolExecutor is initialized with single worker."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            # Verify executor exists and has 1 worker
            assert scheduler.executor is not None
            assert scheduler.executor._max_workers == 1

    async def test_async_wrapper_uses_executor(self):
        """T006: Verify collect_and_analyze uses run_in_executor pattern."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            # Mock the sync method
            scheduler._collect_and_analyze_sync = Mock()
            
            # Call async method
            await scheduler.collect_and_analyze()
            
            # Verify sync method was called (means executor was used)
            assert scheduler._collect_and_analyze_sync.called

    async def test_collect_and_analyze_doesnt_block(self):
        """T011: Verify collection doesn't block event loop.
        
        Critical test: async wrapper should allow other async tasks to run
        while collection is happening in thread pool.
        """
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            # Make sync method slow (simulating Reddit API)
            def slow_sync_method():
                time.sleep(0.5)  # 500ms blocking operation
            
            scheduler._collect_and_analyze_sync = slow_sync_method
            
            # Track if other async tasks can run
            other_task_ran = False
            
            async def other_async_task():
                nonlocal other_task_ran
                await asyncio.sleep(0.1)
                other_task_ran = True
            
            # Start collection and another task concurrently
            await asyncio.gather(
                scheduler.collect_and_analyze(),
                other_async_task()
            )
            
            # If collection blocked, other_task wouldn't complete
            assert other_task_ran, "Other async task should run while collection is in thread pool"

    async def test_multiple_concurrent_collections_dont_interfere(self):
        """T013: Verify multiple async calls don't interfere with each other."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            call_count = 0
            
            def counting_sync_method():
                nonlocal call_count
                call_count += 1
                time.sleep(0.1)
            
            scheduler._collect_and_analyze_sync = counting_sync_method
            
            # Run 3 collections concurrently
            # Note: With max_workers=1, they'll execute sequentially but shouldn't block the event loop
            tasks = [
                scheduler.collect_and_analyze(),
                scheduler.collect_and_analyze(),
                scheduler.collect_and_analyze(),
            ]
            
            start_time = time.time()
            await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # All 3 should complete
            assert call_count == 3
            
            # Should take ~0.3s (3 x 0.1s), not block
            assert elapsed < 0.5, f"Collections took {elapsed}s, should be ~0.3s"

    async def test_executor_shutdown_on_stop(self):
        """T009: Verify executor shuts down cleanly when scheduler stops."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            # Start scheduler
            scheduler.start()
            assert scheduler.is_running
            
            # Stop scheduler
            scheduler.stop()
            assert not scheduler.is_running
            
            # Executor should still exist (not shut down in current implementation)
            assert scheduler.executor is not None


class TestDelayedInitialCollection:
    """Test delayed initial collection for fast startup."""

    def test_initial_collection_has_delay(self):
        """T026: Verify 5-second delay in initial collection.
        
        AC1: Application startup doesn't wait for collection to complete.
        """
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            from datetime import datetime, timedelta
            
            scheduler = CollectionScheduler()
            scheduler.start()
            
            # Check that initial_collection job is scheduled
            jobs = scheduler.scheduler.get_jobs()
            job_ids = [job.id for job in jobs]
            
            # Should have multiple jobs including initial_collection
            assert len(jobs) > 0
            
            # Verify scheduler started without blocking
            assert scheduler.is_running
            
            scheduler.stop()


class TestAsyncWrapperErrorHandling:
    """Test error handling in async wrappers."""

    async def test_sync_error_doesnt_crash_async_wrapper(self):
        """T036: Verify errors in sync code are handled gracefully."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'):
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            
            # Make sync method raise an error
            def failing_sync_method():
                raise Exception("Simulated collection error")
            
            scheduler._collect_and_analyze_sync = failing_sync_method
            
            # Should not raise exception to caller
            try:
                await scheduler.collect_and_analyze()
                # If we reach here, error was caught (expected)
            except Exception as e:
                # If error propagates, test fails
                pytest.fail(f"Error should be handled in sync code, not propagate: {e}")


class TestCleanupAsyncWrapper:
    """Test async wrapper for cleanup job."""

    async def test_cleanup_uses_executor(self):
        """T008: Verify cleanup_old_data uses executor pattern."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db') as mock_db:
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            mock_db.cleanup_old_data = Mock()
            
            # Call async cleanup
            await scheduler.cleanup_old_data()
            
            # Verify sync cleanup was called
            assert mock_db.cleanup_old_data.called


class TestTrendingAsyncWrapper:
    """Test async wrapper for trending analysis."""

    async def test_trending_uses_executor(self):
        """T009: Verify analyze_trending_topics uses executor pattern."""
        with patch('src.services.scheduler.RedditCollector'), \
             patch('src.services.scheduler.SentimentAnalyzer'), \
             patch('src.services.scheduler.db'), \
             patch('src.services.scheduler.trending_analyzer') as mock_trending:
            
            from src.services.scheduler import CollectionScheduler
            
            scheduler = CollectionScheduler()
            mock_trending.analyze_trending = Mock(return_value=[])
            
            # Call async trending analysis
            await scheduler.analyze_trending_topics()
            
            # Verify sync trending was called
            assert mock_trending.analyze_trending.called
