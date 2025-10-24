"""Admin API endpoints for tool approval workflow and tool management."""

from typing import Optional

import structlog
from fastapi import APIRouter, Header, HTTPException, Query, Depends

from ..models.tool import (
    ToolCreateRequest,
    ToolUpdateRequest,
    AliasLinkRequest,
    ToolMergeRequest,
)
from ..models.reanalysis import (
    ReanalysisJobRequest,
    ReanalysisJobResponse,
)
from ..services.database import db
from ..services.tool_manager import tool_manager
from ..services.tool_service import ToolService
from ..services.reanalysis_service import ReanalysisService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Dependency to get ToolService instance
async def get_tool_service() -> ToolService:
    """Get ToolService instance from database containers."""
    if not db.client or not db.database:
        raise HTTPException(status_code=500, detail="Database not initialized")

    tools_container = db.database.get_container_client("Tools")
    aliases_container = db.database.get_container_client("ToolAliases")
    admin_logs_container = db.database.get_container_client("AdminActionLogs")

    # Get sentiment container for cascade delete
    sentiment_container = None
    try:
        sentiment_container = db.database.get_container_client("sentiment_scores")
    except Exception as e:
        logger.warning("Sentiment container not available", error=str(e))

    return ToolService(
        tools_container=tools_container,
        aliases_container=aliases_container,
        admin_logs_container=admin_logs_container,
        sentiment_container=sentiment_container
    )


