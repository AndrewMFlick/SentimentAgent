"""Sentiment cache service for pre-calculated aggregates.

Feature 017: Pre-Cached Sentiment Analysis
This service manages pre-calculated sentiment aggregates to enable fast
(<1 second) sentiment queries without loading thousands of documents.

Key Responsibilities:
- Cache lookup and validation (freshness checks)
- On-demand calculation with cache population
- Background refresh of all active tools
- Cache health metrics tracking

Architecture:
- Cache storage: Cosmos DB sentiment_cache container
- Partition key: /tool_id (all periods for a tool co-located)
- Cache entries: 4 periods per tool (1h, 24h, 7d, 30d)
- Refresh strategy: APScheduler background job (15-min intervals)
- Fallback: On cache miss, calculate on-demand and populate cache

Reference: specs/017-pre-cached-sentiment/
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from ..config import settings
from ..models.cache import (  # noqa: F401
    CacheMetadata,
    CachePeriod,
    SentimentCacheEntry,
)

logger = structlog.get_logger(__name__)


class CacheService:
    """Manages sentiment cache operations for fast query performance.
    
    This service provides:
    - Fast sentiment lookups from pre-calculated cache
    - Automatic cache refresh via background jobs
    - Graceful fallback to on-demand calculation
    - Cache health monitoring and metrics
    
    Example:
        >>> cache_service = CacheService(
        ...     cache_container,
        ...     sentiment_container,
        ...     tools_container
        ... )
        >>> sentiment = await cache_service.get_cached_sentiment(
        ...     tool_id="877eb2d8-...",
        ...     hours=24
        ... )
    """

    def __init__(
        self,
        cache_container: ContainerProxy,
        sentiment_container: ContainerProxy,
        tools_container: ContainerProxy,
    ):
        """Initialize cache service with required containers.
        
        Args:
            cache_container: sentiment_cache container for cache entries
            sentiment_container: sentiment_scores container for raw data
            tools_container: Tools container for active tool lookup
        """
        self.cache_container = cache_container
        self.sentiment_container = sentiment_container
        self.tools_container = tools_container
        self.cache_enabled = settings.enable_sentiment_cache
        self.cache_ttl_minutes = settings.cache_ttl_minutes
        
        logger.info(
            "CacheService initialized",
            cache_enabled=self.cache_enabled,
            cache_ttl_minutes=self.cache_ttl_minutes,
        )

    def _map_hours_to_period(self, hours: int) -> Optional[CachePeriod]:
        """Map request hours to standard cache period.
        
        Args:
            hours: Time window in hours
            
        Returns:
            CachePeriod enum if standard period, None otherwise
            
        Example:
            >>> period = cache_service._map_hours_to_period(24)
            >>> print(period)
            CachePeriod.HOUR_24
        """
        mapping = {
            1: CachePeriod.HOUR_1,
            24: CachePeriod.HOUR_24,
            168: CachePeriod.DAY_7,  # 7 days
            720: CachePeriod.DAY_30,  # 30 days
        }
        return mapping.get(hours)
    
    def _calculate_cache_key(self, tool_id: str, period: CachePeriod) -> str:
        """Generate cache document ID from tool_id and period.
        
        Args:
            tool_id: UUID of the tool
            period: Cache period enum
            
        Returns:
            Cache key string (format: {tool_id}:{period})
            
        Example:
            >>> key = cache_service._calculate_cache_key("tool-123", CachePeriod.HOUR_24)
            >>> print(key)
            "tool-123:HOUR_24"
        """
        return f"{tool_id}:{period.value}"
    
    def _is_cache_fresh(self, cache_entry: SentimentCacheEntry) -> bool:
        """Check if cache entry is within TTL (not stale).
        
        Args:
            cache_entry: Cache entry to check
            
        Returns:
            True if cache is fresh (within TTL), False if stale
            
        Example:
            >>> is_fresh = cache_service._is_cache_fresh(entry)
            >>> print(is_fresh)
            True
        """
        now_ts = int(datetime.now(timezone.utc).timestamp())
        cache_age_seconds = now_ts - cache_entry.last_updated_ts
        cache_age_minutes = cache_age_seconds / 60
        
        return cache_age_minutes <= self.cache_ttl_minutes
    
    async def _calculate_sentiment_aggregate(
        self,
        tool_id: str,
        hours: int
    ) -> dict:
        """Calculate sentiment aggregate from raw sentiment_scores data.
        
        Queries sentiment_scores container for the specified time window,
        aggregates in Python (CosmosDB limitation), and returns statistics.
        
        Args:
            tool_id: UUID of the tool
            hours: Time window in hours
            
        Returns:
            Dictionary with sentiment statistics
            
        Example:
            >>> result = await cache_service._calculate_sentiment_aggregate("tool-123", 24)
            >>> print(result)
            {
                'total_mentions': 100,
                'positive_count': 60,
                'negative_count': 25,
                'neutral_count': 15,
                'positive_percentage': 60.0,
                'negative_percentage': 25.0,
                'neutral_percentage': 15.0,
                'average_sentiment': 0.35,
                'period_start_ts': 1698451200,
                'period_end_ts': 1698537600
            }
        """
        start_time = time.time()
        
        # Calculate time window
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        cutoff_ts = int(cutoff.timestamp())
        now_ts = int(now.timestamp())
        
        # Query sentiment scores for this tool in time window
        query = """
            SELECT c.sentiment_score, c.detected_tool_ids, c._ts
            FROM c
            WHERE ARRAY_CONTAINS(c.detected_tool_ids, @tool_id)
            AND c._ts >= @cutoff_ts
        """
        
        parameters = [
            {"name": "@tool_id", "value": tool_id},
            {"name": "@cutoff_ts", "value": cutoff_ts}
        ]
        
        # Aggregate data in Python
        scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        try:
            items = self.sentiment_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            )
            
            async for item in items:
                score = item.get("sentiment_score", 0.0)
                scores.append(score)
                
                # Categorize sentiment (same logic as existing system)
                if score > 0.1:
                    positive_count += 1
                elif score < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
                    
        except Exception as e:
            logger.error(
                "Failed to query sentiment scores",
                tool_id=tool_id,
                hours=hours,
                error=str(e),
                exc_info=True
            )
            # Return empty stats on error
            scores = []
        
        # Calculate statistics
        total_mentions = len(scores)
        
        if total_mentions > 0:
            positive_percentage = (positive_count / total_mentions) * 100
            negative_percentage = (negative_count / total_mentions) * 100
            neutral_percentage = (neutral_count / total_mentions) * 100
            average_sentiment = sum(scores) / total_mentions
        else:
            positive_percentage = 0.0
            negative_percentage = 0.0
            neutral_percentage = 0.0
            average_sentiment = 0.0
        
        duration = time.time() - start_time
        
        logger.info(
            "Sentiment aggregate calculated",
            tool_id=tool_id,
            hours=hours,
            total_mentions=total_mentions,
            duration_ms=int(duration * 1000)
        )
        
        return {
            "total_mentions": total_mentions,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": round(positive_percentage, 2),
            "negative_percentage": round(negative_percentage, 2),
            "neutral_percentage": round(neutral_percentage, 2),
            "average_sentiment": round(average_sentiment, 3),
            "period_start_ts": cutoff_ts,
            "period_end_ts": now_ts
        }
    
    async def _save_to_cache(self, cache_entry: SentimentCacheEntry) -> None:
        """Save cache entry to sentiment_cache container.
        
        Args:
            cache_entry: Cache entry to save
            
        Example:
            >>> await cache_service._save_to_cache(entry)
        """
        try:
            # Convert Pydantic model to dict for Cosmos
            entry_dict = cache_entry.model_dump()
            
            # Upsert to cache container
            self.cache_container.upsert_item(body=entry_dict)
            
            logger.debug(
                "Cache entry saved",
                cache_id=cache_entry.id,
                tool_id=cache_entry.tool_id,
                period=cache_entry.period.value
            )
        except Exception as e:
            # Log error but don't fail - cache save is not critical
            logger.warning(
                "Failed to save cache entry",
                cache_id=cache_entry.id,
                error=str(e),
                exc_info=True
            )
    
    async def get_cached_sentiment(
        self,
        tool_id: str,
        hours: int
    ) -> dict:
        """Get sentiment data from cache or calculate on-demand.
        
        Main entry point for sentiment queries. Attempts cache lookup first,
        falls back to on-demand calculation if cache miss or stale.
        
        Args:
            tool_id: UUID of the tool
            hours: Time window in hours (1, 24, 168, 720)
            
        Returns:
            Sentiment aggregate dictionary with counts and percentages
            
        Example:
            >>> result = await cache_service.get_cached_sentiment(
            ...     "877eb2d8-...",
            ...     24
            ... )
            >>> print(result)
            {
                'total_mentions': 150,
                'positive_count': 100,
                'negative_count': 30,
                'neutral_count': 20,
                'positive_percentage': 66.7,
                'negative_percentage': 20.0,
                'neutral_percentage': 13.3,
                'average_sentiment': 0.45,
                'is_cached': True,
                'cached_at': 1698451200
            }
        """
        start_time = time.time()
        
        logger.info(
            "Cache lookup started",
            tool_id=tool_id,
            hours=hours,
            cache_enabled=self.cache_enabled,
        )
        
        # Check if cache is enabled
        if not self.cache_enabled:
            logger.debug("Cache disabled, calculating on-demand")
            result = await self._calculate_sentiment_aggregate(tool_id, hours)
            result["is_cached"] = False
            return result
        
        # Map hours to cache period
        period = self._map_hours_to_period(hours)
        
        # Non-standard period - calculate on-demand without caching
        if period is None:
            logger.info(
                "Non-standard time period, calculating on-demand",
                hours=hours
            )
            result = await self._calculate_sentiment_aggregate(tool_id, hours)
            result["is_cached"] = False
            return result
        
        # Try cache lookup
        cache_key = self._calculate_cache_key(tool_id, period)
        cache_hit = False
        cached_at = None
        
        try:
            cache_data = self.cache_container.read_item(
                item=cache_key,
                partition_key=tool_id
            )
            
            # Parse cache entry
            cache_entry = SentimentCacheEntry(**cache_data)
            
            # Check if cache is fresh
            if self._is_cache_fresh(cache_entry):
                # Cache hit! Return cached data
                cache_hit = True
                cached_at = cache_entry.last_updated_ts
                
                duration = time.time() - start_time
                logger.info(
                    "Cache hit",
                    tool_id=tool_id,
                    period=period.value,
                    cache_age_minutes=int((int(datetime.now(timezone.utc).timestamp()) - cached_at) / 60),
                    duration_ms=int(duration * 1000)
                )
                
                return {
                    "total_mentions": cache_entry.total_mentions,
                    "positive_count": cache_entry.positive_count,
                    "negative_count": cache_entry.negative_count,
                    "neutral_count": cache_entry.neutral_count,
                    "positive_percentage": cache_entry.positive_percentage,
                    "negative_percentage": cache_entry.negative_percentage,
                    "neutral_percentage": cache_entry.neutral_percentage,
                    "average_sentiment": cache_entry.average_sentiment,
                    "is_cached": True,
                    "cached_at": cached_at
                }
            else:
                logger.info(
                    "Cache stale, recalculating",
                    tool_id=tool_id,
                    period=period.value,
                    cache_age_minutes=int((int(datetime.now(timezone.utc).timestamp()) - cache_entry.last_updated_ts) / 60)
                )
                
        except CosmosResourceNotFoundError:
            logger.info(
                "Cache miss",
                tool_id=tool_id,
                period=period.value
            )
        except Exception as e:
            # Log error but continue with fallback
            logger.warning(
                "Cache lookup error, falling back to on-demand calculation",
                tool_id=tool_id,
                error=str(e),
                exc_info=True
            )
        
        # Cache miss or stale - calculate on-demand
        sentiment_data = await self._calculate_sentiment_aggregate(tool_id, hours)
        
        # Save to cache for next request (fire-and-forget)
        try:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            cache_entry = SentimentCacheEntry(
                id=cache_key,
                tool_id=tool_id,
                period=period,
                total_mentions=sentiment_data["total_mentions"],
                positive_count=sentiment_data["positive_count"],
                negative_count=sentiment_data["negative_count"],
                neutral_count=sentiment_data["neutral_count"],
                positive_percentage=sentiment_data["positive_percentage"],
                negative_percentage=sentiment_data["negative_percentage"],
                neutral_percentage=sentiment_data["neutral_percentage"],
                average_sentiment=sentiment_data["average_sentiment"],
                period_start_ts=sentiment_data["period_start_ts"],
                period_end_ts=sentiment_data["period_end_ts"],
                last_updated_ts=now_ts
            )
            
            await self._save_to_cache(cache_entry)
            
        except Exception as e:
            # Log but don't fail - cache population is not critical
            logger.warning(
                "Failed to populate cache after calculation",
                tool_id=tool_id,
                error=str(e)
            )
        
        # Return calculated data
        duration = time.time() - start_time
        logger.info(
            "Sentiment data calculated",
            tool_id=tool_id,
            hours=hours,
            is_cached=cache_hit,
            duration_ms=int(duration * 1000)
        )
        
        sentiment_data["is_cached"] = False
        return sentiment_data

    async def refresh_all_tools(self) -> dict:
        """Refresh cache for all active tools (background job).
        
        Called by APScheduler every 15 minutes to keep cache fresh.
        Processes all active tools, calculating all 4 periods for each.
        
        Error handling: Logs and continues on individual tool failures.
        
        Returns:
            Summary with counts and duration
            
        Example:
            >>> result = await cache_service.refresh_all_tools()
            >>> print(result)
            {
                'tools_refreshed': 15,
                'entries_created': 60,
                'duration_ms': 5432,
                'errors': 0
            }
        """
        logger.info("Cache refresh job started")
        
        # TODO: Implement in Phase 4 (User Story 2)
        # 1. Get all active tool IDs
        # 2. For each tool, refresh all 4 periods
        # 3. Track errors but continue processing
        # 4. Update CacheMetadata
        # 5. Log summary statistics
        
        raise NotImplementedError(
            "Cache refresh not yet implemented (Phase 4 - User Story 2)"
        )

    async def invalidate_tool_cache(self, tool_id: str) -> None:
        """Invalidate (delete) all cache entries for a tool.
        
        Called when tool sentiment data changes (e.g., reanalysis).
        Cache will be repopulated on next query or refresh job.
        
        Args:
            tool_id: UUID of the tool
        """
        logger.info(
            "Cache invalidation started",
            tool_id=tool_id,
        )
        
        # TODO: Implement in Phase 7 (Invalidation)
        # 1. Query all cache entries for tool_id
        # 2. Delete each entry
        # 3. Log count of entries deleted
        
        raise NotImplementedError(
            "Cache invalidation not yet implemented (Phase 7)"
        )

    async def get_cache_health(self) -> dict:
        """Get cache health metrics for monitoring.
        
        Returns metadata including hit rate, last refresh time,
        and error counts.
        
        Returns:
            Cache health metrics dictionary
            
        Example:
            >>> health = await cache_service.get_cache_health()
            >>> print(health)
            {
                'status': 'healthy',
                'cache_hit_rate': 0.95,
                'last_refresh_ts': 1698451200,
                'last_refresh_duration_ms': 5432,
                'total_entries': 60,
                'error_count_24h': 0
            }
        """
        logger.debug("Cache health check started")
        
        # TODO: Implement in Phase 6 (Monitoring)
        # 1. Read CacheMetadata singleton
        # 2. Calculate status (healthy/degraded/unhealthy)
        # 3. Return metrics
        
        raise NotImplementedError(
            "Cache health check not yet implemented (Phase 6)"
        )


# Global instance (will be set in main.py lifespan)
cache_service: CacheService | None = None
