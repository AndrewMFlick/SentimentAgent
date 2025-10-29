"""Unit tests for tool merging (Phase 7: User Story 5)."""

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
    merge_records_container = MagicMock()
    return (
        tools_container,
        aliases_container,
        admin_logs_container,
        sentiment_container,
        merge_records_container,
    )


@pytest.fixture
def tool_service(mock_containers):
    """Create ToolService instance with mock containers."""
    (
        tools_container,
        aliases_container,
        admin_logs_container,
        sentiment_container,
        merge_records_container,
    ) = mock_containers
    return ToolService(
        tools_container=tools_container,
        aliases_container=aliases_container,
        admin_logs_container=admin_logs_container,
        sentiment_container=sentiment_container,
        merge_records_container=merge_records_container,
    )


@pytest.fixture
def sample_target_tool():
    """Create sample target tool document."""
    return {
        "id": "target-tool-123",
        "partitionKey": "TOOL",
        "name": "Target Tool",
        "slug": "target-tool",
        "vendor": "Target Vendor",
        "categories": ["code_assistant"],
        "status": "active",
        "description": "Target tool for merging",
        "metadata": {},
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z",
        "created_by": "admin",
        "updated_by": "admin",
    }


@pytest.fixture
def sample_source_tools():
    """Create sample source tool documents."""
    return [
        {
            "id": "source-tool-1",
            "partitionKey": "TOOL",
            "name": "Source Tool 1",
            "slug": "source-tool-1",
            "vendor": "Target Vendor",
            "categories": ["code_assistant", "code_review"],
            "status": "active",
            "description": "First source tool",
            "metadata": {},
            "created_at": "2025-01-14T10:00:00Z",
            "updated_at": "2025-01-14T10:00:00Z",
            "created_by": "admin",
            "updated_by": "admin",
        },
        {
            "id": "source-tool-2",
            "partitionKey": "TOOL",
            "name": "Source Tool 2",
            "slug": "source-tool-2",
            "vendor": "Target Vendor",
            "categories": ["testing"],
            "status": "active",
            "description": "Second source tool",
            "metadata": {},
            "created_at": "2025-01-13T10:00:00Z",
            "updated_at": "2025-01-13T10:00:00Z",
            "created_by": "admin",
            "updated_by": "admin",
        },
    ]


def create_mock_query_function(target_tool, source_tools, sentiment_items=None):
    """
    Helper function to create a mock query_items function for merge tests.

    Args:
        target_tool: The target tool document
        source_tools: List of source tool documents
        sentiment_items: Dict mapping tool_id to list of sentiment items

    Returns:
        A function that can be used as side_effect for query_items mock
    """
    if sentiment_items is None:
        sentiment_items = {}

    # Create lookup dictionary
    all_tools = {target_tool["id"]: target_tool}
    for tool in source_tools:
        all_tools[tool["id"]] = tool

    def mock_query_items(query=None, parameters=None, **kwargs):
        # Tool lookup by ID
        if "t.id = @id" in query:
            tool_id = next(
                (p["value"] for p in parameters if p["name"] == "@id"), None
            )
            tool = all_tools.get(tool_id)
            return [tool] if tool else []

        # Sentiment data query
        if "c.tool_id = @tool_id" in query:
            tool_id = next(
                (p["value"] for p in parameters if p["name"] == "@tool_id"), None
            )
            return sentiment_items.get(tool_id, [])

        # Default case
        return []

    return mock_query_items


