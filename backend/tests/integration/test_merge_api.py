"""Integration tests for merge API endpoint (Phase 7: User Story 5)."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_merge_request():
    """Sample merge request data."""
    return {
        "target_tool_id": "target-tool-123",
        "source_tool_ids": ["source-tool-1", "source-tool-2"],
        "final_categories": ["code_assistant", "code_review"],
        "final_vendor": "Merged Vendor",
        "notes": "Merging tools after acquisition"
    }


@pytest.fixture
def sample_merge_result():
    """Sample merge operation result."""
    return {
        "merge_record": {
            "id": "merge-record-123",
            "target_tool_id": "target-tool-123",
            "source_tool_ids": ["source-tool-1", "source-tool-2"],
            "merged_at": "2025-01-15T10:00:00Z",
            "merged_by": "admin",
            "sentiment_count": 100,
            "target_categories_before": ["code_assistant"],
            "target_categories_after": ["code_assistant", "code_review"],
            "target_vendor_before": "Old Vendor",
            "target_vendor_after": "Merged Vendor",
            "source_tools_metadata": [
                {
                    "id": "source-tool-1",
                    "name": "Source Tool 1",
                    "vendor": "Old Vendor",
                    "categories": ["code_assistant"]
                },
                {
                    "id": "source-tool-2",
                    "name": "Source Tool 2",
                    "vendor": "Old Vendor",
                    "categories": ["code_review"]
                }
            ],
            "notes": "Merging tools after acquisition"
        },
        "target_tool": {
            "id": "target-tool-123",
            "name": "Target Tool",
            "vendor": "Merged Vendor",
            "categories": ["code_assistant", "code_review"],
            "status": "active"
        },
        "archived_tools": [
            {
                "id": "source-tool-1",
                "name": "Source Tool 1",
                "status": "archived",
                "merged_into": "target-tool-123"
            },
            {
                "id": "source-tool-2",
                "name": "Source Tool 2",
                "status": "archived",
                "merged_into": "target-tool-123"
            }
        ],
        "warnings": []
    }


def test_merge_tools_success(client, sample_merge_request, sample_merge_result):
    """Test successful merge operation."""
    # Create mock ToolService
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(return_value=sample_merge_result)
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "merge_record" in data
        assert "target_tool" in data
        assert "archived_tools" in data
        assert "message" in data
        assert "Successfully merged 2 tool" in data["message"]
        assert "100" in data["message"]  # Sentiment count


def test_merge_tools_with_warnings(client, sample_merge_request, sample_merge_result):
    """Test merge operation with metadata warnings."""
    # Add warnings to result
    sample_merge_result["warnings"] = [
        {
            "type": "vendor_mismatch",
            "message": "Source tools have different vendors than target"
        }
    ]
    
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(return_value=sample_merge_result)
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["warnings"]) == 1
        assert "vendor_mismatch" in data["warnings"][0]["type"]
        assert "warnings" in data["message"].lower()


def test_merge_tools_no_auth(client, sample_merge_request):
    """Test merge without authentication."""
    response = client.post(
        "/api/v1/admin/tools/merge",
        json=sample_merge_request
    )
    
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()


def test_merge_tools_too_many_sources(client):
    """Test merge with more than 10 source tools."""
    merge_request = {
        "target_tool_id": "target-tool-123",
        "source_tool_ids": [f"source-{i}" for i in range(11)],  # 11 sources
        "final_categories": ["code_assistant"],
        "final_vendor": "Vendor"
    }
    
    mock_service = MagicMock()
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "more than 10" in response.json()["detail"]


def test_merge_tools_duplicate_source_ids(client):
    """Test merge with duplicate source tool IDs."""
    merge_request = {
        "target_tool_id": "target-tool-123",
        "source_tool_ids": ["source-tool-1", "source-tool-1"],  # Duplicate
        "final_categories": ["code_assistant"],
        "final_vendor": "Vendor"
    }
    
    mock_service = MagicMock()
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "unique" in response.json()["detail"].lower()


def test_merge_tools_circular_reference(client, sample_merge_request):
    """Test merge where target is in source list."""
    # Make request with target in sources
    merge_request = sample_merge_request.copy()
    merge_request["source_tool_ids"].append(merge_request["target_tool_id"])
    
    mock_service = MagicMock()
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 400
        assert "cannot merge tool into itself" in response.json()["detail"].lower()


def test_merge_tools_target_not_found(client, sample_merge_request):
    """Test merge when target tool doesn't exist."""
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(
        side_effect=ValueError("Target tool 'target-tool-123' not found")
    )
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_merge_tools_already_merged(client, sample_merge_request):
    """Test merge when tool already merged."""
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(
        side_effect=ValueError("Source tool 'Source Tool 1' has already been merged")
    )
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 409
        assert "already merged" in response.json()["detail"].lower()


def test_merge_tools_not_active(client, sample_merge_request):
    """Test merge when tool is not active."""
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(
        side_effect=ValueError("Target tool must be active")
    )
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 409
        assert "must be active" in response.json()["detail"].lower()


def test_merge_tools_server_error(client, sample_merge_request):
    """Test merge with unexpected server error."""
    mock_service = MagicMock()
    mock_service.merge_tools = AsyncMock(
        side_effect=Exception("Unexpected database error")
    )
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.post(
            "/api/v1/admin/tools/merge",
            json=sample_merge_request,
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 500
        assert "error occurred" in response.json()["detail"].lower()


def test_get_merge_history_success(client):
    """Test retrieving merge history for a tool."""
    mock_service = MagicMock()
    mock_service.get_merge_history = AsyncMock(return_value={
        "merge_records": [
            {
                "id": "merge-1",
                "target_tool_id": "target-tool-123",
                "source_tool_ids": ["source-1", "source-2"],
                "merged_at": "2025-01-15T10:00:00Z",
                "sentiment_count": 100
            }
        ],
        "total": 1,
        "page": 1,
        "limit": 10,
        "has_more": False
    })
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.get(
            "/api/v1/admin/tools/target-tool-123/merge-history",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "merge_records" in data
        assert data["total"] == 1
        assert len(data["merge_records"]) == 1
        assert data["merge_records"][0]["id"] == "merge-1"


def test_get_merge_history_pagination(client):
    """Test merge history with pagination."""
    mock_service = MagicMock()
    mock_service.get_merge_history = AsyncMock(return_value={
        "merge_records": [],
        "total": 25,
        "page": 2,
        "limit": 10,
        "has_more": True
    })
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.get(
            "/api/v1/admin/tools/target-tool-123/merge-history?page=2&limit=10",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["has_more"] is True


def test_get_merge_history_tool_not_found(client):
    """Test merge history for non-existent tool."""
    mock_service = MagicMock()
    mock_service.get_merge_history = AsyncMock(
        side_effect=ValueError("Tool 'invalid-tool' not found")
    )
    
    with patch(
        'src.api.admin.get_tool_service',
        return_value=mock_service
    ):
        response = client.get(
            "/api/v1/admin/tools/invalid-tool/merge-history",
            headers={"X-Admin-Token": "admin-secret"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_merge_history_no_auth(client):
    """Test merge history without authentication."""
    response = client.get(
        "/api/v1/admin/tools/target-tool-123/merge-history"
    )
    
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()
