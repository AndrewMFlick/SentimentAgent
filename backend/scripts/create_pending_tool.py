#!/usr/bin/env python3
"""Create a pending tool for testing the Admin page."""
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


async def create_pending_tool():
    """Create a sample pending tool for admin approval testing."""
    logger.info("Creating pending tool for admin page testing")
    
    pending_tool = {
        "id": "cursor-editor",
        "name": "Cursor Editor",
        "vendor": "Cursor",
        "category": "AI Assistant",
        "aliases": [
            "cursor",
            "cursor editor",
            "cursor ide",
            "cursor app"
        ],
        "status": "pending",  # This makes it appear in admin panel
        "detection_threshold": 0.7,
        "first_detected_at": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    async with CosmosClient(
        settings.cosmos_endpoint,
        credential=settings.cosmos_key
    ) as client:
        database = client.get_database_client(settings.cosmos_database)
        container = database.get_container_client("ai_tools")
        
        try:
            # Check if tool already exists
            await container.read_item(
                item=pending_tool["id"],
                partition_key=pending_tool["id"]
            )
            logger.info(
                f"Tool already exists: {pending_tool['name']}",
                tool_id=pending_tool["id"]
            )
        except Exception:
            # Create tool
            await container.create_item(body=pending_tool)
            logger.info(
                f"✅ Created pending tool: {pending_tool['name']}",
                tool_id=pending_tool["id"],
                status=pending_tool["status"]
            )
    
    print("\n" + "="*60)
    print("✅ PENDING TOOL CREATED!")
    print("="*60)
    print(f"\nTool: {pending_tool['name']}")
    print(f"Status: {pending_tool['status']}")
    print(f"ID: {pending_tool['id']}")
    print("\nNext steps:")
    print("1. Open http://localhost:5173/admin")
    print("2. Enter admin token: 'admin' (or any text)")
    print("3. You should see 'Cursor Editor' in the pending tools list")
    print("4. Click '✓ Approve' to approve it")
    print("5. Navigate to the main dashboard to see it appear!")
    print("\nTo test rejection:")
    print("- Run this script again to re-create the tool")
    print("- Click '✗ Reject' instead of approve")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(create_pending_tool())
