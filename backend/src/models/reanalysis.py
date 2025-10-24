"""
Pydantic models for Admin Sentiment Reanalysis feature (Feature 013).

Models for job tracking, progress monitoring, and API request/response.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job execution status - follows strict state transitions"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TriggerType(str, Enum):
    """How the reanalysis job was initiated"""

    MANUAL = "manual"
    AUTOMATIC = "automatic"


# Nested models


class ReanalysisParameters(BaseModel):
    """Parameters defining scope of reanalysis job"""

    date_range: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="ISO 8601 date range: {start, end}. None = all dates",
    )
    tool_ids: Optional[List[str]] = Field(
        default=None, description="Tool IDs to check. None/empty = all tools"
    )
    batch_size: int = Field(
        default=100, ge=1, le=1000, description="Docs per batch checkpoint"
    )


class JobProgress(BaseModel):
    """Real-time progress tracking for UI updates"""

    total_count: int = Field(default=0, ge=0)
    processed_count: int = Field(default=0, ge=0)
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    last_checkpoint_id: Optional[str] = Field(
        default=None, description="Last processed doc ID for resumption"
    )

    @field_validator("percentage", mode="before")
    @classmethod
    def calculate_percentage(cls, v, info):
        """Auto-calculate percentage from processed/total if not provided"""
        if v is None and info.data:
            total = info.data.get("total_count", 0)
            processed = info.data.get("processed_count", 0)
            return (processed / total * 100) if total > 0 else 0.0
        return v


class JobStatistics(BaseModel):
    """Aggregate statistics for completed/running jobs"""

    tools_detected: Dict[str, int] = Field(
        default_factory=dict,
        description="tool_id -> count of mentions detected",
    )
    errors_count: int = Field(default=0, ge=0)
    categorized_count: int = Field(
        default=0, ge=0, description="Docs with tools found"
    )
    uncategorized_count: int = Field(
        default=0, ge=0, description="Docs with no tools found"
    )


class ErrorEntry(BaseModel):
    """Individual error during processing"""

    doc_id: str = Field(description="sentiment_score document ID")
    error: str = Field(description="Error message")
    timestamp: str = Field(description="ISO 8601 timestamp")


# Main entity models


class ReanalysisJob(BaseModel):
    """
    Complete reanalysis job entity (stored in ReanalysisJobs collection)

    State transitions:
        queued -> running -> completed
                          -> failed
    """

    id: str = Field(description="Primary key: job-{uuid}")
    status: JobStatus
    trigger_type: TriggerType
    triggered_by: str = Field(description="Admin user ID or system")
    parameters: ReanalysisParameters
    progress: JobProgress = Field(default_factory=JobProgress)
    statistics: JobStatistics = Field(default_factory=JobStatistics)
    error_log: List[ErrorEntry] = Field(default_factory=list)
    start_time: Optional[str] = Field(
        default=None, description="ISO 8601 - when status became running"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="ISO 8601 - when status became completed/failed",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v, info):
        """start_time required for running/completed/failed jobs"""
        status = info.data.get("status")
        if status in {
            JobStatus.RUNNING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        }:
            if not v:
                raise ValueError(
                    f"start_time required when status={status.value}"
                )
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        """end_time required for completed/failed jobs"""
        status = info.data.get("status")
        if status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            if not v:
                raise ValueError(
                    f"end_time required when status={status.value}"
                )
        return v


# API request/response models


class ReanalysisJobRequest(BaseModel):
    """Request body for POST /admin/reanalysis/jobs"""

    date_range: Optional[Dict[str, Optional[str]]] = Field(
        default=None,
        description="Filter by date: {start: ISO, end: ISO}",
        examples=[
            {"start": "2025-01-01T00:00:00Z", "end": "2025-01-31T23:59:59Z"}
        ],
    )
    tool_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific tools to check. Omit for all tools.",
        examples=[["github-copilot", "cursor"]],
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Checkpoint frequency (docs per batch)",
    )


class ReanalysisJobResponse(BaseModel):
    """Response for POST /admin/reanalysis/jobs (202 Accepted)"""

    job_id: str = Field(description="Unique job identifier")
    status: JobStatus
    message: str = Field(
        default="Reanalysis job queued successfully",
        examples=["Reanalysis job queued successfully"],
    )
    estimated_docs: Optional[int] = Field(
        default=None, description="Estimated document count to process"
    )


class ReanalysisJobDetail(BaseModel):
    """Response for GET /admin/reanalysis/jobs/{job_id}"""

    job: ReanalysisJob
    message: str = Field(default="Job details retrieved successfully")


class ReanalysisJobList(BaseModel):
    """Response for GET /admin/reanalysis/jobs"""

    jobs: List[ReanalysisJob]
    total_count: int = Field(ge=0)
    message: str = Field(default="Jobs retrieved successfully")
