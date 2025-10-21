"""Integration tests for tool comparison endpoint."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    """Create test client."""
    from src.main import app
    return TestClient(app)


def test_compare_tools_success(client):
    """Test GET /tools/compare with multiple tools."""
    async def mock_get_tool_sentiment(tool_id, hours=None, start_date=None, end_date=None):
        # Mock different sentiment for each tool
        if tool_id == "github-copilot":
            return {
                "total_mentions": 100,
                "positive_count": 60,
                "negative_count": 25,
                "neutral_count": 15,
                "avg_sentiment": 0.35
            }
        else:  # jules-ai
            return {
                "total_mentions": 50,
                "positive_count": 35,
                "negative_count": 10,
                "neutral_count": 5,
                "avg_sentiment": 0.50
            }
    
    async def mock_get_tool(tool_id):
        if tool_id == "github-copilot":
            return {"id": tool_id, "name": "GitHub Copilot", "status": "approved"}
        else:
            return {"id": tool_id, "name": "Jules AI", "status": "approved"}
    
    with patch('src.services.database.db.get_tool', side_effect=mock_get_tool):
        with patch('src.services.database.db.get_tool_sentiment', side_effect=mock_get_tool_sentiment):
            response = client.get(
                "/api/v1/tools/compare?tool_ids=github-copilot,jules-ai&hours=24"
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify structure
            assert "tools" in data
            assert "deltas" in data
            assert len(data["tools"]) == 2
            
            # Verify tools data
            assert data["tools"][0]["tool_id"] == "github-copilot"
            assert data["tools"][1]["tool_id"] == "jules-ai"
            
            # Verify delta calculations exist
            assert len(data["deltas"]) > 0
            delta = data["deltas"][0]
            assert "tool_a_id" in delta
            assert "tool_b_id" in delta
            assert "positive_delta" in delta
            assert "negative_delta" in delta
            assert "sentiment_delta" in delta


def test_compare_tools_single_tool(client):
    """Test GET /tools/compare with only one tool (should work but no deltas)."""
    async def mock_get_tool_sentiment(tool_id, hours=None, start_date=None, end_date=None):
        return {
            "total_mentions": 100,
            "positive_count": 60,
            "negative_count": 25,
            "neutral_count": 15,
            "avg_sentiment": 0.35
        }
    
    async def mock_get_tool(tool_id):
        return {"id": tool_id, "name": "GitHub Copilot", "status": "approved"}
    
    with patch('src.services.database.db.get_tool', side_effect=mock_get_tool):
        with patch('src.services.database.db.get_tool_sentiment', side_effect=mock_get_tool_sentiment):
            response = client.get(
                "/api/v1/tools/compare?tool_ids=github-copilot&hours=24"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["tools"]) == 1
            assert len(data["deltas"]) == 0  # No comparison with single tool


def test_compare_tools_no_tool_ids(client):
    """Test GET /tools/compare without tool_ids parameter."""
    response = client.get("/api/v1/tools/compare?hours=24")
    
    # FastAPI returns 422 for missing required parameters
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_compare_tools_invalid_tool(client):
    """Test GET /tools/compare with non-existent tool."""
    async def mock_get_tool(tool_id):
        if tool_id == "github-copilot":
            return {
                "id": tool_id,
                "name": "GitHub Copilot",
                "status": "approved"
            }
        else:
            return None  # Tool not found
    
    with patch('src.services.database.db.get_tool', side_effect=mock_get_tool):
        response = client.get(
            "/api/v1/tools/compare?tool_ids=github-copilot,invalid-tool"
        )
        
        assert response.status_code == 404
        assert "invalid-tool" in response.json()["detail"].lower()
