"""Data models for tool management."""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from enum import Enum


class ToolCategory(str, Enum):
    """Tool category enumeration."""

    CODE_COMPLETION = "code-completion"
    CHAT = "chat"
    ANALYSIS = "analysis"


class ToolStatus(str, Enum):
    """Tool status enumeration."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class Tool(BaseModel):
    """Tool entity model."""

    id: str
    partitionKey: str = "tool"
    name: str = Field(..., min_length=1, max_length=100)
    slug: str
    vendor: str = Field(..., min_length=1, max_length=100)
    category: ToolCategory
    description: str = Field(default="", max_length=500)
    status: ToolStatus = ToolStatus.ACTIVE
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ToolAlias(BaseModel):
    """Tool alias relationship model."""

    id: str
    partitionKey: str = "alias"
    alias_tool_id: str
    primary_tool_id: str
    created_at: str
    created_by: str


class ToolCreateRequest(BaseModel):
    """Request model for creating a new tool."""

    name: str = Field(..., min_length=1, max_length=100)
    vendor: str = Field(..., min_length=1, max_length=100)
    category: ToolCategory
    description: Optional[str] = Field(default="", max_length=500)
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ToolUpdateRequest(BaseModel):
    """Request model for updating a tool."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    vendor: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[ToolCategory] = None
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[ToolStatus] = None
    metadata: Optional[Dict[str, str]] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class AliasLinkRequest(BaseModel):
    """Request model for linking a tool alias."""

    primary_tool_id: str = Field(..., regex=r"^[a-f0-9-]{36}$")


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: str
    name: str
    slug: str
    vendor: str
    category: str
    description: str
    status: str
    metadata: Dict[str, str]
    created_at: str
    updated_at: str
