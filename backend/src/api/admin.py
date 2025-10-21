"""Admin API endpoints for tool approval workflow."""

from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Depends

from ..services.database import db
from ..services.tool_manager import tool_manager
from ..services.tool_service import ToolService
from ..models.tool import AliasLinkRequest

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Dependency to get ToolService instance
async def get_tool_service() -> ToolService:
    """Get ToolService instance with database containers."""
    if not db.tools_container or not db.aliases_container:
        raise HTTPException(
            status_code=500,
            detail="Database containers not initialized"
        )
    return ToolService(db.tools_container, db.aliases_container)


# Simple authentication middleware (check for admin token)
def verify_admin(x_admin_token: Optional[str] = Header(None)) -> str:
    """
    Verify admin authentication token.

    Args:
        x_admin_token: Admin token from header

    Returns:
        Admin username

    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Replace with proper authentication system
    # For now, just check if token exists
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin authentication required")

    # In production, validate token against auth service
    # For now, return a placeholder admin user
    return "admin"


@router.get("/tools/pending")
async def get_pending_tools(x_admin_token: Optional[str] = Header(None)):
    """
    Get list of pending tools awaiting approval.

    Requires admin authentication.

    Returns:
        List of pending tools with mention counts
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info("Admin fetching pending tools", admin=admin_user)

        # Get pending tools from database
        pending_tools = await db.get_pending_tools()

        logger.info(
            "Retrieved pending tools", count=len(pending_tools), admin=admin_user
        )

        return {"tools": pending_tools, "count": len(pending_tools)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get pending tools", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve pending tools")


