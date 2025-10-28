"""Data models for tool management."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ToolCategory(str, Enum):
    """Tool category enumeration."""

    CODE_ASSISTANT = "code_assistant"
    AUTONOMOUS_AGENT = "autonomous_agent"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DEVOPS = "devops"
    PROJECT_MANAGEMENT = "project_management"
    COLLABORATION = "collaboration"
    OTHER = "other"
    # Legacy values for backward compatibility
    CODE_COMPLETION = "code-completion"
    CHAT = "chat"
    ANALYSIS = "analysis"


class ToolStatus(str, Enum):
    """Tool status enumeration."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class Tool(BaseModel):
    """Tool entity model with multi-category support."""

    id: str
    partitionKey: str = "TOOL"
    name: str = Field(..., min_length=1, max_length=200)
    slug: str
    vendor: str = Field(..., min_length=1, max_length=100)
    categories: List[ToolCategory] = Field(
        ..., min_length=1, max_length=5, description="1-5 categories per tool"
    )
    status: ToolStatus = ToolStatus.ACTIVE
    description: Optional[str] = Field(default=None, max_length=1000)
    merged_into: Optional[str] = Field(
        default=None, description="UUID of primary tool if this tool was merged"
    )
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    created_by: str = Field(..., description="Admin ID who created")
    updated_by: str = Field(..., description="Admin ID who last updated")

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate categories array."""
        if not v:
            raise ValueError("At least 1 category required")
        if len(v) > 5:
            raise ValueError("Maximum 5 categories allowed")
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate categories not allowed")
        return v

    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v):
        """Validate vendor is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Vendor cannot be empty or whitespace")
        return v.strip()

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


class ToolMergeRecord(BaseModel):
    """Tool merge operation record for audit trail."""

    id: str
    partitionKey: str  # Set to target_tool_id
    target_tool_id: str = Field(..., description="Primary tool (merged into)")
    source_tool_ids: List[str] = Field(
        ..., min_length=1, description="Tools being merged (1+ items)"
    )
    merged_at: str = Field(..., description="ISO 8601 timestamp")
    merged_by: str = Field(..., description="Admin ID")
    sentiment_count: int = Field(
        ..., ge=0, description="Number of sentiment records migrated"
    )
    target_categories_before: List[str] = Field(
        ..., description="Target tool categories before merge"
    )
    target_categories_after: List[str] = Field(
        ..., description="Target tool categories after merge"
    )
    target_vendor_before: str
    target_vendor_after: str
    source_tools_metadata: List[Dict] = Field(
        ..., description="Snapshot of source tools at merge time"
    )
    notes: Optional[str] = Field(default=None, description="Admin notes about merge")


class AdminActionLog(BaseModel):
    """Immutable audit trail of administrative actions."""

    id: str
    partitionKey: str = Field(
        ..., description="YYYYMM format for time-series partitioning"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    admin_id: str = Field(..., description="Administrator ID")
    action_type: str = Field(
        ..., description="create|edit|archive|unarchive|delete|merge"
    )
    tool_id: str = Field(..., description="Primary tool affected")
    tool_name: str = Field(..., description="Tool name (denormalized for readability)")
    before_state: Optional[Dict] = Field(
        default=None, description="Tool state before action"
    )
    after_state: Optional[Dict] = Field(
        default=None, description="Tool state after action"
    )
    metadata: Dict = Field(default_factory=dict, description="Additional context")
    ip_address: Optional[str] = Field(default=None, description="Admin IP address")
    user_agent: Optional[str] = Field(default=None, description="Browser/client info")


class ToolCreateRequest(BaseModel):
    """Request model for creating a new tool."""

    name: str = Field(..., min_length=1, max_length=200)
    vendor: str = Field(..., min_length=1, max_length=100)
    categories: List[ToolCategory] = Field(
        ..., min_length=1, max_length=5, description="1-5 categories per tool"
    )
    description: Optional[str] = Field(default="", max_length=1000)
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate categories array."""
        if not v:
            raise ValueError("At least 1 category required")
        if len(v) > 5:
            raise ValueError("Maximum 5 categories allowed")
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate categories not allowed")
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ToolUpdateRequest(BaseModel):
    """Request model for updating a tool (for US2)."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    vendor: Optional[str] = Field(None, min_length=1, max_length=100)
    categories: Optional[List[ToolCategory]] = Field(
        None, min_length=1, max_length=5, description="1-5 categories per tool"
    )
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[Dict[str, str]] = None

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate categories array if provided."""
        if v is not None:
            if len(v) < 1:
                raise ValueError("At least 1 category required")
            if len(v) > 5:
                raise ValueError("Maximum 5 categories allowed")
            # Check for duplicates
            if len(v) != len(set(v)):
                raise ValueError("Duplicate categories not allowed")
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ToolMergeRequest(BaseModel):
    """Request model for merging tools (for US5)."""

    target_tool_id: str = Field(..., description="Primary tool to merge into")
    source_tool_ids: List[str] = Field(
        ..., min_length=1, description="Tools to merge (1+ items)"
    )
    final_categories: List[ToolCategory] = Field(
        ..., min_length=1, max_length=5, description="Categories for merged tool"
    )
    final_vendor: str = Field(
        ..., min_length=1, max_length=100, description="Vendor for merged tool"
    )
    notes: Optional[str] = Field(
        default=None, max_length=2000, description="Admin notes about merge"
    )

    @field_validator("source_tool_ids")
    @classmethod
    def validate_source_tools(cls, v, values):
        """Validate source tools don't include target."""
        if "target_tool_id" in values.data:
            target = values.data["target_tool_id"]
            if target in v:
                raise ValueError("Source tools cannot include target tool")
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate source tools not allowed")
        return v

    @field_validator("final_categories")
    @classmethod
    def validate_categories(cls, v):
        """Validate categories array."""
        if len(v) < 1:
            raise ValueError("At least 1 category required")
        if len(v) > 5:
            raise ValueError("Maximum 5 categories allowed")
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Duplicate categories not allowed")
        return v

    class Config:
        """Pydantic config."""

        use_enum_values = True


class AliasLinkRequest(BaseModel):
    """Request model for linking a tool alias."""

    primary_tool_id: str = Field(..., pattern=r"^[a-f0-9-]{36}$")


class ToolResponse(BaseModel):
    """Response model for tool data."""

    id: str
    name: str
    slug: str
    vendor: str
    categories: List[str]  # Array of category strings
    status: str
    description: Optional[str]
    merged_into: Optional[str]
    metadata: Dict[str, str]
    created_at: str
    updated_at: str
    created_by: str
    updated_by: str
