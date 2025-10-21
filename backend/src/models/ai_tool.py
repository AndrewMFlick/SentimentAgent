"""AI Tool model for tracking developer tools."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AITool(BaseModel):
    """AI developer tool tracking model."""
    
    id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Tool display name")
    vendor: str = Field(..., description="Tool vendor/company")
    category: str = Field(
        ...,
        description="Tool category: IDE, assistant, code-generator, etc."
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names/keywords for detection"
    )
    status: str = Field(
        default="pending",
        description="Approval status: pending, approved, rejected"
    )
    detection_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for mention detection"
    )
    approved_by: Optional[str] = Field(
        None,
        description="Admin username who approved"
    )
    approved_at: Optional[datetime] = Field(
        None,
        description="Approval timestamp"
    )
    rejected_by: Optional[str] = Field(
        None,
        description="Admin username who rejected"
    )
    rejected_at: Optional[datetime] = Field(
        None,
        description="Rejection timestamp"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Tool creation timestamp"
    )