@router.post("/tools/{tool_id}/approve")
async def approve_tool(tool_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Approve a pending tool.

    This will:
    1. Update tool status to 'approved'
    2. Trigger historical data backfill (TODO: implement)
    3. Register tool with detector for future mentions

    Args:
        tool_id: Tool identifier (sanitized, alphanumeric + hyphens only)
        x_admin_token: Admin authentication token

    Returns:
        Updated tool record
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        # Input validation and sanitization for tool_id
        # Allow only alphanumeric characters, hyphens, and underscores
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", tool_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid tool_id format. Only alphanumeric "
                "characters, hyphens, and underscores allowed.",
            )

        if len(tool_id) > 100:
            raise HTTPException(
                status_code=400, detail="tool_id too long (max 100 characters)"
            )

        logger.info("Admin approving tool", tool_id=tool_id, admin=admin_user)

        # Check if tool exists
        tool = await db.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Check if already approved
        if tool.get("status") == "approved":
            raise HTTPException(status_code=400, detail="Tool is already approved")

        # Approve tool using tool_manager
        if not tool_manager:
            raise HTTPException(status_code=500, detail="Tool manager not initialized")

        updated_tool = await tool_manager.approve_tool(
            tool_id=tool_id, approved_by=admin_user
        )

        # TODO: Trigger historical data backfill job
        # This would scan past sentiment_scores for this tool
        # and create tool_mentions and aggregates

        # Security audit log
        logger.warning(
            "AUDIT: Tool approved",
            action="approve_tool",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin_user=admin_user,
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success",
        )

        logger.info(
            "Tool approved successfully",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin=admin_user,
        )

        return {"tool": updated_tool, "message": "Tool approved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to approve tool", tool_id=tool_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to approve tool")


@router.post("/tools/{tool_id}/reject")
async def reject_tool(tool_id: str, x_admin_token: Optional[str] = Header(None)):
    """
    Reject a pending tool.

    This will mark the tool as rejected and prevent it from
    appearing in pending lists.

    Args:
        tool_id: Tool identifier (sanitized, alphanumeric + hyphens only)
        x_admin_token: Admin authentication token

    Returns:
        Updated tool record
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        # Input validation and sanitization for tool_id
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", tool_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid tool_id format. Only alphanumeric "
                "characters, hyphens, and underscores allowed.",
            )

        if len(tool_id) > 100:
            raise HTTPException(
                status_code=400, detail="tool_id too long (max 100 characters)"
            )

        logger.info("Admin rejecting tool", tool_id=tool_id, admin=admin_user)

        # Check if tool exists
        tool = await db.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Check if already rejected
        if tool.get("status") == "rejected":
            raise HTTPException(status_code=400, detail="Tool is already rejected")

        # Reject tool using tool_manager
        if not tool_manager:
            raise HTTPException(status_code=500, detail="Tool manager not initialized")

        updated_tool = await tool_manager.reject_tool(
            tool_id=tool_id, rejected_by=admin_user
        )

        # Security audit log
        logger.warning(
            "AUDIT: Tool rejected",
            action="reject_tool",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin_user=admin_user,
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success",
        )

        logger.info(
            "Tool rejected successfully",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin=admin_user,
        )

        return {"tool": updated_tool, "message": "Tool rejected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to reject tool", tool_id=tool_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to reject tool")


@router.put("/tools/{tool_id}/alias")
async def link_alias(
    tool_id: str,
    link: AliasLinkRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Link a tool as an alias of another primary tool.

    This consolidates sentiment data for the alias tool under the primary tool.

    Args:
        tool_id: ID of the tool to set as alias
        link: Request containing primary_tool_id
        x_admin_token: Admin authentication token
        tool_service: ToolService dependency

    Returns:
        Success message with alias and primary tool details
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin linking alias",
            alias_tool_id=tool_id,
            primary_tool_id=link.primary_tool_id,
            admin=admin_user
        )

        # Validate both tools exist
        alias_tool = await tool_service.get_tool(tool_id)
        primary_tool = await tool_service.get_tool(link.primary_tool_id)

        if not alias_tool or not primary_tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        # Prevent self-referencing alias
        if tool_id == link.primary_tool_id:
            raise HTTPException(
                status_code=400,
                detail="Tool cannot be alias of itself"
            )

        # Check for circular aliases
        if await tool_service.has_circular_alias(tool_id, link.primary_tool_id):
            raise HTTPException(
                status_code=400,
                detail="Circular alias detected"
            )

        # Check if alias tool is already a primary for other tools
        existing_aliases = await tool_service.get_aliases(tool_id)
        if existing_aliases:
            raise HTTPException(
                status_code=400,
                detail="Alias tool is already primary for other aliases"
            )

        # Create alias relationship
        alias = await tool_service.create_alias(
            tool_id,
            link.primary_tool_id,
            admin_user
        )

        # Security audit log
        logger.warning(
            "AUDIT: Alias linked",
            action="link_alias",
            alias_tool_id=tool_id,
            alias_tool_name=alias_tool.get("name"),
            primary_tool_id=link.primary_tool_id,
            primary_tool_name=primary_tool.get("name"),
            admin_user=admin_user,
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success"
        )

        logger.info(
            "Alias linked successfully",
            alias_tool=alias_tool.get("name"),
            primary_tool=primary_tool.get("name"),
            admin=admin_user
        )

        return {
            "message": "Alias linked successfully",
            "alias_tool": {
                "id": alias_tool["id"],
                "name": alias_tool["name"]
            },
            "primary_tool": {
                "id": primary_tool["id"],
                "name": primary_tool["name"]
            }
        }

    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors from ToolService
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to link alias",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/tools/{tool_id}/alias")
async def unlink_alias(
    tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Remove alias relationship for a tool.

    This will remove the alias link, making the tool independent again.

    Args:
        tool_id: ID of the alias tool to unlink
        x_admin_token: Admin authentication token
        tool_service: ToolService dependency

    Returns:
        Success message
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin unlinking alias",
            alias_tool_id=tool_id,
            admin=admin_user
        )

        # Find the alias relationship
        query = (
            "SELECT * FROM ToolAliases ta "
            "WHERE ta.alias_tool_id = @id AND ta.partitionKey = 'alias'"
        )
        items = db.aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": tool_id}]
        )

        alias = None
        async for item in items:
            alias = item
            break

        if not alias:
            raise HTTPException(
                status_code=404,
                detail="No alias relationship found for this tool"
            )

        # Remove the alias
        removed = await tool_service.remove_alias(alias["id"])
        if not removed:
            raise HTTPException(
                status_code=404,
                detail="Alias relationship not found"
            )

        # Security audit log
        logger.warning(
            "AUDIT: Alias unlinked",
            action="unlink_alias",
            alias_tool_id=tool_id,
            admin_user=admin_user,
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success"
        )

        logger.info(
            "Alias unlinked successfully",
            alias_tool_id=tool_id,
            admin=admin_user
        )

        return {"message": "Alias unlinked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to unlink alias",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
