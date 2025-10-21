#!/usr/bin/env python3
"""Seed initial AI tools (GitHub Copilot, Jules AI)."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos.aio import CosmosClient
from src.config import settings
import structlog

logger = structlog.get_logger()


async def seed_tools():
    """Seed initial approved AI tools."""
    logger.info("Starting tool seeding")
    
    # Initial tools to seed
    initial_tools = [
        {
            "id": "github-copilot",
            "name": "GitHub Copilot",
            "vendor": "GitHub/Microsoft",
            "category": "AI Assistant",
            "aliases": [
                "copilot",
                "gh copilot",
                "github copilot",
                "ghcopilot"
            ],
            "status": "approved",
            "detection_threshold": 0.7,
            "approved_by": "system",
            "approved_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "jules-ai",
            "name": "Jules AI",
            "vendor": "Jules",
            "category": "AI Agent",
            "aliases": [
                "jules",
                "julesai",
                "jules ai",
                "jules agent"
            ],
            "status": "approved",
            "detection_threshold": 0.7,
            "approved_by": "system",
            "approved_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    async with CosmosClient(
        settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        container = database.get_container_client("ai_tools")
        
        for tool in initial_tools:
            try:
                # Check if tool exists
                await container.read_item(
                    item=tool["id"],
                    partition_key=tool["id"]
                )
                logger.info(
                    f"Tool already exists: {tool['name']}",
                    tool_id=tool["id"]
                )
            except Exception:
                # Create tool
                await container.create_item(body=tool)
                logger.info(
                    f"✅ Seeded tool: {tool['name']}",
                    tool_id=tool["id"],
                    status=tool["status"]
                )
    
    logger.info("Tool seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_tools())
