#!/usr/bin/env python3
"""Create a pending tool for testing the Admin page."""
import sys
import os
import warnings
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos import CosmosClient, exceptions
from src.config import settings
import structlog

# Disable SSL warnings for local emulator
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = structlog.get_logger()


def create_pending_tool():
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
    
    # For local emulator, disable SSL verification
    if "localhost" in settings.cosmos_endpoint:
        os.environ['AZURE_COSMOS_DISABLE_SSL_VERIFICATION'] = 'true'
        client = CosmosClient(
            settings.cosmos_endpoint,
            credential=settings.cosmos_key,
            connection_verify=False
        )
    else:
        client = CosmosClient(
            settings.cosmos_endpoint,
            credential=settings.cosmos_key
        )
    
    database = client.get_database_client(settings.cosmos_database)
    container = database.get_container_client("ai_tools")
    
    try:
        # Check if tool already exists
        container.read_item(
            item=pending_tool["id"],
            partition_key=pending_tool["id"]
        )
        logger.info(
            f"Tool already exists: {pending_tool['name']}",
            tool_id=pending_tool["id"]
        )
        print(f"\nℹ️  Tool '{pending_tool['name']}' already exists in database.")
        print("   To see it in admin panel, it may have been approved or rejected.")
        print("   Check its current status or delete it first to test again.\n")
    except exceptions.CosmosResourceNotFoundError:
        # Create tool
        container.upsert_item(body=pending_tool)
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
    create_pending_tool()
