#!/usr/bin/env python3
"""
Debug script to check why reanalysis job fails.
Run this to diagnose the 400 error.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from azure.cosmos import CosmosClient

async def check_reanalysis_prerequisites():
    """Check all prerequisites for reanalysis"""
    print("=== Reanalysis Prerequisites Check ===\n")
    
    # 1. Check admin token
    print(f"1. Admin Token: {settings.ADMIN_TOKEN}")
    print(f"   - Use this token in your curl command\n")
    
    # 2. Check database connection
    print("2. Connecting to Cosmos DB...")
    try:
        client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        database = client.get_database_client(settings.COSMOS_DATABASE)
        print(f"   ✓ Connected to: {settings.COSMOS_ENDPOINT}")
        print(f"   ✓ Database: {settings.COSMOS_DATABASE}\n")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}\n")
        return
    
    # 3. Check sentiment_scores container
    print("3. Checking sentiment_scores container...")
    try:
        sentiment_container = database.get_container_client("sentiment_scores")
        
        # Count total sentiment scores
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE true"
        result = list(sentiment_container.query_items(
            query=count_query,
            enable_cross_partition_query=True
        ))
        
        # Handle different response formats
        if result and len(result) > 0:
            first = result[0]
            total_count = int(first['count']) if isinstance(first, dict) else int(first)
        else:
            total_count = 0
            
        print(f"   ✓ Total sentiment scores: {total_count}")
        
        if total_count == 0:
            print("   ⚠️  No sentiment scores to reanalyze!")
            print("   → Wait for Reddit data collection to run first\n")
            return
        
        # Count scores without detected_tool_ids
        missing_query = "SELECT VALUE COUNT(1) FROM c WHERE true AND (NOT IS_DEFINED(c.detected_tool_ids) OR ARRAY_LENGTH(c.detected_tool_ids) = 0)"
        result = list(sentiment_container.query_items(
            query=missing_query,
            enable_cross_partition_query=True
        ))
        
        if result and len(result) > 0:
            first = result[0]
            missing_count = int(first['count']) if isinstance(first, dict) else int(first)
        else:
            missing_count = 0
            
        print(f"   ✓ Scores missing detected_tool_ids: {missing_count}")
        print(f"   → {missing_count} documents need reanalysis\n")
        
    except Exception as e:
        print(f"   ✗ Query failed: {e}\n")
        return
    
    # 4. Check for active reanalysis jobs
    print("4. Checking for active reanalysis jobs...")
    try:
        jobs_container = database.get_container_client("ReanalysisJobs")
        
        active_query = "SELECT * FROM c WHERE c.status IN ('queued', 'running')"
        active_jobs = list(jobs_container.query_items(
            query=active_query,
            enable_cross_partition_query=True
        ))
        
        if active_jobs:
            print(f"   ⚠️  Found {len(active_jobs)} active job(s):")
            for job in active_jobs:
                print(f"      - Job ID: {job['id']}")
                print(f"        Status: {job['status']}")
                print(f"        Progress: {job['progress']['percentage']:.1f}%")
            print("   → Wait for these jobs to complete or cancel them\n")
        else:
            print("   ✓ No active jobs - ready to start new job\n")
            
    except Exception as e:
        print(f"   ✗ Query failed: {e}\n")
    
    # 5. Check Tools container
    print("5. Checking Tools container...")
    try:
        tools_container = database.get_container_client("Tools")
        
        tools_query = "SELECT * FROM c WHERE c.status = 'active'"
        tools = list(tools_container.query_items(
            query=tools_query,
            enable_cross_partition_query=True
        ))
        
        print(f"   ✓ Active tools: {len(tools)}")
        for tool in tools:
            print(f"      - {tool['name']} ({tool['vendor']})")
        print()
        
    except Exception as e:
        print(f"   ✗ Query failed: {e}\n")
    
    # 6. Generate curl command
    print("=== Ready to Test ===\n")
    print("Use this curl command to trigger reanalysis:\n")
    print(f"""curl -X POST http://localhost:8000/api/v1/admin/reanalysis/jobs \\
  -H "Content-Type: application/json" \\
  -H "X-Admin-Token: {settings.ADMIN_TOKEN}" \\
  -d '{{"batch_size": 100}}'
""")
    
    print("\nOr check job status with:\n")
    print(f"""curl -H "X-Admin-Token: {settings.ADMIN_TOKEN}" \\
  http://localhost:8000/api/v1/admin/reanalysis/jobs
""")

if __name__ == "__main__":
    asyncio.run(check_reanalysis_prerequisites())
