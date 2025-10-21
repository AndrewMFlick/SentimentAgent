"""Integration tests for time series API endpoint."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_tool_timeseries_success(client):
    """Test GET /tools/{tool_id}/timeseries with valid data."""
    async def mock_get_tool(tool_id):
        return {
            "id": "github-copilot",
            "name": "GitHub Copilot",
            "status": "approved"
        }
    
    async def mock_get_timeseries(tool_id, start_date, end_date):
        # Return 3 days of mock data
        return [
            {
                "date": "2025-01-01",
                "total_mentions": 100,
                "positive_count": 60,
                "negative_count": 30,
                "neutral_count": 10,
                "avg_sentiment": 0.35
            },
            {
                "date": "2025-01-02",
                "total_mentions": 120,
                "positive_count": 70,
                "negative_count": 35,
                "neutral_count": 15,
                "avg_sentiment": 0.40
            },
            {
                "date": "2025-01-03",
                "total_mentions": 110,
                "positive_count": 65,
                "negative_count": 32,
                "neutral_count": 13,
                "avg_sentiment": 0.37
            }
        ]
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ), patch(
        'src.services.database.db.get_tool_timeseries',
        side_effect=mock_get_timeseries
    ):
        response = client.get(
            "/api/v1/tools/github-copilot/timeseries"
            "?start_date=2025-01-01&end_date=2025-01-03"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["tool_id"] == "github-copilot"
        assert data["tool_name"] == "GitHub Copilot"
        assert data["granularity"] == "daily"
        assert data["time_period"]["start"] == "2025-01-01"
        assert data["time_period"]["end"] == "2025-01-03"
        
        # Verify data points
        assert len(data["data_points"]) == 3
        assert data["data_points"][0]["date"] == "2025-01-01"
        assert data["data_points"][0]["total_mentions"] == 100
        assert data["data_points"][0]["positive_count"] == 60


def test_get_tool_timeseries_tool_not_found(client):
    """Test GET /tools/{tool_id}/timeseries with non-existent tool."""
    async def mock_get_tool(tool_id):
        return None
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.get(
            "/api/v1/tools/invalid-tool/timeseries"
            "?start_date=2025-01-01&end_date=2025-01-03"
        )
        
        assert response.status_code == 404
        assert "invalid-tool" in response.json()["detail"].lower()


def test_get_tool_timeseries_invalid_date_format(client):
    """Test timeseries endpoint with invalid date format."""
    async def mock_get_tool(tool_id):
        return {
            "id": "github-copilot",
            "name": "GitHub Copilot"
        }
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.get(
            "/api/v1/tools/github-copilot/timeseries"
            "?start_date=01-01-2025&end_date=01-03-2025"
        )
        
        assert response.status_code == 400
        assert "invalid date format" in response.json()[
            "detail"
        ].lower()


def test_get_tool_timeseries_date_range_exceeded(client):
    """Test timeseries with date range > 90 days."""
    async def mock_get_tool(tool_id):
        return {
            "id": "github-copilot",
            "name": "GitHub Copilot"
        }
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.get(
            "/api/v1/tools/github-copilot/timeseries"
            "?start_date=2025-01-01&end_date=2025-05-01"
        )
        
        assert response.status_code == 400
        assert "90 days" in response.json()["detail"].lower()


def test_get_tool_timeseries_start_after_end(client):
    """Test timeseries with start_date after end_date."""
    async def mock_get_tool(tool_id):
        return {
            "id": "github-copilot",
            "name": "GitHub Copilot"
        }
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.get(
            "/api/v1/tools/github-copilot/timeseries"
            "?start_date=2025-01-10&end_date=2025-01-01"
        )
        
        assert response.status_code == 400
        assert "before" in response.json()["detail"].lower()


def test_get_tool_timeseries_no_data(client):
    """Test timeseries endpoint when no data exists."""
    async def mock_get_tool(tool_id):
        return {
            "id": "github-copilot",
            "name": "GitHub Copilot"
        }
    
    async def mock_get_timeseries(tool_id, start_date, end_date):
        return []  # No data
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ), patch(
        'src.services.database.db.get_tool_timeseries',
        side_effect=mock_get_timeseries
    ):
        response = client.get(
            "/api/v1/tools/github-copilot/timeseries"
            "?start_date=2025-01-01&end_date=2025-01-03"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data_points"]) == 0
