"""Tool management service for CRUD operations and alias resolution."""

from azure.cosmos import exceptions
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import structlog

from ..models.tool import (
    Tool,
    ToolAlias,
    ToolCreateRequest,
    ToolUpdateRequest,
    ToolStatus,
)

logger = structlog.get_logger()


class ToolService:
    """Service for managing AI tools and their aliases."""

    def __init__(
        self,
        tools_container,
        aliases_container,
        merge_records_container=None,
        admin_logs_container=None
    ):
        """
        Initialize ToolService.

        Args:
            tools_container: Cosmos DB container for Tools (sync)
            aliases_container: Cosmos DB container for ToolAliases (sync)
            merge_records_container: Cosmos DB container for ToolMergeRecords
            admin_logs_container: Cosmos DB container for AdminActionLogs
        """
        self.tools_container = tools_container
        self.aliases_container = aliases_container
        self.merge_records_container = merge_records_container
        self.admin_logs_container = admin_logs_container

    async def create_tool(self, tool_data: ToolCreateRequest) -> Dict[str, Any]:
        """
        Create a new tool.

        Args:
            tool_data: Tool creation request data

        Returns:
            Created tool document

        Raises:
            ValueError: If tool name already exists
        """
        # Check for duplicate name
        existing = await self.get_tool_by_name(tool_data.name)
        if existing:
            raise ValueError(f"Tool name '{tool_data.name}' already exists")

        now = datetime.now(timezone.utc).isoformat()
        tool_id = str(uuid.uuid4())

        tool = {
            "id": tool_id,
            "partitionKey": "tool",
            "name": tool_data.name,
            "slug": tool_data.name.lower().replace(" ", "-"),
            "vendor": tool_data.vendor,
            "category": tool_data.category,
            "description": tool_data.description or "",
            "status": "active",
            "metadata": tool_data.metadata or {},
            "created_at": now,
            "updated_at": now
        }

        # Sync operation - no await
        self.tools_container.create_item(body=tool)
        logger.info(
            "Tool created",
            tool_id=tool_id,
            name=tool_data.name,
            category=tool_data.category
        )

        return tool

    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tool by ID.

        Args:
            tool_id: Tool UUID

        Returns:
            Tool document or None if not found
        """
        try:
            query = (
                "SELECT * FROM Tools t "
                "WHERE t.id = @id AND t.partitionKey = 'tool' "
                "AND t.status != 'deleted'"
            )
            # Sync iteration - no await
            items = self.tools_container.query_items(
                query=query,
                parameters=[{"name": "@id", "value": tool_id}]
            )

            results = list(items)

            return results[0] if results else None
        except Exception as e:
            logger.error("Failed to get tool", tool_id=tool_id, error=str(e))
            return None

    async def get_tool_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool document or None if not found
        """
        try:
            query = (
                "SELECT * FROM Tools t "
                "WHERE t.name = @name AND t.partitionKey = 'tool' "
                "AND t.status != 'deleted'"
            )
            # Sync iteration - no await
            items = self.tools_container.query_items(
                query=query,
                parameters=[{"name": "@name", "value": name}]
            )

            results = list(items)

            return results[0] if results else None
        except Exception as e:
            logger.error("Failed to get tool by name", name=name, error=str(e))
            return None

    async def list_tools(
        self,
        page: int = 1,
        limit: int = 20,
        search: str = "",
        status: Optional[str] = None,
        categories: Optional[List[str]] = None,
        vendor: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """
        List all tools with pagination, filtering, search, and sorting.

        Args:
            page: Page number (1-indexed)
            limit: Results per page
            search: Search query for tool name
            status: Filter by status (active/archived/all)
            categories: Filter by categories (array support)
            vendor: Filter by vendor
            sort_by: Sort field (name/vendor/updated_at)
            sort_order: Sort order (asc/desc)

        Returns:
            List of tool documents
        """
        offset = (page - 1) * limit

        # Build query
        query = "SELECT * FROM Tools t WHERE t.partitionKey = 'TOOL'"

        # Status filter (default to active only)
        if status and status != "all":
            query += f" AND t.status = '{status}'"
        elif not status:
            # Default: show only active tools
            query += " AND t.status = 'active'"

        # Search by name (case-insensitive)
        if search:
            query += f" AND CONTAINS(LOWER(t.name), LOWER('{search}'))"

        # Category filter (supports multi-category)
        if categories:
            category_conditions = []
            for cat in categories:
                category_conditions.append(
                    f"ARRAY_CONTAINS(t.categories, '{cat}')"
                )
            query += f" AND ({' OR '.join(category_conditions)})"

        # Vendor filter
        if vendor:
            query += f" AND t.vendor = '{vendor}'"

        # Sorting
        sort_direction = "ASC" if sort_order == "asc" else "DESC"
        query += f" ORDER BY t.{sort_by} {sort_direction}"

        # Pagination
        query += f" OFFSET {offset} LIMIT {limit}"

        try:
            # Sync iteration - no await
            items = self.tools_container.query_items(query=query)
            results = list(items)

            logger.info(
                "Tools listed",
                count=len(results),
                page=page,
                search=search,
                status=status,
                categories=categories,
                vendor=vendor
            )
            return results
        except Exception as e:
            logger.error("Failed to list tools", error=str(e))
            return []

    async def count_tools(
        self,
        search: str = "",
        status: Optional[str] = None,
        categories: Optional[List[str]] = None,
        vendor: Optional[str] = None
    ) -> int:
        """
        Count total tools matching filters.

        Args:
            search: Search query
            status: Status filter (active/archived/all)
            categories: Category filter (array)
            vendor: Vendor filter

        Returns:
            Total count
        """
        query = (
            "SELECT VALUE COUNT(1) FROM Tools t "
            "WHERE t.partitionKey = 'TOOL'"
        )

        # Status filter (default to active only)
        if status and status != "all":
            query += f" AND t.status = '{status}'"
        elif not status:
            query += " AND t.status = 'active'"

        if search:
            query += f" AND CONTAINS(LOWER(t.name), LOWER('{search}'))"

        # Category filter (supports multi-category)
        if categories:
            category_conditions = []
            for cat in categories:
                category_conditions.append(
                    f"ARRAY_CONTAINS(t.categories, '{cat}')"
                )
            query += f" AND ({' OR '.join(category_conditions)})"

        if vendor:
            query += f" AND t.vendor = '{vendor}'"

        try:
            # Sync iteration - no await
            items = self.tools_container.query_items(query=query)
            results = list(items)
            return results[0] if results else 0
        except Exception as e:
            logger.error("Failed to count tools", error=str(e))
            return 0

    async def _log_admin_action(
        self,
        admin_id: str,
        action_type: str,
        tool_id: str,
        tool_name: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log administrative action to AdminActionLogs container.

        Args:
            admin_id: Administrator ID
            action_type: create|edit|archive|unarchive|delete|merge
            tool_id: Tool UUID affected
            tool_name: Tool name (denormalized)
            before_state: Tool state before action
            after_state: Tool state after action
            metadata: Additional context
            ip_address: Admin IP address
            user_agent: Browser/client info
        """
        if not self.admin_logs_container:
            logger.warning("Admin logs container not available - skipping log")
            return

        now = datetime.now(timezone.utc)
        partition_key = now.strftime("%Y%m")  # YYYYMM format

        log_entry = {
            "id": str(uuid.uuid4()),
            "partitionKey": partition_key,
            "timestamp": now.isoformat(),
            "admin_id": admin_id,
            "action_type": action_type,
            "tool_id": tool_id,
            "tool_name": tool_name,
            "before_state": before_state,
            "after_state": after_state,
            "metadata": metadata or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }

        try:
            self.admin_logs_container.create_item(body=log_entry)
            logger.info(
                "Admin action logged",
                action_type=action_type,
                tool_id=tool_id,
                admin_id=admin_id
            )
        except Exception as e:
            logger.error(
                "Failed to log admin action",
                error=str(e),
                action_type=action_type,
                tool_id=tool_id
            )

    async def update_tool(
        self,
        tool_id: str,
        updates: ToolUpdateRequest,
        updated_by: str,
        etag: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update tool details with optimistic concurrency control.

        Args:
            tool_id: Tool UUID
            updates: Fields to update
            updated_by: Admin ID performing update
            etag: ETag for optimistic concurrency (If-Match header)
            ip_address: Admin IP address
            user_agent: Browser/client info

        Returns:
            Updated tool document or None if not found

        Raises:
            ValueError: If validation fails (duplicate name, invalid
                categories)
            exceptions.CosmosHttpResponseError: If ETag mismatch
                (409 Conflict)
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            return None

        # Store before state for audit log
        before_state = tool.copy()

        # Validate name uniqueness if name is being changed
        if updates.name and updates.name != tool["name"]:
            existing = await self.get_tool_by_name(updates.name)
            if existing and existing["id"] != tool_id:
                # Check if existing tool is active
                if existing.get("status") == "active":
                    raise ValueError(
                        f"Tool name '{updates.name}' already exists"
                    )

        # Apply updates
        update_dict = updates.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                tool[key] = value

        # Auto-regenerate slug if name changed
        if "name" in update_dict:
            tool["slug"] = update_dict["name"].lower().replace(" ", "-")

        # Update audit fields
        tool["updated_at"] = datetime.now(timezone.utc).isoformat()
        tool["updated_by"] = updated_by

        try:
            # Use ETag for optimistic concurrency if provided
            if etag:
                # Cosmos SDK will raise 412 if ETag doesn't match
                self.tools_container.replace_item(
                    item=tool_id,
                    body=tool,
                    etag=etag,
                    match_condition=exceptions.MatchConditions.IfNotModified
                )
            else:
                # No concurrency control
                self.tools_container.replace_item(item=tool_id, body=tool)

            logger.info(
                "Tool updated",
                tool_id=tool_id,
                updates=update_dict,
                updated_by=updated_by
            )

            # Log admin action
            await self._log_admin_action(
                admin_id=updated_by,
                action_type="edit",
                tool_id=tool_id,
                tool_name=tool["name"],
                before_state=before_state,
                after_state=tool,
                metadata={"fields_updated": list(update_dict.keys())},
                ip_address=ip_address,
                user_agent=user_agent
            )

            return tool
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 412:
                # ETag mismatch - concurrent modification detected
                logger.warning(
                    "Concurrent modification detected",
                    tool_id=tool_id,
                    updated_by=updated_by
                )
                raise  # Re-raise to be handled by API layer
            else:
                logger.error(
                    "Failed to update tool",
                    tool_id=tool_id,
                    error=str(e)
                )
                raise

    async def delete_tool(
        self,
        tool_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete tool (soft delete by default).

        Args:
            tool_id: Tool UUID
            hard_delete: If True, permanently delete; else set status='deleted'

        Returns:
            True if deleted, False if not found
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            return False

        if hard_delete:
            # Sync operation - no await
            self.tools_container.delete_item(
                item=tool_id,
                partition_key="tool"
            )
            logger.info("Tool hard deleted", tool_id=tool_id)
        else:
            tool["status"] = "deleted"
            tool["updated_at"] = datetime.now(timezone.utc).isoformat()
            # Sync operation - no await
            self.tools_container.replace_item(item=tool_id, body=tool)
            logger.info("Tool soft deleted", tool_id=tool_id)

        return True

    async def create_alias(
        self,
        alias_tool_id: str,
        primary_tool_id: str,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Create alias relationship.

        Args:
            alias_tool_id: Tool ID to set as alias
            primary_tool_id: Primary tool ID
            created_by: Admin user ID

        Returns:
            Created alias document

        Raises:
            ValueError: If validation fails
        """
        # Validate both tools exist
        alias_tool = await self.get_tool(alias_tool_id)
        primary_tool = await self.get_tool(primary_tool_id)

        if not alias_tool or not primary_tool:
            raise ValueError("Tool not found")

        # Prevent self-referencing
        if alias_tool_id == primary_tool_id:
            raise ValueError("Tool cannot be alias of itself")

        # Check for circular aliases
        if await self.has_circular_alias(alias_tool_id, primary_tool_id):
            raise ValueError("Circular alias detected")

        # Create alias
        alias_id = str(uuid.uuid4())
        alias = {
            "id": alias_id,
            "partitionKey": "alias",
            "alias_tool_id": alias_tool_id,
            "primary_tool_id": primary_tool_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by
        }

        # Sync operation - no await
        self.aliases_container.create_item(body=alias)
        logger.info(
            "Alias created",
            alias_id=alias_id,
            alias_tool=alias_tool["name"],
            primary_tool=primary_tool["name"]
        )

        return alias

    async def get_aliases(
        self,
        primary_tool_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all aliases for a primary tool.

        Args:
            primary_tool_id: Primary tool ID

        Returns:
            List of alias documents
        """
        query = (
            "SELECT * FROM ToolAliases ta "
            "WHERE ta.primary_tool_id = @id AND ta.partitionKey = 'alias'"
        )
        # Sync iteration - no await
        items = self.aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": primary_tool_id}]
        )

        results = list(items)

        return results

    async def remove_alias(self, alias_id: str) -> bool:
        """
        Remove alias relationship.

        Args:
            alias_id: Alias document ID

        Returns:
            True if removed, False if not found
        """
        try:
            # Sync operation - no await
            self.aliases_container.delete_item(
                item=alias_id,
                partition_key="alias"
            )
            logger.info("Alias removed", alias_id=alias_id)
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False

    async def resolve_tool_id(self, tool_id: str) -> str:
        """
        Resolve tool ID to primary tool ID (follows aliases).

        Args:
            tool_id: Tool ID (may be alias or primary)

        Returns:
            Primary tool ID
        """
        query = (
            "SELECT * FROM ToolAliases ta "
            "WHERE ta.alias_tool_id = @id AND ta.partitionKey = 'alias'"
        )
        # Sync iteration - no await
        items = self.aliases_container.query_items(
            query=query,
            parameters=[{"name": "@id", "value": tool_id}]
        )

        results = list(items)

        return results[0]["primary_tool_id"] if results else tool_id

    async def has_circular_alias(
        self,
        alias_tool_id: str,
        primary_tool_id: str
    ) -> bool:
        """
        Check if creating alias would create circular reference.

        Args:
            alias_tool_id: Proposed alias tool ID
            primary_tool_id: Proposed primary tool ID

        Returns:
            True if circular reference detected
        """
        visited = set()
        current_id = primary_tool_id

        # Traverse alias chain
        while current_id:
            if current_id in visited:
                return True  # Circular reference

            visited.add(current_id)

            # Check if current_id is an alias of something
            query = (
                "SELECT * FROM ToolAliases ta "
                "WHERE ta.alias_tool_id = @id AND ta.partitionKey = 'alias'"
            )
            # Sync iteration - no await
            items = self.aliases_container.query_items(
                query=query,
                parameters=[{"name": "@id", "value": current_id}]
            )

            results = list(items)

            if results:
                current_id = results[0]["primary_tool_id"]
            else:
                break

        return alias_tool_id in visited
