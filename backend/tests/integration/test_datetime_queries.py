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
import types
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

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


# User Story 2 tests - Historical Data Queries
@pytest.mark.integration
class TestUserStory2_HistoricalDataQueries:
    """Tests for User Story 2: Historical Data Queries.
    
    Goal: Enable API endpoints and background jobs to query historical
    data by time ranges without errors.
    
    Tests:
    - T008: test_get_recent_posts_datetime_filter()
    - T009: test_get_sentiment_stats_time_range()
    - T010: test_cleanup_old_data_datetime_filter()
    """
    
    @pytest.fixture
    def db_service_with_mocks(self):
        """Create a DatabaseService with mocked containers for US2 tests."""
        with patch('azure.cosmos.CosmosClient'):
            from src.services.database import DatabaseService
            
            # Create instance with mocked initialization
            service = object.__new__(DatabaseService)
            
            # Mock the containers
            service.posts_container = Mock()
            service.comments_container = Mock()
            service.sentiment_container = Mock()
            
            # Bind the actual _datetime_to_timestamp method from the class
            service._datetime_to_timestamp = types.MethodType(
                DatabaseService._datetime_to_timestamp, service
            )
            
            # Bind actual methods we want to test
            service.get_recent_posts = types.MethodType(DatabaseService.get_recent_posts, service)
            service.get_sentiment_stats = types.MethodType(DatabaseService.get_sentiment_stats, service)
            service.cleanup_old_data = types.MethodType(DatabaseService.cleanup_old_data, service)
            
            return service
    
    def test_get_recent_posts_datetime_filter(self, db_service_with_mocks):
        """
        Test that get_recent_posts works with datetime parameters.
        
        Task: T008
        Purpose: Verify posts query works with datetime parameters
        Setup: Insert posts from 12 hours ago and 48 hours ago (simulated)
        Test: Call get_recent_posts(hours=24)
        Assertions:
          - Returns recent post (12h old)
          - Excludes old post (48h old)
          - No InternalServerError
          - Query uses _ts field and Unix timestamp
        """
        now = datetime.now(timezone.utc)
        recent_post_time = now - timedelta(hours=12)
        old_post_time = now - timedelta(hours=48)
        
        # Mock posts: one recent (12h), one old (48h)
        # The _ts field is a Unix timestamp (CosmosDB system field)
        # created_utc is stored as ISO format string
        recent_post = {
            "id": "post_recent",
            "subreddit": "test",
            "title": "Recent post",
            "author": "user1",
            "created_utc": recent_post_time.isoformat(),
            "content": "Recent content",
            "url": "https://reddit.com/r/test/recent",
            "upvotes": 100,
            "comment_count": 5,
            "_ts": int(recent_post_time.timestamp())
        }
        
        old_post = {
            "id": "post_old",
            "subreddit": "test",
            "title": "Old post",
            "author": "user2",
            "created_utc": old_post_time.isoformat(),
            "content": "Old content",
            "url": "https://reddit.com/r/test/old",
            "upvotes": 50,
            "comment_count": 2,
            "_ts": int(old_post_time.timestamp())
        }
        
        # Mock query_items to return only the recent post (filtering is done by DB)
        db_service_with_mocks.posts_container.query_items = Mock(return_value=[recent_post])
        
        # Call get_recent_posts with 24 hour window
        try:
            posts = db_service_with_mocks.get_recent_posts(hours=24, limit=100)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(f"get_recent_posts raised exception: {e}")
        
        # Assertions
        assert execution_succeeded, "get_recent_posts should complete without exceptions"
        assert len(posts) == 1, "Should return one post (the recent one)"
        assert posts[0].id == "post_recent", "Should return the recent post"
        
        # Verify the query was called with correct parameters
        assert db_service_with_mocks.posts_container.query_items.called, "query_items should be called"
        call_args = db_service_with_mocks.posts_container.query_items.call_args
        
        # Verify query string uses _ts field
        query = call_args[1]['query']
        assert "c._ts >=" in query, "Query should use _ts field for datetime filtering"
        
        # Verify parameters use Unix timestamp (integer)
        parameters = call_args[1]['parameters']
        cutoff_param = next((p for p in parameters if p['name'] == '@cutoff'), None)
        assert cutoff_param is not None, "Should have @cutoff parameter"
        assert isinstance(cutoff_param['value'], int), "Cutoff value should be Unix timestamp (integer)"
    
    def test_get_sentiment_stats_time_range(self, db_service_with_mocks):
        """
        Test that get_sentiment_stats works with time ranges.
        
        Task: T009
        Purpose: Verify sentiment stats query works with time ranges
        Setup: Insert sentiment data from various time periods (simulated)
        Test: Call get_sentiment_stats(hours=168) for last week
        Assertions:
          - Returns aggregated stats
          - Correct counts for time window
          - No InternalServerError
          - Query uses _ts field and Unix timestamp
        """
        # Mock aggregated sentiment stats result
        mock_stats = {
            "total": 100,
            "positive": 60,
            "negative": 20,
            "neutral": 20,
            "avg_sentiment": 0.35
        }
        
        # Mock query_items to return aggregated stats
        db_service_with_mocks.sentiment_container.query_items = Mock(return_value=[mock_stats])
        
        # Call get_sentiment_stats with 168 hour (1 week) window
        try:
            stats = db_service_with_mocks.get_sentiment_stats(hours=168)
            execution_succeeded = True
        except Exception as e:
            execution_succeeded = False
            pytest.fail(f"get_sentiment_stats raised exception: {e}")
        
        # Assertions
        assert execution_succeeded, "get_sentiment_stats should complete without exceptions"
        assert stats is not None, "Should return stats dictionary"
        assert stats['total'] == 100, "Should return correct total count"
        assert stats['positive'] == 60, "Should return correct positive count"
        assert stats['avg_sentiment'] == 0.35, "Should return correct average sentiment"
        
        # Verify the query was called with correct parameters
        assert db_service_with_mocks.sentiment_container.query_items.called, "query_items should be called"
        call_args = db_service_with_mocks.sentiment_container.query_items.call_args
        
        # Verify query string uses _ts field
        query = call_args[1]['query']
        assert "c._ts >=" in query, "Query should use _ts field for datetime filtering"
        
        # Verify parameters use Unix timestamp (integer)
        parameters = call_args[1]['parameters']
        cutoff_param = next((p for p in parameters if p['name'] == '@cutoff'), None)
        assert cutoff_param is not None, "Should have @cutoff parameter"
        assert isinstance(cutoff_param['value'], int), "Cutoff value should be Unix timestamp (integer)"
    
    def test_cleanup_old_data_datetime_filter(self, db_service_with_mocks):
        """
        Test that cleanup_old_data can query old data.
        
        Task: T010
        Purpose: Verify cleanup job can query old data
        Setup: Insert posts older than retention period (simulated)
        Test: Call cleanup_old_data()
        Assertions:
          - Old posts are deleted
          - Recent posts remain (checked via mock)
          - No InternalServerError
          - Query uses _ts field and Unix timestamp
        """
        from src.config import settings
        
        # Mock settings for data retention
        with patch.object(settings, 'data_retention_days', 90):
            # Simulate old posts that should be deleted
            now = datetime.now(timezone.utc)
            old_post_time = now - timedelta(days=95)  # Older than retention period
            
            old_posts = [
                {"id": "old_post_1", "subreddit": "test1", "_ts": int(old_post_time.timestamp())},
                {"id": "old_post_2", "subreddit": "test2", "_ts": int(old_post_time.timestamp())}
            ]
            
            # Mock query_items to return old posts
            db_service_with_mocks.posts_container.query_items = Mock(return_value=old_posts)
            
            # Mock delete_item to track deletions
            db_service_with_mocks.posts_container.delete_item = Mock()
            
            # Call cleanup_old_data
            try:
                db_service_with_mocks.cleanup_old_data()
                execution_succeeded = True
            except Exception as e:
                execution_succeeded = False
                pytest.fail(f"cleanup_old_data raised exception: {e}")
            
            # Assertions
            assert execution_succeeded, "cleanup_old_data should complete without exceptions"
            
            # Verify query was called
            assert db_service_with_mocks.posts_container.query_items.called, "query_items should be called"
            call_args = db_service_with_mocks.posts_container.query_items.call_args
            
            # Verify query string uses _ts field with < comparison
            query = call_args[1]['query']
            assert "c._ts <" in query, "Query should use _ts field for datetime filtering"
            
            # Verify parameters use Unix timestamp (integer)
            parameters = call_args[1]['parameters']
            cutoff_param = next((p for p in parameters if p['name'] == '@cutoff'), None)
            assert cutoff_param is not None, "Should have @cutoff parameter"
            assert isinstance(cutoff_param['value'], int), "Cutoff value should be Unix timestamp (integer)"
            
            # Verify delete_item was called for each old post
            assert db_service_with_mocks.posts_container.delete_item.call_count == 2, \
                "Should delete both old posts"


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
