"""Test trending analyzer."""
import pytest
from datetime import datetime, timedelta
from src.services.trending_analyzer import TrendingAnalyzer
from src.models import RedditPost


def test_trending_analyzer_init():
    """Test trending analyzer initialization."""
    analyzer = TrendingAnalyzer()
    assert analyzer is not None


def test_calculate_engagement_velocity():
    """Test engagement velocity calculation."""
    analyzer = TrendingAnalyzer()
    
    # Create a test post
    post = RedditPost(
        id="test1",
        subreddit="test",
        author="testuser",
        title="Test Post",
        content="Test content",
        url="https://reddit.com/test",
        created_utc=datetime.utcnow() - timedelta(hours=1),
        upvotes=100,
        comment_count=20
    )
    
    velocity = analyzer._calculate_engagement_velocity(post)
    assert velocity > 0
    assert isinstance(velocity, float)


def test_extract_keywords():
    """Test keyword extraction."""
    analyzer = TrendingAnalyzer()
    
    posts = [
        RedditPost(
            id="test1",
            subreddit="test",
            author="user1",
            title="GitHub Copilot is amazing for productivity",
            content="",
            url="https://reddit.com/1",
            created_utc=datetime.utcnow(),
            upvotes=10,
            comment_count=5
        ),
        RedditPost(
            id="test2",
            subreddit="test",
            author="user2",
            title="Copilot helps with coding efficiency",
            content="",
            url="https://reddit.com/2",
            created_utc=datetime.utcnow(),
            upvotes=15,
            comment_count=3
        )
    ]
    
    keywords = analyzer._extract_keywords(posts, "productivity")
    assert len(keywords) > 0
    assert isinstance(keywords, list)
    assert all(isinstance(k, str) for k in keywords)


def test_group_by_theme():
    """Test post grouping by theme."""
    analyzer = TrendingAnalyzer()
    
    posts_with_velocity = [
        (
            RedditPost(
                id="test1",
                subreddit="test",
                author="user1",
                title="Bug in the latest version",
                content="",
                url="https://reddit.com/1",
                created_utc=datetime.utcnow(),
                upvotes=10,
                comment_count=5
            ),
            10.0
        ),
        (
            RedditPost(
                id="test2",
                subreddit="test",
                author="user2",
                title="New feature announcement",
                content="",
                url="https://reddit.com/2",
                created_utc=datetime.utcnow(),
                upvotes=20,
                comment_count=8
            ),
            15.0
        )
    ]
    
    themes = analyzer._group_by_theme(posts_with_velocity)
    assert len(themes) > 0
    assert isinstance(themes, dict)