# Dependency to get ReanalysisService instance
async def get_reanalysis_service() -> ReanalysisService:
    """Get ReanalysisService instance from database containers."""
    if not db.client or not db.database:
        raise HTTPException(status_code=500, detail="Database not initialized")

    jobs_container = db.database.get_container_client("ReanalysisJobs")
    sentiment_container = db.database.get_container_client("sentiment_scores")
    tools_container = db.database.get_container_client("Tools")
    aliases_container = db.database.get_container_client("ToolAliases")

    return ReanalysisService(
        reanalysis_jobs_container=jobs_container,
        sentiment_container=sentiment_container,
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
    limit: int = Query(
        default=20, ge=1, le=100, description="Results per page"
    ),
    search: str = Query(default="", description="Search by tool name"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by status: active, archived, or all"
    ),
    category: Optional[str] = Query(
        default=None,
        description="Filter by category (can repeat for multiple)"
    ),
    vendor: Optional[str] = Query(
        default=None,
        description="Filter by vendor name"
    ),
    sort_by: str = Query(
        default="name",
        description="Sort by field: name, vendor, or updated_at"
    ),
    sort_order: str = Query(
        default="asc",
        description="Sort order: asc or desc"
    ),
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    List all tools with pagination, filtering, search, and sorting.

    Requires admin authentication.

    Query Parameters:
        page: Page number (1-indexed)
        limit: Results per page (max 100)
        search: Search query for tool name (case-insensitive)
        status: Filter by status (active, archived, or all)
        category: Filter by category (supports multiple)
        vendor: Filter by vendor name
        sort_by: Sort field (name, vendor, updated_at)
        sort_order: Sort order (asc or desc)

    Returns:
        Paginated list of tools with metadata
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        # Parse categories (if provided as comma-separated)
        categories = None
        if category:
            categories = [c.strip() for c in category.split(",")]

        logger.info(
            "Admin listing tools",
            page=page,
            limit=limit,
            search=search,
            status=status,
            categories=categories,
            vendor=vendor,
            sort_by=sort_by,
            sort_order=sort_order,
            admin=admin_user
        )

        # Get tools and total count
        tools = await tool_service.list_tools(
            page=page,
            limit=limit,
            search=search,
            status=status,
            categories=categories,
            vendor=vendor,
            sort_by=sort_by,
            sort_order=sort_order
        )

        total = await tool_service.count_tools(
            search=search,
            status=status,
            categories=categories,
            vendor=vendor
        )

        # Calculate pagination metadata
        total_pages = (total + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1

        # Build filters_applied metadata
        filters_applied = {}
        if status:
            filters_applied["status"] = status
        if categories:
            filters_applied["categories"] = categories
        if vendor:
            filters_applied["vendor"] = vendor
        if search:
            filters_applied["search"] = search

        logger.info(
            "Tools listed successfully",
            count=len(tools),
            total=total,
            total_pages=total_pages,
            admin=admin_user
        )

        return {
            "tools": tools,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev,
            "filters_applied": filters_applied
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
    if_match: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Update tool details with optimistic concurrency control.

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        updates: Fields to update
        x_admin_token: Admin authentication token
        if_match: ETag value for optimistic concurrency (optional)

    Returns:
        Updated tool record

    Raises:
        400: Validation error (duplicate name, invalid categories)
        404: Tool not found
        409: Concurrent modification detected (ETag mismatch)
        500: Server error
    """
    from azure.cosmos import exceptions

    admin_user = None

    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin updating tool",
            tool_id=tool_id,
            updates=updates.dict(exclude_unset=True),
            admin=admin_user,
            has_etag=bool(if_match)
        )

        # Update tool with ETag-based concurrency control
        tool = await tool_service.update_tool(
            tool_id=tool_id,
            updates=updates,
            updated_by=admin_user,
            etag=if_match,
            # Note: FastAPI doesn't provide easy access to client IP/UA
            # In production, you'd extract these from Request object
            ip_address=None,
            user_agent=None
        )

        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_id}' not found"
            )

        logger.info(
            "Tool updated successfully",
            tool_id=tool_id,
            admin=admin_user
        )

        return {"tool": tool, "message": "Tool updated successfully"}

    except ValueError as e:
        # Validation errors (duplicate name, invalid categories)
        logger.warning(
            "Tool update validation error",
            tool_id=tool_id,
            error=str(e),
            admin=admin_user
        )
        raise HTTPException(status_code=400, detail=str(e))
    except exceptions.CosmosHttpResponseError as e:
        if e.status_code == 412:
            # Precondition failed - ETag mismatch
            logger.warning(
                "Concurrent modification detected",
                tool_id=tool_id,
                admin=admin_user
            )
            raise HTTPException(
                status_code=409,
                detail="Concurrent modification detected. "
                "Please refresh and try again."
            )
        else:
            logger.error(
                "Cosmos DB error during tool update",
                tool_id=tool_id,
                status_code=e.status_code,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Database error occurred"
            )
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
    Permanently delete a tool including all associated sentiment data.

    This is a destructive operation that:
    1. Validates the tool can be deleted (not referenced by other tools)
    2. Retrieves sentiment count for confirmation
    3. Permanently deletes the tool
    4. Cascade deletes all associated sentiment data
    5. Logs the deletion action

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        x_admin_token: Admin authentication token

    Returns:
        Deletion result with sentiment count

    Raises:
        404: Tool not found
        409: Tool cannot be deleted (referenced by merged tools or in active job)
        500: Server error
    """
    admin_user = None

    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin permanently deleting tool",
            tool_id=tool_id,
            admin=admin_user
        )

        # Delete tool with hard delete (Phase 6 requirement)
        result = await tool_service.delete_tool(
            tool_id=tool_id,
            deleted_by=admin_user,
            hard_delete=True,  # Phase 6: always hard delete
            ip_address=None,  # TODO: Extract from Request
            user_agent=None   # TODO: Extract from Request
        )

        logger.info(
            "Tool permanently deleted",
            tool_id=tool_id,
            tool_name=result["tool_name"],
            sentiment_count=result["sentiment_count"],
            admin=admin_user
        )

        return {
            "message": "Tool permanently deleted",
            "tool_id": result["tool_id"],
            "tool_name": result["tool_name"],
            "sentiment_count": result["sentiment_count"]
        }

    except ValueError as e:
        # Validation errors (tool not found, referenced, in use)
        error_msg = str(e)
        logger.warning(
            "Tool deletion validation error",
            tool_id=tool_id,
            error=error_msg,
            admin=admin_user
        )

        # T068: Return 409 Conflict if tool is referenced or in active job
        if "referenced by" in error_msg or "in use" in error_msg:
            raise HTTPException(
                status_code=409,
                detail=error_msg
            )

        # 404 if tool not found
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)

        # Other validation errors
        raise HTTPException(status_code=400, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete tool",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to delete tool"
        )


@router.post("/tools/{tool_id}/archive")
async def archive_tool(
    tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Archive a tool (set status to 'archived').

    This preserves historical sentiment data while removing the tool
    from the active list.

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        x_admin_token: Admin authentication token

    Returns:
        Updated tool record

    Raises:
        404: Tool not found
        409: Tool cannot be archived (e.g., has tools merged into it)
        500: Server error
    """
    admin_user = None

    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info("Admin archiving tool", tool_id=tool_id, admin=admin_user)

        # Archive tool
        tool = await tool_service.archive_tool(
            tool_id=tool_id,
            archived_by=admin_user,
            ip_address=None,
            user_agent=None
        )

        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_id}' not found"
            )

        logger.info(
            "Tool archived successfully",
            tool_id=tool_id,
            tool_name=tool.get("name"),
            admin=admin_user
        )

        return {"tool": tool, "message": "Tool archived successfully"}

    except ValueError as e:
        # Validation errors (e.g., tool has merged tools)
        logger.warning(
            "Tool archive validation error",
            tool_id=tool_id,
            error=str(e),
            admin=admin_user
        )
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to archive tool",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to archive tool")


@router.post("/tools/{tool_id}/unarchive")
async def unarchive_tool(
    tool_id: str,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Unarchive a tool (set status to 'active').

    This restores a previously archived tool to the active list.

    Requires admin authentication.

    Args:
        tool_id: Tool UUID
        x_admin_token: Admin authentication token

    Returns:
        Updated tool record

    Raises:
        404: Tool not found
        500: Server error
    """
    admin_user = None

    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info("Admin unarchiving tool", tool_id=tool_id, admin=admin_user)

        # Unarchive tool
        tool = await tool_service.unarchive_tool(
            tool_id=tool_id,
            unarchived_by=admin_user,
            ip_address=None,
            user_agent=None
        )

        if not tool:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_id}' not found"
            )

        logger.info(
            "Tool unarchived successfully",
            tool_id=tool_id,
            tool_name=tool.get("name"),
            admin=admin_user
        )

        return {"tool": tool, "message": "Tool unarchived successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to unarchive tool",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to unarchive tool")


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


@router.post("/tools/merge")
async def merge_tools(
    merge_request: ToolMergeRequest,
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Merge multiple tools into a single primary tool.

    This operation:
    - Validates all tools exist and are active
    - Migrates sentiment data with source attribution
    - Updates target tool with new categories/vendor
    - Archives source tools with merged_into reference
    - Creates merge record and audit log

    Requires admin authentication.

    Args:
        merge_request: Merge request with target, sources, categories, vendor, notes
        x_admin_token: Admin authentication token

    Returns:
        merge_record: Full merge metadata
        target_tool: Updated target tool
        archived_tools: List of archived source tools
        warnings: List of metadata conflict warnings (if any)
        message: Success message with counts

    Raises:
        400: Validation error (invalid request, circular merge, etc.)
        404: One or more tools not found
        409: Conflict (tool already merged, not active, etc.)
        500: Server error
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin initiating tool merge",
            target_tool_id=merge_request.target_tool_id,
            source_tool_count=len(merge_request.source_tool_ids),
            admin=admin_user
        )

        # Validate merge request
        if len(merge_request.source_tool_ids) > 10:
            raise HTTPException(
                status_code=400,
                detail="Cannot merge more than 10 source tools at once"
            )

        if len(set(merge_request.source_tool_ids)) != len(
            merge_request.source_tool_ids
        ):
            raise HTTPException(
                status_code=400,
                detail="Source tool IDs must be unique"
            )

        if merge_request.target_tool_id in merge_request.source_tool_ids:
            raise HTTPException(
                status_code=400,
                detail="Cannot merge tool into itself"
            )

        # Validate categories are valid enum values
        try:
            # Convert request categories to strings for the service
            target_categories = [
                cat.value if hasattr(cat, 'value') else cat
                for cat in merge_request.final_categories
            ]
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category values: {str(e)}"
            )

        # Perform merge
        result = await tool_service.merge_tools(
            target_tool_id=merge_request.target_tool_id,
            source_tool_ids=merge_request.source_tool_ids,
            target_categories=target_categories,
            target_vendor=merge_request.final_vendor,
            merged_by=admin_user,
            notes=merge_request.notes
        )

        sentiment_count = result["merge_record"]["sentiment_count"]
        source_count = len(result["archived_tools"])
        target_name = result["target_tool"].get("name", "tool")

        plural = 's' if source_count != 1 else ''
        message = (
            f"Successfully merged {source_count} tool{plural} "
            f"into {target_name}. "
            f"Migrated {sentiment_count:,} sentiment records."
        )

        if result.get("warnings"):
            message += (
                " Merge completed with warnings. "
                "Please review metadata differences."
            )

        logger.info(
            "Tools merged successfully",
            target_tool_id=merge_request.target_tool_id,
            source_count=source_count,
            sentiment_count=sentiment_count,
            admin=admin_user
        )

        return {
            "merge_record": result["merge_record"],
            "target_tool": result["target_tool"],
            "archived_tools": result["archived_tools"],
            "warnings": result.get("warnings", []),
            "message": message
        }

    except ValueError as e:
        # Validation errors from ToolService
        error_msg = str(e)
        admin_user = verify_admin(x_admin_token)  # Get admin for logging

        # Determine appropriate status code
        if "not found" in error_msg.lower():
            status_code = 404
        elif any(
            word in error_msg.lower()
            for word in ["already merged", "must be active", "merged into"]
        ):
            status_code = 409
        else:
            status_code = 400

        logger.warning(
            "Tool merge validation error",
            error=error_msg,
            status_code=status_code,
            admin=admin_user
        )
        raise HTTPException(status_code=status_code, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to merge tools",
            target_tool_id=merge_request.target_tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred during the merge operation. "
                "All changes have been rolled back."
            )
        )


