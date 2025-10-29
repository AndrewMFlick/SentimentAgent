#!/usr/bin/env python3
"""Quick validation script for Phase 3 cache implementation.

This script verifies that the cache service implementation is working correctly
by testing key functionality without requiring a full database setup.

Usage:
    python backend/scripts/validate_phase3.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# Add backend/src to path
sys.path.insert(0, '/home/runner/work/SentimentAgent/SentimentAgent/backend/src')

from models.cache import CachePeriod, SentimentCacheEntry
from services.cache_service import CacheService


def test_map_hours_to_period():
    """Test T013: Time period mapping."""
    print("\n🧪 Test 1: _map_hours_to_period()")
    
    # Create mock service
    cache_container = MagicMock()
    sentiment_container = MagicMock()
    tools_container = MagicMock()
    
    service = CacheService(
        cache_container=cache_container,
        sentiment_container=sentiment_container,
        tools_container=tools_container,
    )
    
    # Test standard periods
    tests = [
        (1, CachePeriod.HOUR_1),
        (24, CachePeriod.HOUR_24),
        (168, CachePeriod.DAY_7),
        (720, CachePeriod.DAY_30),
        (12, None),  # Non-standard
    ]
    
    for hours, expected in tests:
        result = service._map_hours_to_period(hours)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {hours} hours → {result} (expected {expected})")
        if result != expected:
            return False
    
    print("  ✅ All period mappings correct!")
    return True


def test_calculate_cache_key():
    """Test T017: Cache key generation."""
    print("\n🧪 Test 2: _calculate_cache_key()")
    
    cache_container = MagicMock()
    sentiment_container = MagicMock()
    tools_container = MagicMock()
    
    service = CacheService(
        cache_container=cache_container,
        sentiment_container=sentiment_container,
        tools_container=tools_container,
    )
    
    tool_id = "test-tool-123"
    period = CachePeriod.HOUR_24
    
    result = service._calculate_cache_key(tool_id, period)
    expected = f"{tool_id}:HOUR_24"
    
    if result == expected:
        print(f"  ✅ Cache key: {result}")
        return True
    else:
        print(f"  ❌ Expected: {expected}, Got: {result}")
        return False


def test_is_cache_fresh():
    """Test T018: Cache freshness check."""
    print("\n🧪 Test 3: _is_cache_fresh()")
    
    cache_container = MagicMock()
    sentiment_container = MagicMock()
    tools_container = MagicMock()
    
    service = CacheService(
        cache_container=cache_container,
        sentiment_container=sentiment_container,
        tools_container=tools_container,
    )
    
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    # Test fresh cache (5 minutes old, TTL is 30)
    fresh_entry = SentimentCacheEntry(
        id="test:HOUR_24",
        tool_id="test",
        period=CachePeriod.HOUR_24,
        total_mentions=100,
        positive_count=60,
        negative_count=20,
        neutral_count=20,
        positive_percentage=60.0,
        negative_percentage=20.0,
        neutral_percentage=20.0,
        average_sentiment=0.4,
        period_start_ts=now_ts - 86400,
        period_end_ts=now_ts,
        last_updated_ts=now_ts - 300,  # 5 minutes ago
    )
    
    is_fresh = service._is_cache_fresh(fresh_entry)
    if is_fresh:
        print(f"  ✅ Fresh cache (5 min old) detected correctly")
    else:
        print(f"  ❌ Fresh cache incorrectly marked as stale")
        return False
    
    # Test stale cache (45 minutes old, TTL is 30)
    stale_entry = SentimentCacheEntry(
        id="test:HOUR_24",
        tool_id="test",
        period=CachePeriod.HOUR_24,
        total_mentions=100,
        positive_count=60,
        negative_count=20,
        neutral_count=20,
        positive_percentage=60.0,
        negative_percentage=20.0,
        neutral_percentage=20.0,
        average_sentiment=0.4,
        period_start_ts=now_ts - 86400,
        period_end_ts=now_ts,
        last_updated_ts=now_ts - 2700,  # 45 minutes ago
    )
    
    is_fresh = service._is_cache_fresh(stale_entry)
    if not is_fresh:
        print(f"  ✅ Stale cache (45 min old) detected correctly")
    else:
        print(f"  ❌ Stale cache incorrectly marked as fresh")
        return False
    
    return True


async def test_calculate_sentiment_aggregate():
    """Test T019: Sentiment aggregation calculation."""
    print("\n🧪 Test 4: _calculate_sentiment_aggregate()")
    
    cache_container = MagicMock()
    sentiment_container = MagicMock()
    tools_container = MagicMock()
    
    # Mock sentiment data
    mock_data = [
        {"sentiment_score": 0.8, "detected_tool_ids": ["test"], "_ts": 1698451200},  # positive
        {"sentiment_score": 0.6, "detected_tool_ids": ["test"], "_ts": 1698451300},  # positive
        {"sentiment_score": -0.5, "detected_tool_ids": ["test"], "_ts": 1698451400},  # negative
        {"sentiment_score": 0.0, "detected_tool_ids": ["test"], "_ts": 1698451500},  # neutral
    ]
    
    async def mock_query(*args, **kwargs):
        for item in mock_data:
            yield item
    
    sentiment_container.query_items = AsyncMock(return_value=mock_query())
    
    service = CacheService(
        cache_container=cache_container,
        sentiment_container=sentiment_container,
        tools_container=tools_container,
    )
    
    result = await service._calculate_sentiment_aggregate("test", 24)
    
    # Verify counts
    if result["total_mentions"] == 4:
        print(f"  ✅ Total mentions: {result['total_mentions']}")
    else:
        print(f"  ❌ Expected 4 mentions, got {result['total_mentions']}")
        return False
    
    if result["positive_count"] == 2:
        print(f"  ✅ Positive count: {result['positive_count']}")
    else:
        print(f"  ❌ Expected 2 positive, got {result['positive_count']}")
        return False
    
    if result["negative_count"] == 1:
        print(f"  ✅ Negative count: {result['negative_count']}")
    else:
        print(f"  ❌ Expected 1 negative, got {result['negative_count']}")
        return False
    
    if result["neutral_count"] == 1:
        print(f"  ✅ Neutral count: {result['neutral_count']}")
    else:
        print(f"  ❌ Expected 1 neutral, got {result['neutral_count']}")
        return False
    
    # Verify percentages sum to 100
    total_pct = (
        result["positive_percentage"] +
        result["negative_percentage"] +
        result["neutral_percentage"]
    )
    if abs(total_pct - 100.0) < 0.1:
        print(f"  ✅ Percentages sum to 100%")
    else:
        print(f"  ❌ Percentages sum to {total_pct}%, expected 100%")
        return False
    
    return True


async def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Phase 3 Implementation Validation")
    print("=" * 60)
    print("\nValidating cache service implementation...")
    
    results = []
    
    # Run synchronous tests
    results.append(("Period Mapping", test_map_hours_to_period()))
    results.append(("Cache Key Generation", test_calculate_cache_key()))
    results.append(("Cache Freshness", test_is_cache_fresh()))
    
    # Run async tests
    results.append(("Sentiment Aggregation", await test_calculate_sentiment_aggregate()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All validation tests PASSED!")
        print("\nPhase 3 implementation is working correctly.")
        print("\nNext steps:")
        print("  1. Create cache container: python backend/scripts/create_cache_container.py")
        print("  2. Run full test suite: pytest backend/tests/")
        print("  3. Start backend and test API endpoints")
        return 0
    else:
        print("\n❌ Some validation tests FAILED")
        print("\nPlease review the implementation and fix the issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
