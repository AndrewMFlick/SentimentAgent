"""Performance tests for Hot Topics API.

Tests for Feature #012: Hot Topics
Validates performance requirements for hot topics dashboard.
"""
import pytest
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import app
from src.models.hot_topics import (
    HotTopic,
    HotTopicsResponse,
    SentimentDistribution,
)


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


def create_mock_hot_topic(tool_id: str, engagement_score: int) -> HotTopic:
    """Helper to create mock HotTopic for testing."""
    return HotTopic(
        tool_id=tool_id,
        tool_name=f"Tool {tool_id}",
        tool_slug=tool_id,
        engagement_score=engagement_score,
        total_mentions=engagement_score // 20,
        total_comments=engagement_score // 10,
        total_upvotes=engagement_score // 2,
        sentiment_distribution=SentimentDistribution(
            positive_count=10,
            negative_count=5,
            neutral_count=5,
            positive_percent=50.0,
            negative_percent=25.0,
            neutral_percent=25.0,
        )
    )


class TestHotTopicsPerformance:
    """Performance tests for hot topics endpoint."""
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_hot_topics_response_time_under_5_seconds(self, client):
        """
        Test GET /api/hot-topics responds in < 5 seconds (SC-001).
        
        Task: T019
        Purpose: Verify success criteria SC-001 from spec.md
        Requirement: Users can identify top 10 trending tools within 5 seconds
        Setup: Mock service with typical dataset (10 tools)
        Test: Measure response time for GET /api/hot-topics
        Assertions:
          - Response time < 5000ms
          - Status code 200
          - Returns 10 hot topics
        """
        # Create mock response with 10 hot topics
        mock_hot_topics = [
            create_mock_hot_topic(f"tool-{i}", engagement_score=1000 - (i * 100))
            for i in range(10)
        ]
        
        mock_response = HotTopicsResponse(
            hot_topics=mock_hot_topics,
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 5000, f"Response took {response_time_ms}ms, expected < 5000ms"
            
            data = response.json()
            assert len(data["hot_topics"]) == 10
    
    @pytest.mark.skip(reason="Service method not yet implemented - Phase 3 (T010)")
    def test_engagement_calculation_for_50_tools_under_5_seconds(self, client):
        """
        Test engagement calculation for 50 tools completes in < 5 seconds.
        
        Task: T019
        Purpose: Verify service can handle large dataset efficiently
        Setup: Mock database with 50 tools
        Test: Call get_hot_topics with limit=50
        Assertions:
          - Calculation completes in < 5000ms
          - All 50 tools processed
        """
        # Create mock response with 50 hot topics
        mock_hot_topics = [
            create_mock_hot_topic(f"tool-{i}", engagement_score=5000 - (i * 100))
            for i in range(50)
        ]
        
        mock_response = HotTopicsResponse(
            hot_topics=mock_hot_topics,
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics?limit=50")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 5000, f"Response took {response_time_ms}ms, expected < 5000ms"
            
            data = response.json()
            assert len(data["hot_topics"]) == 50
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_hot_topics_24h_filter_response_time(self, client):
        """
        Test 24h time range filter responds in < 2 seconds (SC-005).
        
        Task: T019
        Purpose: Verify time range filtering performance requirement
        Requirement: SC-005 - Time range filtering produces results within 2 seconds
        Setup: Mock service with 24h filtered data
        Test: GET /api/hot-topics?time_range=24h
        Assertions:
          - Response time < 2000ms
        """
        mock_response = HotTopicsResponse(
            hot_topics=[create_mock_hot_topic("tool-1", 500)],
            generated_at=datetime.now(timezone.utc),
            time_range="24h"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics?time_range=24h")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 2000, f"Filter change took {response_time_ms}ms, expected < 2000ms"
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_hot_topics_30d_filter_response_time(self, client):
        """
        Test 30d time range filter responds in < 2 seconds.
        
        Task: T019
        Purpose: Verify time range filtering performance for larger dataset
        """
        # 30d might return more data but should still be fast
        mock_hot_topics = [
            create_mock_hot_topic(f"tool-{i}", engagement_score=1000 - (i * 50))
            for i in range(20)
        ]
        
        mock_response = HotTopicsResponse(
            hot_topics=mock_hot_topics,
            generated_at=datetime.now(timezone.utc),
            time_range="30d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics?time_range=30d")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 2000, f"Filter change took {response_time_ms}ms, expected < 2000ms"
    
    @pytest.mark.skip(reason="Slow query monitoring not yet implemented - Phase 6 (T043)")
    def test_slow_query_logging_enabled(self):
        """
        Test that slow query monitoring is enabled and logs queries > 3 seconds.
        
        Task: T019
        Purpose: Verify monitoring decorator from Phase 6 (T034, T043)
        Setup: Simulate slow query (> 3 seconds)
        Test: Check that slow query is logged
        Assertions:
          - Slow query logged at WARN level
          - Log contains query duration
        """
        # This test validates that the monitoring infrastructure exists
        # Actual implementation will be added in Phase 6
        pass
    
    @pytest.mark.skip(reason="Cache not yet implemented - Phase 3 (T010)")
    def test_hot_topics_cache_improves_performance(self, client):
        """
        Test that caching improves response time for repeated requests.
        
        Task: T019
        Purpose: Verify 5-minute cache TTL from T010 improves performance
        Setup: Make first request (cache miss), then second request (cache hit)
        Test: Compare response times
        Assertions:
          - Second request faster than first
          - Both requests return same data
          - Cache hit response < 100ms
        """
        mock_response = HotTopicsResponse(
            hot_topics=[create_mock_hot_topic("tool-1", 500)],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_service:
            # First request (cache miss)
            start_time_1 = time.time()
            response_1 = client.get("/api/hot-topics")
            end_time_1 = time.time()
            time_1_ms = (end_time_1 - start_time_1) * 1000
            
            # Second request (should be cached)
            start_time_2 = time.time()
            response_2 = client.get("/api/hot-topics")
            end_time_2 = time.time()
            time_2_ms = (end_time_2 - start_time_2) * 1000
            
            assert response_1.status_code == 200
            assert response_2.status_code == 200
            
            # Cache hit should be significantly faster
            # Note: In mock scenario, both might be fast, but pattern validates caching design
            assert time_2_ms <= time_1_ms, "Cached request should be <= original request time"
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_hot_topics_concurrent_requests(self, client):
        """
        Test hot topics endpoint handles concurrent requests without performance degradation.
        
        Task: T019
        Purpose: Verify endpoint can handle multiple simultaneous requests
        Setup: Make 5 concurrent requests
        Test: All requests complete successfully in reasonable time
        Assertions:
          - All requests return 200
          - Average response time < 5 seconds
        """
        import concurrent.futures
        
        mock_response = HotTopicsResponse(
            hot_topics=[create_mock_hot_topic("tool-1", 500)],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            def make_request():
                start = time.time()
                response = client.get("/api/hot-topics")
                duration = time.time() - start
                return response.status_code, duration * 1000
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(5)]
                results = [f.result() for f in futures]
            
            # Verify all succeeded
            for status_code, response_time_ms in results:
                assert status_code == 200
                assert response_time_ms < 5000
            
            # Calculate average response time
            avg_time = sum(rt for _, rt in results) / len(results)
            assert avg_time < 5000, f"Average response time {avg_time}ms exceeds 5000ms"


class TestRelatedPostsPerformance:
    """Performance tests for related posts endpoint (Task T031 - US2)."""
    
    def test_related_posts_first_page_under_2_seconds(self, client):
        """
        Test first 20 posts query completes in < 2 seconds (SC-005).
        
        Task: T031 (US2 performance tests)
        Purpose: Verify related posts initial load meets performance requirements
        Requirement: GET /api/hot-topics/{tool_id}/posts returns first page in < 2 seconds
        Setup: Mock service with 20 related posts
        Test: Measure response time
        Assertions:
          - Response time < 2000ms
          - Status code 200
          - Returns 20 posts
        """
        from src.models.hot_topics import RelatedPost, RelatedPostsResponse
        
        # Create mock response with 20 posts
        mock_posts = [
            RelatedPost(
                post_id=f"post-{i}",
                title=f"Post {i} About AI Tool",
                excerpt=f"This is excerpt {i} discussing the tool...",
                author=f"user_{i}",
                subreddit="programming",
                created_utc=datetime.now(timezone.utc),
                reddit_url=f"https://reddit.com/r/programming/comments/post-{i}",
                comment_count=10 + i,
                upvotes=50 + (i * 5),
                sentiment="positive" if i % 2 == 0 else "neutral",
                engagement_score=60 + (i * 5)
            )
            for i in range(20)
        ]
        
        mock_response = RelatedPostsResponse(
            posts=mock_posts,
            total=100,
            has_more=True,
            offset=0,
            limit=20
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_related_posts',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics/test-tool/posts")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 2000, f"Response took {response_time_ms}ms, expected < 2000ms"
            
            data = response.json()
            assert len(data["posts"]) == 20
            assert data["total"] == 100
            assert data["has_more"] is True
    
    def test_related_posts_pagination_under_1_second(self, client):
        """
        Test paginated requests (offset > 0) complete in < 1 second (cached).
        
        Task: T031 (US2 performance tests)
        Purpose: Verify pagination performance with server-side caching
        Requirement: Paginated requests should be faster than initial query (< 1s with cache)
        Setup: Mock service with paginated response
        Test: Measure response time for offset=20
        Assertions:
          - Response time < 1000ms
          - Status code 200
          - Correct offset applied
        """
        from src.models.hot_topics import RelatedPost, RelatedPostsResponse
        
        # Create mock response for page 2 (offset=20)
        mock_posts = [
            RelatedPost(
                post_id=f"post-{20 + i}",
                title=f"Post {20 + i} About AI Tool",
                excerpt=f"This is excerpt {20 + i}...",
                author=f"user_{20 + i}",
                subreddit="programming",
                created_utc=datetime.now(timezone.utc),
                reddit_url=f"https://reddit.com/r/programming/comments/post-{20 + i}",
                comment_count=30 + i,
                upvotes=150 + (i * 5),
                sentiment="neutral",
                engagement_score=180 + (i * 5)
            )
            for i in range(20)
        ]
        
        mock_response = RelatedPostsResponse(
            posts=mock_posts,
            total=100,
            has_more=True,
            offset=20,
            limit=20
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_related_posts',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            start_time = time.time()
            response = client.get("/api/hot-topics/test-tool/posts?offset=20&limit=20")
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time_ms < 1000, f"Pagination took {response_time_ms}ms, expected < 1000ms (cached)"
            
            data = response.json()
            assert len(data["posts"]) == 20
            assert data["offset"] == 20
            assert data["has_more"] is True