@router.get("/tools/{tool_id}/merge-history")
async def get_merge_history(
    tool_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Records per page (1-100)"
    ),
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Get merge history for a tool.

    Returns all merge operations where the specified tool was the target
    (i.e., other tools were merged into it).

    Requires admin authentication.

    Args:
        tool_id: Tool identifier
        page: Page number (1-indexed)
        limit: Records per page (1-100)
        x_admin_token: Admin authentication token

    Returns:
        merge_records: List of merge operation records
        total: Total number of merge operations
        page: Current page number
        limit: Records per page
        has_more: Whether there are more records

    Raises:
        404: Tool not found
        500: Server error
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin fetching merge history",
            tool_id=tool_id,
            page=page,
            limit=limit,
            admin=admin_user
        )

        # Get merge history
        result = await tool_service.get_merge_history(
            tool_id=tool_id,
            page=page,
            limit=limit
        )

        logger.info(
            "Merge history retrieved",
            tool_id=tool_id,
            count=len(result["merge_records"]),
            total=result["total"],
            admin=admin_user
        )

        return result

    except ValueError as e:
        error_msg = str(e)
        admin_user = verify_admin(x_admin_token)  # Get admin for logging

        # Determine status code
        if "not found" in error_msg.lower():
            status_code = 404
        else:
            status_code = 400

        logger.warning(
            "Merge history validation error",
            error=error_msg,
            status_code=status_code,
            tool_id=tool_id,
            admin=admin_user
        )
        raise HTTPException(status_code=status_code, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get merge history",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve merge history"
        )


