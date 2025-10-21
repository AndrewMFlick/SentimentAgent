"""Integration tests for admin API endpoints."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_pending_tools_success(client):
    """Test GET /admin/tools/pending with valid admin token."""
    async def mock_get_pending_tools():
        return [
            {
                "id": "new-tool",
                "name": "New AI Tool",
                "status": "pending",
                "mention_count_7d": 75,
                "first_detected": "2025-01-01T00:00:00"
            }
        ]
    
    with patch(
        'src.services.database.db.get_pending_tools',
        side_effect=mock_get_pending_tools
    ):
        response = client.get(
            "/api/v1/admin/tools/pending",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["count"] == 1
        assert data["tools"][0]["id"] == "new-tool"


def test_get_pending_tools_no_auth(client):
    """Test GET /admin/tools/pending without authentication."""
    response = client.get("/api/v1/admin/tools/pending")
    
    assert response.status_code == 401
    assert "authentication required" in response.json()[
        "detail"
    ].lower()


def test_approve_tool_success(client):
    """Test POST /admin/tools/{tool_id}/approve."""
    from unittest.mock import AsyncMock, MagicMock
    
    async def mock_get_tool(tool_id):
        return {
            "id": tool_id,
            "name": "New Tool",
            "status": "pending"
        }
    
    # Create a mock ToolManager instance
    mock_manager = MagicMock()
    mock_manager.approve_tool = AsyncMock(return_value={
        "id": "new-tool",
        "name": "New Tool",
        "status": "approved",
        "approved_by": "admin",
        "approved_at": "2025-01-15T00:00:00"
    })
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ), patch(
        'src.api.admin.tool_manager',
        mock_manager
    ):
        response = client.post(
            "/api/v1/admin/tools/new-tool/approve",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["status"] == "approved"
        assert "approved successfully" in data["message"].lower()


def test_approve_tool_not_found(client):
    """Test approve with non-existent tool."""
    async def mock_get_tool(tool_id):
        return None
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.post(
            "/api/v1/admin/tools/invalid-tool/approve",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_approve_tool_already_approved(client):
    """Test approve tool that is already approved."""
    async def mock_get_tool(tool_id):
        return {
            "id": tool_id,
            "name": "Existing Tool",
            "status": "approved"
        }
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ):
        response = client.post(
            "/api/v1/admin/tools/existing-tool/approve",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "already approved" in response.json()["detail"].lower()


def test_reject_tool_success(client):
    """Test POST /admin/tools/{tool_id}/reject."""
    from unittest.mock import AsyncMock, MagicMock
    
    async def mock_get_tool(tool_id):
        return {
            "id": tool_id,
            "name": "New Tool",
            "status": "pending"
        }
    
    # Create a mock ToolManager instance
    mock_manager = MagicMock()
    mock_manager.reject_tool = AsyncMock(return_value={
        "id": "new-tool",
        "name": "New Tool",
        "status": "rejected",
        "rejected_by": "admin",
        "rejected_at": "2025-01-15T00:00:00"
    })
    
    with patch(
        'src.services.database.db.get_tool',
        side_effect=mock_get_tool
    ), patch(
        'src.api.admin.tool_manager',
        mock_manager
    ):
        response = client.post(
            "/api/v1/admin/tools/new-tool/reject",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["status"] == "rejected"
        assert "rejected successfully" in data["message"].lower()


def test_reject_tool_no_auth(client):
    """Test reject without authentication."""
    response = client.post(
        "/api/v1/admin/tools/some-tool/reject"
    )
    
    assert response.status_code == 401
