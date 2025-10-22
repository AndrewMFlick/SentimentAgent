"""Verify Phase 1 setup results."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from azure.cosmos.aio import CosmosClient  # noqa: E402
from config import settings  # noqa: E402
import structlog  # noqa: E402

logger = structlog.get_logger()


async def main():
    """Verify Phase 1 setup."""
    logger.info("=" * 60)
    logger.info("Phase 1 Verification")
    logger.info("=" * 60)

    async with CosmosClient(
        url=settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)

        # Verify containers exist
        logger.info("\n✓ Checking containers...")
        containers = ["Tools", "ToolMergeRecords", "AdminActionLogs"]
        for container_name in containers:
            try:
                container = database.get_container_client(container_name)
                await container.read()
                logger.info(f"  ✅ {container_name} exists")
            except Exception as e:
                logger.error(f"  ❌ {container_name} missing: {e}")

        # Check migrated tools
        logger.info("\n✓ Checking migrated tools...")
        tools_container = database.get_container_client("Tools")

        try:
            async for tool in tools_container.query_items(
                query="SELECT * FROM c"
            ):
                logger.info(f"\n  Tool: {tool.get('name', 'Unknown')}")
                logger.info(f"    ID: {tool.get('id')}")
                logger.info(
                    f"    Categories: {tool.get('categories', [])}"
                )
                logger.info(f"    Status: {tool.get('status', 'N/A')}")
                logger.info(
                    f"    Merged Into: {tool.get('merged_into', 'N/A')}"
                )
                logger.info(
                    f"    Created By: {tool.get('created_by', 'N/A')}"
                )
                logger.info(
                    f"    Updated By: {tool.get('updated_by', 'N/A')}"
                )
        except Exception as e:
            logger.error(f"Failed to query tools: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("Verification Complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
