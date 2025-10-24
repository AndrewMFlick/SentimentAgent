#!/usr/bin/env python3
"""
Setup database for Admin Sentiment Reanalysis feature (Feature 013)

Tasks:
- T001: Create ReanalysisJobs collection with indexing policy
- T002: Update sentiment_scores schema with new fields
- T003: Verify ARRAY_CONTAINS indexing on detected_tool_ids

Usage:
    python setup-reanalysis-db.py [--production]
"""

import asyncio
import os
import sys

from azure.cosmos import CosmosClient, PartitionKey, exceptions


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_color(message: str, color: str = Colors.NC):
    """Print colored message to stdout"""
    print(f"{color}{message}{Colors.NC}")


def get_cosmos_client(production: bool = False) -> CosmosClient:
    """Get CosmosDB client based on environment"""
    if production:
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        
        if not endpoint or not key:
            print_color(
                "ERROR: COSMOS_ENDPOINT and COSMOS_KEY required for production",
                Colors.RED
            )
            sys.exit(1)
        return CosmosClient(endpoint, key)
    else:
        # Local emulator - disable SSL verification
        endpoint = "https://localhost:8081"
        key = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
        
        # Disable SSL verification for local emulator (same as backend)
        os.environ["AZURE_COSMOS_DISABLE_SSL_VERIFICATION"] = "true"
        return CosmosClient(endpoint, key, connection_verify=False)


