"""Tool management service for CRUD operations and alias resolution."""

from azure.cosmos import exceptions
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
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
        admin_logs_container=None,
        sentiment_container=None
    ):
        """
        Initialize ToolService.

        Args:
            tools_container: Cosmos DB container for Tools (sync)
            aliases_container: Cosmos DB container for ToolAliases (sync)
            merge_records_container: Cosmos DB container for ToolMergeRecords
            admin_logs_container: Cosmos DB container for AdminActionLogs
            sentiment_container: Cosmos DB container for sentiment data (for deletion)
        """
        self.tools_container = tools_container
        self.aliases_container = aliases_container
        self.merge_records_container = merge_records_container
        self.admin_logs_container = admin_logs_container
        self.sentiment_container = sentiment_container

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

        # Sanitize description for CosmosDB compatibility
        description = tool_data.description or ""
        # Replace literal \n with actual newlines
        description = description.replace("\\n", "\n")
        # Replace em-dash and other special chars that cause issues
        description = description.replace("—", "-").replace("'", "'").replace(""", '"').replace(""", '"')
        description = description.strip()

        tool = {
            "id": tool_id,
            "partitionKey": "tool",
            "name": tool_data.name,
            "slug": tool_data.name.lower().replace(" ", "-"),
            "vendor": tool_data.vendor,
            "categories": tool_data.categories,
            "description": description,
            "status": "active",
            "metadata": tool_data.metadata or {},
            "created_at": now,
            "updated_at": now,
            "created_by": "admin",  # TODO: Get from auth context
            "updated_by": "admin"
        }

        # Sync operation - no await
        self.tools_container.create_item(body=tool)
        logger.info(
            "Tool created",
            tool_id=tool_id,
            name=tool_data.name,
            categories=tool_data.categories
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
        query = "SELECT * FROM Tools t WHERE t.partitionKey = 'tool'"

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
            "WHERE t.partitionKey = 'tool'"
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
            if not results:
                return 0
            # Handle both plain int and dict response
            count_value = results[0]
            if isinstance(count_value, dict):
                # Extract count from dict (CosmosDB may return {'$1': count})
                return count_value.get('$1', count_value.get('count', 0))
            return count_value
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

    async def get_sentiment_count(self, tool_id: str) -> int:
        """
        Get count of sentiment records for a tool.

        Args:
            tool_id: Tool UUID

        Returns:
            Count of sentiment records for this tool
        """
        # Query sentiment container for this tool
        # Note: This assumes sentiment records have a tool_id field
        # Adjust query based on actual sentiment data structure
        try:
            query = (
                "SELECT VALUE COUNT(1) FROM c "
                "WHERE c.tool_id = @tool_id"
            )

            # We need access to sentiment container
            # For now, return 0 if container not available
            # This will be updated when sentiment container is passed in
            if not hasattr(self, 'sentiment_container') or self.sentiment_container is None:
                logger.warning(
                    "Sentiment container not available for count",
                    tool_id=tool_id
                )
                return 0

            items = self.sentiment_container.query_items(
                query=query,
                parameters=[{"name": "@tool_id", "value": tool_id}],
                enable_cross_partition_query=True
            )

            results = list(items)
            if not results:
                return 0

            count_value = results[0]
            if isinstance(count_value, dict):
                return count_value.get('$1', count_value.get('count', 0))
            return count_value

        except Exception as e:
            logger.error(
                "Failed to get sentiment count",
                tool_id=tool_id,
                error=str(e)
            )
            return 0

    async def delete_tool(
        self,
        tool_id: str,
        deleted_by: str,
        hard_delete: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete tool permanently with validation and cascade.

        Args:
            tool_id: Tool UUID
            deleted_by: Admin ID performing deletion
            hard_delete: If True, permanently delete (default for Phase 6);
                        else set status='deleted'
            ip_address: Admin IP address
            user_agent: Browser/client info

        Returns:
            Dictionary with deletion result and sentiment_count

        Raises:
            ValueError: If tool cannot be deleted (referenced or in use)
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool '{tool_id}' not found")

        # T063: Validate tool is not referenced in merged_into
        query = (
            "SELECT * FROM Tools t "
            "WHERE t.merged_into = @tool_id "
            "AND t.partitionKey = 'tool'"
        )
        items = self.tools_container.query_items(
            query=query,
            parameters=[{"name": "@tool_id", "value": tool_id}]
        )
        referencing_tools = list(items)

        if referencing_tools:
            tool_names = [t.get('name', 'Unknown') for t in referencing_tools]
            raise ValueError(
                f"Cannot delete tool: referenced by {len(referencing_tools)} "
                f"merged tool(s): {', '.join(tool_names[:3])}"
                + ("..." if len(tool_names) > 3 else "")
            )

        # T064: Validate tool is not in active sentiment analysis job
        # For now, we'll add a placeholder check
        # In a real implementation, this would check a jobs/tasks container
        # or a scheduler state
        # TODO: Implement actual job check when job tracking is available

        # Get sentiment count before deletion
        sentiment_count = await self.get_sentiment_count(tool_id)

        # Store before state for audit log
        before_state = tool.copy()

        # T065: Log admin action before deletion (after state is null)
        await self._log_admin_action(
            admin_id=deleted_by,
            action_type="delete",
            tool_id=tool_id,
            tool_name=tool["name"],
            before_state=before_state,
            after_state=None,  # No after state for deletion
            metadata={
                "sentiment_count": sentiment_count,
                "hard_delete": hard_delete
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        if hard_delete:
            # T062: Cascade delete sentiment data
            # Delete sentiment records associated with this tool
            if hasattr(self, 'sentiment_container') and self.sentiment_container:
                try:
                    # Query all sentiment records for this tool
                    query = "SELECT * FROM c WHERE c.tool_id = @tool_id"
                    sentiment_items = self.sentiment_container.query_items(
                        query=query,
                        parameters=[{"name": "@tool_id", "value": tool_id}],
                        enable_cross_partition_query=True
                    )

                    # Delete each sentiment record
                    deleted_sentiment_count = 0
                    for sentiment in sentiment_items:
                        try:
                            self.sentiment_container.delete_item(
                                item=sentiment['id'],
                                partition_key=sentiment.get('partitionKey', sentiment['id'])
                            )
                            deleted_sentiment_count += 1
                        except Exception as e:
                            logger.warning(
                                "Failed to delete sentiment record",
                                sentiment_id=sentiment.get('id'),
                                error=str(e)
                            )

                    logger.info(
                        "Cascade deleted sentiment records",
                        tool_id=tool_id,
                        count=deleted_sentiment_count
                    )
                except Exception as e:
                    logger.error(
                        "Failed to cascade delete sentiment data",
                        tool_id=tool_id,
                        error=str(e)
                    )

            # Delete the tool itself
            # Note: When partition key path is /id, pass the id value as partition_key
            # CosmosDB requires both the document id and the partition key value
            self.tools_container.delete_item(
                item=tool_id,
                partition_key='tool'  # Use the partitionKey field value, not the id
            )
            logger.info(
                "Tool permanently deleted",
                tool_id=tool_id,
                deleted_by=deleted_by,
                sentiment_count=sentiment_count
            )
        else:
            # Soft delete - set status to deleted
            tool["status"] = "deleted"
            tool["updated_at"] = datetime.now(timezone.utc).isoformat()
            tool["updated_by"] = deleted_by
            self.tools_container.replace_item(item=tool_id, body=tool)
            logger.info(
                "Tool soft deleted",
                tool_id=tool_id,
                deleted_by=deleted_by
            )

        return {
            "tool_id": tool_id,
            "tool_name": tool["name"],
            "sentiment_count": sentiment_count,
            "hard_delete": hard_delete
        }

    async def archive_tool(
        self,
        tool_id: str,
        archived_by: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Archive a tool (set status to 'archived').

        This preserves historical sentiment data while removing the tool
        from the active list.

        Args:
            tool_id: Tool UUID
            archived_by: Admin ID performing archive
            ip_address: Admin IP address
            user_agent: Browser/client info

        Returns:
            Updated tool document or None if not found

        Raises:
            ValueError: If tool cannot be archived (e.g., referenced by other tools)
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            return None

        # Store before state for audit log
        before_state = tool.copy()

        # Check if this tool is referenced in other tools' merged_into field
        # (tools that were merged into this one should not allow archiving)
        query = (
            "SELECT * FROM Tools t "
            "WHERE t.partitionKey = 'tool' "
            "AND t.merged_into = @tool_id "
            "AND t.status != 'deleted'"
        )
        items = self.tools_container.query_items(
            query=query,
            parameters=[{"name": "@tool_id", "value": tool_id}]
        )
        referencing_tools = list(items)

        if referencing_tools:
            tool_names = [t["name"] for t in referencing_tools]
            raise ValueError(
                f"Cannot archive tool: {len(referencing_tools)} tool(s) "
                f"were merged into this tool ({', '.join(tool_names[:3])}). "
                "Please unmerge or archive those tools first."
            )

        # Update status to archived
        tool["status"] = "archived"
        tool["updated_at"] = datetime.now(timezone.utc).isoformat()
        tool["updated_by"] = archived_by

        try:
            # Sync operation - no await
            self.tools_container.replace_item(item=tool_id, body=tool)

            logger.info(
                "Tool archived",
                tool_id=tool_id,
                tool_name=tool["name"],
                archived_by=archived_by
            )

            # Log admin action
            await self._log_admin_action(
                admin_id=archived_by,
                action_type="archive",
                tool_id=tool_id,
                tool_name=tool["name"],
                before_state=before_state,
                after_state=tool,
                metadata={"reason": "archived by admin"},
                ip_address=ip_address,
                user_agent=user_agent
            )

            return tool
        except Exception as e:
            logger.error(
                "Failed to archive tool",
                tool_id=tool_id,
                error=str(e)
            )
            raise

    async def unarchive_tool(
        self,
        tool_id: str,
        unarchived_by: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Unarchive a tool (set status to 'active').

        This restores a previously archived tool to the active list.

        Args:
            tool_id: Tool UUID
            unarchived_by: Admin ID performing unarchive
            ip_address: Admin IP address
            user_agent: Browser/client info

        Returns:
            Updated tool document or None if not found
        """
        # Note: get_tool filters out 'deleted' status, not 'archived'
        # We need to query directly to get archived tools
        try:
            query = (
                "SELECT * FROM Tools t "
                "WHERE t.id = @id AND t.partitionKey = 'tool'"
            )
            items = self.tools_container.query_items(
                query=query,
                parameters=[{"name": "@id", "value": tool_id}]
            )
            results = list(items)

            if not results:
                return None

            tool = results[0]

            # Store before state for audit log
            before_state = tool.copy()

            # Update status to active
            tool["status"] = "active"
            tool["updated_at"] = datetime.now(timezone.utc).isoformat()
            tool["updated_by"] = unarchived_by

            # Sync operation - no await
            self.tools_container.replace_item(item=tool_id, body=tool)

            logger.info(
                "Tool unarchived",
                tool_id=tool_id,
                tool_name=tool["name"],
                unarchived_by=unarchived_by
            )

            # Log admin action
            await self._log_admin_action(
                admin_id=unarchived_by,
                action_type="unarchive",
                tool_id=tool_id,
                tool_name=tool["name"],
                before_state=before_state,
                after_state=tool,
                metadata={"reason": "unarchived by admin"},
                ip_address=ip_address,
                user_agent=user_agent
            )

            return tool
        except Exception as e:
            logger.error(
                "Failed to unarchive tool",
                tool_id=tool_id,
                error=str(e)
            )
            return None

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

    async def _validate_merge(
        self,
        target_tool_id: str,
        source_tool_ids: List[str]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate merge operation and return tools with warnings.

        Args:
            target_tool_id: Primary tool that will receive merged data
            source_tool_ids: Tools to merge into target

        Returns:
            Tuple of (target_tool, source_tools, warnings)

        Raises:
            ValueError: If validation fails
        """
        # Validate target tool exists and is active
        target_tool = await self.get_tool(target_tool_id)
        if not target_tool:
            raise ValueError(f"Target tool '{target_tool_id}' not found")

        if target_tool.get("status") != "active":
            raise ValueError(f"Target tool must be active, current status: {target_tool.get('status')}")

        if target_tool.get("merged_into"):
            raise ValueError(f"Target tool has already been merged into another tool")

        # Validate source tools
        source_tools = []
        for source_id in source_tool_ids:
            # Prevent circular merge
            if source_id == target_tool_id:
                raise ValueError("Cannot merge tool into itself")

            source_tool = await self.get_tool(source_id)
            if not source_tool:
                raise ValueError(f"Source tool '{source_id}' not found")

            if source_tool.get("status") != "active":
                raise ValueError(f"Source tool '{source_tool['name']}' must be active")

            if source_tool.get("merged_into"):
                raise ValueError(f"Source tool '{source_tool['name']}' has already been merged")

            source_tools.append(source_tool)

        # Generate warnings for metadata differences
        warnings = []

        # Check vendor mismatches
        source_vendors = list(set([t.get("vendor", "") for t in source_tools]))
        target_vendor = target_tool.get("vendor", "")
        if any(v != target_vendor for v in source_vendors if v):
            warnings.append({
                "type": "vendor_mismatch",
                "message": "Source tools have different vendors than target",
                "details": {
                    "target_vendor": target_vendor,
                    "source_vendors": source_vendors
                }
            })

        return target_tool, source_tools, warnings

    async def _migrate_sentiment_data(
        self,
        target_tool_id: str,
        source_tool_ids: List[str]
    ) -> int:
        """
        Migrate sentiment data from source tools to target tool.

        Args:
            target_tool_id: Tool to receive sentiment data
            source_tool_ids: Tools whose sentiment data will be migrated

        Returns:
            Total count of migrated sentiment records
        """
        if not hasattr(self, 'sentiment_container') or not self.sentiment_container:
            logger.warning("No sentiment container available for migration")
            return 0

        total_migrated = 0

        for source_id in source_tool_ids:
            try:
                # Query all sentiment records for this source tool
                query = "SELECT * FROM c WHERE c.tool_id = @tool_id"
                sentiment_items = self.sentiment_container.query_items(
                    query=query,
                    parameters=[{"name": "@tool_id", "value": source_id}],
                    enable_cross_partition_query=True
                )

                # Update each sentiment record
                for sentiment in sentiment_items:
                    try:
                        # Add source attribution
                        sentiment['original_tool_id'] = source_id
                        sentiment['tool_id'] = target_tool_id
                        sentiment['migrated_at'] = datetime.now(timezone.utc).isoformat()

                        # Update the sentiment record
                        self.sentiment_container.upsert_item(body=sentiment)
                        total_migrated += 1
                    except Exception as e:
                        logger.error(
                            "Failed to migrate sentiment record",
                            sentiment_id=sentiment.get('id'),
                            source_tool_id=source_id,
                            error=str(e)
                        )

                logger.info(
                    "Migrated sentiment data",
                    source_tool_id=source_id,
                    target_tool_id=target_tool_id,
                    count=total_migrated
                )
            except Exception as e:
                logger.error(
                    "Failed to query sentiment data for migration",
                    source_tool_id=source_id,
                    error=str(e)
                )

        return total_migrated

    async def merge_tools(
        self,
        target_tool_id: str,
        source_tool_ids: List[str],
        target_categories: List[str],
        target_vendor: str,
        merged_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Merge multiple tools into a single tool.

        This is an atomic operation that:
        1. Validates all tools exist and are active
        2. Migrates sentiment data with source attribution
        3. Updates target tool with new categories/vendor
        4. Archives source tools with merged_into reference
        5. Creates merge record and audit log

        Args:
            target_tool_id: Primary tool receiving merged data
            source_tool_ids: Tools to merge (1-10 tools)
            target_categories: Final categories for merged tool
            target_vendor: Final vendor for merged tool
            merged_by: Admin user ID performing merge
            notes: Optional notes explaining merge reason

        Returns:
            Dict containing merge_record, target_tool, archived_tools, warnings

        Raises:
            ValueError: If validation fails
        """
        # Step 1: Validation
        target_tool, source_tools, warnings = await self._validate_merge(
            target_tool_id,
            source_tool_ids
        )

        # Store before state for audit
        target_categories_before = target_tool.get("categories", [])
        target_vendor_before = target_tool.get("vendor", "")

        # Step 2: Migrate sentiment data
        sentiment_count = await self._migrate_sentiment_data(
            target_tool_id,
            source_tool_ids
        )

        # Step 3: Update target tool
        target_tool["categories"] = target_categories
        target_tool["vendor"] = target_vendor
        target_tool["updated_at"] = datetime.now(timezone.utc).isoformat()
        target_tool["updated_by"] = merged_by

        self.tools_container.replace_item(item=target_tool_id, body=target_tool)

        # Step 4: Archive source tools
        archived_tools = []
        for source_tool in source_tools:
            source_tool["status"] = "archived"
            source_tool["merged_into"] = target_tool_id
            source_tool["updated_at"] = datetime.now(timezone.utc).isoformat()
            source_tool["updated_by"] = merged_by

            self.tools_container.replace_item(
                item=source_tool["id"],
                body=source_tool
            )
            archived_tools.append(source_tool)

        # Step 5: Create merge record
        merge_record_id = str(uuid.uuid4())
        merge_record = {
            "id": merge_record_id,
            "partitionKey": "merge",
            "target_tool_id": target_tool_id,
            "source_tool_ids": source_tool_ids,
            "merged_at": datetime.now(timezone.utc).isoformat(),
            "merged_by": merged_by,
            "sentiment_count": sentiment_count,
            "target_categories_before": target_categories_before,
            "target_categories_after": target_categories,
            "target_vendor_before": target_vendor_before,
            "target_vendor_after": target_vendor,
            "source_tools_metadata": [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "vendor": t.get("vendor", ""),
                    "categories": t.get("categories", []),
                    "sentiment_count": 0  # Could be calculated if needed
                }
                for t in source_tools
            ],
            "notes": notes or ""
        }

        if hasattr(self, 'merge_records_container') and self.merge_records_container:
            self.merge_records_container.create_item(body=merge_record)

        # Step 6: Create audit log
        await self._log_admin_action(
            admin_id=merged_by,
            action_type="merge",
            tool_id=target_tool_id,
            tool_name=target_tool.get("name", ""),
            before_state={
                "target_categories": target_categories_before,
                "target_vendor": target_vendor_before,
                "source_tool_ids": source_tool_ids
            },
            after_state={
                "target_categories": target_categories,
                "target_vendor": target_vendor,
                "sentiment_migrated": sentiment_count,
                "source_tools_archived": len(source_tools)
            },
            metadata={"notes": notes, "merge_record_id": merge_record_id}
        )

        logger.info(
            "Tools merged successfully",
            target_tool_id=target_tool_id,
            source_count=len(source_tools),
            sentiment_count=sentiment_count,
            merged_by=merged_by
        )

        return {
            "merge_record": merge_record,
            "target_tool": target_tool,
            "archived_tools": archived_tools,
            "warnings": warnings
        }

    async def get_merge_history(
        self,
        tool_id: str,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get merge history for a tool (where tool was the target).

        Args:
            tool_id: Tool identifier
            page: Page number (1-indexed)
            limit: Records per page (1-100)

        Returns:
            Dict with merge_records, total, page, limit, has_more

        Raises:
            ValueError: If tool not found or pagination invalid
        """
        # Validate tool exists
        try:
            self.tools_container.read_item(
                item=tool_id,
                partition_key=tool_id
            )
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Tool '{tool_id}' not found")

        # Validate pagination
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        # Check if merge records container exists
        if not hasattr(self, 'merge_records_container'):
            return {
                "merge_records": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "has_more": False
            }

        # Query merge records for this tool (as target)
        query = """
            SELECT * FROM c
            WHERE c.target_tool_id = @tool_id
            ORDER BY c.merged_at DESC
        """

        # Get total count
        count_query = """
            SELECT VALUE COUNT(1) FROM c
            WHERE c.target_tool_id = @tool_id
        """

        try:
            count_result = list(
                self.merge_records_container.query_items(
                    query=count_query,
                    parameters=[{"name": "@tool_id", "value": tool_id}],
                    enable_cross_partition_query=True
                )
            )
            total = count_result[0] if count_result else 0
        except Exception as e:
            logger.warning(
                "Failed to count merge records",
                tool_id=tool_id,
                error=str(e)
            )
            total = 0

        # Get paginated results
        offset = (page - 1) * limit

        try:
            merge_records = list(
                self.merge_records_container.query_items(
                    query=f"{query} OFFSET {offset} LIMIT {limit}",
                    parameters=[{"name": "@tool_id", "value": tool_id}],
                    enable_cross_partition_query=True
                )
            )
        except Exception as e:
            logger.error(
                "Failed to query merge records",
                tool_id=tool_id,
                error=str(e),
                exc_info=True
            )
            merge_records = []

        has_more = (offset + len(merge_records)) < total

        return {
            "merge_records": merge_records,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": has_more
        }

    async def get_audit_log(
        self,
        tool_id: str,
        page: int = 1,
        limit: int = 20,
        action_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit log for a specific tool.

        Returns all administrative actions performed on the tool,
        sorted by timestamp descending (newest first).

        Args:
            tool_id: Tool identifier
            page: Page number (1-indexed)
            limit: Records per page (1-100)
            action_type: Optional filter by action type

        Returns:
            Dict with audit_records, total, page, limit, has_more

        Raises:
            ValueError: If tool not found or pagination invalid
        """
        # Validate tool exists
        try:
            self.tools_container.read_item(
                item=tool_id,
                partition_key=tool_id
            )
        except exceptions.CosmosResourceNotFoundError:
            raise ValueError(f"Tool '{tool_id}' not found")

        # Validate pagination
        if page < 1:
            raise ValueError("Page must be >= 1")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        # Build query
        query_conditions = ["c.tool_id = @tool_id"]
        parameters = [{"name": "@tool_id", "value": tool_id}]

        if action_type:
            query_conditions.append("c.action_type = @action_type")
            parameters.append({"name": "@action_type", "value": action_type})

        where_clause = " AND ".join(query_conditions)

        query = f"""
            SELECT * FROM c
            WHERE {where_clause}
            ORDER BY c.timestamp DESC
        """

        # Get total count
        count_query = f"""
            SELECT VALUE COUNT(1) FROM c
            WHERE {where_clause}
        """

        try:
            count_result = list(
                self.admin_logs_container.query_items(
                    query=count_query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                )
            )
            total = count_result[0] if count_result else 0
        except Exception as e:
            logger.warning(
                "Failed to count audit records",
                tool_id=tool_id,
                error=str(e)
            )
            total = 0

        # Get paginated results
        offset = (page - 1) * limit

        try:
            audit_records = list(
                self.admin_logs_container.query_items(
                    query=f"{query} OFFSET {offset} LIMIT {limit}",
                    parameters=parameters,
                    enable_cross_partition_query=True
                )
            )
        except Exception as e:
            logger.error(
                "Failed to query audit records",
                tool_id=tool_id,
                error=str(e),
                exc_info=True
            )
            audit_records = []

        has_more = (offset + len(audit_records)) < total

        return {
            "audit_records": audit_records,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": has_more
        }
