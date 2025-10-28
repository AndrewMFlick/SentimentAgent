"""Data models for sentiment cache management."""

from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class CachePeriod(str, Enum):
    """Time period granularities for cache entries."""

    HOUR_1 = "HOUR_1"
    HOUR_24 = "HOUR_24"
    DAY_7 = "DAY_7"
    DAY_30 = "DAY_30"


class SentimentCacheEntry(BaseModel):
    """Pre-calculated sentiment aggregates for a tool and time period.

    Attributes:
        id: Unique identifier, format: {tool_id}:{period}
        tool_id: ID of the tool this cache entry represents
        period: Time period (HOUR_1, HOUR_24, DAY_7, DAY_30)
        total_mentions: Total times tool was mentioned in this period
        positive_count: Number of positive sentiment mentions
        negative_count: Number of negative sentiment mentions
        neutral_count: Number of neutral sentiment mentions
        positive_percentage: Percentage of positive mentions (0-100)
        negative_percentage: Percentage of negative mentions (0-100)
        neutral_percentage: Percentage of neutral mentions (0-100)
        average_sentiment: Average sentiment score (-1.0 to 1.0)
        period_start_ts: Unix timestamp of period start
        period_end_ts: Unix timestamp of period end
        last_updated_ts: Unix timestamp when cache was refreshed
        is_stale: Whether cache is older than TTL (computed)
    """

    id: str = Field(..., description="Format: {tool_id}:{period}")
    tool_id: str = Field(..., description="UUID of the tool")
    period: CachePeriod
    total_mentions: int = Field(ge=0, description="Total mentions")
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)
    positive_percentage: float = Field(ge=0.0, le=100.0)
    negative_percentage: float = Field(ge=0.0, le=100.0)
    neutral_percentage: float = Field(ge=0.0, le=100.0)
    average_sentiment: float = Field(ge=-1.0, le=1.0)
    period_start_ts: int = Field(..., description="Unix timestamp")
    period_end_ts: int = Field(..., description="Unix timestamp")
    last_updated_ts: int = Field(..., description="Unix timestamp")
    is_stale: bool = Field(default=False, description="Computed: exceeds TTL")

    @field_validator("total_mentions")
    @classmethod
    def validate_total_mentions(cls, v, info):
        """Validate that total_mentions equals sum of sentiment counts."""
        if info.data:
            positive = info.data.get("positive_count", 0)
            negative = info.data.get("negative_count", 0)
            neutral = info.data.get("neutral_count", 0)

            if v != positive + negative + neutral:
                raise ValueError(
                    f"total_mentions ({v}) must equal sum of counts "
                    f"({positive} + {negative} + {neutral} = "
                    f"{positive + negative + neutral})"
                )
        return v

    @field_validator("neutral_percentage")
    @classmethod
    def validate_percentages_sum(cls, v, info):
        """Validate that percentages sum to 100 (within tolerance)."""
        if info.data:
            positive_pct = info.data.get("positive_percentage", 0.0)
            negative_pct = info.data.get("negative_percentage", 0.0)
            total = positive_pct + negative_pct + v

            if abs(total - 100.0) > 0.1:
                raise ValueError(
                    f"Percentages must sum to 100.0 (got {total:.2f})"
                )
        return v

    @field_validator("period_end_ts")
    @classmethod
    def validate_period_end(cls, v, info):
        """Validate that period_end_ts is after period_start_ts."""
        if info.data:
            start_ts = info.data.get("period_start_ts")
            if start_ts and v <= start_ts:
                raise ValueError(
                    f"period_end_ts ({v}) must be greater than "
                    f"period_start_ts ({start_ts})"
                )
        return v

    @field_validator("last_updated_ts")
    @classmethod
    def validate_last_updated(cls, v):
        """Validate that last_updated_ts is not in the future."""
        now_ts = int(datetime.now(timezone.utc).timestamp())
        if v > now_ts + 60:  # Allow 60s tolerance for clock skew
            raise ValueError(
                f"last_updated_ts ({v}) cannot be in the future "
                f"(now: {now_ts})"
            )
        return v


class CacheMetadata(BaseModel):
    """Tracks cache health and performance metrics for monitoring.
    
    Singleton document (id='metadata').
    
    Attributes:
        id: Always "metadata" (singleton document)
        last_refresh_ts: Unix timestamp of last successful refresh
        last_refresh_duration_ms: How long last refresh took (ms)
        total_entries: Current count of cache entries
        cache_hits_24h: Number of cache hits in last 24 hours
        cache_misses_24h: Number of cache misses in last 24 hours
        cache_hit_rate: Computed hit rate (hits / (hits + misses))
        error_count_24h: Number of errors in last 24 hours
        tools_refreshed: List of tool IDs refreshed in last cycle
    """

    id: str = Field(
        default="metadata",
        description="Always 'metadata' (singleton)"
    )
    last_refresh_ts: int = Field(
        ...,
        description="Unix timestamp of last refresh"
    )
    last_refresh_duration_ms: int = Field(
        ge=0,
        description="Duration in milliseconds"
    )
    total_entries: int = Field(
        ge=0,
        description="Current cache entry count"
    )
    cache_hits_24h: int = Field(ge=0, default=0)
    cache_misses_24h: int = Field(ge=0, default=0)
    error_count_24h: int = Field(ge=0, default=0)
    tools_refreshed: List[str] = Field(
        default_factory=list, description="Tool IDs refreshed in last cycle"
    )

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total_requests = self.cache_hits_24h + self.cache_misses_24h
        if total_requests == 0:
            return 0.0
        return self.cache_hits_24h / total_requests

    @field_validator("id")
    @classmethod
    def validate_singleton_id(cls, v):
        """Ensure id is always 'metadata' for singleton pattern."""
        if v != "metadata":
            raise ValueError("CacheMetadata id must be 'metadata' (singleton)")
        return v
