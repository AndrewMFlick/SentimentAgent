"""
Quick test for Phase 3 User Story 1 - List Tools API

Tests the enhanced list_tools endpoint with filtering and pagination.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from azure.cosmos.aio import CosmosClient  # noqa: E402
from config import settings  # noqa: E402
from services.tool_service import ToolService  # noqa: E402
import structlog  # noqa: E402

logger = structlog.get_logger()


async def test_list_tools():
    """Test list_tools with various filters."""
    logger.info("Testing list_tools functionality...")

    async with CosmosClient(
        url=settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        tools_container = database.get_container_client("Tools")
        aliases_container = database.get_container_client("ToolAliases")

        tool_service = ToolService(
            tools_container=tools_container,
            aliases_container=aliases_container
        )

        # Test 1: List all active tools (default)
        logger.info("\n=== Test 1: List all active tools ===")
        tools = await tool_service.list_tools()
        logger.info(f"Found {len(tools)} active tools")
        for tool in tools:
            logger.info(
                f"  - {tool.get('name')}: "
                f"categories={tool.get('categories')}, "
                f"status={tool.get('status')}"
            )

        # Test 2: Filter by status = all
        logger.info("\n=== Test 2: List all tools (active + archived) ===")
        all_tools = await tool_service.list_tools(status="all")
        logger.info(f"Found {len(all_tools)} total tools")

        # Test 3: Search by name
        logger.info("\n=== Test 3: Search for 'copilot' ===")
        search_results = await tool_service.list_tools(search="copilot")
        logger.info(f"Found {len(search_results)} matching tools")
        for tool in search_results:
            logger.info(f"  - {tool.get('name')}")

        # Test 4: Filter by category
        logger.info("\n=== Test 4: Filter by code-completion category ===")
        category_results = await tool_service.list_tools(
            categories=["code-completion"]
        )
        logger.info(f"Found {len(category_results)} code-completion tools")

        # Test 5: Pagination
        logger.info("\n=== Test 5: Pagination (page 1, limit 2) ===")
        page1 = await tool_service.list_tools(page=1, limit=2)
        logger.info(f"Page 1: {len(page1)} tools")
        for tool in page1:
            logger.info(f"  - {tool.get('name')}")

        # Test 6: Count tools
        logger.info("\n=== Test 6: Count tools ===")
        count = await tool_service.count_tools()
        logger.info(f"Total active tools: {count}")

        logger.info("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_list_tools())
