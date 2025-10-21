"""Integration tests for admin API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.models.tool import ToolCategory


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Return test admin token."""
    return "test-admin-token"


@pytest.fixture
def mock_tool_service():
    """Create mock ToolService."""
    with patch('src.api.admin.get_tool_service') as mock:
        service = AsyncMock()
        mock.return_value = service
        yield service


class TestCreateToolEndpoint:
    """Test POST /admin/tools endpoint."""

    def test_create_tool_success(self, client, admin_token, mock_tool_service):
        """Test successful tool creation."""
        mock_tool_service.create_tool.return_value = {
            "id": "new-tool-123",
            "name": "New Tool",
            "vendor": "Test Vendor",
            "category": "code_assistant",
            "status": "active"
        }

        response = client.post(
            "/admin/tools",
            json={
                "name": "New Tool",
                "vendor": "Test Vendor",
                "category": "code_assistant"
            },
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["name"] == "New Tool"
        assert "message" in data

    def test_create_tool_duplicate_name(self, client, admin_token, mock_tool_service):
        """Test creating tool with duplicate name."""
        mock_tool_service.create_tool.side_effect = ValueError("already exists")

        response = client.post(
            "/admin/tools",
            json={
                "name": "Duplicate Tool",
                "vendor": "Test Vendor",
                "category": "code_assistant"
            },
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_tool_no_auth(self, client):
        """Test creating tool without authentication."""
        response = client.post(
            "/admin/tools",
            json={
                "name": "New Tool",
                "vendor": "Test Vendor",
                "category": "code_assistant"
            }
        )

        assert response.status_code == 401

    def test_create_tool_validation_error(self, client, admin_token):
        """Test creating tool with invalid data."""
        response = client.post(
            "/admin/tools",
            json={
                "name": "",  # Empty name
                "vendor": "Test Vendor"
                # Missing required category
            },
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 422  # Validation error


class TestListToolsEndpoint:
    """Test GET /admin/tools endpoint."""

    def test_list_tools_success(self, client, admin_token, mock_tool_service):
        """Test successful tool listing."""
        mock_tool_service.list_tools.return_value = [
            {"id": "tool-1", "name": "Tool 1"},
            {"id": "tool-2", "name": "Tool 2"}
        ]
        mock_tool_service.count_tools.return_value = 2

        response = client.get(
            "/admin/tools",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1

    def test_list_tools_pagination(self, client, admin_token, mock_tool_service):
        """Test tool listing with pagination."""
        mock_tool_service.list_tools.return_value = []
        mock_tool_service.count_tools.return_value = 50

        response = client.get(
            "/admin/tools?page=2&limit=10",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["limit"] == 10

    def test_list_tools_search(self, client, admin_token, mock_tool_service):
        """Test tool listing with search."""
        mock_tool_service.list_tools.return_value = [
            {"id": "copilot", "name": "GitHub Copilot"}
        ]
        mock_tool_service.count_tools.return_value = 1

        response = client.get(
            "/admin/tools?search=copilot",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1


class TestUpdateToolEndpoint:
    """Test PUT /admin/tools/{tool_id} endpoint."""

    def test_update_tool_success(self, client, admin_token, mock_tool_service):
        """Test successful tool update."""
        mock_tool_service.update_tool.return_value = {
            "id": "tool-123",
            "name": "Updated Tool",
            "description": "Updated description"
        }

        response = client.put(
            "/admin/tools/tool-123",
            json={"name": "Updated Tool", "description": "Updated description"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tool"]["name"] == "Updated Tool"

    def test_update_tool_not_found(self, client, admin_token, mock_tool_service):
        """Test updating non-existent tool."""
        mock_tool_service.update_tool.return_value = None

        response = client.put(
            "/admin/tools/non-existent",
            json={"name": "Updated"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 404


class TestDeleteToolEndpoint:
    """Test DELETE /admin/tools/{tool_id} endpoint."""

    def test_delete_tool_success(self, client, admin_token, mock_tool_service):
        """Test successful tool deletion."""
        mock_tool_service.delete_tool.return_value = True

        response = client.delete(
            "/admin/tools/tool-123",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_delete_tool_not_found(self, client, admin_token, mock_tool_service):
        """Test deleting non-existent tool."""
        mock_tool_service.delete_tool.return_value = False

        response = client.delete(
            "/admin/tools/non-existent",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 404


class TestLinkAliasEndpoint:
    """Test PUT /admin/tools/{tool_id}/alias endpoint."""

    def test_link_alias_success(self, client, admin_token, mock_tool_service):
        """Test successful alias linking."""
        mock_tool_service.create_alias.return_value = {
            "id": "alias-123",
            "alias_tool_id": "codex",
            "primary_tool_id": "openai"
        }

        response = client.put(
            "/admin/tools/codex/alias",
            json={"primary_tool_id": "openai"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alias"]["alias_tool_id"] == "codex"

    def test_link_alias_circular(self, client, admin_token, mock_tool_service):
        """Test linking alias with circular reference."""
        mock_tool_service.create_alias.side_effect = ValueError(
            "Circular alias detected"
        )

        response = client.put(
            "/admin/tools/tool-a/alias",
            json={"primary_tool_id": "tool-b"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 400
        assert "Circular" in response.json()["detail"]

    def test_link_alias_self_reference(self, client, admin_token, mock_tool_service):
        """Test linking tool as alias of itself."""
        mock_tool_service.create_alias.side_effect = ValueError(
            "cannot be alias of itself"
        )

        response = client.put(
            "/admin/tools/same-id/alias",
            json={"primary_tool_id": "same-id"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 400


class TestErrorHandling:
    """Test comprehensive error handling."""

    def test_database_error_handling(self, client, admin_token, mock_tool_service):
        """Test handling of database errors."""
        mock_tool_service.list_tools.side_effect = Exception("Database error")

        response = client.get(
            "/admin/tools",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 500
        assert "Failed to list tools" in response.json()["detail"]

    def test_validation_error_response_format(self, client, admin_token):
        """Test validation error response format."""
        response = client.post(
            "/admin/tools",
            json={"invalid": "data"},
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    def test_missing_token(self, client):
        """Test request without admin token."""
        response = client.get("/admin/tools")
        assert response.status_code == 401

    def test_with_valid_token(self, client, admin_token, mock_tool_service):
        """Test request with valid admin token."""
        mock_tool_service.list_tools.return_value = []
        mock_tool_service.count_tools.return_value = 0

        response = client.get(
            "/admin/tools",
            headers={"X-Admin-Token": admin_token}
        )

        assert response.status_code == 200
