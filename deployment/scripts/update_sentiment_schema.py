#!/usr/bin/env python3
"""
Quick script to update sentiment_scores schema (T002)
Uses backend's DatabaseService for connection
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.services.database import DatabaseService


async def update_sentiment_scores_schema():
    """Add new fields to all sentiment_scores documents"""
    
    db = DatabaseService()
    await db.initialize()
    
    print("Updating sentiment_scores schema...")
    print("Target: All sentiment_scores documents\n")
    
    # Process documents in streaming fashion (no timeout)
    query = "SELECT * FROM c"
    
    updated = 0
    already_updated = 0
    
    # Stream through results
    for item in db.sentiment_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ):
        needs_update = False
        
        # Add missing fields
        if "detected_tool_ids" not in item:
            item["detected_tool_ids"] = []
            needs_update = True
        if "last_analyzed_at" not in item:
            item["last_analyzed_at"] = None
            needs_update = True
        if "analysis_version" not in item:
            item["analysis_version"] = "1.0.0"
            needs_update = True
        
        if needs_update:
            # Update document
            db.sentiment_container.upsert_item(item)
            updated += 1
            
            if updated % 100 == 0:
                print(f"Progress: {updated} documents updated...")
        else:
            already_updated += 1
    
    total = updated + already_updated
    print(f"\nCompleted processing {total} documents:")
    print(f"  - Updated: {updated}")
    print(f"  - Already had schema: {already_updated}")


if __name__ == "__main__":
    asyncio.run(update_sentiment_scores_schema())
