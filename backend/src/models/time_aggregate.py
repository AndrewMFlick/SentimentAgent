"""Time Period Aggregate model for pre-computed sentiment stats."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TimePeriodAggregate(BaseModel):
    """Daily sentiment aggregates for AI tools."""
    
    id: str = Field(..., description="Unique aggregate identifier")
    tool_id: str = Field(..., description="AI tool ID")
    date: str = Field(
        ...,
        description="Date in YYYY-MM-DD format"
    )
    total_mentions: int = Field(
        default=0,
        ge=0,
        description="Total mentions on this date"
    )
    positive_count: int = Field(
        default=0,
        ge=0,
        description="Positive sentiment mentions"
    )
    negative_count: int = Field(
        default=0,
        ge=0,
        description="Negative sentiment mentions"
    )
    neutral_count: int = Field(
        default=0,
        ge=0,
        description="Neutral sentiment mentions"
    )
    avg_sentiment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Average compound sentiment score"
    )
    computed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Computation timestamp"
    )
    deleted_at: Optional[datetime] = Field(
        None,
        description="Soft delete timestamp for retention policy"
    )
