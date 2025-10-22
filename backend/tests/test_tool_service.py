"""Unit tests for ToolService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.services.tool_service import ToolService
from src.models.tool import ToolCreateRequest, ToolUpdateRequest, ToolCategory


@pytest.fixture
def mock_containers():
    """Create mock Cosmos DB containers."""
    tools_container = MagicMock()
    aliases_container = MagicMock()
    return tools_container, aliases_container


@pytest.fixture
def tool_service(mock_containers):
    """Create ToolService instance with mock containers."""
    tools_container, aliases_container = mock_containers
    return ToolService(
        tools_container=tools_container,
        aliases_container=aliases_container
    )


@pytest.fixture
def sample_tool():
    """Create sample tool document."""
    return {
        "id": "test-tool-123",
        "partitionKey": "tool",
        "name": "Test Tool",
        "slug": "test-tool",
        "vendor": "Test Vendor",
        "category": "code_assistant",
        "description": "A test tool",
        "status": "active",
        "metadata": {},
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    }


class TestCreateTool:
    """Test tool creation."""

    @pytest.mark.asyncio
    async def test_create_tool_success(self, tool_service, mock_containers):
        """Test successful tool creation."""
        tools_container, _ = mock_containers
        
        # Mock query to return no existing tool
        async def async_iter():
            return
            yield  # Make it an async generator
        
        tools_container.query_items.return_value = async_iter()
        tools_container.create_item = AsyncMock()

        tool_data = ToolCreateRequest(
            name="New Tool",
            vendor="Test Vendor",
            category=ToolCategory.CODE_ASSISTANT,
            description="Test description"
        )

        result = await tool_service.create_tool(tool_data)

        assert result["name"] == "New Tool"
        assert result["slug"] == "new-tool"
        assert result["vendor"] == "Test Vendor"
        assert result["category"] == "code_assistant"
        assert result["status"] == "active"
        assert "id" in result
        tools_container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_duplicate_name(self, tool_service, mock_containers, sample_tool):
        """Test creating tool with duplicate name raises error."""
        tools_container, _ = mock_containers
        
        # Mock query to return existing tool
        async def async_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = async_iter()

        tool_data = ToolCreateRequest(
            name="Test Tool",  # Duplicate
            vendor="Another Vendor",
            category=ToolCategory.CODE_ASSISTANT
        )

        with pytest.raises(ValueError, match="already exists"):
            await tool_service.create_tool(tool_data)

    @pytest.mark.asyncio
    async def test_create_tool_generates_slug(self, tool_service, mock_containers):
        """Test that slug is generated from name."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            return
            yield
        
        tools_container.query_items.return_value = async_iter()
        tools_container.create_item = AsyncMock()

        tool_data = ToolCreateRequest(
            name="GitHub Copilot X",
            vendor="GitHub",
            category=ToolCategory.CODE_ASSISTANT
        )

        result = await tool_service.create_tool(tool_data)

        assert result["slug"] == "github-copilot-x"


