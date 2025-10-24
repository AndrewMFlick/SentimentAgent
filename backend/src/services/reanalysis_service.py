"""Reanalysis service for sentiment re-processing jobs."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import structlog
import uuid

from ..models.reanalysis import (
    JobStatus,
    ReanalysisJob,
    ReanalysisJobRequest,
)

logger = structlog.get_logger()


class ReanalysisService:
    """Service for managing sentiment reanalysis jobs."""

    def __init__(
        self,
        reanalysis_jobs_container,
        sentiment_container,
        tools_container,
        aliases_container,
    ):
        """
        Initialize ReanalysisService.

        Args:
            reanalysis_jobs_container: Cosmos DB container for ReanalysisJobs
            sentiment_container: Cosmos DB container for sentiment_scores
            tools_container: Cosmos DB container for Tools
            aliases_container: Cosmos DB container for ToolAliases
        """
        self.jobs = reanalysis_jobs_container
        self.sentiment = sentiment_container
        self.tools = tools_container
        self.aliases = aliases_container

    async def _resolve_tool_aliases(self, tool_id: str) -> List[str]:
        """
        Resolve a tool ID to include all related tools via aliases.

        Follows alias chains to find:
        - The primary tool this aliases to (if this is an alias)
        - All aliases that point to this tool (if this is primary)

        Args:
            tool_id: The tool ID to resolve

        Returns:
            List of all related tool IDs (including the original)

        Example:
            tool_id="copilot-alias" -> ["copilot", "copilot-alias", "copilot-v2"]
        """
        related_ids = {tool_id}  # Start with original ID

        # Find if this tool is an alias (points to another tool)
        query = "SELECT c.primary_tool_id FROM c WHERE c.alias_tool_id = @tool_id"
        params = [{"name": "@tool_id", "value": tool_id}]
        
        try:
            items = list(self.aliases.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            if items:
                primary_id = items[0]["primary_tool_id"]
                related_ids.add(primary_id)
                tool_id = primary_id  # Continue search from primary
        except Exception as e:
            logger.warning(
                "Failed to query aliases for primary tool",
                tool_id=tool_id,
                error=str(e)
            )

        # Find all aliases that point to this tool (now the primary)
        query = "SELECT c.alias_tool_id FROM c WHERE c.primary_tool_id = @tool_id"
        params = [{"name": "@tool_id", "value": tool_id}]
        
        try:
            items = list(self.aliases.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            
            for item in items:
                related_ids.add(item["alias_tool_id"])
        except Exception as e:
            logger.warning(
                "Failed to query aliases for tool",
                tool_id=tool_id,
                error=str(e)
            )

        result = list(related_ids)
        logger.debug(
            "Resolved tool aliases",
            original_tool_id=tool_id,
            related_ids=result,
            count=len(result)
        )
        return result

    def _validate_state_transition(
        self,
        current_status: JobStatus,
        new_status: JobStatus
    ) -> None:
        """
        Validate that a state transition is allowed.

        State machine rules:
        - QUEUED can transition to: RUNNING, FAILED
        - RUNNING can transition to: COMPLETED, FAILED
        - COMPLETED is terminal (no transitions)
        - FAILED is terminal (no transitions)

        Args:
            current_status: Current job status
            new_status: Desired new status

        Raises:
            ValueError: If transition is not allowed
        """
        valid_transitions = {
            JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.FAILED},
            JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED},
            JobStatus.COMPLETED: set(),  # Terminal state
            JobStatus.FAILED: set(),  # Terminal state
        }

        allowed = valid_transitions.get(current_status, set())
        
        if new_status not in allowed:
            raise ValueError(
                f"Invalid state transition: {current_status.value} -> "
                f"{new_status.value}. Allowed: {[s.value for s in allowed]}"
            )

        logger.debug(
            "State transition validated",
            current=current_status.value,
            new=new_status.value
        )

    async def check_active_jobs(self) -> int:
        """
        Check for active (queued or running) reanalysis jobs.

        Returns:
            Count of active jobs

        Example usage:
            active_count = await service.check_active_jobs()
            if active_count > 0:
                raise ValueError("Cannot start job: existing job in progress")
        """
        query = (
            "SELECT VALUE COUNT(1) FROM c "
            "WHERE c.status IN ('queued', 'running')"
        )
        
        try:
            result = list(self.jobs.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            count = result[0] if result else 0
            logger.debug("Active jobs check", count=count)
            return count
        except Exception as e:
            logger.error(
                "Failed to check active jobs",
                error=str(e),
                exc_info=True
            )
            # Fail-safe: assume no active jobs to avoid blocking
            return 0

    async def trigger_manual_reanalysis(
        self,
        job_request: ReanalysisJobRequest,
        triggered_by: str
    ) -> Dict[str, Any]:
        """
        Trigger a manual reanalysis job.

        Args:
            job_request: Job parameters (date_range, tool_ids, batch_size)
            triggered_by: Admin username who triggered the job

        Returns:
            Created job document with job_id, status, estimated_docs

        Raises:
            ValueError: If active job exists or parameters are invalid
        """
        # Check for concurrent jobs
        active_count = await self.check_active_jobs()
        if active_count > 0:
            raise ValueError(
                f"Cannot start job: {active_count} job(s) already active"
            )

        # Build query to count documents that need reanalysis
        query_parts = ["SELECT VALUE COUNT(1) FROM c WHERE 1=1"]
        params = []

        # Optional date range filter
        if job_request.date_range:
            date_range = job_request.date_range
            if date_range.get("start"):
                query_parts.append("AND c._ts >= @start_ts")
                # Convert ISO 8601 to Unix timestamp
                start_dt = datetime.fromisoformat(
                    date_range["start"].replace("Z", "+00:00")
                )
                params.append({
                    "name": "@start_ts",
                    "value": int(start_dt.timestamp())
                })
            if date_range.get("end"):
                query_parts.append("AND c._ts <= @end_ts")
                end_dt = datetime.fromisoformat(
                    date_range["end"].replace("Z", "+00:00")
                )
                params.append({
                    "name": "@end_ts",
                    "value": int(end_dt.timestamp())
                })

        # Optional tool filter (for re-processing specific tools)
        if job_request.tool_ids:
            # This would reprocess docs that mention these tools
            # For initial backfill, we typically process all docs
            pass

        count_query = " ".join(query_parts)
        
        try:
            result = list(self.sentiment.query_items(
                query=count_query,
                parameters=params if params else None,
                enable_cross_partition_query=True
            ))
            total_count = result[0] if result else 0
        except Exception as e:
            logger.error(
                "Failed to count documents for reanalysis",
                error=str(e),
                exc_info=True
            )
            raise ValueError(f"Failed to estimate job size: {str(e)}")

        # Create job document
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        job_doc = {
            "id": job_id,
            "status": JobStatus.QUEUED.value,
            "trigger_type": "manual",
            "triggered_by": triggered_by,
            "parameters": {
                "date_range": job_request.date_range,
                "tool_ids": job_request.tool_ids,
                "batch_size": job_request.batch_size
            },
            "progress": {
                "total_count": total_count,
                "processed_count": 0,
                "percentage": 0.0,
                "last_checkpoint_id": None
            },
            "statistics": {
                "tools_detected": {},
                "errors_count": 0,
                "categorized_count": 0,
                "uncategorized_count": 0
            },
            "error_log": [],
            "start_time": None,
            "end_time": None,
            "created_at": now
        }

        # Save to database
        try:
            self.jobs.create_item(body=job_doc)
            logger.info(
                "Reanalysis job created",
                job_id=job_id,
                triggered_by=triggered_by,
                total_count=total_count,
                batch_size=job_request.batch_size
            )
        except Exception as e:
            logger.error(
                "Failed to create reanalysis job",
                error=str(e),
                exc_info=True
            )
            raise ValueError(f"Failed to create job: {str(e)}")

        return {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "estimated_docs": total_count,
            "created_at": now
        }
