#!/usr/bin/env python3
"""Test the COUNT query to see what it returns."""
import sys
sys.path.insert(0, '/Users/andrewflick/Documents/SentimentAgent/backend/src')

from azure.cosmos import CosmosClient
import json

# Connect to emulator
client = CosmosClient(
    url="https://localhost:8081/",
    credential="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    connection_verify=False
)

try:
    database = client.get_database_client("sentiment_analysis")
    jobs_container = database.get_container_client("ReanalysisJobs")
    
    # Test different count queries
    print("Query 1: SELECT VALUE COUNT(1) FROM c WHERE 1=1")
    result1 = list(jobs_container.query_items(
        query="SELECT VALUE COUNT(1) FROM c WHERE 1=1",
        enable_cross_partition_query=True
    ))
    print(f"Result: {result1}")
    print(f"Type: {type(result1[0]) if result1 else 'empty'}")
    print()
    
    print("Query 2: SELECT COUNT(1) as count FROM c WHERE 1=1")
    result2 = list(jobs_container.query_items(
        query="SELECT COUNT(1) as count FROM c WHERE 1=1",
        enable_cross_partition_query=True
    ))
    print(f"Result: {result2}")
    print()
    
    print("Query 3: SELECT * FROM c WHERE 1=1")
    result3 = list(jobs_container.query_items(
        query="SELECT * FROM c WHERE 1=1",
        enable_cross_partition_query=True
    ))
    print(f"Result count: {len(result3)}")
    if result3:
        print(f"First job: {result3[0].get('id')}, status: {result3[0].get('status')}")
    print()
    
finally:
    client.close()
