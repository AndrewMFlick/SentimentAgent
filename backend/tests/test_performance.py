#!/usr/bin/env python3
"""
Performance Test for T049 - Reanalysis Job Performance

Target: Process 5,699+ docs in <60 seconds (100+ docs/sec)
"""

import asyncio
import time
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, "/Users/andrewflick/Documents/SentimentAgent/backend")

from src.config import settings
from src.services.database import DatabaseService
from src.services.reanalysis_service import ReanalysisService
from src.services.sentiment_analyzer import SentimentAnalyzer
from src.models.reanalysis import ReanalysisJobRequest


async def run_performance_test():
    """Run performance test for reanalysis job."""
    
    print("="*70)
    print("PERFORMANCE TEST (T049) - Reanalysis Job")
    print("="*70)
    print(f"Target: Process 5,699+ docs in <60 seconds (100+ docs/sec)\n")
    
    # Initialize services
    print("1. Initializing database connection...")
    db = DatabaseService()
    await db.initialize()
    
    sentiment_container = db.sentiment_container
    jobs_container = db.reanalysis_jobs_container
    tools_container = db.tools_container
    aliases_container = db.aliases_container
    
    # Count total documents
    print("2. Counting total sentiment documents...")
    query = "SELECT COUNT(1) as count FROM c"
    count_items = sentiment_container.query_items(
        query=query,
        enable_cross_partition_query=True
    )
    count_result = list(count_items)
    total_docs = count_result[0]['count'] if count_result else 0
    
    print(f"   Total documents: {total_docs:,}")
    
    if total_docs < 1000:
        print(f"\n⚠️  WARNING: Only {total_docs} documents found.")
        print("   Performance test requires at least 1,000 documents for meaningful results.")
        print("   Continuing anyway...\n")
    
    # Cancel any existing queued jobs
    print("3. Checking for existing queued jobs...")
    existing_jobs = list(jobs_container.query_items(
        query="SELECT * FROM c WHERE c.status = 'queued'",
        enable_cross_partition_query=True
    ))
    
    if existing_jobs:
        print(f"   Found {len(existing_jobs)} queued job(s). Canceling...")
        for job in existing_jobs:
            job["status"] = "canceled"
            job["end_time"] = datetime.now(timezone.utc).isoformat()
            jobs_container.upsert_item(body=job)
        print(f"   ✓ Canceled {len(existing_jobs)} job(s)")
    else:
        print("   ✓ No existing queued jobs")
    
    # Create reanalysis service
    print("4. Creating reanalysis job...")
    reanalysis_service = ReanalysisService(
        jobs_container,
        sentiment_container,
        tools_container,
        aliases_container
    )
    
    # Create job with parameters
    job_request = ReanalysisJobRequest(
        batch_size=100,  # Standard batch size
        date_range=None,  # Process all documents
        tool_ids=None     # All tools
    )
    
    job_doc = await reanalysis_service.trigger_manual_reanalysis(
        job_request=job_request,
        triggered_by="performance_test"
    )
    
    job_id = job_doc["job_id"]
    
    print(f"   ✓ Job created: {job_id}")
    print(f"   Batch size: {job_request.batch_size}")
    est_batches = (total_docs // job_request.batch_size) + 1
    print(f"   Estimated batches: {est_batches}")
    
    # Start performance measurement
    print("\n5. Starting reanalysis job...")
    print(f"   Start time: {datetime.now().strftime('%H:%M:%S')}")
    print("   " + "="*66)
    
    start_time = time.time()
    
    # Create sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Process the job
    try:
        await reanalysis_service.process_reanalysis_job(
            job_id,
            sentiment_analyzer
        )
        
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        
        print("   " + "="*66)
        print(f"   End time: {datetime.now().strftime('%H:%M:%S')}")
        
        # Get final job stats
        job_doc = jobs_container.read_item(item=job_id, partition_key=job_id)
        
        # Calculate metrics
        processed = job_doc["progress"]["processed_count"]
        docs_per_sec = processed / elapsed_seconds if elapsed_seconds > 0 else 0
        
        print("\n" + "="*70)
        print("PERFORMANCE TEST RESULTS")
        print("="*70)
        print(f"\n✅ Job Status: {job_doc['status'].upper()}")
        print(f"\n⏱️  TIMING:")
        print(f"   • Duration: {elapsed_seconds:.2f} seconds")
        print(f"   • Target: <60 seconds")
        print(f"   • Result: {'✅ PASS' if elapsed_seconds < 60 else '❌ FAIL'}")
        
        print(f"\n📊 THROUGHPUT:")
        print(f"   • Documents processed: {processed:,}")
        print(f"   • Processing rate: {docs_per_sec:.2f} docs/sec")
        print(f"   • Target: >100 docs/sec")
        print(f"   • Result: {'✅ PASS' if docs_per_sec >= 100 else '❌ FAIL'}")
        
        print(f"\n📈 STATISTICS:")
        print(f"   • Categorized: {job_doc['statistics']['categorized_count']:,}")
        print(f"   • Uncategorized: {job_doc['statistics']['uncategorized_count']:,}")
        print(f"   • Errors: {job_doc['statistics']['errors_count']}")
        print(f"   • Tools detected: {len(job_doc['statistics']['tools_detected'])}")
        
        # Rate limiting info
        print(f"\n🔧 RATE LIMITING CONFIG:")
        print(f"   • Batch delay: {settings.reanalysis_batch_delay_ms}ms")
        print(f"   • Max retries: {settings.reanalysis_max_retries}")
        print(f"   • Base delay: {settings.reanalysis_retry_base_delay}s")
        print(f"   • Max delay: {settings.reanalysis_retry_max_delay}s")
        
        # Overall result
        print(f"\n" + "="*70)
        passed = elapsed_seconds < 60 and docs_per_sec >= 100
        if passed:
            print("✅ PERFORMANCE TEST PASSED")
            print(f"   Processed {processed:,} docs in {elapsed_seconds:.2f}s ({docs_per_sec:.2f} docs/sec)")
        else:
            print("❌ PERFORMANCE TEST FAILED")
            if elapsed_seconds >= 60:
                print(f"   Duration ({elapsed_seconds:.2f}s) exceeded target (60s)")
            if docs_per_sec < 100:
                print(f"   Throughput ({docs_per_sec:.2f} docs/sec) below target (100 docs/sec)")
        print("="*70 + "\n")
        
        return passed
        
    except Exception as e:
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        
        print("\n" + "="*70)
        print("❌ PERFORMANCE TEST ERROR")
        print("="*70)
        print(f"Error: {e}")
        print(f"Duration before error: {elapsed_seconds:.2f} seconds")
        print("="*70 + "\n")
        
        raise
    
    finally:
        # No disconnect needed - client handles cleanup
        pass


if __name__ == "__main__":
    try:
        passed = asyncio.run(run_performance_test())
        sys.exit(0 if passed else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
