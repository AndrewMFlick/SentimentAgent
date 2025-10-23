"""Integration tests for admin tool management API endpoints."""
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ['REDDIT_CLIENT_ID'] = 'test_client_id'
os.environ['REDDIT_CLIENT_SECRET'] = 'test_client_secret'
os.environ['COSMOS_ENDPOINT'] = 'https://localhost:8081/'
os.environ['COSMOS_KEY'] = 'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=='

# Mock the database service to avoid connection attempts
with patch('src.services.database.CosmosClient'):
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
    service.archive_tool = AsyncMock()
    service.unarchive_tool = AsyncMock()
    service.create_alias = AsyncMock()
    service.get_aliases = AsyncMock()
    service.remove_alias = AsyncMock()
    service.merge_tools = AsyncMock()
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
        "categories": ["code_completion", "code_assistant"],
        "description": "A test tool",
        "status": "active",
        "metadata": {},
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
        "created_by": "admin",
        "updated_by": "admin"
    }
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.post(
            "/api/v1/admin/tools",
            json={
                "name": "Test Tool",
                "vendor": "Test Vendor",
                "categories": ["code_completion", "code_assistant"],
                "description": "A test tool"
            },
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tool" in data
        assert data["tool"]["name"] == "Test Tool"
        assert len(data["tool"]["categories"]) == 2
        assert data["message"] == "Tool created successfully"


def test_create_tool_no_auth(client):
    """Test POST /admin/tools without authentication."""
    response = client.post(
        "/api/v1/admin/tools",
        json={
            "name": "Test Tool",
            "vendor": "Test Vendor",
            "categories": ["code_completion"]
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
                "categories": ["code_completion"]
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
            "categories": ["code_completion"],
            "status": "active"
        },
        {
            "id": "tool-2",
            "name": "Tool 2",
            "vendor": "Vendor 2",
            "categories": ["chat", "code_assistant"],
            "status": "active"
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
        assert data["total_pages"] == 1
        assert data["has_next"] == False
        assert data["has_prev"] == False
        assert "filters_applied" in data


def test_get_tool_details_success(client, mock_tool_service):
    """Test GET /admin/tools/{tool_id}."""
    
    # Mock the tool and aliases
    mock_tool_service.get_tool.return_value = {
        "id": "tool-1",
        "name": "Tool 1",
        "vendor": "Vendor 1",
        "categories": ["code_completion"],
        "status": "active"
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
        "categories": ["code_completion"],
        "status": "active"
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
    mock_tool_service.delete_tool.return_value = {
        "tool_id": "tool-1",
        "tool_name": "Test Tool",
        "sentiment_count": 0
    }
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.delete(
            "/api/v1/admin/tools/tool-1",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tool permanently deleted"
        assert data["tool_id"] == "tool-1"


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


# =========================================================================
# User Story 1 (US1) Tests: View All Active Tools with Filters
# =========================================================================


def test_list_tools_filter_by_status_active(client, mock_tool_service):
    """Test GET /admin/tools with status=active filter."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "Active Tool",
            "vendor": "Vendor 1",
            "categories": ["code_completion"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?status=active",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["status"] == "active"
        assert data["filters_applied"]["status"] == "active"
        
        # Verify service was called with correct parameters
        mock_tool_service.list_tools.assert_called_once()
        call_kwargs = mock_tool_service.list_tools.call_args.kwargs
        assert call_kwargs["status"] == "active"


def test_list_tools_filter_by_status_archived(client, mock_tool_service):
    """Test GET /admin/tools with status=archived filter."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-2",
            "name": "Archived Tool",
            "vendor": "Vendor 2",
            "categories": ["chat"],
            "status": "archived"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?status=archived",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["status"] == "archived"
        assert data["filters_applied"]["status"] == "archived"


def test_list_tools_filter_by_category(client, mock_tool_service):
    """Test GET /admin/tools with category filter."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "Code Tool",
            "vendor": "Vendor 1",
            "categories": ["code_completion", "code_assistant"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?category=code_completion",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert "code_completion" in data["tools"][0]["categories"]
        assert data["filters_applied"]["categories"] == ["code_completion"]


def test_list_tools_filter_by_multiple_categories(client, mock_tool_service):
    """Test GET /admin/tools with multiple category filters (comma-separated)."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "Multi-Category Tool",
            "vendor": "Vendor 1",
            "categories": ["code_completion", "chat"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?category=code_completion,chat",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["filters_applied"]["categories"] == ["code_completion", "chat"]
        
        # Verify service was called with categories array
        call_kwargs = mock_tool_service.list_tools.call_args.kwargs
        assert call_kwargs["categories"] == ["code_completion", "chat"]


def test_list_tools_filter_by_vendor(client, mock_tool_service):
    """Test GET /admin/tools with vendor filter."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "Tool 1",
            "vendor": "Specific Vendor",
            "categories": ["code_completion"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?vendor=Specific Vendor",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["vendor"] == "Specific Vendor"
        assert data["filters_applied"]["vendor"] == "Specific Vendor"


def test_list_tools_search_by_name(client, mock_tool_service):
    """Test GET /admin/tools with search filter."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "GitHub Copilot",
            "vendor": "GitHub",
            "categories": ["code_completion"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?search=copilot",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert "copilot" in data["tools"][0]["name"].lower()
        assert data["filters_applied"]["search"] == "copilot"


def test_list_tools_combined_filters(client, mock_tool_service):
    """Test GET /admin/tools with multiple filters combined."""
    
    mock_tool_service.list_tools.return_value = [
        {
            "id": "tool-1",
            "name": "GitHub Copilot",
            "vendor": "GitHub",
            "categories": ["code_completion"],
            "status": "active"
        }
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?status=active&category=code_completion&vendor=GitHub&search=copilot",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["filters_applied"]["status"] == "active"
        assert data["filters_applied"]["categories"] == ["code_completion"]
        assert data["filters_applied"]["vendor"] == "GitHub"
        assert data["filters_applied"]["search"] == "copilot"


def test_list_tools_pagination_first_page(client, mock_tool_service):
    """Test GET /admin/tools pagination - first page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(1, 11)  # 10 items
    ]
    mock_tool_service.count_tools.return_value = 25  # Total of 25 items
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?page=1&limit=10",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 10
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["total"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] == True
        assert data["has_prev"] == False


def test_list_tools_pagination_middle_page(client, mock_tool_service):
    """Test GET /admin/tools pagination - middle page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(11, 21)  # 10 items
    ]
    mock_tool_service.count_tools.return_value = 25
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?page=2&limit=10",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["total_pages"] == 3
        assert data["has_next"] == True
        assert data["has_prev"] == True


def test_list_tools_pagination_last_page(client, mock_tool_service):
    """Test GET /admin/tools pagination - last page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(21, 26)  # 5 items
    ]
    mock_tool_service.count_tools.return_value = 25
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?page=3&limit=10",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 5
        assert data["page"] == 3
        assert data["total_pages"] == 3
        assert data["has_next"] == False
        assert data["has_prev"] == True


def test_list_tools_sort_by_name_asc(client, mock_tool_service):
    """Test GET /admin/tools with sort_by=name, sort_order=asc."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "A Tool", "categories": ["code_completion"], "status": "active"},
        {"id": "tool-2", "name": "B Tool", "categories": ["chat"], "status": "active"},
    ]
    mock_tool_service.count_tools.return_value = 2
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?sort_by=name&sort_order=asc",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tools"][0]["name"] == "A Tool"
        assert data["tools"][1]["name"] == "B Tool"
        
        # Verify service was called with sort parameters
        call_kwargs = mock_tool_service.list_tools.call_args.kwargs
        assert call_kwargs["sort_by"] == "name"
        assert call_kwargs["sort_order"] == "asc"


def test_list_tools_sort_by_vendor_desc(client, mock_tool_service):
    """Test GET /admin/tools with sort_by=vendor, sort_order=desc."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "Tool 1", "vendor": "Zebra", "categories": ["code_completion"], "status": "active"},
        {"id": "tool-2", "name": "Tool 2", "vendor": "Alpha", "categories": ["chat"], "status": "active"},
    ]
    mock_tool_service.count_tools.return_value = 2
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?sort_by=vendor&sort_order=desc",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should be sorted by vendor descending (Z before A)
        assert data["tools"][0]["vendor"] == "Zebra"
        assert data["tools"][1]["vendor"] == "Alpha"
        
        # Verify service was called with sort parameters
        call_kwargs = mock_tool_service.list_tools.call_args.kwargs
        assert call_kwargs["sort_by"] == "vendor"
        assert call_kwargs["sort_order"] == "desc"


def test_list_tools_empty_result(client, mock_tool_service):
    """Test GET /admin/tools with filters that return no results."""
    
    mock_tool_service.list_tools.return_value = []
    mock_tool_service.count_tools.return_value = 0
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools?search=nonexistent",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 0
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert data["has_next"] == False
        assert data["has_prev"] == False


def test_list_tools_default_parameters(client, mock_tool_service):
    """Test GET /admin/tools with default parameters (no query params)."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "Tool 1", "categories": ["code_completion"], "status": "active"}
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
        response = client.get(
            "/api/v1/admin/tools",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Verify default pagination values
        assert data["page"] == 1
        assert data["limit"] == 20
        
        # Verify service was called with defaults
        call_kwargs = mock_tool_service.list_tools.call_args.kwargs
        assert call_kwargs["page"] == 1
        assert call_kwargs["limit"] == 20
        assert call_kwargs["sort_by"] == "name"
        assert call_kwargs["sort_order"] == "asc"