@router.get("/tools/{tool_id}/audit-log")
async def get_audit_log(
    tool_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Records per page (1-100)"
    ),
    action_type: Optional[str] = Query(
        None,
        description="Filter by action type (created, edited, archived, unarchived, deleted, merged)"
    ),
    x_admin_token: Optional[str] = Header(None),
    tool_service: ToolService = Depends(get_tool_service)
):
    """
    Get audit log for a specific tool.

    Returns all administrative actions performed on the tool,
    including create, edit, archive, delete, and merge operations.

    Requires admin authentication.

    Args:
        tool_id: Tool identifier
        page: Page number (1-indexed)
        limit: Records per page (1-100)
        action_type: Optional filter by action type
        x_admin_token: Admin authentication token

    Returns:
        audit_records: List of audit log entries
        total: Total number of audit records
        page: Current page number
        limit: Records per page
        has_more: Whether there are more records

    Raises:
        404: Tool not found
        500: Server error
    """
    try:
        # Verify admin access
        admin_user = verify_admin(x_admin_token)

        logger.info(
            "Admin fetching audit log",
            tool_id=tool_id,
            page=page,
            limit=limit,
            action_type=action_type,
            admin=admin_user
        )

        # Get audit log
        result = await tool_service.get_audit_log(
            tool_id=tool_id,
            page=page,
            limit=limit,
            action_type=action_type
        )

        logger.info(
            "Audit log retrieved",
            tool_id=tool_id,
            count=len(result["audit_records"]),
            total=result["total"],
            admin=admin_user
        )

        return result

    except ValueError as e:
        error_msg = str(e)
        admin_user = verify_admin(x_admin_token)  # Get admin for logging

        # Determine status code
        if "not found" in error_msg.lower():
            status_code = 404
        else:
            status_code = 400

        logger.warning(
            "Audit log validation error",
            error=error_msg,
            status_code=status_code,
            tool_id=tool_id,
            admin=admin_user
        )
        raise HTTPException(status_code=status_code, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get audit log",
            tool_id=tool_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit log"
        )