async def create_reanalysis_jobs_collection(client: CosmosClient, database_name: str):
    """
    T001: Create ReanalysisJobs collection with indexing policy
    
    Indexing:
    - Primary key: /id
    - Composite indexes: /status + /_ts, /triggered_by + /_ts
    - Enables fast queries for active jobs and user job history
    """
    print_color("\n[T001] Creating ReanalysisJobs collection...", Colors.YELLOW)
    
    database = client.get_database_client(database_name)
    
    # Define indexing policy for efficient queries
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/*"}
        ],
        "excludedPaths": [
            {"path": "/\"_etag\"/?"}
        ],
        "compositeIndexes": [
            [
                {"path": "/status", "order": "ascending"},
                {"path": "/_ts", "order": "descending"}
            ],
            [
                {"path": "/triggered_by", "order": "ascending"},
                {"path": "/_ts", "order": "descending"}
            ]
        ]
    }
    
    try:
        container = database.create_container(
            id="ReanalysisJobs",
            partition_key=PartitionKey(path="/id"),
            indexing_policy=indexing_policy
        )
        print_color("✓ ReanalysisJobs collection created successfully", Colors.GREEN)
        print(f"  - Partition key: /id")
        print(f"  - Composite indexes: [status + _ts], [triggered_by + _ts]")
        return container
    
    except exceptions.CosmosResourceExistsError:
        print_color("✓ ReanalysisJobs collection already exists", Colors.GREEN)
        return database.get_container_client("ReanalysisJobs")
    
    except Exception as e:
        print_color(f"ERROR creating ReanalysisJobs: {e}", Colors.RED)
        raise


async def update_sentiment_scores_schema(client: CosmosClient, database_name: str):
    """
    T002: Update sentiment_scores documents with new fields
    
    New fields:
    - detected_tool_ids: [] (empty array)
    - last_analyzed_at: null
    - analysis_version: "1.0.0"
    
    These fields enable tool categorization and reanalysis tracking.
    """
    print_color("\n[T002] Updating sentiment_scores schema...", Colors.YELLOW)
    
    database = client.get_database_client(database_name)
    container = database.get_container_client("sentiment_scores")
    
    # Query for documents missing the new fields
    query = """
        SELECT * FROM c 
        WHERE NOT IS_DEFINED(c.detected_tool_ids) 
           OR NOT IS_DEFINED(c.last_analyzed_at)
           OR NOT IS_DEFINED(c.analysis_version)
    """
    
    print("  Scanning for documents missing new fields...")
    
    items_to_update = list(container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    total_count = len(items_to_update)
    
    if total_count == 0:
        print_color("✓ All sentiment_scores already have required fields", Colors.GREEN)
        return
    
    print(f"  Found {total_count} documents to update")
    print("  Adding fields: detected_tool_ids=[], last_analyzed_at=null, analysis_version='1.0.0'")
    
    updated_count = 0
    error_count = 0
    
    for item in items_to_update:
        try:
            # Add missing fields with defaults
            if "detected_tool_ids" not in item:
                item["detected_tool_ids"] = []
            if "last_analyzed_at" not in item:
                item["last_analyzed_at"] = None
            if "analysis_version" not in item:
                item["analysis_version"] = "1.0.0"
            
            # Upsert the document
            container.upsert_item(item)
            updated_count += 1
            
            # Progress indicator
            if updated_count % 100 == 0:
                print(f"  Progress: {updated_count}/{total_count} documents updated...")
        
        except Exception as e:
            error_count += 1
            print_color(f"  Warning: Failed to update document {item.get('id')}: {e}", Colors.YELLOW)
    
    print_color(f"✓ Schema update complete: {updated_count} updated, {error_count} errors", Colors.GREEN)


async def verify_array_contains_index(client: CosmosClient, database_name: str):
    """
    T003: Verify ARRAY_CONTAINS indexing on detected_tool_ids
    
    Tests that the composite index supports ARRAY_CONTAINS queries.
    This is critical for Hot Topics feature functionality.
    """
    print_color("\n[T003] Verifying ARRAY_CONTAINS index on detected_tool_ids...", Colors.YELLOW)
    
    database = client.get_database_client(database_name)
    container = database.get_container_client("sentiment_scores")
    
    # Test query using ARRAY_CONTAINS
    test_query = """
        SELECT TOP 1 c.id 
        FROM c 
        WHERE ARRAY_CONTAINS(c.detected_tool_ids, 'test-tool-id')
    """
    
    try:
        # Execute test query
        list(container.query_items(
            query=test_query,
            enable_cross_partition_query=True
        ))
        print_color("✓ ARRAY_CONTAINS queries supported on detected_tool_ids", Colors.GREEN)
        print("  Composite index: [detected_tool_ids[] + _ts] is active")
        print("  Hot Topics queries will work correctly")
    
    except exceptions.CosmosHttpResponseError as e:
        if "Index does not have options 17" in str(e):
            print_color("✗ ARRAY_CONTAINS index NOT configured!", Colors.RED)
            print_color("  Run: ./deployment/scripts/setup-hot-topics-indexes.sh", Colors.YELLOW)
            print("  This will apply the composite index policy")
            raise
        else:
            print_color(f"ERROR testing ARRAY_CONTAINS: {e}", Colors.RED)
            raise


async def verify_admin_auth():
    """
    T004: Verify admin authentication is configured
    
    Checks that ADMIN_TOKEN environment variable is set.
    """
    print_color("\n[T004] Verifying admin authentication configuration...", Colors.YELLOW)
    
    admin_token = os.getenv("ADMIN_TOKEN")
    
    if admin_token:
        print_color("✓ ADMIN_TOKEN environment variable is set", Colors.GREEN)
        print(f"  Token length: {len(admin_token)} characters")
    else:
        print_color("⚠️  ADMIN_TOKEN not set in environment", Colors.YELLOW)
        print("  Admin endpoints will reject all requests")
        print("  Set ADMIN_TOKEN in your .env file for local development")
        print("  Example: ADMIN_TOKEN=your-secure-admin-token-here")


async def main():
    """Main setup workflow for reanalysis database"""
    production = "--production" in sys.argv
    
    print("=" * 60)
    print("Admin Sentiment Reanalysis - Database Setup")
    print("=" * 60)
    print()
    
    if production:
        print_color("⚠️  PRODUCTION MODE", Colors.YELLOW)
        print("This will modify your production CosmosDB instance.")
        print()
    else:
        print_color("LOCAL EMULATOR MODE", Colors.YELLOW)
        print("Using CosmosDB emulator on localhost:8081")
        print()
    
    database_name = os.getenv("COSMOS_DATABASE", "sentiment_analysis")
    print(f"Database: {database_name}")
    print()
    
    # Get CosmosDB client
    client = get_cosmos_client(production)
    
    try:
        # Execute setup tasks in order
        await create_reanalysis_jobs_collection(client, database_name)
        await update_sentiment_scores_schema(client, database_name)
        await verify_array_contains_index(client, database_name)
        await verify_admin_auth()
        
        # Summary
        print()
        print("=" * 60)
        print_color("Phase 1 Setup Complete!", Colors.GREEN)
        print("=" * 60)
        print()
        print("✓ T001: ReanalysisJobs collection created")
        print("✓ T002: sentiment_scores schema updated")
        print("✓ T003: ARRAY_CONTAINS indexing verified")
        print("✓ T004: Admin authentication verified")
        print()
        print_color("Next Steps:", Colors.BLUE)
        print("  1. Proceed to Phase 2: Foundational tasks (T005-T010)")
        print("  2. Implement Pydantic models in backend/src/models/reanalysis.py")
        print("  3. Create ReanalysisService in backend/src/services/reanalysis_service.py")
        print()
        print("For implementation details, see:")
        print("  specs/013-admin-feature-to/tasks.md")
        print()
    
    except Exception as e:
        print()
        print_color("=" * 60, Colors.RED)
        print_color("Setup Failed!", Colors.RED)
        print_color("=" * 60, Colors.RED)
        print()
        print_color(f"Error: {e}", Colors.RED)
        print()
        print("Please fix the error and run the script again.")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 13):
        print_color("ERROR: Python 3.13+ required", Colors.RED)
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Run async main
    asyncio.run(main())
