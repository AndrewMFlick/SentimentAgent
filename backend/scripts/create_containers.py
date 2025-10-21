#!/usr/bin/env python3
"""Create CosmosDB containers for AI Tools feature."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from src.config import settings
import structlog

logger = structlog.get_logger()


async def create_containers():
    """Create new containers for AI Tools feature."""
    logger.info("Starting container creation for AI Tools feature")
    
    async with CosmosClient(
        settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        
        # Container configurations
        containers = [
            {
                "id": "ai_tools",
                "partition_key": PartitionKey(path="/id"),
                "description": "AI developer tools tracking"
            },
            {
                "id": "tool_mentions",
                "partition_key": PartitionKey(path="/tool_id"),
                "description": "Tool mentions in Reddit content"
            },
            {
                "id": "time_period_aggregates",
                "partition_key": PartitionKey(path="/tool_id"),
                "description": "Pre-computed daily sentiment aggregates"
            }
        ]
        
        for container_config in containers:
            container_id = container_config["id"]
            try:
                # Check if container exists
                container = database.get_container_client(container_id)
                await container.read()
                logger.info(
                    f"Container already exists: {container_id}",
                    container=container_id
                )
            except Exception:
                # Create container
                logger.info(
                    f"Creating container: {container_id}",
                    container=container_id,
                    description=container_config["description"]
                )
                await database.create_container(
                    id=container_id,
                    partition_key=container_config["partition_key"]
                )
                logger.info(
                    f"✅ Created container: {container_id}",
                    container=container_id
                )
    
    logger.info("Container creation complete")


if __name__ == "__main__":
    asyncio.run(create_containers())
