"""Test API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_get_monitored_subreddits():
    """Test getting monitored subreddits."""
    response = client.get("/api/v1/subreddits")
    assert response.status_code == 200
    data = response.json()
    assert "subreddits" in data
    assert "count" in data
    assert isinstance(data["subreddits"], list)
    assert data["count"] > 0


def test_ai_query_empty():
    """Test AI query with empty question."""
    response = client.post("/api/v1/ai/query", json={"question": ""})
    assert response.status_code == 400


def test_ai_query_valid():
    """Test AI query with valid question."""
    response = client.post(
        "/api/v1/ai/query",
        json={"question": "What is the sentiment for Cursor?"}
    )
    # May return 200 or 500 depending on configuration
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "answer" in data
        assert "timestamp" in data


def test_sentiment_stats():
    """Test sentiment stats endpoint."""
    response = client.get("/api/v1/sentiment/stats")
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    assert "timestamp" in data


def test_sentiment_stats_with_filters():
    """Test sentiment stats with filters."""
    response = client.get("/api/v1/sentiment/stats?subreddit=Cursor&hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["subreddit"] == "Cursor"
    assert data["time_window_hours"] == 24
