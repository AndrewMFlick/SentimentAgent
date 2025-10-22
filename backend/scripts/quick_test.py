#!/usr/bin/env python3
"""Quick test of Tools container query"""
import os
os.environ["AZURE_COSMOS_DISABLE_SSL_VERIFICATION"] = "true"

from azure.cosmos import CosmosClient

# Connect
endpoint = "http://127.0.0.1:8081"
key = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
client = CosmosClient(endpoint, key, connection_verify=False)
database = client.get_database_client("sentiment_analysis")
tools = database.get_container_client("Tools")

# Query ALL tools to see what exists
query = "SELECT * FROM c"
items = list(tools.query_items(query=query, enable_cross_partition_query=True))

print(f"Found {len(items)} total items:")
for tool in items:
    pk = tool.get('partition_key', tool.get('partitionKey', 'MISSING'))
    print(f"  - {tool.get('name', 'NO_NAME')} | PK: {pk} | Status: {tool.get('status', 'MISSING')} | Categories: {tool.get('categories', 'MISSING')}")