@pytest.mark.asyncio
async def test_validate_merge_success(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test successful merge validation."""
    tools_container = mock_containers[0]

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation
    target, sources, warnings = await tool_service._validate_merge(
        "target-tool-123", ["source-tool-1", "source-tool-2"]
    )

    # Assertions
    assert target["id"] == "target-tool-123"
    assert len(sources) == 2
    assert sources[0]["id"] == "source-tool-1"
    assert sources[1]["id"] == "source-tool-2"
    assert len(warnings) == 0  # Same vendor, so no warnings


@pytest.mark.asyncio
async def test_validate_merge_vendor_mismatch_warning(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test merge validation generates warning for vendor mismatch."""
    tools_container = mock_containers[0]

    # Change vendor on one source tool
    sample_source_tools[1]["vendor"] = "Different Vendor"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation
    target, sources, warnings = await tool_service._validate_merge(
        "target-tool-123", ["source-tool-1", "source-tool-2"]
    )

    # Assertions
    assert len(warnings) == 1
    assert warnings[0]["type"] == "vendor_mismatch"
    assert "different vendors" in warnings[0]["message"].lower()


@pytest.mark.asyncio
async def test_validate_merge_target_not_found(
    tool_service, mock_containers, sample_source_tools
):
    """Test merge validation fails when target tool not found."""
    tools_container = mock_containers[0]

    # Setup mock query that returns empty for target
    def mock_query(query=None, parameters=None, **kwargs):
        return []

    tools_container.query_items.side_effect = mock_query

    # Call validation and expect error
    with pytest.raises(ValueError, match="Target tool .* not found"):
        await tool_service._validate_merge(
            "nonexistent-tool", ["source-tool-1", "source-tool-2"]
        )


@pytest.mark.asyncio
async def test_validate_merge_source_not_found(
    tool_service, mock_containers, sample_target_tool
):
    """Test merge validation fails when source tool not found."""
    tools_container = mock_containers[0]

    # Setup mock query that only returns target tool
    def mock_query(query=None, parameters=None, **kwargs):
        if "t.id = @id" in query:
            tool_id = next(
                (p["value"] for p in parameters if p["name"] == "@id"), None
            )
            if tool_id == "target-tool-123":
                return [sample_target_tool]
        return []

    tools_container.query_items.side_effect = mock_query

    # Call validation and expect error
    with pytest.raises(ValueError, match="Source tool .* not found"):
        await tool_service._validate_merge(
            "target-tool-123", ["nonexistent-source"]
        )


@pytest.mark.asyncio
async def test_validate_merge_target_not_active(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test merge validation fails when target tool is not active."""
    tools_container = mock_containers[0]

    # Set target as archived
    sample_target_tool["status"] = "archived"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation and expect error
    with pytest.raises(ValueError, match="Target tool must be active"):
        await tool_service._validate_merge(
            "target-tool-123", ["source-tool-1", "source-tool-2"]
        )


@pytest.mark.asyncio
async def test_validate_merge_source_not_active(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test merge validation fails when source tool is not active."""
    tools_container = mock_containers[0]

    # Set one source as archived
    sample_source_tools[0]["status"] = "archived"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation and expect error
    with pytest.raises(ValueError, match="Source tool .* must be active"):
        await tool_service._validate_merge(
            "target-tool-123", ["source-tool-1", "source-tool-2"]
        )


@pytest.mark.asyncio
async def test_validate_merge_target_already_merged(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test merge validation fails when target tool already merged."""
    tools_container = mock_containers[0]

    # Set target as already merged
    sample_target_tool["merged_into"] = "some-other-tool"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation and expect error
    with pytest.raises(ValueError, match="Target tool has already been merged"):
        await tool_service._validate_merge(
            "target-tool-123", ["source-tool-1", "source-tool-2"]
        )


@pytest.mark.asyncio
async def test_validate_merge_source_already_merged(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test merge validation fails when source tool already merged."""
    tools_container = mock_containers[0]

    # Set source as already merged
    sample_source_tools[1]["merged_into"] = "some-other-tool"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Call validation and expect error
    with pytest.raises(ValueError, match="Source tool .* has already been merged"):
        await tool_service._validate_merge(
            "target-tool-123", ["source-tool-1", "source-tool-2"]
        )


@pytest.mark.asyncio
async def test_validate_merge_circular_reference(
    tool_service, mock_containers, sample_target_tool
):
    """Test merge validation fails when trying to merge tool into itself."""
    tools_container = mock_containers[0]

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, []
    )

    # Call validation and expect error
    with pytest.raises(ValueError, match="Cannot merge tool into itself"):
        await tool_service._validate_merge(
            "target-tool-123", ["target-tool-123"]
        )


@pytest.mark.asyncio
async def test_migrate_sentiment_data_success(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test successful sentiment data migration."""
    sentiment_container = mock_containers[3]

    # Create sample sentiment items
    sentiment_items = {
        "source-tool-1": [
            {
                "id": "sentiment-1",
                "tool_id": "source-tool-1",
                "sentiment": "positive",
                "score": 0.8,
            },
            {
                "id": "sentiment-2",
                "tool_id": "source-tool-1",
                "sentiment": "negative",
                "score": -0.5,
            },
        ],
        "source-tool-2": [
            {
                "id": "sentiment-3",
                "tool_id": "source-tool-2",
                "sentiment": "neutral",
                "score": 0.1,
            }
        ],
    }

    # Setup mock query - need to return iterables
    def mock_sentiment_query(query=None, parameters=None, **kwargs):
        if "c.tool_id = @tool_id" in query:
            tool_id = next(
                (p["value"] for p in parameters if p["name"] == "@tool_id"), None
            )
            return sentiment_items.get(tool_id, [])
        return []

    sentiment_container.query_items.side_effect = mock_sentiment_query

    # Mock upsert_item (not create_item)
    sentiment_container.upsert_item = MagicMock()

    # Call migration
    count = await tool_service._migrate_sentiment_data(
        "target-tool-123", ["source-tool-1", "source-tool-2"]
    )

    # Assertions
    assert count == 3
    assert sentiment_container.upsert_item.call_count == 3

    # Verify migrated items have correct structure
    for call in sentiment_container.upsert_item.call_args_list:
        migrated_item = call[1]["body"]
        assert migrated_item["tool_id"] == "target-tool-123"
        assert "original_tool_id" in migrated_item
        assert "migrated_at" in migrated_item


@pytest.mark.asyncio
async def test_migrate_sentiment_data_no_container(
    tool_service, sample_target_tool, sample_source_tools
):
    """Test sentiment data migration when sentiment container not available."""
    # Create service without sentiment container
    tool_service_no_sentiment = ToolService(
        tools_container=MagicMock(),
        aliases_container=MagicMock(),
        admin_logs_container=MagicMock(),
    )

    # Call migration
    count = await tool_service_no_sentiment._migrate_sentiment_data(
        "target-tool-123", ["source-tool-1", "source-tool-2"]
    )

    # Should return 0 without error
    assert count == 0


@pytest.mark.asyncio
async def test_merge_tools_success(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test successful tool merge operation."""
    (
        tools_container,
        aliases_container,
        admin_logs_container,
        sentiment_container,
        merge_records_container,
    ) = mock_containers

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )

    # Mock sentiment migration (3 items)
    sentiment_items = {
        "source-tool-1": [{"id": "s1"}],
        "source-tool-2": [{"id": "s2"}, {"id": "s3"}],
    }
    sentiment_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools, sentiment_items
    )
    sentiment_container.create_item = MagicMock()

    # Mock replace_item for tools
    tools_container.replace_item = MagicMock()

    # Mock create_item for merge record
    merge_records_container.create_item = MagicMock()

    # Mock create_item for admin log
    admin_logs_container.create_item = MagicMock()

    # Call merge
    result = await tool_service.merge_tools(
        target_tool_id="target-tool-123",
        source_tool_ids=["source-tool-1", "source-tool-2"],
        target_categories=["code_assistant", "code_review", "testing"],
        target_vendor="Target Vendor",
        merged_by="admin-user",
        notes="Merging tools after acquisition",
    )

    # Assertions
    assert "merge_record" in result
    assert "target_tool" in result
    assert "archived_tools" in result
    assert "warnings" in result

    # Verify merge record
    merge_record = result["merge_record"]
    assert merge_record["target_tool_id"] == "target-tool-123"
    assert merge_record["source_tool_ids"] == ["source-tool-1", "source-tool-2"]
    assert merge_record["sentiment_count"] == 3
    assert merge_record["merged_by"] == "admin-user"
    assert merge_record["notes"] == "Merging tools after acquisition"

    # Verify target tool updated
    target_tool = result["target_tool"]
    assert target_tool["categories"] == ["code_assistant", "code_review", "testing"]
    assert target_tool["vendor"] == "Target Vendor"
    assert target_tool["updated_by"] == "admin-user"

    # Verify source tools archived
    archived_tools = result["archived_tools"]
    assert len(archived_tools) == 2
    for archived_tool in archived_tools:
        assert archived_tool["status"] == "archived"
        assert archived_tool["merged_into"] == "target-tool-123"
        assert archived_tool["updated_by"] == "admin-user"

    # Verify containers called correctly
    assert tools_container.replace_item.call_count == 3  # 1 target + 2 sources
    assert merge_records_container.create_item.call_count == 1
    assert admin_logs_container.create_item.call_count == 1


@pytest.mark.asyncio
async def test_merge_tools_with_warnings(
    tool_service, mock_containers, sample_target_tool, sample_source_tools
):
    """Test tool merge operation with metadata warnings."""
    (
        tools_container,
        aliases_container,
        admin_logs_container,
        sentiment_container,
        merge_records_container,
    ) = mock_containers

    # Change vendor on source to trigger warning
    sample_source_tools[1]["vendor"] = "Different Vendor"

    # Setup mock query
    tools_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools
    )
    sentiment_container.query_items.side_effect = create_mock_query_function(
        sample_target_tool, sample_source_tools, {}
    )
    sentiment_container.create_item = MagicMock()
    tools_container.replace_item = MagicMock()
    merge_records_container.create_item = MagicMock()
    admin_logs_container.create_item = MagicMock()

    # Call merge
    result = await tool_service.merge_tools(
        target_tool_id="target-tool-123",
        source_tool_ids=["source-tool-1", "source-tool-2"],
        target_categories=["code_assistant"],
        target_vendor="Target Vendor",
        merged_by="admin-user",
    )

    # Assertions - should have vendor mismatch warning
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["type"] == "vendor_mismatch"


