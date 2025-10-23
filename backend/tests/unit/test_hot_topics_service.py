"""Unit tests for HotTopicsService.

Tests for Feature #012: Hot Topics
Tests core business logic methods for engagement scoring and sentiment aggregation.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from src.services.hot_topics_service import HotTopicsService
from src.models.hot_topics import SentimentDistribution


class TestCalculateCutoffTimestamp:
    """Unit tests for _calculate_cutoff_timestamp helper method."""
    
    @pytest.fixture
    def hot_topics_service(self):
        """Create a HotTopicsService with mocked containers."""
        sentiment_scores = Mock()
        reddit_posts = Mock()
        reddit_comments = Mock()
        tools = Mock()
        
        return HotTopicsService(
            sentiment_scores_container=sentiment_scores,
            reddit_posts_container=reddit_posts,
            reddit_comments_container=reddit_comments,
            tools_container=tools,
        )
    
    def test_calculate_cutoff_24h(self, hot_topics_service):
        """
        Test that _calculate_cutoff_timestamp correctly calculates 24 hour cutoff.
        
        Task: T017
        Purpose: Verify time range calculation for 24 hour filter
        Setup: Create service with current time
        Test: Call _calculate_cutoff_timestamp("24h")
        Assertions:
          - Returns Unix timestamp from 24 hours ago
          - Cutoff is approximately 86400 seconds before now
        """
        now = datetime.now(timezone.utc)
        cutoff_ts = hot_topics_service._calculate_cutoff_timestamp("24h")
        
        # Convert back to datetime for comparison
        cutoff_dt = datetime.fromtimestamp(cutoff_ts, tz=timezone.utc)
        expected_cutoff = now - timedelta(hours=24)
        
        # Allow 5 second tolerance for test execution time
        delta = abs((expected_cutoff - cutoff_dt).total_seconds())
        assert delta < 5, f"Cutoff should be ~24h ago, got {delta}s difference"
        
        # Verify it's in the past
        assert cutoff_ts < int(now.timestamp())
    
    def test_calculate_cutoff_7d(self, hot_topics_service):
        """
        Test that _calculate_cutoff_timestamp correctly calculates 7 day cutoff.
        
        Task: T017
        Purpose: Verify time range calculation for 7 day filter
        """
        now = datetime.now(timezone.utc)
        cutoff_ts = hot_topics_service._calculate_cutoff_timestamp("7d")
        
        cutoff_dt = datetime.fromtimestamp(cutoff_ts, tz=timezone.utc)
        expected_cutoff = now - timedelta(days=7)
        
        # Allow 5 second tolerance
        delta = abs((expected_cutoff - cutoff_dt).total_seconds())
        assert delta < 5
        assert cutoff_ts < int(now.timestamp())
    
    def test_calculate_cutoff_30d(self, hot_topics_service):
        """
        Test that _calculate_cutoff_timestamp correctly calculates 30 day cutoff.
        
        Task: T017
        Purpose: Verify time range calculation for 30 day filter
        """
        now = datetime.now(timezone.utc)
        cutoff_ts = hot_topics_service._calculate_cutoff_timestamp("30d")
        
        cutoff_dt = datetime.fromtimestamp(cutoff_ts, tz=timezone.utc)
        expected_cutoff = now - timedelta(days=30)
        
        # Allow 5 second tolerance
        delta = abs((expected_cutoff - cutoff_dt).total_seconds())
        assert delta < 5
        assert cutoff_ts < int(now.timestamp())
    
    def test_calculate_cutoff_invalid_range(self, hot_topics_service):
        """
        Test that _calculate_cutoff_timestamp raises ValueError for invalid time range.
        
        Task: T017
        Purpose: Verify input validation for time_range parameter
        """
        with pytest.raises(ValueError, match="Invalid time_range"):
            hot_topics_service._calculate_cutoff_timestamp("invalid")
        
        with pytest.raises(ValueError, match="Invalid time_range"):
            hot_topics_service._calculate_cutoff_timestamp("1h")
        
        with pytest.raises(ValueError, match="Invalid time_range"):
            hot_topics_service._calculate_cutoff_timestamp("90d")


class TestCalculateEngagementScore:
    """Unit tests for calculate_engagement_score method (to be implemented in Phase 3)."""
    
    @pytest.fixture
    def hot_topics_service(self):
        """Create a HotTopicsService with mocked containers."""
        sentiment_scores = Mock()
        reddit_posts = Mock()
        reddit_comments = Mock()
        tools = Mock()
        
        return HotTopicsService(
            sentiment_scores_container=sentiment_scores,
            reddit_posts_container=reddit_posts,
            reddit_comments_container=reddit_comments,
            tools_container=tools,
        )
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T008)")
    def test_engagement_score_formula(self, hot_topics_service):
        """
        Test engagement score calculation formula: (mentions × 10) + (comments × 2) + upvotes.
        
        Task: T017 (tests T008 implementation)
        Purpose: Verify engagement scoring algorithm
        Setup: Mock data with known mention/comment/upvote counts
        Test: Call calculate_engagement_score()
        Assertions:
          - Formula applied correctly
          - Returns integer score
        
        Example:
          mentions=5, comments=20, upvotes=100
          score = (5 × 10) + (20 × 2) + 100 = 50 + 40 + 100 = 190
        """
        # This test will be enabled once T008 is implemented
        pass
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T008)")
    def test_engagement_score_zero_activity(self, hot_topics_service):
        """
        Test engagement score with zero activity (no mentions, comments, upvotes).
        
        Task: T017
        Purpose: Verify edge case handling
        """
        # Should return 0 when no activity
        pass


class TestAggregateSentimentDistribution:
    """Unit tests for _aggregate_sentiment_distribution method (to be implemented in Phase 3)."""
    
    @pytest.fixture
    def hot_topics_service(self):
        """Create a HotTopicsService with mocked containers."""
        sentiment_scores = Mock()
        reddit_posts = Mock()
        reddit_comments = Mock()
        tools = Mock()
        
        return HotTopicsService(
            sentiment_scores_container=sentiment_scores,
            reddit_posts_container=reddit_posts,
            reddit_comments_container=reddit_comments,
            tools_container=tools,
        )
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T009)")
    def test_sentiment_distribution_percentages(self, hot_topics_service):
        """
        Test sentiment distribution percentage calculations.
        
        Task: T017 (tests T009 implementation)
        Purpose: Verify percentage calculation accuracy
        Setup: Mock sentiment_scores with known positive/negative/neutral counts
        Test: Call _aggregate_sentiment_distribution()
        Assertions:
          - Percentages sum to 100.0 (within floating point tolerance)
          - Counts match input data
          - Returns SentimentDistribution model
        
        Example:
          positive=60, negative=30, neutral=10 (total=100)
          percentages: 60.0%, 30.0%, 10.0%
        """
        pass
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T009)")
    def test_sentiment_distribution_single_sentiment(self, hot_topics_service):
        """
        Test sentiment distribution when all mentions have same sentiment.
        
        Task: T017
        Purpose: Verify edge case with 100% single sentiment
        
        Example:
          positive=50, negative=0, neutral=0
          percentages: 100.0%, 0.0%, 0.0%
        """
        pass
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T009)")
    def test_sentiment_distribution_rounding(self, hot_topics_service):
        """
        Test sentiment distribution percentage rounding.
        
        Task: T017
        Purpose: Verify percentages rounded to 1 decimal place
        
        Example:
          positive=1, negative=1, neutral=1 (total=3)
          percentages: 33.3%, 33.3%, 33.3% (sum=99.9%, acceptable)
        """
        pass
    
    @pytest.mark.skip(reason="Method not yet implemented - Phase 3 (T009)")
    def test_sentiment_distribution_zero_mentions(self, hot_topics_service):
        """
        Test sentiment distribution with zero mentions.
        
        Task: T017
        Purpose: Verify handling of tools with no sentiment data
        Should return all zeros or raise appropriate error
        """
        pass


class TestGetHotTopicsParameters:
    """Unit tests for get_hot_topics parameter validation."""
    
    @pytest.fixture
    def hot_topics_service(self):
        """Create a HotTopicsService with mocked containers."""
        sentiment_scores = Mock()
        reddit_posts = Mock()
        reddit_comments = Mock()
        tools = Mock()
        
        return HotTopicsService(
            sentiment_scores_container=sentiment_scores,
            reddit_posts_container=reddit_posts,
            reddit_comments_container=reddit_comments,
            tools_container=tools,
        )
    
    @pytest.mark.asyncio
    async def test_get_hot_topics_default_parameters(self, hot_topics_service):
        """
        Test get_hot_topics with default parameters.
        
        Task: T017
        Purpose: Verify default time_range="7d" and limit=10
        """
        response = await hot_topics_service.get_hot_topics()
        
        assert response.time_range == "7d"
        assert response.generated_at is not None
        assert isinstance(response.hot_topics, list)
    
    @pytest.mark.asyncio
    async def test_get_hot_topics_custom_parameters(self, hot_topics_service):
        """
        Test get_hot_topics with custom time_range and limit.
        
        Task: T017
        Purpose: Verify parameter passing
        """
        response = await hot_topics_service.get_hot_topics(
            time_range="24h",
            limit=20
        )
        
        assert response.time_range == "24h"
    
    @pytest.mark.asyncio
    async def test_get_hot_topics_invalid_limit_too_low(self, hot_topics_service):
        """
        Test get_hot_topics rejects limit < 1.
        
        Task: T017
        Purpose: Verify input validation
        """
        with pytest.raises(ValueError, match="limit must be between 1 and 50"):
            await hot_topics_service.get_hot_topics(limit=0)
    
    @pytest.mark.asyncio
    async def test_get_hot_topics_invalid_limit_too_high(self, hot_topics_service):
        """
        Test get_hot_topics rejects limit > 50.
        
        Task: T017
        Purpose: Verify input validation
        """
        with pytest.raises(ValueError, match="limit must be between 1 and 50"):
            await hot_topics_service.get_hot_topics(limit=51)
    
    @pytest.mark.asyncio
    async def test_get_hot_topics_invalid_time_range(self, hot_topics_service):
        """
        Test get_hot_topics rejects invalid time_range.
        
        Task: T017
        Purpose: Verify input validation delegates to _calculate_cutoff_timestamp
        """
        with pytest.raises(ValueError, match="Invalid time_range"):
            await hot_topics_service.get_hot_topics(time_range="invalid")


class TestGetRelatedPostsParameters:
    """Unit tests for get_related_posts parameter validation."""
    
    @pytest.fixture
    def hot_topics_service(self):
        """Create a HotTopicsService with mocked containers."""
        sentiment_scores = Mock()
        reddit_posts = Mock()
        reddit_comments = Mock()
        tools = Mock()
        
        return HotTopicsService(
            sentiment_scores_container=sentiment_scores,
            reddit_posts_container=reddit_posts,
            reddit_comments_container=reddit_comments,
            tools_container=tools,
        )
    
    @pytest.mark.asyncio
    async def test_get_related_posts_default_parameters(self, hot_topics_service):
        """
        Test get_related_posts with default parameters.
        
        Task: T017
        Purpose: Verify default time_range="7d", offset=0, limit=20
        """
        response = await hot_topics_service.get_related_posts(tool_id="test-tool")
        
        assert response.offset == 0
        assert response.limit == 20
        assert isinstance(response.posts, list)
        assert response.total >= 0
        assert isinstance(response.has_more, bool)
    
    @pytest.mark.asyncio
    async def test_get_related_posts_custom_pagination(self, hot_topics_service):
        """
        Test get_related_posts with custom offset and limit.
        
        Task: T017
        Purpose: Verify pagination parameter passing
        """
        response = await hot_topics_service.get_related_posts(
            tool_id="test-tool",
            offset=20,
            limit=50
        )
        
        assert response.offset == 20
        assert response.limit == 50
    
    @pytest.mark.asyncio
    async def test_get_related_posts_invalid_limit_too_low(self, hot_topics_service):
        """
        Test get_related_posts rejects limit < 1.
        
        Task: T017
        Purpose: Verify input validation
        """
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            await hot_topics_service.get_related_posts(
                tool_id="test-tool",
                limit=0
            )
    
    @pytest.mark.asyncio
    async def test_get_related_posts_invalid_limit_too_high(self, hot_topics_service):
        """
        Test get_related_posts rejects limit > 100.
        
        Task: T017
        Purpose: Verify input validation
        """
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            await hot_topics_service.get_related_posts(
                tool_id="test-tool",
                limit=101
            )
    
    @pytest.mark.asyncio
    async def test_get_related_posts_invalid_offset_negative(self, hot_topics_service):
        """
        Test get_related_posts rejects negative offset.
        
        Task: T017
        Purpose: Verify input validation
        """
        with pytest.raises(ValueError, match="offset must be >= 0"):
            await hot_topics_service.get_related_posts(
                tool_id="test-tool",
                offset=-1
            )
