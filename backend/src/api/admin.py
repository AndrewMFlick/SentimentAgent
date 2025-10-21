"""Admin API endpoints for tool approval workflow and tool management."""

from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Query, Depends

from ..services.database import db
from ..services.tool_manager import tool_manager
from ..services.tool_service import ToolService
from ..models.tool import ToolCreateRequest, ToolUpdateRequest, AliasLinkRequest

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Dependency to get ToolService instance
async def get_tool_service() -> ToolService:
    """Get ToolService instance from database containers."""
    if not db.client or not db.database:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    tools_container = db.database.get_container_client("Tools")
    aliases_container = db.database.get_container_client("ToolAliases")
    
    return ToolService(
        tools_container=tools_container,
        aliases_container=aliases_container
    )


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


# =========================================================================
# Tool Management Endpoints (CRUD operations for admin)
# =========================================================================


@router.post("/tools")
async def create_tool(
    tool_data: ToolCreateRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Create a new AI tool.

    Requires admin authentication.

    Args:
        tool_data: Tool creation request data
        x_admin_token: Admin authentication token

    Returns:
        Created tool record
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin creating tool",
            tool_name=tool_data.name,
            admin=admin_user
        )

        # Create tool using ToolService
        tool = await tool_service.create_tool(tool_data)

        logger.info(
            "Tool created successfully",
            tool_id=tool["id"],
            tool_name=tool["name"],
            admin=admin_user
        )

        return {"tool": tool, "message": "Tool created successfully"}

    except ValueError as e:
        logger.warning(
            "Tool creation validation error",
            error=str(e),
            tool_name=tool_data.name
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create tool",
            tool_name=tool_data.name,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create tool")


@router.get("/tools")
async def list_tools(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    search: str = Query(default="", description="Search by tool name"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    List all tools with pagination and filtering.

    Requires admin authentication.

    Args:
        page: Page number (1-indexed)
        limit: Results per page
        search: Search query
        category: Category filter
        x_admin_token: Admin authentication token

    Returns:
        Paginated list of tools
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin listing tools",
            page=page,
            limit=limit,
            search=search,
            category=category,
            admin=admin_user
        )

        # Get tools and total count
        tools = await tool_service.list_tools(
            page=page,
            limit=limit,
            search=search,
            category=category
        )
        
        total = await tool_service.count_tools(
            search=search,
            category=category
        )

        logger.info(
            "Tools listed successfully",
            count=len(tools),
            total=total,
            admin=admin_user
        )

        return {
            "tools": tools,
            "total": total,
            "page": page,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list tools",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to list tools")


@router.get("/tools/{tool_id}")
async def get_tool_details(
    tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Get details of a specific tool.

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        x_admin_token: Admin authentication token

    Returns:
        Tool record with aliases
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info("Admin fetching tool details", tool_id=tool_id, admin=admin_user)

        # Get tool
        tool = await tool_service.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        # Get aliases
        aliases = await tool_service.get_aliases(tool_id)

        logger.info(
            "Tool details retrieved",
            tool_id=tool_id,
            alias_count=len(aliases),
            admin=admin_user
        )

        return {"tool": tool, "aliases": aliases}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get tool details",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve tool details")


@router.put("/tools/{tool_id}")
async def update_tool(
    tool_id: str,
    updates: ToolUpdateRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Update tool details.

    Requires admin authentication.

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

        logger.info(
            "Admin updating tool",
            tool_id=tool_id,
            updates=updates.dict(exclude_unset=True),
            admin=admin_user
        )

        # Update tool
        tool = await tool_service.update_tool(tool_id, updates)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        logger.info(
            "Tool updated successfully",
            tool_id=tool_id,
            admin=admin_user
        )

        return {"tool": tool, "message": "Tool updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update tool",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to update tool")


@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Delete a tool (soft delete - sets status to 'deleted').

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        x_admin_token: Admin authentication token

    Returns:
        Success message
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info("Admin deleting tool", tool_id=tool_id, admin=admin_user)

        # Delete tool (soft delete)
        success = await tool_service.delete_tool(tool_id, hard_delete=False)
        if not success:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")

        logger.info(
            "Tool deleted successfully",
            tool_id=tool_id,
            admin=admin_user
        )

        return {"message": "Tool deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete tool",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to delete tool")


@router.put("/tools/{tool_id}/alias")
async def link_alias(
    tool_id: str,
    link_request: AliasLinkRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Link a tool as an alias to another primary tool.

    Requires admin authentication.

    Args:
        tool_id: Tool ID to set as alias
        link_request: Primary tool ID
        x_admin_token: Admin authentication token

    Returns:
        Created alias relationship
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin linking alias",
            alias_tool_id=tool_id,
            primary_tool_id=link_request.primary_tool_id,
            admin=admin_user
        )

        # Create alias
        alias = await tool_service.create_alias(
            alias_tool_id=tool_id,
            primary_tool_id=link_request.primary_tool_id,
            created_by=admin_user
        )

        logger.info(
            "Alias linked successfully",
            alias_id=alias["id"],
            admin=admin_user
        )

        return {"alias": alias, "message": "Alias linked successfully"}

    except ValueError as e:
        logger.warning(
            "Alias link validation error",
            error=str(e),
            alias_tool_id=tool_id
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to link alias",
            alias_tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to link alias")


@router.delete("/tools/{alias_tool_id}/alias")
async def unlink_alias(
    alias_tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Remove alias relationship for a tool.

    Requires admin authentication.

    Args:
        alias_tool_id: Alias tool ID
        x_admin_token: Admin authentication token

    Returns:
        Success message
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin unlinking alias",
            alias_tool_id=alias_tool_id,
            admin=admin_user
        )

        # Find and remove alias
        query = (
            "SELECT * FROM ToolAliases ta "
            "WHERE ta.alias_tool_id = @id AND ta.partitionKey = 'alias'"
        )
        
        aliases_container = db.database.get_container_client("ToolAliases")
        items = aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": alias_tool_id}]
        )

        results = []
        async for item in items:
            results.append(item)

        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No alias found for tool '{alias_tool_id}'"
            )

        # Remove the alias
        alias_id = results[0]["id"]
        success = await tool_service.remove_alias(alias_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove alias")

        logger.info(
            "Alias unlinked successfully",
            alias_tool_id=alias_tool_id,
            admin=admin_user
        )

        return {"message": "Alias unlinked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to unlink alias",
            alias_tool_id=alias_tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to unlink alias")
