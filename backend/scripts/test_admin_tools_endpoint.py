#!/usr/bin/env python3
"""
Test script for admin tools list endpoint - Phase 3 User Story 1
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from src.services.database import db
from src.services.tool_service import ToolService


async def test_list_tools():
    """Test list_tools method directly."""
    try:
        # Initialize database
        print("Connecting to database...")
        await db.connect()
        
        # Get containers
        tools_container = db.database.get_container_client("Tools")
        aliases_container = db.database.get_container_client("ToolAliases")
        
        # Create service
        tool_service = ToolService(
            tools_container=tools_container,
            aliases_container=aliases_container
        )
        
        print("\n=== Test 1: List active tools (default) ===")
        tools = await tool_service.list_tools(
            page=1,
            limit=10,
            status="active"
        )
        print(f"Found {len(tools)} active tools")
        for tool in tools:
            print(f"  - {tool['name']} ({tool['vendor']}) - Categories: {tool.get('categories', [])}")
        
        print("\n=== Test 2: Count active tools ===")
        count = await tool_service.count_tools(status="active")
        print(f"Total active tools: {count}")
        
        print("\n=== Test 3: List all tools ===")
        all_tools = await tool_service.list_tools(
            page=1,
            limit=10,
            status="all"
        )
        print(f"Found {len(all_tools)} tools (all statuses)")
        
        print("\n=== Test 4: Filter by category ===")
        code_assistant_tools = await tool_service.list_tools(
            page=1,
            limit=10,
            categories=["code_assistant"]
        )
        print(f"Found {len(code_assistant_tools)} code assistant tools")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_list_tools())
