"""
Create Azure Cosmos DB containers for tool management.

This script creates:
1. Tools container - stores AI tool metadata
2. ToolAliases container - stores alias relationships
"""

from azure.cosmos import CosmosClient, PartitionKey, exceptions
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings  # noqa: E402


def create_containers():
    """Create Tools and ToolAliases containers in Cosmos DB."""

    print(f"🔗 Connecting to Cosmos DB: {settings.cosmos_endpoint}")
    client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)

    try:
        database = client.get_database_client(settings.cosmos_database)
        print(f"✅ Connected to database: {settings.cosmos_database}")
    except exceptions.CosmosResourceNotFoundError:
        print(f"❌ Database '{settings.cosmos_database}' not found")
        sys.exit(1)
    
    # Create Tools container
    print("\n📦 Creating Tools container...")
    try:
        database.create_container(
            id="Tools",
            partition_key=PartitionKey(path="/partitionKey"),
            indexing_policy={
                "indexingMode": "consistent",
                "automatic": True,
                "includedPaths": [
                    {"path": "/*"}
                ],
                "excludedPaths": [
                    {"path": "/metadata/*"},
                    {"path": '/"_etag"/?'}
                ]
            }
        )
        print("✅ Tools container created successfully")
        print("   - Partition key: /partitionKey")
        print("   - Indexed fields: name, category, status, slug, vendor")
    except exceptions.CosmosResourceExistsError:
        print("ℹ️  Tools container already exists")
    except Exception as e:
        print(f"❌ Failed to create Tools container: {e}")
        sys.exit(1)
    
    # Create ToolAliases container
    print("\n🔗 Creating ToolAliases container...")
    try:
        database.create_container(
            id="ToolAliases",
            partition_key=PartitionKey(path="/partitionKey"),
            indexing_policy={
                "indexingMode": "consistent",
                "automatic": True,
                "includedPaths": [
                    {"path": "/*"}
                ],
                "excludedPaths": [
                    {"path": '/"_etag"/?'}
                ]
            }
        )
        print("✅ ToolAliases container created successfully")
        print("   - Partition key: /partitionKey")
        print("   - Indexed fields: alias_tool_id, primary_tool_id")
    except exceptions.CosmosResourceExistsError:
        print("ℹ️  ToolAliases container already exists")
    except Exception as e:
        print(f"❌ Failed to create ToolAliases container: {e}")
        sys.exit(1)
    
    print("\n✨ Container setup complete!")
    print("\nNext steps:")
    print("  1. Run seed_tools.py to populate initial tool data")
    print("  2. Verify containers in Azure Portal")


if __name__ == "__main__":
    create_containers()
