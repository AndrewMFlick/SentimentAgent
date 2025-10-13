"""Test Reddit collector."""
import pytest
from unittest.mock import Mock, patch
from src.services.reddit_collector import RedditCollector


def test_reddit_collector_init():
    """Test Reddit collector initialization."""
    with patch('praw.Reddit') as mock_reddit:
        collector = RedditCollector()
        assert collector is not None
        mock_reddit.assert_called_once()


def test_submission_to_post():
    """Test converting PRAW submission to RedditPost."""
    with patch('praw.Reddit'):
        collector = RedditCollector()
        
        # Mock submission
        mock_submission = Mock()
        mock_submission.id = "test123"
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value="testuser")
        mock_submission.title = "Test Title"
        mock_submission.selftext = "Test content"
        mock_submission.url = "https://reddit.com/test"
        mock_submission.created_utc = 1234567890
        mock_submission.score = 100
        mock_submission.num_comments = 25
        
        post = collector._submission_to_post(mock_submission, "testsubreddit")
        
        assert post.id == "test123"
        assert post.subreddit == "testsubreddit"
        assert post.author == "testuser"
        assert post.title == "Test Title"
        assert post.content == "Test content"
        assert post.upvotes == 100
        assert post.comment_count == 25


def test_comment_to_model():
    """Test converting PRAW comment to RedditComment."""
    with patch('praw.Reddit'):
        collector = RedditCollector()
        
        # Mock comment
        mock_comment = Mock()
        mock_comment.id = "comment123"
        mock_comment.parent_id = "t3_post123"  # Top-level comment
        mock_comment.author = Mock()
        mock_comment.author.__str__ = Mock(return_value="commenter")
        mock_comment.body = "Test comment"
        mock_comment.created_utc = 1234567890
        mock_comment.score = 10
        
        comment = collector._comment_to_model(mock_comment, "post123")
        
        assert comment.id == "comment123"
        assert comment.post_id == "post123"
        assert comment.parent_id is None  # Top-level comment
        assert comment.author == "commenter"
        assert comment.content == "Test comment"
        assert comment.upvotes == 10
