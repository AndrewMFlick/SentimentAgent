"""Integration tests for admin tool management API endpoints."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_tool_service():
    """Mock ToolService for testing."""
    service = MagicMock()
    service.create_tool = AsyncMock()
    service.get_tool = AsyncMock()
    service.list_tools = AsyncMock()
    service.count_tools = AsyncMock()
    service.update_tool = AsyncMock()
    service.delete_tool = AsyncMock()
    service.create_alias = AsyncMock()
    service.get_aliases = AsyncMock()
    service.remove_alias = AsyncMock()
    return service


def test_create_tool_success(client, mock_tool_service):
    """Test POST /admin/tools with valid data."""
    
    # Mock the tool creation
    mock_tool_service.create_tool.return_value = {
        "id": "test-id-123",
        "partitionKey": "tool",
        "name": "Test Tool",
        "slug": "test-tool",
        "vendor": "Test Vendor",
        "category": "code-completion",
        "description": "A test tool",
        "status": "active",
        "metadata": {},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.post(
            "/api/v1/admin/tools",
            json={
                "name": "Test Tool",
                "vendor": "Test Vendor",
                "category": "code-completion",
                "description": "A test tool"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tool" in data
        assert data["tool"]["name"] == "Test Tool"
        assert data["message"] == "Tool created successfully"


def test_create_tool_no_auth(client):
    """Test POST /admin/tools without authentication."""
    response = client.post(
        "/api/v1/admin/tools",
        json={
            "name": "Test Tool",
            "vendor": "Test Vendor",
            "category": "code-completion"
        }
    )
    
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()


def test_create_tool_duplicate_name(client, mock_tool_service):
    """Test POST /admin/tools with duplicate name."""
    
    # Mock duplicate name error
    mock_tool_service.create_tool.side_effect = ValueError("Tool name 'Test Tool' already exists")
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.post(
            "/api/v1/admin/tools",
            json={
                "name": "Test Tool",
                "vendor": "Test Vendor",
                "category": "code-completion"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


def test_list_tools_success(client, mock_tool_service):
    """Test GET /admin/tools with pagination."""
    
    # Mock the tool list
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "Tool 1",
            "vendor": "Vendor 1",
            "category": "code-completion"
        },
        {
            "id": "tool-2",
            "name": "Tool 2",
            "vendor": "Vendor 2",
            "category": "chat"
        }
    ]
    mock_tool_service.count_tools.return_value = 2
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?page=1&limit=20",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["limit"] == 20


def test_get_tool_details_success(client, mock_tool_service):
    """Test GET /admin/tools/{tool_id}."""
    
    # Mock the tool and aliases
    mock_tool_service.get_tool.return_value = {
        "id": "tool-1",
        "name": "Tool 1",
        "vendor": "Vendor 1",
        "category": "code-completion"
    }
    mock_tool_service.get_aliases.return_value = []
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools/tool-1",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tool" in data
        assert "aliases" in data
        assert data["tool"]["id"] == "tool-1"


def test_get_tool_details_not_found(client, mock_tool_service):
    """Test GET /admin/tools/{tool_id} with non-existent tool."""
    
    # Mock tool not found
    mock_tool_service.get_tool.return_value = None
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools/invalid-tool-id",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_update_tool_success(client, mock_tool_service):
    """Test PUT /admin/tools/{tool_id}."""
    
    # Mock the tool update
    mock_tool_service.update_tool.return_value = {
        "id": "tool-1",
        "name": "Updated Tool Name",
        "vendor": "Vendor 1",
        "category": "code-completion"
    }
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.put(
            "/api/v1/admin/tools/tool-1",
            json={
                "name": "Updated Tool Name"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["name"] == "Updated Tool Name"
        assert data["message"] == "Tool updated successfully"


def test_delete_tool_success(client, mock_tool_service):
    """Test DELETE /admin/tools/{tool_id}."""
    
    # Mock the tool deletion
    mock_tool_service.delete_tool.return_value = True
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.delete(
            "/api/v1/admin/tools/tool-1",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tool deleted successfully"


def test_link_alias_success(client, mock_tool_service):
    """Test PUT /admin/tools/{tool_id}/alias."""
    
    # Mock the alias creation
    mock_tool_service.create_alias.return_value = {
        "id": "alias-1",
        "partitionKey": "alias",
        "alias_tool_id": "tool-1",
        "primary_tool_id": "tool-2",
        "created_at": "2025-01-01T00:00:00Z",
        "created_by": "admin"
    }
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.put(
            "/api/v1/admin/tools/tool-1/alias",
            json={
                "primary_tool_id": "tool-2"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "alias" in data
        assert data["message"] == "Alias linked successfully"


def test_link_alias_circular_reference(client, mock_tool_service):
    """Test PUT /admin/tools/{tool_id}/alias with circular reference."""
    
    # Mock circular reference error
    mock_tool_service.create_alias.side_effect = ValueError("Circular alias detected")
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.put(
            "/api/v1/admin/tools/tool-1/alias",
            json={
                "primary_tool_id": "tool-2"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "Circular alias" in response.json()["detail"]
