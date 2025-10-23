"""Unit tests for HotTopicsService.get_related_posts() method.

Tests the US2 implementation for retrieving related posts for a specific tool.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from backend.src.services.hot_topics_service import HotTopicsService
from backend.src.models.hot_topics import RelatedPostsResponse


@pytest.fixture
def mock_containers():
    """Create mock container clients for testing."""
    sentiment_scores = MagicMock()
    reddit_posts = MagicMock()
    reddit_comments = MagicMock()
    tools = MagicMock()
    
    return {
        'sentiment_scores': sentiment_scores,
        'reddit_posts': reddit_posts,
        'reddit_comments': reddit_comments,
        'tools': tools,
    }


@pytest.fixture
def hot_topics_service(mock_containers):
    """Create HotTopicsService instance with mock containers."""
    return HotTopicsService(
        sentiment_scores_container=mock_containers['sentiment_scores'],
        reddit_posts_container=mock_containers['reddit_posts'],
        reddit_comments_container=mock_containers['reddit_comments'],
        tools_container=mock_containers['tools'],
    )


@pytest.mark.asyncio
async def test_get_related_posts_empty_results(hot_topics_service, mock_containers):
    """Test get_related_posts returns empty response when no posts found."""
    # Mock empty sentiment_scores query
    mock_containers['sentiment_scores'].query_items.return_value = iter([])
    
    result = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="7d",
        offset=0,
        limit=20,
    )
    
    assert isinstance(result, RelatedPostsResponse)
    assert result.posts == []
    assert result.total == 0
    assert result.has_more is False
    assert result.offset == 0
    assert result.limit == 20


@pytest.mark.asyncio
async def test_get_related_posts_with_data(hot_topics_service, mock_containers):
    """Test get_related_posts returns properly formatted posts."""
    # Mock sentiment_scores query
    sentiment_scores_data = [
        {"content_id": "post1", "sentiment": "positive"},
        {"content_id": "post2", "sentiment": "negative"},
        {"content_id": "post3", "sentiment": "neutral"},
    ]
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    
    # Mock reddit_posts query
    reddit_posts_data = [
        {
            "id": "post1",
            "title": "Test Post 1",
            "selftext": "This is a test post with some content that should be truncated if it's too long.",
            "author": "user1",
            "subreddit": "test",
            "created_utc": 1704067200,  # 2024-01-01 00:00:00 UTC
            "num_comments": 10,
            "score": 50,
            "permalink": "/r/test/comments/post1/test_post_1",
        },
        {
            "id": "post2",
            "title": "Test Post 2",
            "selftext": "Short content",
            "author": "user2",
            "subreddit": "test",
            "created_utc": 1704153600,  # 2024-01-02 00:00:00 UTC
            "num_comments": 5,
            "score": 25,
            "permalink": "/r/test/comments/post2/test_post_2",
        },
        {
            "id": "post3",
            "title": "Test Post 3",
            "selftext": "",
            "author": "user3",
            "subreddit": "test",
            "created_utc": 1704240000,  # 2024-01-03 00:00:00 UTC
            "num_comments": 2,
            "score": 10,
            "permalink": "/r/test/comments/post3/test_post_3",
        },
    ]
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    result = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="7d",
        offset=0,
        limit=20,
    )
    
    assert isinstance(result, RelatedPostsResponse)
    assert len(result.posts) == 3
    assert result.total == 3
    assert result.has_more is False
    
    # Verify posts are sorted by engagement (comments + upvotes) DESC
    # post1: 10 + 50 = 60
    # post2: 5 + 25 = 30
    # post3: 2 + 10 = 12
    assert result.posts[0].post_id == "post1"
    assert result.posts[1].post_id == "post2"
    assert result.posts[2].post_id == "post3"
    
    # Verify first post details
    post1 = result.posts[0]
    assert post1.title == "Test Post 1"
    assert post1.author == "user1"
    assert post1.subreddit == "test"
    assert post1.comment_count == 10
    assert post1.upvotes == 50
    assert post1.engagement_score == 60
    assert post1.sentiment == "positive"
    assert post1.reddit_url == "https://reddit.com/r/test/comments/post1/test_post_1"
    assert len(post1.excerpt) <= 200


@pytest.mark.asyncio
async def test_get_related_posts_pagination(hot_topics_service, mock_containers):
    """Test get_related_posts pagination with offset and limit."""
    # Create 50 sentiment scores
    sentiment_scores_data = [
        {"content_id": f"post{i}", "sentiment": "neutral"}
        for i in range(50)
    ]
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    
    # Create 50 posts with varying engagement scores
    reddit_posts_data = [
        {
            "id": f"post{i}",
            "title": f"Test Post {i}",
            "selftext": "Test content",
            "author": "user",
            "subreddit": "test",
            "created_utc": 1704067200 + (i * 3600),
            "num_comments": 50 - i,  # Descending
            "score": i,  # Ascending
            "permalink": f"/r/test/comments/post{i}",
        }
        for i in range(50)
    ]
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    # Test first page
    result1 = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="7d",
        offset=0,
        limit=20,
    )
    
    assert len(result1.posts) == 20
    assert result1.total == 50
    assert result1.has_more is True
    assert result1.offset == 0
    assert result1.limit == 20
    
    # Test second page
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    result2 = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="7d",
        offset=20,
        limit=20,
    )
    
    assert len(result2.posts) == 20
    assert result2.total == 50
    assert result2.has_more is True
    assert result2.offset == 20
    
    # Test last page
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    result3 = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="7d",
        offset=40,
        limit=20,
    )
    
    assert len(result3.posts) == 10
    assert result3.total == 50
    assert result3.has_more is False
    assert result3.offset == 40


@pytest.mark.asyncio
async def test_get_related_posts_invalid_parameters(hot_topics_service):
    """Test get_related_posts validates parameters."""
    # Test invalid limit
    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        await hot_topics_service.get_related_posts(
            tool_id="test-tool-id",
            limit=0,
        )
    
    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        await hot_topics_service.get_related_posts(
            tool_id="test-tool-id",
            limit=101,
        )
    
    # Test invalid offset
    with pytest.raises(ValueError, match="offset must be >= 0"):
        await hot_topics_service.get_related_posts(
            tool_id="test-tool-id",
            offset=-1,
        )


@pytest.mark.asyncio
async def test_get_related_posts_time_range_filtering(hot_topics_service, mock_containers):
    """Test get_related_posts applies time range filter correctly."""
    # This test verifies that the cutoff timestamp is calculated
    # The actual filtering happens in CosmosDB query
    
    mock_containers['sentiment_scores'].query_items.return_value = iter([])
    
    # Test 24h time range
    result = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
        time_range="24h",
    )
    assert result.total == 0
    
    # Verify query was called with proper parameters
    query_calls = mock_containers['sentiment_scores'].query_items.call_args_list
    assert len(query_calls) >= 1
    
    # Check that the query includes the cutoff timestamp parameter
    last_call = query_calls[-1]
    parameters = last_call[1].get('parameters', [])
    assert any(param['name'] == '@cutoff_ts' for param in parameters)


@pytest.mark.asyncio
async def test_get_related_posts_excerpt_truncation(hot_topics_service, mock_containers):
    """Test that post excerpts are properly truncated to 150 characters."""
    long_text = "A" * 200  # 200 characters
    
    sentiment_scores_data = [
        {"content_id": "post1", "sentiment": "positive"},
    ]
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    
    reddit_posts_data = [
        {
            "id": "post1",
            "title": "Test Post",
            "selftext": long_text,
            "author": "user1",
            "subreddit": "test",
            "created_utc": 1704067200,
            "num_comments": 10,
            "score": 50,
            "permalink": "/r/test/comments/post1",
        },
    ]
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    result = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
    )
    
    assert len(result.posts) == 1
    post = result.posts[0]
    assert len(post.excerpt) <= 153  # 150 + "..."
    assert post.excerpt.endswith("...")


@pytest.mark.asyncio
async def test_get_related_posts_reddit_url_generation(hot_topics_service, mock_containers):
    """Test that Reddit URLs are generated correctly."""
    sentiment_scores_data = [
        {"content_id": "post1", "sentiment": "positive"},
    ]
    mock_containers['sentiment_scores'].query_items.return_value = iter(sentiment_scores_data)
    
    reddit_posts_data = [
        {
            "id": "post1",
            "title": "Test Post",
            "selftext": "Content",
            "author": "user1",
            "subreddit": "programming",
            "created_utc": 1704067200,
            "num_comments": 10,
            "score": 50,
            "permalink": "/r/programming/comments/abc123/test_post",
        },
    ]
    mock_containers['reddit_posts'].query_items.return_value = iter(reddit_posts_data)
    
    result = await hot_topics_service.get_related_posts(
        tool_id="test-tool-id",
    )
    
    assert len(result.posts) == 1
    post = result.posts[0]
    assert post.reddit_url == "https://reddit.com/r/programming/comments/abc123/test_post"
    assert post.reddit_url.startswith("https://reddit.com")
