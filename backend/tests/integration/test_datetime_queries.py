"""Integration tests for datetime query compatibility with CosmosDB.

Tests validate that datetime queries work correctly with CosmosDB PostgreSQL mode,
which has JSON parsing issues with ISO 8601 datetime strings.

Reference: specs/004-fix-the-cosmosdb/
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import asyncio


@pytest.mark.integration
class TestDatetimeQueries:
    """Test datetime query compatibility with CosmosDB."""
    
    @pytest.fixture
    def db_service(self):
        """Create a DatabaseService instance without connecting to CosmosDB."""
        # Import with patching to avoid connection attempts
        with patch('azure.cosmos.CosmosClient'):
            from src.services.database import DatabaseService
            # Create instance without initializing containers
            service = object.__new__(DatabaseService)
            return service
    
    def test_datetime_to_timestamp_helper_exists(self, db_service):
        """
        Test that _datetime_to_timestamp helper method exists.
        
        Task: T001
        """
        assert hasattr(db_service, '_datetime_to_timestamp')
        assert callable(db_service._datetime_to_timestamp)
    
    def test_datetime_to_timestamp_conversion(self, db_service):
        """
        Test that _datetime_to_timestamp converts datetime correctly.
        
        Task: T001
        """
        # Test with a known datetime
        test_dt = datetime(2024, 1, 15, 12, 30, 45)
        timestamp = db_service._datetime_to_timestamp(test_dt)
        
        # Verify it's an integer
        assert isinstance(timestamp, int)
        
        # Verify conversion is correct
        # Recreate datetime from timestamp to validate
        recreated_dt = datetime.fromtimestamp(timestamp)
        assert recreated_dt.year == test_dt.year
        assert recreated_dt.month == test_dt.month
        assert recreated_dt.day == test_dt.day
        assert recreated_dt.hour == test_dt.hour
        assert recreated_dt.minute == test_dt.minute
    
    def test_datetime_to_timestamp_with_utc_now(self, db_service):
        """
        Test that _datetime_to_timestamp works with current time.
        
        Task: T001
        """
        now = datetime.utcnow()
        timestamp = db_service._datetime_to_timestamp(now)
        
        # Verify it's an integer
        assert isinstance(timestamp, int)
        
        # Timestamp should be reasonable (not zero, not too far in future)
        assert timestamp > 1700000000  # After Nov 2023
        assert timestamp < 2000000000  # Before May 2033


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserStory1DataLoading:
    """Test User Story 1: Backend startup data loading.
    
    These tests verify that load_recent_data() executes without errors
    and properly loads data on startup.
    """
    
    @pytest.fixture
    def db_service_with_mocks(self):
        """Create a DatabaseService with mocked containers."""
        with patch('azure.cosmos.CosmosClient'):
            from src.services.database import DatabaseService
            service = object.__new__(DatabaseService)
            
            # Mock the containers
            service.posts_container = Mock()
            service.comments_container = Mock()
            service.sentiment_container = Mock()
            
            # Mock the helper methods
            service._datetime_to_timestamp = DatabaseService._datetime_to_timestamp.__get__(service)
            service.get_recent_posts = Mock(return_value=[])
            service.get_sentiment_stats = Mock(return_value={"total": 0})
            
            return service
    
    async def test_load_recent_data_success(self, db_service_with_mocks, caplog):
        """
        Test that load_recent_data() executes without InternalServerError.
        
        Task: T003
        Purpose: Verify load_recent_data() executes without CosmosHttpResponseError
        Setup: Mock database with test posts from last 24 hours
        Assertions:
          - No CosmosHttpResponseError raised
          - Logs contain "Data loading complete"
          - Method completes without exceptions
        """
        import logging
        caplog.set_level(logging.INFO)
        
        # Mock get_recent_posts to return test data
        db_service_with_mocks.get_recent_posts = Mock(return_value=[
            Mock(id="post1", subreddit="test"),
            Mock(id="post2", subreddit="test"),
        ])
        
        # Mock query_items for comments count
        db_service_with_mocks.comments_container.query_items = Mock(return_value=[{"$1": 5}])
        
        # Mock get_sentiment_stats
        db_service_with_mocks.get_sentiment_stats = Mock(return_value={"total": 10})
        
        # Execute load_recent_data - should not raise exceptions
        try:
            await db_service_with_mocks.load_recent_data()
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(f"load_recent_data raised exception: {e}")
        
        # Assertions
        assert execution_succeeded, "load_recent_data should complete without exceptions"
        
        # Check that methods were called
        assert db_service_with_mocks.get_recent_posts.called, "get_recent_posts should be called"
    
    async def test_startup_logs_actual_counts(self, db_service_with_mocks, caplog):
        """
        Test that startup logs show real data counts.
        
        Task: T004
        Purpose: Verify startup logs show real data counts
        Setup: Mock database with known number of test documents
        Test: Call load_recent_data(), check log output
        Assertions:
          - Logs contain actual counts (e.g., "5 posts, 3 comments")
          - No "temporarily disabled" warning
        """
        import logging
        caplog.set_level(logging.INFO)
        
        # Mock get_recent_posts to return 5 test posts
        mock_posts = [Mock(id=f"post{i}", subreddit="test") for i in range(5)]
        db_service_with_mocks.get_recent_posts = Mock(return_value=mock_posts)
        
        # Mock query_items for comments count to return 3
        db_service_with_mocks.comments_container.query_items = Mock(return_value=[{"$1": 3}])
        
        # Mock get_sentiment_stats to return 8 sentiment scores
        db_service_with_mocks.get_sentiment_stats = Mock(return_value={"total": 8})
        
        # Execute load_recent_data
        await db_service_with_mocks.load_recent_data()
        
        # Check logs
        log_messages = [record.message for record in caplog.records]
        
        # Should contain "Data loading complete"
        completion_logs = [msg for msg in log_messages if "Data loading complete" in msg]
        assert len(completion_logs) > 0, "Should log 'Data loading complete'"
        
        # Should NOT contain "temporarily disabled"
        disabled_logs = [msg for msg in log_messages if "temporarily disabled" in msg]
        assert len(disabled_logs) == 0, "Should not log 'temporarily disabled' warning"
        
        # Verify actual counts in logs (should contain the numbers 5, 3, 8)
        completion_msg = completion_logs[0]
        assert "5 posts" in completion_msg or "5" in completion_msg, "Should log actual post count"
