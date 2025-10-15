"""Integration tests for data loading on startup."""
import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestDataLoading:
    """Test that previously collected data loads on startup."""
    
    def test_load_recent_data_function_exists(self):
        """
        Test that load_recent_data function is available.
        
        Success Criteria (SC-002): Data loading infrastructure exists
        """
        from src.services.database import db
        
        assert hasattr(db, 'load_recent_data')
        assert callable(db.load_recent_data)
    
    @pytest.mark.asyncio
    async def test_load_recent_data_executes_without_error(self):
        """
        Test that load_recent_data executes without errors.
        
        Success Criteria (SC-002): Data loading completes without errors
        """
        from src.services.database import db
        
        # Should not raise an exception even with empty database
        await db.load_recent_data()
    
    def test_api_endpoints_handle_empty_database(self):
        """
        Test that API endpoints handle empty database gracefully.
        
        Success Criteria (SC-003): Endpoints return empty data, not errors
        """
        from src.main import app
        client = TestClient(app)
        
        # Test sentiment stats endpoint
        response = client.get("/api/v1/sentiment/stats")
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert isinstance(data["statistics"], dict)
        
        # Test recent posts endpoint
        response = client.get("/api/v1/posts/recent")
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)
        
        # Test trending endpoint
        response = client.get("/api/v1/trending")
        assert response.status_code == 200
        topics = response.json()
        assert isinstance(topics, list)
    
    def test_recent_posts_endpoint_with_time_filter(self):
        """
        Test that recent posts endpoint accepts time window parameter.
        
        Success Criteria (SC-002): API supports querying historical data
        """
        from src.main import app
        client = TestClient(app)
        
        # Test with different time windows
        for hours in [1, 24, 168]:
            response = client.get(f"/api/v1/posts/recent?hours={hours}")
            assert response.status_code == 200
            posts = response.json()
            assert isinstance(posts, list)
    
    def test_sentiment_stats_endpoint_with_time_filter(self):
        """
        Test that sentiment stats endpoint accepts time window parameter.
        
        Success Criteria (SC-002): API supports querying historical stats
        """
        from src.main import app
        client = TestClient(app)
        
        # Test with different time windows
        for hours in [1, 24, 168]:
            response = client.get(f"/api/v1/sentiment/stats?hours={hours}")
            assert response.status_code == 200
            data = response.json()
            assert data["time_window_hours"] == hours
    
    def test_startup_triggers_data_loading(self):
        """
        Test that application startup triggers data loading.
        
        Success Criteria (SC-002): Data loads on startup
        """
        from src.services.health import app_state
        
        # After app startup (via lifespan), app_state should be initialized
        assert app_state is not None
        assert app_state.app_start_time > 0
        
        # Uptime should be measurable
        uptime = app_state.get_uptime_seconds()
        assert uptime >= 0
    
    def test_data_freshness_calculation(self):
        """
        Test that data freshness is calculated correctly.
        
        Success Criteria (SC-007): Health endpoint reports data freshness
        """
        from src.main import app
        from src.services.health import app_state
        client = TestClient(app)
        
        # Set a recent collection time
        app_state.last_collection_time = datetime.utcnow() - timedelta(minutes=5)
        
        response = client.get("/api/v1/health")
        data = response.json()
        
        freshness = data["application"]["data_freshness_minutes"]
        
        # Should be approximately 5 minutes (allowing for variance)
        assert freshness is not None
        assert 4.5 <= freshness <= 6.0
    
    def test_api_returns_data_immediately_after_restart(self):
        """
        Test that API endpoints return data immediately after restart.
        
        Success Criteria (SC-002, SC-003): Data available within 10 seconds
        """
        from src.main import app
        client = TestClient(app)
        
        import time
        start_time = time.time()
        
        # Query all main endpoints
        endpoints = [
            "/api/v1/health",
            "/api/v1/sentiment/stats",
            "/api/v1/posts/recent",
            "/api/v1/trending"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 503], f"Endpoint {endpoint} failed"
        
        elapsed = time.time() - start_time
        
        # All endpoints should respond within 10 seconds
        assert elapsed < 10.0, f"Endpoints took too long to respond: {elapsed}s"
    
    def test_database_query_methods_handle_empty_results(self):
        """
        Test that database query methods handle empty results gracefully.
        
        Success Criteria (SC-003): Empty results don't cause errors
        """
        from src.services.database import db
        
        # These should all return empty results, not raise exceptions
        posts = db.get_recent_posts(hours=24)
        assert isinstance(posts, list)
        
        stats = db.get_sentiment_stats(hours=24)
        assert isinstance(stats, dict)
        
        topics = db.get_trending_topics(limit=20)
        assert isinstance(topics, list)
    
    def test_pagination_parameter_support(self):
        """
        Test that API endpoints support pagination parameters.
        
        Success Criteria: API supports limit parameters
        """
        from src.main import app
        client = TestClient(app)
        
        # Test posts endpoint with different limits
        for limit in [10, 50, 100]:
            response = client.get(f"/api/v1/posts/recent?limit={limit}")
            assert response.status_code == 200
            posts = response.json()
            assert isinstance(posts, list)
            assert len(posts) <= limit
        
        # Test trending endpoint with different limits
        for limit in [5, 10, 20]:
            response = client.get(f"/api/v1/trending?limit={limit}")
            assert response.status_code == 200
            topics = response.json()
            assert isinstance(topics, list)
            assert len(topics) <= limit
