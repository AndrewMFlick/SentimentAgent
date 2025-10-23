"""Integration tests for Hot Topics API endpoints.

Tests for Feature #012: Hot Topics
Tests API endpoints for hot topics dashboard and related posts.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from src.main import app
from src.models.hot_topics import (
    HotTopic,
    HotTopicsResponse,
    RelatedPost,
    RelatedPostsResponse,
    SentimentDistribution,
)


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestHotTopicsEndpoint:
    """Integration tests for GET /api/hot-topics endpoint."""
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_returns_200(self, client):
        """
        Test GET /api/hot-topics returns 200 OK with valid data structure.
        
        Task: T018 (tests T011 implementation)
        Purpose: Verify endpoint registration and basic functionality
        Setup: Mock HotTopicsService to return sample data
        Test: GET /api/hot-topics
        Assertions:
          - Status code 200
          - Response contains hot_topics array
          - Response contains generated_at timestamp
          - Response contains time_range field
        """
        # Mock the service
        mock_response = HotTopicsResponse(
            hot_topics=[
                HotTopic(
                    tool_id="github-copilot",
                    tool_name="GitHub Copilot",
                    tool_slug="github-copilot",
                    engagement_score=500,
                    total_mentions=25,
                    total_comments=100,
                    total_upvotes=300,
                    sentiment_distribution=SentimentDistribution(
                        positive_count=15,
                        negative_count=5,
                        neutral_count=5,
                        positive_percent=60.0,
                        negative_percent=20.0,
                        neutral_percent=20.0,
                    )
                )
            ],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "hot_topics" in data
            assert "generated_at" in data
            assert "time_range" in data
            assert data["time_range"] == "7d"
            assert len(data["hot_topics"]) == 1
            assert data["hot_topics"][0]["tool_id"] == "github-copilot"
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_default_parameters(self, client):
        """
        Test GET /api/hot-topics uses default parameters when not specified.
        
        Task: T018
        Purpose: Verify default time_range=7d and limit=10
        """
        mock_response = HotTopicsResponse(
            hot_topics=[],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_service:
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 200
            # Verify service was called with defaults
            mock_service.assert_called_once_with(time_range="7d", limit=10)
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_time_range_24h(self, client):
        """
        Test GET /api/hot-topics with time_range=24h parameter.
        
        Task: T018
        Purpose: Verify time range filtering (24 hours)
        """
        mock_response = HotTopicsResponse(
            hot_topics=[],
            generated_at=datetime.now(timezone.utc),
            time_range="24h"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_service:
            response = client.get("/api/hot-topics?time_range=24h")
            
            assert response.status_code == 200
            data = response.json()
            assert data["time_range"] == "24h"
            mock_service.assert_called_once_with(time_range="24h", limit=10)
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_time_range_30d(self, client):
        """
        Test GET /api/hot-topics with time_range=30d parameter.
        
        Task: T018
        Purpose: Verify time range filtering (30 days)
        """
        mock_response = HotTopicsResponse(
            hot_topics=[],
            generated_at=datetime.now(timezone.utc),
            time_range="30d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_service:
            response = client.get("/api/hot-topics?time_range=30d")
            
            assert response.status_code == 200
            data = response.json()
            assert data["time_range"] == "30d"
            mock_service.assert_called_once_with(time_range="30d", limit=10)
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_custom_limit(self, client):
        """
        Test GET /api/hot-topics with custom limit parameter.
        
        Task: T018
        Purpose: Verify limit parameter (max 50)
        """
        mock_response = HotTopicsResponse(
            hot_topics=[],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ) as mock_service:
            response = client.get("/api/hot-topics?limit=20")
            
            assert response.status_code == 200
            mock_service.assert_called_once_with(time_range="7d", limit=20)
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_invalid_time_range(self, client):
        """
        Test GET /api/hot-topics returns 400 for invalid time_range.
        
        Task: T018
        Purpose: Verify error handling for invalid time_range
        """
        response = client.get("/api/hot-topics?time_range=invalid")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "time_range" in data["detail"].lower()
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_invalid_limit_too_high(self, client):
        """
        Test GET /api/hot-topics returns 400 for limit > 50.
        
        Task: T018
        Purpose: Verify limit validation
        """
        response = client.get("/api/hot-topics?limit=51")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "limit" in data["detail"].lower()
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_invalid_limit_too_low(self, client):
        """
        Test GET /api/hot-topics returns 400 for limit < 1.
        
        Task: T018
        Purpose: Verify limit validation
        """
        response = client.get("/api/hot-topics?limit=0")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_engagement_sorting(self, client):
        """
        Test GET /api/hot-topics returns tools sorted by engagement_score DESC.
        
        Task: T018
        Purpose: Verify hot topics are ranked by engagement
        """
        mock_response = HotTopicsResponse(
            hot_topics=[
                HotTopic(
                    tool_id="tool-1",
                    tool_name="High Engagement Tool",
                    tool_slug="high-engagement",
                    engagement_score=1000,
                    total_mentions=50,
                    total_comments=200,
                    total_upvotes=500,
                    sentiment_distribution=SentimentDistribution(
                        positive_count=40,
                        negative_count=5,
                        neutral_count=5,
                        positive_percent=80.0,
                        negative_percent=10.0,
                        neutral_percent=10.0,
                    )
                ),
                HotTopic(
                    tool_id="tool-2",
                    tool_name="Medium Engagement Tool",
                    tool_slug="medium-engagement",
                    engagement_score=500,
                    total_mentions=25,
                    total_comments=100,
                    total_upvotes=250,
                    sentiment_distribution=SentimentDistribution(
                        positive_count=15,
                        negative_count=5,
                        neutral_count=5,
                        positive_percent=60.0,
                        negative_percent=20.0,
                        neutral_percent=20.0,
                    )
                ),
            ],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify sorting: first tool has higher engagement than second
            assert data["hot_topics"][0]["engagement_score"] > data["hot_topics"][1]["engagement_score"]
            assert data["hot_topics"][0]["engagement_score"] == 1000
            assert data["hot_topics"][1]["engagement_score"] == 500
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_minimum_mentions_threshold(self, client):
        """
        Test GET /api/hot-topics excludes tools with < 3 mentions.
        
        Task: T018
        Purpose: Verify minimum engagement threshold filtering
        Setup: Mock service to return tools above threshold only
        Test: GET /api/hot-topics
        Assertions:
          - All returned tools have total_mentions >= 3
        """
        mock_response = HotTopicsResponse(
            hot_topics=[
                HotTopic(
                    tool_id="tool-1",
                    tool_name="Above Threshold",
                    tool_slug="above-threshold",
                    engagement_score=100,
                    total_mentions=5,  # Above threshold
                    total_comments=20,
                    total_upvotes=50,
                    sentiment_distribution=SentimentDistribution(
                        positive_count=3,
                        negative_count=1,
                        neutral_count=1,
                        positive_percent=60.0,
                        negative_percent=20.0,
                        neutral_percent=20.0,
                    )
                ),
            ],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all tools meet minimum threshold
            for topic in data["hot_topics"]:
                assert topic["total_mentions"] >= 3
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_empty_results(self, client):
        """
        Test GET /api/hot-topics returns empty array when no hot topics.
        
        Task: T018
        Purpose: Verify handling of no results scenario
        """
        mock_response = HotTopicsResponse(
            hot_topics=[],
            generated_at=datetime.now(timezone.utc),
            time_range="7d"
        )
        
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["hot_topics"] == []
            assert "generated_at" in data
    
    @pytest.mark.skip(reason="API endpoint not yet implemented - Phase 3 (T011)")
    def test_get_hot_topics_server_error(self, client):
        """
        Test GET /api/hot-topics returns 500 on server error.
        
        Task: T018
        Purpose: Verify error handling for unexpected errors
        """
        with patch(
            'src.services.hot_topics_service.HotTopicsService.get_hot_topics',
            new_callable=AsyncMock,
            side_effect=Exception("Database error")
        ):
            response = client.get("/api/hot-topics")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestRelatedPostsEndpoint:
    """Integration tests for GET /api/hot-topics/{tool_id}/posts endpoint."""
    
    def test_get_related_posts_returns_200(self, client):
        """
        Test GET /api/hot-topics/{tool_id}/posts returns 200 OK.
        
        Task: T030 (tests T023 implementation for Phase 4/US2)
        Purpose: Verify endpoint registration and basic functionality
        """
        mock_response = RelatedPostsResponse(
            posts=[
                RelatedPost(
                    post_id="abc123",
                    title="Test Post",
                    excerpt="This is a test post about the tool...",
                    author="test_user",
                    subreddit="programming",
                    created_utc=datetime.now(timezone.utc),
                    reddit_url="https://reddit.com/r/programming/comments/abc123",
                    comment_count=10,
                    upvotes=50,
                    sentiment="positive",
                    engagement_score=60
                )
            ],
            total=1,
            has_more=False,
            offset=0,
            limit=20
        )
        
        # Patch the tool query in the database module
        with patch('src.services.database.db.database.get_container_client') as mock_get_container, \
             patch('src.services.hot_topics_service.HotTopicsService.get_related_posts', new_callable=AsyncMock, return_value=mock_response):
            
            # Set up mock container
            mock_container = Mock()
            mock_container.query_items.return_value = [{"id": "test-tool", "name": "Test Tool"}]
            mock_get_container.return_value = mock_container
            
            response = client.get("/api/hot-topics/test-tool/posts")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "posts" in data
            assert "total" in data
            assert "has_more" in data
            assert "offset" in data
            assert "limit" in data
    
    def test_get_related_posts_pagination(self, client):
        """
        Test GET /api/hot-topics/{tool_id}/posts pagination with offset and limit.
        
        Task: T030
        Purpose: Verify pagination parameters work correctly
        """
        mock_response = RelatedPostsResponse(
            posts=[],
            total=50,
            has_more=True,
            offset=20,
            limit=20
        )
        
        with patch('src.services.database.db.database.get_container_client') as mock_get_container, \
             patch('src.services.hot_topics_service.HotTopicsService.get_related_posts', new_callable=AsyncMock, return_value=mock_response) as mock_service:
            
            mock_container = Mock()
            mock_container.query_items.return_value = [{"id": "test-tool"}]
            mock_get_container.return_value = mock_container
            
            response = client.get("/api/hot-topics/test-tool/posts?offset=20&limit=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["offset"] == 20
            assert data["limit"] == 20
            assert data["has_more"] is True
            
            # Verify service was called with correct parameters
            mock_service.assert_called_once_with(
                tool_id="test-tool",
                time_range="7d",
                offset=20,
                limit=20
            )
    
    def test_get_related_posts_time_range_filter(self, client):
        """
        Test GET /api/hot-topics/{tool_id}/posts with time_range filter.
        
        Task: T030
        Purpose: Verify time range filtering for related posts
        """
        mock_response = RelatedPostsResponse(
            posts=[],
            total=0,
            has_more=False,
            offset=0,
            limit=20
        )
        
        with patch('src.services.database.db.database.get_container_client') as mock_get_container, \
             patch('src.services.hot_topics_service.HotTopicsService.get_related_posts', new_callable=AsyncMock, return_value=mock_response) as mock_service:
            
            mock_container = Mock()
            mock_container.query_items.return_value = [{"id": "test-tool"}]
            mock_get_container.return_value = mock_container
            
            response = client.get("/api/hot-topics/test-tool/posts?time_range=24h")
            
            assert response.status_code == 200
            mock_service.assert_called_once_with(
                tool_id="test-tool",
                time_range="24h",
                offset=0,
                limit=20
            )
    
    def test_get_related_posts_tool_not_found(self, client):
        """
        Test GET /api/hot-topics/{tool_id}/posts returns 404 for invalid tool.
        
        Task: T030
        Purpose: Verify error handling for non-existent tool
        """
        with patch('src.services.database.db.database.get_container_client') as mock_get_container:
            mock_container = Mock()
            mock_container.query_items.return_value = []  # Empty result = tool not found
            mock_get_container.return_value = mock_container
            
            response = client.get("/api/hot-topics/nonexistent-tool/posts")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()
    
    def test_get_related_posts_reddit_url_format(self, client):
        """
        Test GET /api/hot-topics/{tool_id}/posts validates Reddit URL format.
        
        Task: T030
        Purpose: Verify Reddit URLs are correctly formatted
        """
        mock_response = RelatedPostsResponse(
            posts=[
                RelatedPost(
                    post_id="abc123",
                    title="Test Post",
                    excerpt="Test excerpt",
                    author="test_user",
                    subreddit="programming",
                    created_utc=datetime.now(timezone.utc),
                    reddit_url="https://reddit.com/r/programming/comments/abc123",
                    comment_count=10,
                    upvotes=50,
                    sentiment="positive",
                    engagement_score=60
                )
            ],
            total=1,
            has_more=False,
            offset=0,
            limit=20
        )
        
        with patch('src.services.database.db.database.get_container_client') as mock_get_container, \
             patch('src.services.hot_topics_service.HotTopicsService.get_related_posts', new_callable=AsyncMock, return_value=mock_response):
            
            mock_container = Mock()
            mock_container.query_items.return_value = [{"id": "test-tool"}]
            mock_get_container.return_value = mock_container
            
            response = client.get("/api/hot-topics/test-tool/posts")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify Reddit URL format
            for post in data["posts"]:
                assert post["reddit_url"].startswith("https://reddit.com/r/")
                assert "/comments/" in post["reddit_url"]
