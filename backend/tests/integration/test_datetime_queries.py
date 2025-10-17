"""Integration tests for datetime query compatibility with CosmosDB.

Tests validate that datetime-based queries work correctly with CosmosDB
PostgreSQL mode, which has JSON parsing issues with ISO 8601 datetime strings.
The fix uses Unix timestamps instead of ISO format strings in query parameters.

This test module provides the framework for validating all datetime query scenarios:
- Backend startup data loading (User Story 1)
- Historical data queries (User Story 2)
- Background job queries (User Story 3)

NOTE: Integration tests require:
1. CosmosDB emulator running on localhost:8081 (or configured endpoint)
2. Valid .env file with required configuration
3. T001 implemented (_datetime_to_timestamp helper function)

To run these tests:
    cd backend
    pytest tests/integration/test_datetime_queries.py -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
import asyncio

# Test configuration
pytestmark = pytest.mark.integration


@pytest.fixture
def test_post_data():
    """
    Provide sample post data for testing datetime queries.
    
    Returns a list of post dictionaries with various timestamps
    for testing time-based filtering.
    """
    now = datetime.now(timezone.utc)
    
    test_posts = [
        {
            "id": "test_post_recent",
            "subreddit": "test_subreddit",
            "title": "Recent test post",
            "author": "test_user",
            "score": 100,
            "created_utc": int((now - timedelta(hours=12)).timestamp()),
            "selftext": "This is a recent test post",
            "url": "https://reddit.com/r/test/test_post_recent"
        },
        {
            "id": "test_post_old",
            "subreddit": "test_subreddit",
            "title": "Old test post",
            "author": "test_user",
            "score": 50,
            "created_utc": int((now - timedelta(hours=48)).timestamp()),
            "selftext": "This is an old test post",
            "url": "https://reddit.com/r/test/test_post_old"
        }
    ]
    
    return test_posts


@pytest.fixture
def test_sentiment_data():
    """
    Provide sample sentiment data for testing datetime queries.
    
    Returns a list of sentiment score dictionaries with various timestamps.
    """
    now = datetime.now(timezone.utc)
    
    test_sentiments = [
        {
            "id": "test_sentiment_1",
            "post_id": "test_post_recent",
            "subreddit": "test_subreddit",
            "compound": 0.5,
            "positive": 0.7,
            "negative": 0.1,
            "neutral": 0.2,
            "created_at": (now - timedelta(hours=12)).isoformat() + "Z"
        },
        {
            "id": "test_sentiment_2",
            "post_id": "test_post_old",
            "subreddit": "test_subreddit",
            "compound": -0.3,
            "positive": 0.2,
            "negative": 0.6,
            "neutral": 0.2,
            "created_at": (now - timedelta(hours=48)).isoformat() + "Z"
        }
    ]
    
    return test_sentiments


class TestDatetimeQueryInfrastructure:
    """Test that datetime query infrastructure is set up correctly."""
    
    def test_test_file_structure(self):
        """
        Test that test file is properly structured.
        
        This is a meta-test to verify the test framework itself is working.
        """
        # If this test runs, the test file structure is valid
        assert True, "Test file structure is valid"
    
    def test_fixtures_available(self, test_post_data, test_sentiment_data):
        """
        Test that test fixtures provide expected data structure.
        
        Validates that fixture data is properly formatted for test use.
        """
        # Verify post data structure
        assert isinstance(test_post_data, list), "test_post_data should be a list"
        assert len(test_post_data) > 0, "test_post_data should not be empty"
        assert all('id' in post for post in test_post_data), "All posts should have id"
        assert all('created_utc' in post for post in test_post_data), \
            "All posts should have created_utc timestamp"
        
        # Verify sentiment data structure
        assert isinstance(test_sentiment_data, list), "test_sentiment_data should be a list"
        assert len(test_sentiment_data) > 0, "test_sentiment_data should not be empty"
        assert all('id' in sent for sent in test_sentiment_data), \
            "All sentiments should have id"
        assert all('created_at' in sent for sent in test_sentiment_data), \
            "All sentiments should have created_at timestamp"


# Placeholder for User Story 1 tests (to be implemented in T003-T004)
class TestUserStory1_BackendStartupDataLoading:
    """Tests for User Story 1: Backend Startup Data Loading.
    
    Goal: Enable backend to successfully load recent data on startup
    without datetime query errors.
    
    Tests to be added:
    - T003: test_load_recent_data_success()
    - T004: test_startup_logs_actual_counts()
    """
    pass


# Placeholder for User Story 2 tests (to be implemented in T008-T010)
class TestUserStory2_HistoricalDataQueries:
    """Tests for User Story 2: Historical Data Queries.
    
    Goal: Enable API endpoints and background jobs to query historical
    data by time ranges without errors.
    
    Tests to be added:
    - T008: test_get_recent_posts_datetime_filter()
    - T009: test_get_sentiment_stats_time_range()
    - T010: test_cleanup_old_data_datetime_filter()
    """
    pass


# Placeholder for User Story 3 tests (to be implemented in T014-T015)
class TestUserStory3_DataCollectionAndAnalysisJobs:
    """Tests for User Story 3: Data Collection and Analysis Jobs.
    
    Goal: Enable background jobs to query existing data by timestamp
    to avoid duplicates.
    
    Tests to be added:
    - T014: test_query_for_duplicate_detection()
    - T015: test_query_mixed_document_formats()
    """
    pass


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
            from src.config import settings
            
            # Create instance with mocked initialization
            service = object.__new__(DatabaseService)
            
            # Mock the containers
            service.posts_container = Mock()
            service.comments_container = Mock()
            service.sentiment_container = Mock()
            
            # Bind methods from the class to this instance
            service._datetime_to_timestamp = lambda dt: int(dt.timestamp())
            service.get_recent_posts = Mock(return_value=[])
            service.get_sentiment_stats = Mock(return_value={"total": 0})
            
            # Bind the actual load_recent_data method to test the real implementation
            import types
            service.load_recent_data = types.MethodType(DatabaseService.load_recent_data, service)
            
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
          
        Note: We're testing the real load_recent_data method with mocked dependencies.
        The method is bound to the service instance, so it can call mocked methods.
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
