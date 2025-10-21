"""Admin API endpoints for tool approval workflow."""

from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Query

from ..models.tool import ToolCreateRequest, ToolUpdateRequest, AliasLinkRequest
from ..services.database import db
from ..services.tool_manager import tool_manager
from ..services.tool_service import ToolService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


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


# Phase 5: User Story 3 - Tool Management Dashboard Endpoints


@router.get("/tools")
async def list_tools(
    x_admin_token: Optional[str] = Header(None),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    search: str = Query("", description="Search query for tool name"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    List all tools with pagination, search, and filtering.

    Args:
        x_admin_token: Admin authentication token
        page: Page number (1-indexed)
        limit: Results per page (max 100)
        search: Search by tool name
        category: Filter by category

    Returns:
        Paginated list of tools with total count
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin listing tools",
            admin=admin_user,
            page=page,
            limit=limit,
            search=search,
            category=category,
        )

        # Initialize tool service
        if not db.tools_container or not db.aliases_container:
            raise HTTPException(
                status_code=500, detail="Database containers not initialized"
            )

        tool_service = ToolService(
            tools_container=db.tools_container,
            aliases_container=db.aliases_container,
        )

        # Get tools and total count
        tools = await tool_service.list_tools(
            page=page, limit=limit, search=search, category=category
        )
        total = await tool_service.count_tools(search=search, category=category)

        logger.info(
            "Tools listed",
            count=len(tools),
            total=total,
            page=page,
            admin=admin_user,
        )

        return {
            "tools": tools,
            "total": total,
            "page": page,
            "limit": limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list tools", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tools")


@router.put("/tools/{tool_id}")
async def update_tool(
    tool_id: str,
    updates: ToolUpdateRequest,
    x_admin_token: Optional[str] = Header(None),
):
    """
    Update tool details.

    Args:
        tool_id: Tool UUID
        updates: Fields to update
        x_admin_token: Admin authentication token

    Returns:
        Updated tool record
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        # Input validation
        import re

        if not re.match(r"^[a-f0-9-]{36}$", tool_id):
            raise HTTPException(
                status_code=400, detail="Invalid tool_id format (expected UUID)"
            )

        logger.info("Admin updating tool", tool_id=tool_id, admin=admin_user)

        # Initialize tool service
        if not db.tools_container or not db.aliases_container:
            raise HTTPException(
                status_code=500, detail="Database containers not initialized"
            )

        tool_service = ToolService(
            tools_container=db.tools_container,
            aliases_container=db.aliases_container,
        )

        # Update tool
        updated_tool = await tool_service.update_tool(tool_id, updates)
        if not updated_tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Security audit log
        logger.warning(
            "AUDIT: Tool updated",
            action="update_tool",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin_user=admin_user,
            updates=updates.dict(exclude_unset=True),
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success",
        )

        logger.info(
            "Tool updated successfully",
            tool_id=tool_id,
            tool_name=updated_tool.get("name"),
            admin=admin_user,
        )

        return {"tool": updated_tool, "message": "Tool updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update tool", tool_id=tool_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to update tool")


@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    hard_delete: bool = Query(
        False, description="Permanently delete (vs soft delete)"
    ),
    x_admin_token: Optional[str] = Header(None),
):
    """
    Delete a tool (soft delete by default).

    Soft delete sets status='deleted' and preserves data.
    Hard delete permanently removes the tool.

    Args:
        tool_id: Tool UUID
        hard_delete: If True, permanently delete; else set status='deleted'
        x_admin_token: Admin authentication token

    Returns:
        Success message
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        # Input validation
        import re

        if not re.match(r"^[a-f0-9-]{36}$", tool_id):
            raise HTTPException(
                status_code=400, detail="Invalid tool_id format (expected UUID)"
            )

        logger.info(
            "Admin deleting tool",
            tool_id=tool_id,
            hard_delete=hard_delete,
            admin=admin_user,
        )

        # Initialize tool service
        if not db.tools_container or not db.aliases_container:
            raise HTTPException(
                status_code=500, detail="Database containers not initialized"
            )

        tool_service = ToolService(
            tools_container=db.tools_container,
            aliases_container=db.aliases_container,
        )

        # Get tool info before deletion for audit log
        tool = await tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        tool_name = tool.get("name", "Unknown")

        # Delete tool
        success = await tool_service.delete_tool(tool_id, hard_delete=hard_delete)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Security audit log
        logger.warning(
            "AUDIT: Tool deleted",
            action="delete_tool",
            tool_id=tool_id,
            tool_name=tool_name,
            admin_user=admin_user,
            hard_delete=hard_delete,
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            status="success",
        )

        delete_type = "permanently" if hard_delete else "soft"
        logger.info(
            f"Tool {delete_type} deleted",
            tool_id=tool_id,
            tool_name=tool_name,
            admin=admin_user,
        )

        return {
            "message": f"Tool '{tool_name}' deleted successfully ({delete_type})",
            "tool_id": tool_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete tool", tool_id=tool_id, error=str(e), exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete tool")
