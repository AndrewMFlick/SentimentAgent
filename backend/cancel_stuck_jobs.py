#!/usr/bin/env python3
"""Cancel all stuck reanalysis jobs."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from azure.cosmos import CosmosClient

# Connect to Cosmos DB
client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)
database = client.get_database_client(settings.cosmos_database)
jobs_container = database.get_container_client("ReanalysisJobs")

# Find all active jobs
query = "SELECT * FROM c WHERE c.status IN ('queued', 'running')"
active_jobs = list(jobs_container.query_items(
    query=query,
    enable_cross_partition_query=True
))

if not active_jobs:
    print("✓ No active jobs found - you can start a new reanalysis!")
    sys.exit(0)

print(f"Found {len(active_jobs)} active job(s):\n")

for job in active_jobs:
    print(f"Job ID: {job['id']}")
    print(f"Status: {job['status']}")
    print(f"Triggered: {job.get('created_at', 'unknown')}")
    print(f"Progress: {job['progress']['percentage']:.1f}%")
    print(f"Processed: {job['progress']['processed_count']}/{job['progress']['total_count']} docs")
    print()
    
    # Cancel the job
    job['status'] = 'cancelled'
    jobs_container.upsert_item(body=job)
    print(f"✓ Cancelled job {job['id']}\n")

print("All stuck jobs have been cancelled. You can now start a new reanalysis.")
