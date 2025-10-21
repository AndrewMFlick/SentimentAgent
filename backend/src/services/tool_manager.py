"""Tool management service for approval workflow."""

from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()


class ToolManager:
    """Manage AI tool approval workflow and auto-detection."""

    def __init__(self, database_service):
        """
        Initialize tool manager.

        Args:
            database_service: Database service instance
        """
        self.db = database_service

    async def approve_tool(self, tool_id: str, approved_by: str) -> dict:
        """
        Approve a pending tool.

        Args:
            tool_id: Tool identifier
            approved_by: Admin username

        Returns:
            Updated tool record
        """
        logger.info("Approving tool", tool_id=tool_id, approved_by=approved_by)

        # Update tool status
        update_data = {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat(),
        }

        tool = await self.db.update_tool(tool_id, update_data)

        logger.info(
            "Tool approved successfully", tool_id=tool_id, tool_name=tool.get("name")
        )

        return tool

    async def reject_tool(self, tool_id: str, rejected_by: str) -> dict:
        """
        Reject a pending tool.

        Args:
            tool_id: Tool identifier
            rejected_by: Admin username

        Returns:
            Updated tool record
        """
        logger.info("Rejecting tool", tool_id=tool_id, rejected_by=rejected_by)

        # Update tool status
        update_data = {
            "status": "rejected",
            "rejected_by": rejected_by,
            "rejected_at": datetime.utcnow().isoformat(),
        }

        tool = await self.db.update_tool(tool_id, update_data)

        logger.info(
            "Tool rejected successfully", tool_id=tool_id, tool_name=tool.get("name")
        )

        return tool

    async def check_auto_detection(self) -> list[dict]:
        """
        Check for tools that should be auto-queued for approval.

        Finds tools with 50+ mentions in last 7 days.

        Returns:
            List of tools to queue for approval
        """
        logger.info("Checking for auto-detection candidates")

        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # Query tool mentions in last 7 days
        query = """
            SELECT
                tool_id,
                COUNT(1) as mention_count
            FROM tool_mentions
            WHERE detected_at >= @start_date
            GROUP BY tool_id
            HAVING COUNT(1) >= 50
        """

        candidates = await self.db.query_items(
            "tool_mentions",
            query,
            parameters=[{"name": "@start_date", "value": seven_days_ago.isoformat()}],
        )

        # Check if tools are already approved or pending
        tools_to_queue = []
        for candidate in candidates:
            tool = await self.db.get_tool(candidate["tool_id"])
            if tool and tool.get("status") not in ["approved", "pending"]:
                # Update to pending status
                await self.db.update_tool(candidate["tool_id"], {"status": "pending"})
                tools_to_queue.append(tool)

        logger.info(
            "Auto-detection check complete", candidates_found=len(tools_to_queue)
        )

        return tools_to_queue


# Create global instance (initialized later with db)
tool_manager: ToolManager | None = None
