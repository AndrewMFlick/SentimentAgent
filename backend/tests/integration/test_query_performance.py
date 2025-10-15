"""Integration tests for query performance."""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestQueryPerformance:
    """Test query performance under various conditions."""
    
    def test_health_endpoint_response_time(self):
        """
        Test that health endpoint responds quickly.
        
        Performance Requirement (PR-001): Health check < 1s
        """
        from src.main import app
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/api/v1/health")
        elapsed = time.time() - start_time
        
        assert response.status_code in [200, 503]
        assert elapsed < 1.0, f"Health check took {elapsed}s, expected < 1s"
    
    def test_sentiment_stats_response_time(self):
        """
        Test that sentiment stats endpoint responds within threshold.
        
        Performance Requirement (PR-002): Stats endpoint < 3s
        """
        from src.main import app
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/api/v1/sentiment/stats?hours=24")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 3.0, f"Stats endpoint took {elapsed}s, expected < 3s"
    
    def test_posts_recent_response_time(self):
        """
        Test that recent posts endpoint responds within threshold.
        
        Performance Requirement (PR-003): Posts endpoint < 2s
        """
        from src.main import app
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/api/v1/posts/recent?hours=24&limit=100")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Posts endpoint took {elapsed}s, expected < 2s"
    
    def test_trending_response_time(self):
        """
        Test that trending endpoint responds within threshold.
        
        Performance Requirement (PR-004): Trending endpoint < 5s
        """
        from src.main import app
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/api/v1/trending?limit=20")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"Trending endpoint took {elapsed}s, expected < 5s"
    
    def test_concurrent_health_requests(self):
        """
        Test concurrent health check requests.
        
        Performance Requirement (PR-006): Handle concurrent requests
        """
        from src.main import app
        client = TestClient(app)
        
        def make_health_request():
            response = client.get("/api/v1/health")
            return response.status_code
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_health_request) for _ in range(10)]
            results = [f.result() for f in futures]
            elapsed = time.time() - start_time
        
        # All requests should succeed
        assert all(status in [200, 503] for status in results)
        
        # Should complete within reasonable time (10 requests in < 5s)
        assert elapsed < 5.0, f"Concurrent requests took {elapsed}s"
    
    def test_concurrent_api_requests_mixed(self):
        """
        Test concurrent mixed API requests.
        
        Performance Requirement (PR-006): Handle 50 concurrent requests
        Success Criteria (SC-005): Endpoints respond within thresholds
        """
        from src.main import app
        client = TestClient(app)
        
        def make_api_request(endpoint):
            start = time.time()
            response = client.get(f"/api/v1{endpoint}")
            elapsed = time.time() - start
            return response.status_code, elapsed
        
        # Mix of different endpoints
        endpoints = [
            "/health",
            "/sentiment/stats",
            "/posts/recent?limit=10",
            "/trending?limit=5",
        ] * 5  # 20 total requests
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            start_time = time.time()
            futures = [executor.submit(make_api_request, ep) for ep in endpoints]
            results = [f.result() for f in futures]
            total_elapsed = time.time() - start_time
        
        # All requests should succeed
        status_codes = [status for status, _ in results]
        assert all(status in [200, 503] for status in status_codes)
        
        # All should complete within 10 seconds total
        assert total_elapsed < 10.0, f"Concurrent requests took {total_elapsed}s"
        
        # Individual requests should be within thresholds
        response_times = [elapsed for _, elapsed in results]
        max_response_time = max(response_times)
        assert max_response_time < 5.0, f"Slowest request took {max_response_time}s"
    
    def test_database_query_with_time_filters(self):
        """
        Test that database queries use time window filters efficiently.
        
        Success Criteria (SC-005): Queries use time window filters
        """
        from src.main import app
        client = TestClient(app)
        
        # Query with different time windows
        time_windows = [1, 24, 168]  # 1 hour, 1 day, 1 week
        
        for hours in time_windows:
            start_time = time.time()
            response = client.get(f"/api/v1/posts/recent?hours={hours}")
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            
            # Even with larger time windows, should respond quickly
            assert elapsed < 3.0, f"Query with {hours}h window took {elapsed}s"
    
    def test_pagination_limits_result_size(self):
        """
        Test that pagination limits prevent large result sets.
        
        Success Criteria: Pagination controls query performance
        """
        from src.main import app
        client = TestClient(app)
        
        # Test with different limits
        for limit in [10, 50, 100, 500]:
            start_time = time.time()
            response = client.get(f"/api/v1/posts/recent?limit={limit}")
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            posts = response.json()
            
            # Result size should not exceed limit
            assert len(posts) <= limit
            
            # Should still be fast even with max limit
            assert elapsed < 3.0, f"Query with limit={limit} took {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_database_connection_check_performance(self):
        """
        Test that database connection check is fast.
        
        Performance: Connection check should be < 1s
        """
        from src.services.database import db
        
        start_time = time.time()
        is_connected = await db.is_connected()
        elapsed = time.time() - start_time
        
        assert isinstance(is_connected, bool)
        assert elapsed < 1.0, f"Connection check took {elapsed}s"
    
    def test_memory_usage_during_queries(self):
        """
        Test that memory usage remains reasonable during queries.
        
        Performance Requirement (PR-005): Memory < 512MB
        """
        from src.main import app
        import psutil
        import os
        client = TestClient(app)
        
        process = psutil.Process(os.getpid())
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Make multiple queries
        for _ in range(10):
            client.get("/api/v1/sentiment/stats")
            client.get("/api/v1/posts/recent?limit=100")
            client.get("/api/v1/trending")
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Memory should not increase significantly
        memory_increase = final_memory - initial_memory
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB during queries"
        
        # Total memory should be reasonable
        assert final_memory < 512, f"Memory usage {final_memory}MB exceeds 512MB threshold"
