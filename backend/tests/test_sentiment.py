"""Test configuration and sentiment analysis."""
import pytest
from src.config import settings
from src.services.sentiment_analyzer import SentimentAnalyzer


def test_settings_load():
    """Test that settings load correctly."""
    assert settings.reddit_client_id is not None
    assert settings.cosmos_endpoint is not None
    assert len(settings.subreddit_list) > 0


def test_sentiment_analyzer_initialization():
    """Test sentiment analyzer initializes."""
    analyzer = SentimentAnalyzer()
    assert analyzer.vader is not None


def test_vader_sentiment_positive():
    """Test VADER sentiment analysis with positive text."""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        content_id="test1",
        content_type="post",
        subreddit="test",
        text="This is amazing! I love this tool, it works great!"
    )
    
    assert result.sentiment == "positive"
    assert result.analysis_method == "VADER"
    assert result.compound_score > 0


def test_vader_sentiment_negative():
    """Test VADER sentiment analysis with negative text."""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        content_id="test2",
        content_type="post",
        subreddit="test",
        text="This is terrible! I hate it, doesn't work at all."
    )
    
    assert result.sentiment == "negative"
    assert result.analysis_method == "VADER"
    assert result.compound_score < 0


def test_vader_sentiment_neutral():
    """Test VADER sentiment analysis with neutral text."""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        content_id="test3",
        content_type="post",
        subreddit="test",
        text="This is a tool. It exists."
    )
    
    assert result.sentiment == "neutral"
    assert result.analysis_method == "VADER"


def test_empty_text_handling():
    """Test handling of empty text."""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(
        content_id="test4",
        content_type="post",
        subreddit="test",
        text=""
    )
    
    assert result.sentiment == "neutral"
    assert result.confidence == 0.5