# ====================================================================
# REANALYSIS ENDPOINTS
# ====================================================================

@router.post(
    "/reanalysis/jobs",
    status_code=202,
    response_model=dict,
    summary="Trigger manual reanalysis job",
    description="""
    Trigger a manual reanalysis job to re-detect tools in historical sentiment data.
    
    **User Story**: US1 - Manual Ad-Hoc Tool Recategorization
    
    **Process**:
    1. Validates no active jobs are running
    2. Counts documents matching filter criteria
    3. Creates job with QUEUED status
    4. Returns job details for polling
    
    **Background Processing**:
    The job is processed asynchronously by the scheduler. Poll using
    GET /admin/reanalysis/jobs/{job_id}/status to check progress.
    """,
)
async def trigger_reanalysis(
    job_request: ReanalysisJobRequest,
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """Trigger a manual sentiment reanalysis job."""
    admin_user = verify_admin(x_admin_token)

    logger.info(
        "Admin triggering reanalysis job",
        admin=admin_user,
        date_range=job_request.date_range,
        tool_ids=job_request.tool_ids,
        batch_size=job_request.batch_size,
    )

    try:
        result = await service.trigger_manual_reanalysis(
            job_request=job_request, triggered_by=admin_user
        )

        logger.info(
            "Reanalysis job queued",
            job_id=result["job_id"],
            estimated_docs=result["estimated_docs"],
            admin=admin_user,
        )

        return {
            "job_id": result["job_id"],
            "status": result["status"],
            "estimated_docs": result["estimated_docs"],
            "message": "Reanalysis job queued successfully",
            "poll_url": f"/admin/reanalysis/jobs/{result['job_id']}/status",
        }

    except ValueError as e:
        logger.warning(
            "Reanalysis job validation error",
            error=str(e),
            admin=admin_user,
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to trigger reanalysis job",
            error=str(e),
            admin=admin_user,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to trigger reanalysis job"
        )


@router.get(
    "/reanalysis/jobs",
    response_model=dict,
    summary="List reanalysis jobs",
    description="""
    List all reanalysis jobs with optional status filter.
    
    **Query Parameters**:
    - `status`: Filter by job status (queued/running/completed/failed)
    - `limit`: Max results (default 50, max 100)
    - `offset`: Pagination offset
    
    Returns jobs ordered by created_at DESC (most recent first).
    """,
)
async def list_reanalysis_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """List all reanalysis jobs with pagination."""
    admin_user = verify_admin(x_admin_token)

    logger.debug(
        "Admin listing reanalysis jobs",
        admin=admin_user,
        status=status,
        limit=limit,
        offset=offset,
    )

    try:
        # Build query
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        params = []

        if status:
            query_parts.append("AND c.status = @status")
            params.append({"name": "@status", "value": status})

        query_parts.append("ORDER BY c.created_at DESC")
        query = " ".join(query_parts)

        # Get paginated results
        paginated_query = f"{query} OFFSET {offset} LIMIT {limit}"

        jobs = list(
            service.jobs.query_items(
                query=paginated_query,
                parameters=params if params else None,
                enable_cross_partition_query=True,
            )
        )

        # Get total count
        count_query = f"SELECT VALUE COUNT(1) FROM c WHERE 1=1"
        if status:
            count_query += " AND c.status = @status"

        total_result = list(
            service.jobs.query_items(
                query=count_query,
                parameters=params if params else None,
                enable_cross_partition_query=True,
            )
        )
        # Extract count: emulator returns [{'count': N}] instead of [N]
        if total_result and len(total_result) > 0:
            first = total_result[0]
            total_count = int(first['count']) if isinstance(first, dict) else int(first)
        else:
            total_count = 0

        return {"jobs": jobs, "total_count": total_count, "limit": limit, "offset": offset}

    except Exception as e:
        logger.error(
            "Failed to list reanalysis jobs",
            error=str(e),
            admin=admin_user,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to list reanalysis jobs"
        )


@router.get(
    "/reanalysis/jobs/{job_id}",
    response_model=dict,
    summary="Get reanalysis job details",
    description="""
    Get full details for a specific reanalysis job.
    
    **Returns**:
    - Job status, progress, statistics
    - Error log entries
    - Tools detected breakdown
    - Timestamps (created_at, start_time, end_time)
    """,
)
async def get_reanalysis_job(
    job_id: str,
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """Get full details for a reanalysis job."""
    admin_user = verify_admin(x_admin_token)

    logger.debug(
        "Admin fetching reanalysis job details", job_id=job_id, admin=admin_user
    )

    try:
        job = service.jobs.read_item(item=job_id, partition_key=job_id)

        return {"job": job}

    except Exception as e:
        if "Resource Not Found" in str(e) or "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        logger.error(
            "Failed to get reanalysis job",
            job_id=job_id,
            error=str(e),
            admin=admin_user,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve job details"
        )


@router.get(
    "/reanalysis/jobs/{job_id}/status",
    response_model=dict,
    summary="Get reanalysis job status (lightweight)",
    description="""
    Lightweight endpoint for polling job status.
    
    **Returns**:
    - job_id
    - status (queued/running/completed/failed)
    - progress percentage
    
    Use this for UI polling instead of full job details endpoint.
    """,
)
async def get_reanalysis_job_status(
    job_id: str,
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """Get lightweight status for a reanalysis job (for polling)."""
    admin_user = verify_admin(x_admin_token)

    try:
        job = service.jobs.read_item(item=job_id, partition_key=job_id)

        return {
            "job_id": job["id"],
            "status": job["status"],
            "progress": {
                "percentage": job["progress"]["percentage"],
                "processed_count": job["progress"]["processed_count"],
                "total_count": job["progress"]["total_count"],
            },
        }

    except Exception as e:
        if "Resource Not Found" in str(e) or "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        logger.error(
            "Failed to get job status",
            job_id=job_id,
            error=str(e),
            admin=admin_user,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve job status")


@router.get("/reanalysis/debug/all-jobs")
async def debug_all_jobs(
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """DEBUG: Get all jobs without ORDER BY"""
    verify_admin(x_admin_token)
    
    # Query without ORDER BY
    jobs_no_order = list(service.jobs.query_items(
        query="SELECT * FROM c WHERE 1=1",
        enable_cross_partition_query=True
    ))
    
    # Query with ORDER BY
    try:
        jobs_with_order = list(service.jobs.query_items(
            query="SELECT * FROM c WHERE 1=1 ORDER BY c.created_at DESC",
            enable_cross_partition_query=True
        ))
    except Exception as e:
        jobs_with_order = f"ERROR: {str(e)}"
    
    # Count active
    count_result = list(service.jobs.query_items(
        query="SELECT VALUE COUNT(1) FROM c WHERE c.status IN ('queued', 'running')",
        enable_cross_partition_query=True
    ))
    
    return {
        "no_order_by": len(jobs_no_order),
        "with_order_by": len(jobs_with_order) if isinstance(jobs_with_order, list) else jobs_with_order,
        "active_count": count_result,
        "jobs": [{
            "id": j["id"],
            "status": j["status"],
            "created_at": j.get("created_at", "MISSING"),
            "has_created_at": "created_at" in j
        } for j in jobs_no_order]
    }


@router.delete("/reanalysis/jobs/{job_id}")
async def cancel_reanalysis_job(
    job_id: str,
    x_admin_token: Optional[str] = Header(None),
    service: ReanalysisService = Depends(get_reanalysis_service),
):
    """
    Cancel a queued reanalysis job.

    Only jobs in QUEUED status can be cancelled. Running jobs cannot be
    stopped mid-execution.

    **Authentication**: Requires X-Admin-Token header

    Args:
        job_id: The reanalysis job ID to cancel
        x_admin_token: Admin authentication token
        service: ReanalysisService dependency

    Returns:
        Cancelled job details

    Raises:
        401: If admin token is invalid
        404: If job not found
        400: If job cannot be cancelled (not in QUEUED status)
        500: If cancellation fails
    """
    admin_user = verify_admin(x_admin_token)

    try:
        job = await service.cancel_job(job_id, cancelled_by=admin_user)

        logger.info(
            "Reanalysis job cancelled via API",
            job_id=job_id,
            admin_user=admin_user
        )

        return {
            "job_id": job["id"],
            "status": job["status"],
            "cancelled_by": admin_user,
            "message": "Reanalysis job cancelled successfully"
        }
    except ValueError as e:
        logger.warning(
            "Invalid cancellation request",
            job_id=job_id,
            admin_user=admin_user,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to cancel reanalysis job",
            job_id=job_id,
            admin_user=admin_user,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to cancel job")

