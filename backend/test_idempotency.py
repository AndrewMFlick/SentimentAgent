#!/usr/bin/env python3
"""
Idempotency Tests for T047 - Reanalysis Job Idempotency

Tests verify that:
1. Multiple job executions produce identical sentiment scores
2. Concurrent job blocking prevents overlapping executions
3. Sequential job runs don't corrupt data
4. Tool detection is deterministic
"""

import asyncio
import time
from datetime import datetime, timezone

from src.config import settings
from src.services.database import DatabaseService
from src.services.reanalysis_service import ReanalysisService
from src.services.sentiment_analyzer import SentimentAnalyzer
from src.models.reanalysis import ReanalysisJobRequest


async def test_idempotency():
    """Test idempotency of reanalysis jobs."""
    
    print("\n" + "=" * 70)
    print("T047 IDEMPOTENCY TESTS")
    print("=" * 70)
    
    # Initialize services
    db = DatabaseService()
    await db.initialize()
    
    sentiment_container = db.sentiment_container
    jobs_container = db.reanalysis_jobs_container
    tools_container = db.tools_container
    aliases_container = db.aliases_container
    
    reanalysis_service = ReanalysisService(
        jobs_container, sentiment_container, tools_container, aliases_container
    )
    sentiment_analyzer = SentimentAnalyzer()
    
    # --- TEST 1: Concurrent Job Blocking ---
    print("\n📋 Test 1: Concurrent Job Blocking")
    print("-" * 70)
    
    # Cancel any existing queued jobs
    existing_jobs = list(jobs_container.query_items(
        query="SELECT * FROM c WHERE c.status IN ('queued', 'running')",
        enable_cross_partition_query=True
    ))
    for job in existing_jobs:
        job["status"] = "canceled"
        jobs_container.upsert_item(body=job)
    print(f"Canceled {len(existing_jobs)} existing active jobs")
    
    # Create first job
    job_request = ReanalysisJobRequest(
        batch_size=50,
        date_range=None,
        tool_ids=None
    )
    
    job1 = await reanalysis_service.trigger_manual_reanalysis(
        job_request=job_request,
        triggered_by="idempotency_test_1"
    )
    job1_id = job1["job_id"]
    print(f"✅ Created job 1: {job1_id}")
    
    # Try to create second job (should fail due to concurrent job check)
    try:
        job2 = await reanalysis_service.trigger_manual_reanalysis(
            job_request=job_request,
            triggered_by="idempotency_test_2"
        )
        print(f"❌ FAIL: Second job was created (should have been blocked)")
        concurrent_blocking_pass = False
    except ValueError as e:
        if "already active" in str(e):
            print(f"✅ PASS: Concurrent job correctly blocked - {e}")
            concurrent_blocking_pass = True
        else:
            print(f"❌ FAIL: Unexpected error - {e}")
            concurrent_blocking_pass = False
    
    # Cancel job1 for cleanup
    job1_doc = jobs_container.read_item(
        item=job1_id,
        partition_key=job1_id
    )
    job1_doc["status"] = "canceled"
    jobs_container.upsert_item(body=job1_doc)
    print("Canceled job 1 for cleanup")
    
    # --- TEST 2: Sequential Job Idempotency ---
    print("\n📋 Test 2: Sequential Job Idempotency")
    print("-" * 70)
    
    # Initialize variables
    scores_after_run1 = {}
    scores_after_run2 = {}
    
    # Select a small subset for testing (first 100 docs)
    # Use simple query without ORDER BY which has issues in emulator
    query = "SELECT TOP 100 * FROM c"
    test_docs = list(sentiment_container.query_items(
        query=query,
        enable_cross_partition_query=True
    ))
    
    print(f"Selected {len(test_docs)} documents for idempotency testing")
    
    if len(test_docs) == 0:
        print("❌ SKIP: No documents in database for testing")
        sequential_idempotency_pass = False
    else:
        # Store original sentiment scores
        original_scores = {}
        for doc in test_docs:
            doc_id = doc["id"]
            original_scores[doc_id] = {
                "sentiment_label": doc.get("sentiment_label"),
                "sentiment_score": doc.get("sentiment_score"),
                "detected_tools": doc.get("detected_tools", [])
            }
        
        print(f"Stored original scores for {len(original_scores)} documents")
        
        # Run first reanalysis job
        print("\nRunning first reanalysis job...")
        job_request_1 = ReanalysisJobRequest(
            batch_size=50,
            date_range=None,
            tool_ids=None
        )
        job_1 = await reanalysis_service.trigger_manual_reanalysis(
            job_request=job_request_1,
            triggered_by="idempotency_test_run1"
        )
        
        start_time = time.time()
        await reanalysis_service.process_reanalysis_job(
            job_1["job_id"], sentiment_analyzer
        )
        elapsed_1 = time.time() - start_time
        
        # Get job results
        job_1_result = jobs_container.read_item(
            item=job_1["job_id"],
            partition_key=job_1["job_id"]
        )
        print(f"✅ Job 1 completed in {elapsed_1:.2f}s")
        print(f"   Processed: {job_1_result['progress']['processed_count']}")
        
        # Store scores after first run
        scores_after_run1 = {}
        for doc_id in original_scores.keys():
            try:
                doc = sentiment_container.read_item(
                    item=doc_id,
                    partition_key=doc_id
                )
                scores_after_run1[doc_id] = {
                    "sentiment_label": doc.get("sentiment_label"),
                    "sentiment_score": doc.get("sentiment_score"),
                    "detected_tools": doc.get("detected_tools", [])
                }
            except Exception:
                pass
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Run second reanalysis job (should produce identical results)
        print("\nRunning second reanalysis job...")
        job_request_2 = ReanalysisJobRequest(
            batch_size=50,
            date_range=None,
            tool_ids=None
        )
        job_2 = await reanalysis_service.trigger_manual_reanalysis(
            job_request=job_request_2,
            triggered_by="idempotency_test_run2"
        )
        
        start_time = time.time()
        await reanalysis_service.process_reanalysis_job(
            job_2["job_id"], sentiment_analyzer
        )
        elapsed_2 = time.time() - start_time
        
        # Get job results
        job_2_result = jobs_container.read_item(
            item=job_2["job_id"],
            partition_key=job_2["job_id"]
        )
        print(f"✅ Job 2 completed in {elapsed_2:.2f}s")
        print(f"   Processed: {job_2_result['progress']['processed_count']}")
        
        # Store scores after second run
        scores_after_run2 = {}
        for doc_id in original_scores.keys():
            try:
                doc = sentiment_container.read_item(
                    item=doc_id,
                    partition_key=doc_id
                )
                scores_after_run2[doc_id] = {
                    "sentiment_label": doc.get("sentiment_label"),
                    "sentiment_score": doc.get("sentiment_score"),
                    "detected_tools": doc.get("detected_tools", [])
                }
            except Exception:
                pass
        
        # Compare results
        print("\n📊 Comparing Results...")
        identical_count = 0
        different_count = 0
        differences = []
        
        for doc_id in scores_after_run1.keys():
            if doc_id not in scores_after_run2:
                continue
                
            score1 = scores_after_run1[doc_id]
            score2 = scores_after_run2[doc_id]
            
            # Compare sentiment scores (allow small float differences)
            score_diff = abs(
                (score1.get("sentiment_score") or 0) -
                (score2.get("sentiment_score") or 0)
            )
            
            labels_match = (
                score1["sentiment_label"] == score2["sentiment_label"]
            )
            scores_match = score_diff < 0.0001
            tools_match = (
                score1["detected_tools"] == score2["detected_tools"]
            )
            
            if labels_match and scores_match and tools_match:
                identical_count += 1
            else:
                different_count += 1
                if len(differences) < 5:  # Show first 5 differences
                    differences.append({
                        "doc_id": doc_id,
                        "run1": score1,
                        "run2": score2
                    })
        
        print(f"\nIdentical: {identical_count}/{len(scores_after_run1)}")
        print(f"Different: {different_count}/{len(scores_after_run1)}")
        
        if different_count > 0:
            print("\nFirst 5 differences:")
            for diff in differences[:5]:
                print(f"  Doc {diff['doc_id']}:")
                print(f"    Run 1: {diff['run1']}")
                print(f"    Run 2: {diff['run2']}")
        
        # Test passes if >95% identical (allowing for minor variations)
        if len(scores_after_run1) == 0:
            print("\n❌ SKIP: No documents with sentiment scores to compare")
            sequential_idempotency_pass = False
        else:
            identical_pct = (identical_count / len(scores_after_run1)) * 100
            if identical_pct >= 95.0:
                msg = f"✅ PASS: {identical_pct:.1f}% identical (≥95%)"
                print(f"\n{msg}")
                sequential_idempotency_pass = True
            else:
                msg = f"❌ FAIL: {identical_pct:.1f}% identical (<95%)"
                print(f"\n{msg}")
                sequential_idempotency_pass = False
    
    # --- TEST 3: Deterministic Tool Detection ---
    print("\n📋 Test 3: Deterministic Tool Detection")
    print("-" * 70)
    
    # Count documents with tool mentions
    tools_detected_run1 = 0
    tools_detected_run2 = 0
    
    for doc_id in scores_after_run1.keys():
        if scores_after_run1[doc_id]["detected_tools"]:
            tools_detected_run1 += 1
        if scores_after_run2[doc_id]["detected_tools"]:
            tools_detected_run2 += 1
    
    print(f"Run 1 detected tools in: {tools_detected_run1} documents")
    print(f"Run 2 detected tools in: {tools_detected_run2} documents")
    
    if tools_detected_run1 == tools_detected_run2:
        print("✅ PASS: Tool detection count is deterministic")
        tool_detection_pass = True
    else:
        msg = (
            f"❌ FAIL: Tool detection varied "
            f"({tools_detected_run1} vs {tools_detected_run2})"
        )
        print(msg)
        tool_detection_pass = False
    
    # --- FINAL RESULTS ---
    print("\n" + "=" * 70)
    print("IDEMPOTENCY TEST RESULTS")
    print("=" * 70)
    
    all_tests = [
        ("Concurrent Job Blocking", concurrent_blocking_pass),
        ("Sequential Job Idempotency", sequential_idempotency_pass),
        ("Deterministic Tool Detection", tool_detection_pass)
    ]
    
    passed = sum(1 for _, result in all_tests if result)
    total = len(all_tests)
    
    for test_name, result in all_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'=' * 70}")
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("=" * 70)
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        return False


if __name__ == "__main__":
    result = asyncio.run(test_idempotency())
    exit(0 if result else 1)
