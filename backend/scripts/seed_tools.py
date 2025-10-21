#!/usr/bin/env python3
"""Seed initial AI tools into Tools container."""
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos.aio import CosmosClient
from src.config import settings
import structlog

logger = structlog.get_logger()


async def seed_tools():
    """Seed initial tools into Tools container."""
    logger.info("Starting tool seeding for Tools container")

    now = datetime.now(timezone.utc).isoformat()

    # Initial tools matching new schema
    initial_tools = [
        {
            "id": str(uuid.uuid4()),
            "partitionKey": "tool",
            "name": "GitHub Copilot",
            "slug": "github-copilot",
            "vendor": "GitHub",
            "category": "code-completion",
            "description": (
                "AI pair programmer that suggests code and entire functions"
            ),
            "status": "active",
            "metadata": {
                "website": "https://github.com/features/copilot",
                "documentation": "https://docs.github.com/copilot",
                "pricing": "subscription"
            },
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid.uuid4()),
            "partitionKey": "tool",
            "name": "Jules AI",
            "slug": "jules-ai",
            "vendor": "Jules",
            "category": "code-completion",
            "description": "AI coding assistant for enhanced productivity",
            "status": "active",
            "metadata": {
                "website": "https://jules.ai",
                "pricing": "freemium"
            },
            "created_at": now,
            "updated_at": now
        }
    ]

    async with CosmosClient(
        settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        container = database.get_container_client("Tools")

        for tool in initial_tools:
            try:
                # Check if tool with same name exists
                query = (
                    "SELECT * FROM Tools t "
                    "WHERE t.name = @name AND t.partitionKey = 'tool'"
                )
                items = container.query_items(
                    query=query,
                    parameters=[{"name": "@name", "value": tool["name"]}]
                )

                # Check if any items exist
                existing = []
                async for item in items:
                    existing.append(item)

                if existing:
                    logger.info(
                        f"Tool already exists: {tool['name']}",
                        tool_id=existing[0]["id"]
                    )
                    continue

                # Create tool
                await container.create_item(body=tool)
                logger.info(
                    f"✅ Seeded tool: {tool['name']}",
                    tool_id=tool["id"],
                    slug=tool["slug"],
                    category=tool["category"]
                )
            except Exception as e:
                logger.error(
                    f"Failed to seed {tool['name']}",
                    error=str(e)
                )

    logger.info("Tool seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_tools())
