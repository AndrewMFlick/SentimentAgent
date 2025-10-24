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