@pytest.mark.asyncio
async def test_get_merge_history(tool_service, mock_containers):
    """Test retrieving merge history for a tool."""
    tools_container = mock_containers[0]
    merge_records_container = mock_containers[4]

    # Mock read_item to validate tool exists
    tools_container.read_item = MagicMock(
        return_value={"id": "target-tool-123", "name": "Target Tool"}
    )

    # Sample merge records
    merge_records = [
        {
            "id": "merge-1",
            "target_tool_id": "target-tool-123",
            "source_tool_ids": ["source-1", "source-2"],
            "merged_at": "2025-01-15T10:00:00Z",
            "sentiment_count": 100,
        },
        {
            "id": "merge-2",
            "target_tool_id": "target-tool-123",
            "source_tool_ids": ["source-3"],
            "merged_at": "2025-01-14T10:00:00Z",
            "sentiment_count": 50,
        },
    ]

    # Setup mock query - need to handle both count and data queries
    def mock_merge_query(query=None, parameters=None, **kwargs):
        if "COUNT(1)" in query:
            return [2]  # Total count
        else:
            return merge_records  # Actual records

    merge_records_container.query_items = MagicMock(side_effect=mock_merge_query)

    # Call get_merge_history
    result = await tool_service.get_merge_history("target-tool-123", page=1, limit=10)

    # Assertions
    assert result["total"] == 2
    assert len(result["merge_records"]) == 2
    assert result["page"] == 1
    assert result["limit"] == 10
    assert result["has_more"] is False
    assert result["merge_records"][0]["id"] == "merge-1"
