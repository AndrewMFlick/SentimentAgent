"""Unit tests for tool deletion (Phase 6: User Story 4)."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

from src.services.tool_service import ToolService


@pytest.fixture
def mock_containers():
    """Create mock Cosmos DB containers."""
    tools_container = MagicMock()
    aliases_container = MagicMock()
    admin_logs_container = MagicMock()
    sentiment_container = MagicMock()
    return tools_container, aliases_container, admin_logs_container, sentiment_container


@pytest.fixture
def tool_service(mock_containers):
    """Create ToolService instance with mock containers."""
    tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
    return ToolService(
        tools_container=tools_container,
        aliases_container=aliases_container,
        admin_logs_container=admin_logs_container,
        sentiment_container=sentiment_container
    )


@pytest.fixture
def sample_tool():
    """Create sample tool document."""
    return {
        "id": "test-tool-123",
        "partitionKey": "TOOL",
        "name": "Test Tool",
        "slug": "test-tool",
        "vendor": "Test Vendor",
        "categories": ["code_assistant"],
        "status": "active",
        "description": "A test tool",
        "metadata": {},
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "created_by": "admin",
        "updated_by": "admin"
    }


def create_mock_query_function(sample_tool, referencing_tools=None):
    """
    Helper function to create a mock query_items function.
    
    This centralizes the query pattern matching logic to make tests more maintainable.
    
    Args:
        sample_tool: The tool document to return for get_tool queries
        referencing_tools: List of tools that reference the target tool (for merge validation)
    
    Returns:
        A function that can be used as side_effect for query_items mock
    """
    if referencing_tools is None:
        referencing_tools = []
    
    def mock_query_items(query=None, parameters=None, **kwargs):
        # Match based on query structure, not just string contains
        if "merged_into" in query:
            # Query for tools that reference this tool
            return referencing_tools
        elif "t.id = @id" in query:
            # get_tool query - return the tool if it exists
            return [sample_tool] if sample_tool else []
        else:
            # Default case
            return []
    
    return mock_query_items


class TestDeleteTool:
    """Test tool deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_tool_success(self, tool_service, mock_containers, sample_tool):
        """Test successful permanent tool deletion."""
        tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
        
        # Use helper to create mock query function with no referencing tools
        tools_container.query_items.side_effect = create_mock_query_function(
            sample_tool, referencing_tools=[]
        )
        
        # Mock sentiment container to return 0 records
        sentiment_container.query_items.return_value = []
        
        # Mock delete operations
        tools_container.delete_item = MagicMock()
        admin_logs_container.create_item = MagicMock()
        
        # Delete the tool
        result = await tool_service.delete_tool(
            tool_id="test-tool-123",
            deleted_by="admin",
            hard_delete=True
        )
        
        # Verify result
        assert result["tool_id"] == "test-tool-123"
        assert result["tool_name"] == "Test Tool"
        assert result["sentiment_count"] == 0
        assert result["hard_delete"] is True
        
        # Verify delete was called
        tools_container.delete_item.assert_called_once()
        
        # Verify admin log was created
        admin_logs_container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_tool_referenced_by_merged_tool(self, tool_service, mock_containers, sample_tool):
        """Test deletion fails when tool is referenced by merged_into."""
        tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
        
        # Mock a referencing tool
        referencing_tool = {
            "id": "merged-tool-456",
            "name": "Merged Tool",
            "merged_into": "test-tool-123"
        }
        
        # Use helper to create mock query function with referencing tool
        tools_container.query_items.side_effect = create_mock_query_function(
            sample_tool, referencing_tools=[referencing_tool]
        )
        
        # Attempt to delete should raise ValueError
        with pytest.raises(ValueError, match="Cannot delete tool: referenced by"):
            await tool_service.delete_tool(
                tool_id="test-tool-123",
                deleted_by="admin",
                hard_delete=True
            )

    @pytest.mark.asyncio
    async def test_delete_tool_not_found(self, tool_service, mock_containers):
        """Test deletion fails when tool doesn't exist."""
        tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
        
        # Mock get_tool to return None (tool not found)
        tools_container.query_items.return_value = []
        
        # Attempt to delete should raise ValueError
        with pytest.raises(ValueError, match="not found"):
            await tool_service.delete_tool(
                tool_id="nonexistent-tool",
                deleted_by="admin",
                hard_delete=True
            )

    @pytest.mark.asyncio
    async def test_delete_tool_with_sentiment_data(self, tool_service, mock_containers, sample_tool):
        """Test deletion cascades to sentiment data."""
        tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
        
        # Mock sentiment records
        sentiment_records = [
            {"id": "sent-1", "partitionKey": "sent-1", "tool_id": "test-tool-123"},
            {"id": "sent-2", "partitionKey": "sent-2", "tool_id": "test-tool-123"}
        ]
        
        # Use helper to create mock query function with no referencing tools
        tools_container.query_items.side_effect = create_mock_query_function(
            sample_tool, referencing_tools=[]
        )
        sentiment_container.query_items.return_value = sentiment_records
        
        # Mock delete operations
        tools_container.delete_item = MagicMock()
        sentiment_container.delete_item = MagicMock()
        admin_logs_container.create_item = MagicMock()
        
        # Delete the tool
        result = await tool_service.delete_tool(
            tool_id="test-tool-123",
            deleted_by="admin",
            hard_delete=True
        )
        
        # Verify sentiment records were deleted
        assert sentiment_container.delete_item.call_count == 2
        
        # Verify tool was deleted
        tools_container.delete_item.assert_called_once()


class TestGetSentimentCount:
    """Test get_sentiment_count functionality."""

    @pytest.mark.asyncio
    async def test_get_sentiment_count_no_container(self, tool_service):
        """Test sentiment count returns 0 when container not available."""
        # Service doesn't have sentiment_container set
        tool_service.sentiment_container = None
        
        count = await tool_service.get_sentiment_count("test-tool-123")
        
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_sentiment_count_with_data(self, mock_containers):
        """Test sentiment count returns correct count."""
        tools_container, aliases_container, admin_logs_container, sentiment_container = mock_containers
        
        service = ToolService(
            tools_container=tools_container,
            aliases_container=aliases_container,
            admin_logs_container=admin_logs_container,
            sentiment_container=sentiment_container
        )
        
        # Mock sentiment count query to return 42
        sentiment_container.query_items.return_value = [42]
        
        count = await service.get_sentiment_count("test-tool-123")
        
        assert count == 42