class TestGetTool:
    """Test tool retrieval."""

    @pytest.mark.asyncio
    async def test_get_tool_success(self, tool_service, mock_containers, sample_tool):
        """Test successful tool retrieval."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = async_iter()

        result = await tool_service.get_tool("test-tool-123")

        assert result == sample_tool

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, tool_service, mock_containers):
        """Test getting non-existent tool returns None."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            return
            yield
        
        tools_container.query_items.return_value = async_iter()

        result = await tool_service.get_tool("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_tool_filters_deleted(self, tool_service, mock_containers):
        """Test that deleted tools are not returned."""
        tools_container, _ = mock_containers
        
        deleted_tool = {
            "id": "deleted-tool",
            "status": "deleted"
        }
        
        async def async_iter():
            return  # Empty result - deleted tools filtered by query
            yield
        
        tools_container.query_items.return_value = async_iter()

        result = await tool_service.get_tool("deleted-tool")

        assert result is None


class TestUpdateTool:
    """Test tool updates."""

    @pytest.mark.asyncio
    async def test_update_tool_success(self, tool_service, mock_containers, sample_tool):
        """Test successful tool update."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = async_iter()
        tools_container.replace_item = AsyncMock()

        updates = ToolUpdateRequest(
            name="Updated Name",
            description="Updated description"
        )

        result = await tool_service.update_tool("test-tool-123", updates)

        assert result["name"] == "Updated Name"
        assert result["description"] == "Updated description"
        assert result["slug"] == "updated-name"  # Slug regenerated
        tools_container.replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tool_not_found(self, tool_service, mock_containers):
        """Test updating non-existent tool returns None."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            return
            yield
        
        tools_container.query_items.return_value = async_iter()

        updates = ToolUpdateRequest(name="New Name")
        result = await tool_service.update_tool("non-existent", updates)

        assert result is None


class TestDeleteTool:
    """Test tool deletion."""

    @pytest.mark.asyncio
    async def test_soft_delete_tool(self, tool_service, mock_containers, sample_tool):
        """Test soft delete sets status to deleted."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = async_iter()
        tools_container.replace_item = AsyncMock()

        result = await tool_service.delete_tool("test-tool-123", hard_delete=False)

        assert result is True
        # Verify replace was called (soft delete)
        tools_container.replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_hard_delete_tool(self, tool_service, mock_containers, sample_tool):
        """Test hard delete removes tool from database."""
        tools_container, _ = mock_containers
        
        async def async_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = async_iter()
        tools_container.delete_item = AsyncMock()

        result = await tool_service.delete_tool("test-tool-123", hard_delete=True)

        assert result is True
        # Verify delete was called (hard delete)
        tools_container.delete_item.assert_called_once()


class TestAliasOperations:
    """Test alias creation and management."""

    @pytest.mark.asyncio
    async def test_create_alias_success(self, tool_service, mock_containers, sample_tool):
        """Test successful alias creation."""
        tools_container, aliases_container = mock_containers
        
        # Mock tool queries
        async def tool_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = tool_iter()
        aliases_container.create_item = AsyncMock()

        # Mock alias query (no existing alias)
        async def alias_iter():
            return
            yield
        
        aliases_container.query_items.return_value = alias_iter()

        result = await tool_service.create_alias(
            alias_tool_id="alias-123",
            primary_tool_id="primary-456",
            created_by="admin"
        )

        assert result["alias_tool_id"] == "alias-123"
        assert result["primary_tool_id"] == "primary-456"
        assert result["created_by"] == "admin"
        aliases_container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_alias_self_reference(self, tool_service, mock_containers, sample_tool):
        """Test that tool cannot be alias of itself."""
        tools_container, _ = mock_containers
        
        async def tool_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = tool_iter()

        with pytest.raises(ValueError, match="cannot be alias of itself"):
            await tool_service.create_alias(
                alias_tool_id="same-id",
                primary_tool_id="same-id",
                created_by="admin"
            )

    @pytest.mark.asyncio
    async def test_create_alias_circular_detection(self, tool_service, mock_containers, sample_tool):
        """Test circular alias detection."""
        tools_container, aliases_container = mock_containers
        
        # Mock tools exist
        async def tool_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = tool_iter()

        # Mock circular alias chain
        async def alias_iter():
            yield {"alias_tool_id": "b", "primary_tool_id": "a"}
        
        aliases_container.query_items.return_value = alias_iter()

        # Try to create: a -> b (but b -> a already exists)
        with pytest.raises(ValueError, match="Circular alias"):
            await tool_service.create_alias(
                alias_tool_id="a",
                primary_tool_id="b",
                created_by="admin"
            )

    @pytest.mark.asyncio
    async def test_resolve_tool_id_with_alias(self, tool_service, mock_containers):
        """Test resolving alias to primary tool."""
        _, aliases_container = mock_containers
        
        # Mock alias exists
        async def alias_iter():
            yield {"alias_tool_id": "alias-123", "primary_tool_id": "primary-456"}
        
        aliases_container.query_items.return_value = alias_iter()

        result = await tool_service.resolve_tool_id("alias-123")

        assert result == "primary-456"

    @pytest.mark.asyncio
    async def test_resolve_tool_id_no_alias(self, tool_service, mock_containers):
        """Test resolving non-alias returns same ID."""
        _, aliases_container = mock_containers
        
        # Mock no alias
        async def alias_iter():
            return
            yield
        
        aliases_container.query_items.return_value = alias_iter()

        result = await tool_service.resolve_tool_id("primary-123")

        assert result == "primary-123"


class TestListTools:
    """Test tool listing with pagination and filtering."""

    @pytest.mark.asyncio
    async def test_list_tools_pagination(self, tool_service, mock_containers, sample_tool):
        """Test tool listing with pagination."""
        tools_container, _ = mock_containers
        
        async def tools_iter():
            yield sample_tool
            yield {**sample_tool, "id": "tool-2", "name": "Tool 2"}
        
        tools_container.query_items.return_value = tools_iter()

        results = await tool_service.list_tools(page=1, limit=20)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_list_tools_search(self, tool_service, mock_containers, sample_tool):
        """Test tool listing with search filter."""
        tools_container, _ = mock_containers
        
        async def tools_iter():
            yield sample_tool
        
        tools_container.query_items.return_value = tools_iter()

        results = await tool_service.list_tools(search="Test")

        assert len(results) == 1
        # Verify query includes search filter
        call_args = tools_container.query_items.call_args
        query = call_args[1]['query']
        assert 'CONTAINS' in query or 'test' in query.lower()

    @pytest.mark.asyncio
    async def test_count_tools(self, tool_service, mock_containers):
        """Test counting tools."""
        tools_container, _ = mock_containers
        
        async def count_iter():
            yield 42
        
        tools_container.query_items.return_value = count_iter()

        result = await tool_service.count_tools()

        assert result == 42
