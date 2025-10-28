#!/usr/bin/env python3
"""
Create Azure Cosmos DB container for sentiment cache.

This script creates the sentiment_cache container with proper indexing
for the pre-cached sentiment analysis feature (017-pre-cached-sentiment).

Container specifications:
- Partition key: /tool_id (co-locate all periods for a tool)
- Indexed fields: tool_id, period, last_updated_ts, _ts
- Purpose: Store pre-calculated sentiment aggregates for fast queries
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from src.config import settings


def create_cache_container():
    """Create sentiment_cache container in Cosmos DB."""

    print(f"🔗 Connecting to Cosmos DB: {settings.cosmos_endpoint}")
    client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)

    try:
        database = client.get_database_client(settings.cosmos_database)
        print(f"✅ Connected to database: {settings.cosmos_database}")
    except exceptions.CosmosResourceNotFoundError:
        print(f"❌ Database '{settings.cosmos_database}' not found")
        sys.exit(1)

    # Create sentiment_cache container
    print("\n📦 Creating sentiment_cache container...")
    try:
        database.create_container(
            id="sentiment_cache",
            partition_key=PartitionKey(path="/tool_id"),
            indexing_policy={
                "indexingMode": "consistent",
                "automatic": True,
                "includedPaths": [
                    {"path": "/tool_id/?"},
                    {"path": "/period/?"},
                    {"path": "/last_updated_ts/?"},
                    {"path": "/_ts/?"}
                ],
                "excludedPaths": [
                    {"path": "/*"}
                ]
            }
        )
        print("✅ sentiment_cache container created successfully")
        print("   - Partition key: /tool_id")
        print("   - Indexed fields: tool_id, period, last_updated_ts, _ts")
        print("   - Purpose: Pre-calculated sentiment aggregates")
    except exceptions.CosmosResourceExistsError:
        print("ℹ️  sentiment_cache container already exists")
    except Exception as e:
        print(f"❌ Failed to create sentiment_cache container: {e}")
        sys.exit(1)

    print("\n✨ Cache container setup complete!")
    print("\nNext steps:")
    print("  1. Add cache configuration to backend/.env")
    print("  2. Start backend to trigger initial cache population")
    print("  3. Verify cache with: curl http://localhost:8000/api/v1/cache/health")


if __name__ == "__main__":
    create_cache_container()
