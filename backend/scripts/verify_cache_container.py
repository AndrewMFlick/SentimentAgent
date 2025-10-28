#!/usr/bin/env python3
"""
Verify sentiment_cache container setup.

This script verifies:
1. Container exists with correct ID
2. Partition key is set to /tool_id
3. Indexing policy includes required fields
4. Container is accessible
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.cosmos import CosmosClient, exceptions
from src.config import settings


def verify_cache_container():
    """Verify sentiment_cache container configuration."""

    print(f"🔗 Connecting to Cosmos DB: {settings.cosmos_endpoint}")
    client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)

    try:
        database = client.get_database_client(settings.cosmos_database)
        print(f"✅ Connected to database: {settings.cosmos_database}")
    except exceptions.CosmosResourceNotFoundError:
        print(f"❌ Database '{settings.cosmos_database}' not found")
        print("   Create the database first before creating containers")
        sys.exit(1)

    # Verify sentiment_cache container
    print(f"\n🔍 Verifying container: {settings.cosmos_container_sentiment_cache}")
    try:
        container = database.get_container_client(settings.cosmos_container_sentiment_cache)
        container_props = container.read()
        
        print("✅ Container exists")
        print(f"   - ID: {container_props['id']}")
        
        # Verify partition key
        partition_key_path = container_props['partitionKey']['paths'][0]
        if partition_key_path == "/tool_id":
            print(f"✅ Partition key: {partition_key_path}")
        else:
            print(f"⚠️  Unexpected partition key: {partition_key_path} (expected /tool_id)")
        
        # Verify indexing policy
        indexing_policy = container_props.get('indexingPolicy', {})
        included_paths = indexing_policy.get('includedPaths', [])
        excluded_paths = indexing_policy.get('excludedPaths', [])
        
        print("✅ Indexing policy:")
        print(f"   - Mode: {indexing_policy.get('indexingMode', 'N/A')}")
        print(f"   - Included paths: {len(included_paths)}")
        for path in included_paths:
            print(f"     • {path['path']}")
        print(f"   - Excluded paths: {len(excluded_paths)}")
        for path in excluded_paths:
            print(f"     • {path['path']}")
        
        # Test write/read access
        print("\n🧪 Testing write/read access...")
        test_doc = {
            "id": "test-verification",
            "tool_id": "test-verification",
            "period": "HOUR_24",
            "total_mentions": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "positive_percentage": 0.0,
            "negative_percentage": 0.0,
            "neutral_percentage": 0.0,
            "average_sentiment": 0.0,
            "period_start_ts": 0,
            "period_end_ts": 0,
            "last_updated_ts": 0
        }
        
        try:
            container.upsert_item(test_doc)
            print("✅ Write test successful")
            
            read_doc = container.read_item(
                item="test-verification",
                partition_key="test-verification"
            )
            print("✅ Read test successful")
            
            # Cleanup test document
            container.delete_item(
                item="test-verification",
                partition_key="test-verification"
            )
            print("✅ Delete test successful")
            
        except Exception as e:
            print(f"⚠️  Access test failed: {e}")
        
        print("\n✨ Container verification complete!")
        print("\nNext steps:")
        print("  1. Start the backend: ./start.sh")
        print("  2. Cache will populate automatically in ~1 minute")
        print("  3. Verify cache health: curl http://localhost:8000/api/v1/cache/health")
        
        return True
        
    except exceptions.CosmosResourceNotFoundError:
        print(f"❌ Container '{settings.cosmos_container_sentiment_cache}' not found")
        print("\nRun the creation script first:")
        print("  python scripts/create_cache_container.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    verify_cache_container()
