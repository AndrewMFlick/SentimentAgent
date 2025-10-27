#!/usr/bin/env python3
"""Check all reanalysis jobs in the database."""
import asyncio
from azure.cosmos.aio import CosmosClient

async def main():
    # Connect to emulator
    client = CosmosClient(
        url="https://localhost:8081/",
        credential="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
        connection_verify=False
    )
    
    try:
        database = client.get_database_client("sentiment_analysis")
        jobs_container = database.get_container_client("ReanalysisJobs")
        
        # Query all jobs
        query = "SELECT * FROM c ORDER BY c.created_at DESC"
        jobs_iter = jobs_container.query_items(
            query=query,
            enable_cross_partition_query=True
        )
        jobs = [job async for job in jobs_iter]
        
        print(f"Total jobs in database: {len(jobs)}")
        print()
        
        if len(jobs) == 0:
            print("No jobs found in database")
        
        for job in jobs:
            print(f"Job ID: {job['id']}")
            print(f"  Status: {job['status']}")
            print(f"  Triggered by: {job.get('triggered_by', 'N/A')}")
            print(f"  Created: {job.get('created_at', 'N/A')}")
            progress = job.get('progress', {})
            print(f"  Total docs: {progress.get('total_count', 'N/A')}")
            print(f"  Processed: {progress.get('processed_count', 0)}")
            print()
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
