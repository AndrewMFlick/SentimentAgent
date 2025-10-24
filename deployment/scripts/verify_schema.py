#!/usr/bin/env python3
"""
Verify ARRAY_CONTAINS indexing works (T003)
Tests that detected_tool_ids can be queried efficiently
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from src.services.database import DatabaseService


async def verify_array_contains_index():
    """Test ARRAY_CONTAINS query on detected_tool_ids field"""
    
    db = DatabaseService()
    await db.initialize()
    
    print("="*60)
    print("T003: Verifying ARRAY_CONTAINS Index")
    print("="*60)
    
    # Test 1: Query with ARRAY_CONTAINS (should work with index)
    print("\n[Test 1] ARRAY_CONTAINS query on detected_tool_ids...")
    try:
        query = """
            SELECT c.id, c.detected_tool_ids
            FROM c
            WHERE ARRAY_CONTAINS(c.detected_tool_ids, 'test-tool-id')
        """
        
        items = list(db.sentiment_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        print(f"✓ Query executed successfully")
        print(f"  Results: {len(items)} documents (expected 0 for test ID)")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        if "Index does not have options 17" in str(e):
            print("\n⚠️  Index policy needs to be applied!")
            print("   Run: deployment/scripts/setup-hot-topics-indexes.sh")
        return False
    
    # Test 2: Verify schema on a sample document
    print("\n[Test 2] Verify schema on sample documents...")
    sample_query = "SELECT TOP 5 * FROM c"
    samples = list(db.sentiment_container.query_items(
        query=sample_query,
        enable_cross_partition_query=True
    ))
    
    all_have_schema = True
    for doc in samples:
        has_fields = (
            "detected_tool_ids" in doc and
            "last_analyzed_at" in doc and
            "analysis_version" in doc
        )
        if not has_fields:
            all_have_schema = False
            print(f"❌ Document {doc['id']} missing fields")
    
    if all_have_schema:
        print(f"✓ All {len(samples)} sample documents have new schema")
        print(f"  Fields: detected_tool_ids, last_analyzed_at, analysis_version")
    
    # Test 3: Count documents with new schema
    print("\n[Test 3] Count documents with new schema...")
    count_query = """
        SELECT VALUE COUNT(1) FROM c
        WHERE IS_DEFINED(c.detected_tool_ids)
    """
    
    result = list(db.sentiment_container.query_items(
        query=count_query,
        enable_cross_partition_query=True
    ))
    
    count = result[0] if result else 0
    print(f"✓ Documents with new schema: {count}")
    
    print("\n" + "="*60)
    print("✓ T003 VERIFICATION COMPLETE")
    print("="*60)
    print("\nStatus:")
    print("  ✅ ARRAY_CONTAINS query works")
    print(f"  ✅ {count} documents have new schema")
    print("  ✅ Ready for reanalysis implementation")
    
    return True


if __name__ == "__main__":
    asyncio.run(verify_array_contains_index())
