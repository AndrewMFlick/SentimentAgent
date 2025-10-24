#!/usr/bin/env python3
"""
Update sentiment_scores schema using pagination to avoid timeouts
Works around CosmosDB PostgreSQL emulator timeout issues
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.services.database import DatabaseService


async def update_sentiment_scores_schema():
    """Add new fields to all sentiment_scores documents using pagination"""
    
    db = DatabaseService()
    await db.initialize()
    
    print("Updating sentiment_scores schema (paginated approach)...")
    print("This works around emulator timeout issues\n")
    
    # Pagination settings
    page_size = 100
    offset = 0
    total_updated = 0
    total_processed = 0
    
    while True:
        # Query one page at a time
        query = f"SELECT * FROM c OFFSET {offset} LIMIT {page_size}"
        
        try:
            items = list(db.sentiment_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
        except Exception as e:
            print(f"\n❌ Error querying at offset {offset}: {e}")
            print("Trying smaller batch size...")
            break
        
        if not items:
            print(f"\n✓ Reached end of collection")
            break
        
        # Update each document in this page
        updated_in_batch = 0
        for item in items:
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
                db.sentiment_container.upsert_item(item)
                updated_in_batch += 1
                total_updated += 1
        
        total_processed += len(items)
        offset += page_size
        
        print(f"Page {offset // page_size}: Processed {len(items)} docs, "
              f"Updated {updated_in_batch} | "
              f"Total: {total_processed} processed, {total_updated} updated")
        
        # Small delay to avoid overwhelming the emulator
        await asyncio.sleep(0.1)
    
    print(f"\n" + "="*60)
    print(f"✓ Schema update complete!")
    print(f"  Total processed: {total_processed}")
    print(f"  Total updated: {total_updated}")
    print(f"  Already had schema: {total_processed - total_updated}")
    print(f"\nNew fields added:")
    print(f"  - detected_tool_ids: []")
    print(f"  - last_analyzed_at: null")
    print(f"  - analysis_version: '1.0.0'")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(update_sentiment_scores_schema())
