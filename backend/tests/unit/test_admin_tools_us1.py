"""Unit tests for US1: Admin Tools List API with filtering and pagination.

These tests focus on the admin tools list endpoint with filtering, search,
pagination, and sorting functionality implemented in Phase 3 US1.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment before any imports
os.environ['REDDIT_CLIENT_ID'] = 'test_client_id'
os.environ['REDDIT_CLIENT_SECRET'] = 'test_client_secret'
os.environ['COSMOS_ENDPOINT'] = 'https://localhost:8081/'
os.environ['COSMOS_KEY'] = 'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=='

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the admin router module level items we need
from src.api.admin import router, verify_admin


# Create test app with admin router
app = FastAPI()

@app.get("/")
def root():
    return {"message": "test"}


app.include_router(router, prefix="/api/v1")


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tool_service():
    """Mock ToolService for testing."""
    service = MagicMock()
    service.list_tools = AsyncMock()
    service.count_tools = AsyncMock()
    return service


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    db.client = MagicMock()
    db.database = MagicMock()
    db.database.get_container_client = MagicMock()
    return db


# =========================================================================
# User Story 1 (US1) Tests: View All Active Tools with Filters
# =========================================================================


def test_list_tools_filter_by_status_active(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_filter_by_status_archived(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_filter_by_category(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_filter_by_multiple_categories(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_filter_by_vendor(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_search_by_name(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_combined_filters(client, mock_tool_service, mock_db):
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
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_pagination_first_page(client, mock_tool_service, mock_db):
    """Test GET /admin/tools pagination - first page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(1, 11)  # 10 items
    ]
    mock_tool_service.count_tools.return_value = 25  # Total of 25 items
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_pagination_middle_page(client, mock_tool_service, mock_db):
    """Test GET /admin/tools pagination - middle page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(11, 21)  # 10 items
    ]
    mock_tool_service.count_tools.return_value = 25
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_pagination_last_page(client, mock_tool_service, mock_db):
    """Test GET /admin/tools pagination - last page."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(21, 26)  # 5 items
    ]
    mock_tool_service.count_tools.return_value = 25
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_sort_by_name_asc(client, mock_tool_service, mock_db):
    """Test GET /admin/tools with sort_by=name, sort_order=asc."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "A Tool", "categories": ["code_completion"], "status": "active"},
        {"id": "tool-2", "name": "B Tool", "categories": ["chat"], "status": "active"},
    ]
    mock_tool_service.count_tools.return_value = 2
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_sort_by_vendor_desc(client, mock_tool_service, mock_db):
    """Test GET /admin/tools with sort_by=vendor, sort_order=desc."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "Tool 1", "vendor": "Zebra", "categories": ["code_completion"], "status": "active"},
        {"id": "tool-2", "name": "Tool 2", "vendor": "Alpha", "categories": ["chat"], "status": "active"},
    ]
    mock_tool_service.count_tools.return_value = 2
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_empty_result(client, mock_tool_service, mock_db):
    """Test GET /admin/tools with filters that return no results."""
    
    mock_tool_service.list_tools.return_value = []
    mock_tool_service.count_tools.return_value = 0
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_default_parameters(client, mock_tool_service, mock_db):
    """Test GET /admin/tools with default parameters (no query params)."""
    
    mock_tool_service.list_tools.return_value = [
        {"id": "tool-1", "name": "Tool 1", "categories": ["code_completion"], "status": "active"}
    ]
    mock_tool_service.count_tools.return_value = 1
    
    with patch('src.api.admin.db', mock_db):
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


def test_list_tools_no_auth(client, mock_tool_service, mock_db):
    """Test GET /admin/tools without authentication."""
    
    response = client.get("/api/v1/admin/tools")
    
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()


def test_list_tools_pagination_metadata_calculation(client, mock_tool_service, mock_db):
    """Test that pagination metadata is calculated correctly."""
    
    # Test edge case: 21 items with limit=10 should give 3 total pages
    mock_tool_service.list_tools.return_value = [
        {"id": f"tool-{i}", "name": f"Tool {i}", "categories": ["code_completion"], "status": "active"}
        for i in range(1, 11)
    ]
    mock_tool_service.count_tools.return_value = 21
    
    with patch('src.api.admin.db', mock_db):
        with patch('src.api.admin.get_tool_service', return_value=mock_tool_service):
            response = client.get(
                "/api/v1/admin/tools?page=1&limit=10",
                headers={"X-Admin-Token": "admin-secret"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 21
            assert data["total_pages"] == 3  # Ceiling division: (21 + 10 - 1) // 10 = 3
            assert data["has_next"] == True
            assert data["has_prev"] == False
