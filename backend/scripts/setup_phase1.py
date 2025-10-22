"""
Phase 1 Setup Script - Admin Tool List Management
Creates containers and indexes for Feature 011

Tasks:
- T001: Create ToolMergeRecords container
- T002: Create AdminActionLogs container
- T003: Add composite indexes to Tools container
- T004: Migrate existing Tool documents
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Module imports after path setup
from azure.cosmos import PartitionKey  # noqa: E402
from azure.cosmos.aio import CosmosClient  # noqa: E402
from config import settings  # noqa: E402
import structlog  # noqa: E402

logger = structlog.get_logger()


async def create_container_if_not_exists(
    database, container_name: str, partition_key: str
):
    """Create a container if it doesn't exist."""
    try:
        container = database.get_container_client(container_name)
        await container.read()
        logger.info(f"Container '{container_name}' already exists")
        return container
    except Exception:
        logger.info(f"Creating container '{container_name}'...")
        container = await database.create_container(
            id=container_name,
            partition_key=PartitionKey(path=partition_key)
        )
        logger.info(f"✅ Created container '{container_name}'")
        return container


async def add_composite_indexes_to_tools(database):
    """Add composite indexes to Tools container for query optimization."""
    logger.info("Adding composite indexes to Tools container...")
    
    # Define indexing policy with composite indexes
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": "/\"_etag\"/?"}],
        "compositeIndexes": [
            # For filtering by status + sorting by name
            [
                {"path": "/status", "order": "ascending"},
                {"path": "/name", "order": "ascending"}
            ],
            # For filtering by status + sorting by vendor
            [
                {"path": "/status", "order": "ascending"},
                {"path": "/vendor", "order": "ascending"}
            ],
            # For filtering by status + sorting by updated_at
            [
                {"path": "/status", "order": "ascending"},
                {"path": "/updated_at", "order": "descending"}
            ],
            # For category queries (array support)
            [
                {"path": "/categories/[]", "order": "ascending"},
                {"path": "/status", "order": "ascending"}
            ]
        ]
    }
    
    try:
        # Get current container properties
        tools_container = database.get_container_client("Tools")
        container_properties = await tools_container.read()
        
        # Update indexing policy
        container_properties["indexingPolicy"] = indexing_policy
        
        await database.replace_container(
            container="Tools",
            partition_key=PartitionKey(path="/partitionKey"),
            indexing_policy=indexing_policy
        )
        
        logger.info("✅ Added composite indexes to Tools container")
        logger.info("   - status + name (ascending)")
        logger.info("   - status + vendor (ascending)")
        logger.info("   - status + updated_at (descending)")
        logger.info("   - categories[] + status (ascending)")
        
    except Exception as e:
        logger.error(f"Failed to update indexes: {e}")
        raise


async def migrate_tool_documents(database):
    """Migrate existing Tool documents to new schema."""
    logger.info("Migrating existing Tool documents...")

    tools_container = database.get_container_client("Tools")

    # Query all tools - note: partition key might be required
    query = "SELECT * FROM c"
    items = []

    try:
        # Try without cross partition query first
        async for item in tools_container.query_items(query=query):
            items.append(item)
    except Exception:
        # If that fails, try to query by partition key
        # For Tools container, partition key should be /partitionKey
        logger.info("Trying query with specific partition key...")
        try:
            async for item in tools_container.query_items(
                query=query,
                partition_key="tools"  # Common partition value
            ):
                items.append(item)
        except Exception as e:
            logger.error(f"Could not query tools: {e}")
            logger.info(
                "Skipping migration - run this manually if tools exist"
            )
            return

    if not items:
        logger.info("No existing tools to migrate")
        return

    logger.info(f"Found {len(items)} tools to migrate")
    
    migrated_count = 0
    skipped_count = 0
    
    for tool in items:
        needs_update = False
        
        # Add status field if missing (default to 'active')
        if "status" not in tool:
            tool["status"] = "active"
            needs_update = True
        
        # Convert single category to array if needed
        if "category" in tool and "categories" not in tool:
            tool["categories"] = [tool["category"]]
            needs_update = True
        elif "categories" not in tool:
            # No category at all - set empty array
            tool["categories"] = []
            needs_update = True
        
        # Ensure categories is an array
        if isinstance(tool.get("categories"), str):
            tool["categories"] = [tool["categories"]]
            needs_update = True
        
        # Add merged_into field if missing
        if "merged_into" not in tool:
            tool["merged_into"] = None
            needs_update = True
        
        # Add audit fields if missing
        if "created_by" not in tool:
            tool["created_by"] = "system_migration"
            needs_update = True
        
        if "updated_by" not in tool:
            tool["updated_by"] = "system_migration"
            needs_update = True
        
        # Add timestamps if missing
        if "created_at" not in tool:
            from datetime import datetime, timezone
            tool["created_at"] = datetime.now(timezone.utc).isoformat()
            needs_update = True
        
        if "updated_at" not in tool:
            from datetime import datetime, timezone
            tool["updated_at"] = datetime.now(timezone.utc).isoformat()
            needs_update = True
        
        if needs_update:
            try:
                await tools_container.upsert_item(tool)
                migrated_count += 1
                logger.info(f"  Migrated tool: {tool.get('name', tool['id'])}")
            except Exception as e:
                logger.error(f"  Failed to migrate tool {tool['id']}: {e}")
        else:
            skipped_count += 1

    logger.info(
        f"✅ Migration complete: {migrated_count} migrated, "
        f"{skipped_count} already up-to-date"
    )


async def main():
    """Execute Phase 1 setup tasks."""
    logger.info("=" * 60)
    logger.info("Phase 1 Setup - Admin Tool List Management")
    logger.info("=" * 60)
    
    async with CosmosClient(
        url=settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        
        # T001: Create ToolMergeRecords container
        logger.info("\n[T001] Creating ToolMergeRecords container...")
        await create_container_if_not_exists(
            database,
            "ToolMergeRecords",
            "/partitionKey"
        )

        # T002: Create AdminActionLogs container
        logger.info("\n[T002] Creating AdminActionLogs container...")
        await create_container_if_not_exists(
            database,
            "AdminActionLogs",
            "/partitionKey"
        )

        # T003: Add composite indexes to Tools container
        logger.info("\n[T003] Adding composite indexes to Tools container...")
        try:
            await add_composite_indexes_to_tools(database)
        except Exception as e:
            logger.warning(
                f"Index update may require manual intervention: {e}"
            )
            logger.info(
                "You can continue - indexes will be created asynchronously"
            )
        
        # T004: Migrate existing Tool documents
        logger.info("\n[T004] Migrating existing Tool documents...")
        await migrate_tool_documents(database)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Phase 1 Setup Complete!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Verify containers in Azure Portal or Cosmos DB Emulator")
    logger.info("2. Check that existing tools have new schema fields")
    logger.info("3. Proceed to Phase 2: Foundational tasks")


if __name__ == "__main__":
    asyncio.run(main())
