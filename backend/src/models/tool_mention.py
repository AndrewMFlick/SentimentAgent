"""Tool Mention model for tracking tool references in content."""

from datetime import datetime

from pydantic import BaseModel, Field


class ToolMention(BaseModel):
    """Tool mention in Reddit content."""

    id: str = Field(..., description="Unique mention identifier")
    tool_id: str = Field(..., description="Referenced AI tool ID")
    content_id: str = Field(..., description="Reddit post or comment ID")
    content_type: str = Field(..., description="Content type: post or comment")
    subreddit: str = Field(..., description="Source subreddit")
    mention_text: str = Field(
        ..., description="Extracted text snippet containing mention"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score"
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow, description="Detection timestamp"
    )
