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
        # Use SELECT * and count in Python instead of SQL COUNT
        # to avoid CosmosDB emulator COUNT query issues
        query = "SELECT * FROM c WHERE c.status IN ('queued', 'running')"
        
        try:
            result = list(self.jobs.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            count = len(result)
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
            # Extract count: emulator returns [{'count': N}] instead of [N]
            if result and len(result) > 0:
                first = result[0]
                total_count = int(first['count']) if isinstance(first, dict) else int(first)
            else:
                total_count = 0
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
                "last_checkpoint_id": None,
                "estimated_time_remaining": None
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

    async def trigger_automatic_reanalysis(
        self,
        tool_ids: Optional[List[str]] = None,
        triggered_by: str = "system",
        reason: str = "Tool status change"
    ) -> Dict[str, Any]:
        """
        Trigger an automatic reanalysis job.

        Used when tools are created, activated, or modified to automatically
        recategorize historical data.

        Args:
            tool_ids: Specific tools to reanalyze. None for all tools.
            triggered_by: User or system that triggered the reanalysis
            reason: Reason for automatic trigger (e.g., "New tool created")

        Returns:
            Created job document with job_id, status, estimated_docs

        Raises:
            ValueError: If active job exists or parameters are invalid
        """
        # Check for concurrent jobs (optional - may allow automatic jobs)
        # For now, we'll queue them even if another job is running
        # The scheduler will process them FIFO
        
        # Build query to count documents that need reanalysis
        query_parts = ["SELECT VALUE COUNT(1) FROM c WHERE 1=1"]
        params = []

        # Optional tool filter - typically used for automatic reanalysis
        # to only reprocess docs that might mention the new/changed tool
        if tool_ids:
            # For automatic reanalysis, we still process all docs
            # because we need to detect the new tool in historical content
            # The tool_ids are stored in parameters for context only
            pass

        count_query = " ".join(query_parts)
        
        try:
            result = list(self.sentiment.query_items(
                query=count_query,
                parameters=params if params else None,
                enable_cross_partition_query=True
            ))
            # Extract count: emulator returns [{'count': N}] instead of [N]
            if result and len(result) > 0:
                first = result[0]
                total_count = int(first['count']) if isinstance(first, dict) else int(first)
            else:
                total_count = 0
        except Exception as e:
            logger.error(
                "Failed to count documents for automatic reanalysis",
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
            "trigger_type": "automatic",
            "triggered_by": triggered_by,
            "parameters": {
                "date_range": None,
                "tool_ids": tool_ids,
                "batch_size": 100  # Default batch size for automatic jobs
            },
            "progress": {
                "total_count": total_count,
                "processed_count": 0,
                "percentage": 0.0,
                "last_checkpoint_id": None,
                "estimated_time_remaining": None
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
            "created_at": now,
            "reason": reason  # Extra field for automatic jobs
        }

        # Save to database
        try:
            self.jobs.create_item(body=job_doc)
            logger.info(
                "Automatic reanalysis job created",
                job_id=job_id,
                triggered_by=triggered_by,
                reason=reason,
                tool_ids=tool_ids,
                total_count=total_count,
                trigger_type="automatic"
            )
            
            # Log notification-level event for admin visibility (T029)
            logger.warning(
                "NOTIFICATION: Automatic reanalysis queued",
                job_id=job_id,
                triggered_by=triggered_by,
                reason=reason,
                estimated_docs=total_count,
                poll_url=f"/admin/reanalysis/jobs/{job_id}/status"
            )
        except Exception as e:
            logger.error(
                "Failed to create automatic reanalysis job",
                error=str(e),
                exc_info=True
            )
            raise ValueError(f"Failed to create job: {str(e)}")

        return {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "estimated_docs": total_count,
            "created_at": now,
            "reason": reason
        }

    async def update_tool_ids_after_merge(
        self,
        source_tool_ids: List[str],
        target_tool_id: str,
        merged_by: str
    ) -> Dict[str, int]:
        """
        Update detected_tool_ids in sentiment_scores after tool merge.

        Replaces all occurrences of source tool IDs with target tool ID.
        This ensures sentiment data reflects the merged tool structure.

        Args:
            source_tool_ids: Tool IDs being merged (to be replaced)
            target_tool_id: Primary tool ID (replacement)
            merged_by: Admin who performed the merge

        Returns:
            Dict with update statistics:
            - documents_scanned: Total docs checked
            - documents_updated: Docs with changes
            - replacements_made: Total ID replacements

        Example:
            Before: detected_tool_ids = ["copilot-old", "cursor"]
            After:  detected_tool_ids = ["copilot", "cursor"]
        """
        logger.info(
            "Starting tool ID replacement after merge",
            source_tool_ids=source_tool_ids,
            target_tool_id=target_tool_id,
            merged_by=merged_by
        )

        documents_scanned = 0
        documents_updated = 0
        replacements_made = 0

        try:
            # Query for documents that contain any of the source tool IDs
            # Using ARRAY_CONTAINS with OR logic
            conditions = []
            params = []
            
            for idx, source_id in enumerate(source_tool_ids):
                conditions.append(f"ARRAY_CONTAINS(c.detected_tool_ids, @source{idx})")
                params.append({"name": f"@source{idx}", "value": source_id})
            
            where_clause = " OR ".join(conditions)
            query = f"SELECT * FROM c WHERE {where_clause}"

            # Process in batches to avoid memory issues
            batch_size = 100
            offset = 0

            while True:
                batch_query = f"{query} OFFSET {offset} LIMIT {batch_size}"
                
                try:
                    items = list(self.sentiment.query_items(
                        query=batch_query,
                        parameters=params,
                        enable_cross_partition_query=True
                    ))
                except Exception as e:
                    logger.error(
                        "Batch query failed during tool ID replacement",
                        offset=offset,
                        error=str(e),
                        exc_info=True
                    )
                    offset += batch_size
                    continue

                if not items:
                    break

                for item in items:
                    documents_scanned += 1
                    doc_id = item["id"]
                    original_ids = item.get("detected_tool_ids", [])
                    
                    if not original_ids:
                        continue

                    # Replace source IDs with target ID
                    updated_ids = []
                    changed = False
                    
                    for tool_id in original_ids:
                        if tool_id in source_tool_ids:
                            # Only add target_id if not already present
                            if target_tool_id not in updated_ids:
                                updated_ids.append(target_tool_id)
                                replacements_made += 1
                            changed = True
                        else:
                            updated_ids.append(tool_id)
                    
                    # Update document if changes were made
                    if changed:
                        try:
                            item["detected_tool_ids"] = updated_ids
                            item["last_analyzed_at"] = (
                                datetime.now(timezone.utc).isoformat()
                            )
                            # Note: Don't increment analysis_version for merges
                            # This is a data migration, not re-analysis
                            
                            self.sentiment.upsert_item(body=item)
                            documents_updated += 1
                            
                        except Exception as e:
                            logger.error(
                                "Failed to update document after tool merge",
                                doc_id=doc_id,
                                error=str(e),
                                exc_info=True
                            )

                offset += batch_size

            logger.info(
                "Tool ID replacement completed",
                source_tool_ids=source_tool_ids,
                target_tool_id=target_tool_id,
                documents_scanned=documents_scanned,
                documents_updated=documents_updated,
                replacements_made=replacements_made
            )

            return {
                "documents_scanned": documents_scanned,
                "documents_updated": documents_updated,
                "replacements_made": replacements_made
            }

        except Exception as e:
            logger.error(
                "Tool ID replacement failed",
                source_tool_ids=source_tool_ids,
                target_tool_id=target_tool_id,
                error=str(e),
                exc_info=True
            )
            raise

    async def process_reanalysis_job(
        self,
        job_id: str,
        sentiment_analyzer
    ) -> Dict[str, Any]:
        """
        Process a reanalysis job - main batch processing loop.

        This method:
        1. Updates job status to RUNNING
        2. Queries sentiment_scores in batches
        3. Re-runs tool detection on each document
        4. Updates detected_tool_ids and analysis metadata
        5. Checkpoints progress after each batch
        6. Handles errors gracefully (catch-log-continue pattern)
        7. Updates job status to COMPLETED or FAILED

        Args:
            job_id: The job ID to process
            sentiment_analyzer: SentimentAnalyzer instance for tool detection

        Returns:
            Final job document with statistics

        Raises:
            ValueError: If job not found or already completed
        """
        # Load job
        try:
            job_doc = self.jobs.read_item(
                item=job_id,
                partition_key=job_id
            )
        except Exception as e:
            logger.error(
                "Failed to load reanalysis job",
                job_id=job_id,
                error=str(e)
            )
            raise ValueError(f"Job not found: {job_id}")

        # Validate state
        current_status = JobStatus(job_doc["status"])
        if current_status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            raise ValueError(
                f"Job {job_id} already {current_status.value}"
            )

        # Transition to RUNNING
        self._validate_state_transition(current_status, JobStatus.RUNNING)
        job_doc["status"] = JobStatus.RUNNING.value
        job_doc["start_time"] = datetime.now(timezone.utc).isoformat()

        try:
            self.jobs.upsert_item(body=job_doc)
        except Exception as e:
            logger.error(
                "Failed to update job status to RUNNING",
                job_id=job_id,
                error=str(e)
            )
            raise

        logger.info(
            "Reanalysis job started",
            job_id=job_id,
            total_count=job_doc["progress"]["total_count"]
        )

        # Build query for sentiment documents
        query_parts = ["SELECT * FROM c WHERE 1=1"]
        params = []

        # Resume from checkpoint if exists
        if job_doc["progress"]["last_checkpoint_id"]:
            query_parts.append("AND c.id > @checkpoint_id")
            params.append({
                "name": "@checkpoint_id",
                "value": job_doc["progress"]["last_checkpoint_id"]
            })

        # Date range filter
        if job_doc["parameters"].get("date_range"):
            date_range = job_doc["parameters"]["date_range"]
            if date_range.get("start"):
                query_parts.append("AND c._ts >= @start_ts")
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

        # Order by ID for consistent pagination and checkpointing
        query_parts.append("ORDER BY c.id")
        
        query = " ".join(query_parts)
        batch_size = job_doc["parameters"]["batch_size"]
        processed_count = job_doc["progress"]["processed_count"]
        tools_detected = job_doc["statistics"]["tools_detected"]
        categorized_count = job_doc["statistics"]["categorized_count"]
        uncategorized_count = job_doc["statistics"]["uncategorized_count"]

        try:
            # Process in batches using OFFSET/LIMIT
            offset = 0
            while True:
                batch_query = f"{query} OFFSET {offset} LIMIT {batch_size}"
                
                try:
                    items = list(self.sentiment.query_items(
                        query=batch_query,
                        parameters=params if params else None,
                        enable_cross_partition_query=True
                    ))
                except Exception as e:
                    logger.error(
                        "Batch query failed",
                        job_id=job_id,
                        offset=offset,
                        error=str(e),
                        exc_info=True
                    )
                    # Log to job error_log
                    job_doc["error_log"].append({
                        "doc_id": f"batch_offset_{offset}",
                        "error": f"Query failed: {str(e)}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    job_doc["statistics"]["errors_count"] += 1
                    offset += batch_size
                    continue

                if not items:
                    # No more documents
                    break

                # Process each document in batch
                for item in items:
                    doc_id = item["id"]
                    
                    try:
                        # Get original content for tool detection
                        content = item.get("content", "")
                        if not content:
                            logger.warning(
                                "Document has no content",
                                doc_id=doc_id
                            )
                            uncategorized_count += 1
                            processed_count += 1
                            continue

                        # Detect tools using SentimentAnalyzer
                        detected_tool_ids = (
                            sentiment_analyzer.detect_tools_in_content(
                                content
                            )
                        )

                        # Update document
                        item["detected_tool_ids"] = detected_tool_ids
                        item["last_analyzed_at"] = (
                            datetime.now(timezone.utc).isoformat()
                        )
                        # Increment version
                        current_version = item.get("analysis_version", "1.0.0")
                        major, minor, patch = current_version.split(".")
                        item["analysis_version"] = (
                            f"{major}.{minor}.{int(patch) + 1}"
                        )

                        # Save updated document
                        self.sentiment.upsert_item(body=item)

                        # Update statistics
                        if detected_tool_ids:
                            categorized_count += 1
                            for tool_id in detected_tool_ids:
                                tools_detected[tool_id] = (
                                    tools_detected.get(tool_id, 0) + 1
                                )
                        else:
                            uncategorized_count += 1

                        processed_count += 1

                    except Exception as e:
                        # Catch-log-continue pattern for individual errors
                        logger.error(
                            "Failed to process document",
                            job_id=job_id,
                            doc_id=doc_id,
                            error=str(e),
                            exc_info=True
                        )
                        job_doc["error_log"].append({
                            "doc_id": doc_id,
                            "error": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        job_doc["statistics"]["errors_count"] += 1
                        processed_count += 1

                # Checkpoint after batch
                last_doc_id = items[-1]["id"] if items else None
                job_doc["progress"]["processed_count"] = processed_count
                job_doc["progress"]["last_checkpoint_id"] = last_doc_id
                job_doc["progress"]["percentage"] = (
                    (processed_count / job_doc["progress"]["total_count"] * 100)
                    if job_doc["progress"]["total_count"] > 0
                    else 100.0
                )
                
                # Calculate estimated time remaining
                if processed_count > 0:
                    start_time = datetime.fromisoformat(
                        job_doc["start_time"].replace("Z", "+00:00")
                    )
                    elapsed_seconds = (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds()
                    
                    if elapsed_seconds > 0:
                        processing_rate = processed_count / elapsed_seconds
                        total_count = job_doc["progress"]["total_count"]
                        remaining_docs = total_count - processed_count
                        
                        if processing_rate > 0:
                            eta_seconds = remaining_docs / processing_rate
                            job_doc["progress"][
                                "estimated_time_remaining"
                            ] = int(eta_seconds)
                        else:
                            job_doc["progress"][
                                "estimated_time_remaining"
                            ] = None
                    else:
                        job_doc["progress"][
                            "estimated_time_remaining"
                        ] = None
                else:
                    job_doc["progress"]["estimated_time_remaining"] = None
                
                job_doc["statistics"]["tools_detected"] = tools_detected
                job_doc["statistics"]["categorized_count"] = categorized_count
                job_doc["statistics"]["uncategorized_count"] = (
                    uncategorized_count
                )

                # Save checkpoint
                try:
                    self.jobs.upsert_item(body=job_doc)
                    logger.debug(
                        "Checkpoint saved",
                        job_id=job_id,
                        processed=processed_count,
                        total=job_doc["progress"]["total_count"],
                        percentage=job_doc["progress"]["percentage"]
                    )
                except Exception as e:
                    logger.error(
                        "Failed to save checkpoint",
                        job_id=job_id,
                        error=str(e)
                    )
                    # Continue processing even if checkpoint fails

                offset += batch_size

            # Job completed successfully
            job_doc["status"] = JobStatus.COMPLETED.value
            job_doc["end_time"] = datetime.now(timezone.utc).isoformat()
            job_doc["progress"]["percentage"] = 100.0

            logger.info(
                "Reanalysis job completed",
                job_id=job_id,
                processed=processed_count,
                categorized=categorized_count,
                uncategorized=uncategorized_count,
                errors=job_doc["statistics"]["errors_count"],
                tools_detected=len(tools_detected)
            )

            # Log notification for automatic jobs (T029)
            if job_doc.get("trigger_type") == "automatic":
                logger.warning(
                    "NOTIFICATION: Automatic reanalysis completed",
                    job_id=job_id,
                    triggered_by=job_doc.get("triggered_by"),
                    reason=job_doc.get("reason"),
                    documents_processed=processed_count,
                    tools_detected_count=len(tools_detected),
                    errors=job_doc["statistics"]["errors_count"],
                    status="success"
                )

        except Exception as e:
            # Job failed with unrecoverable error
            logger.error(
                "Reanalysis job failed",
                job_id=job_id,
                error=str(e),
                exc_info=True
            )
            job_doc["status"] = JobStatus.FAILED.value
            job_doc["end_time"] = datetime.now(timezone.utc).isoformat()
            job_doc["error_log"].append({
                "doc_id": "job_level",
                "error": f"Job failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            # Log notification for automatic job failures (T029)
            if job_doc.get("trigger_type") == "automatic":
                logger.error(
                    "NOTIFICATION: Automatic reanalysis failed",
                    job_id=job_id,
                    triggered_by=job_doc.get("triggered_by"),
                    reason=job_doc.get("reason"),
                    error=str(e),
                    status="failed"
                )

        # Final save
        try:
            self.jobs.upsert_item(body=job_doc)
        except Exception as e:
            logger.error(
                "Failed to save final job state",
                job_id=job_id,
                error=str(e)
            )

        return job_doc

    async def cancel_job(
        self, job_id: str, cancelled_by: str
    ) -> Dict[str, Any]:
        """
        Cancel a reanalysis job.

        Only jobs in QUEUED status can be cancelled.
        Running jobs cannot be stopped mid-execution.

        Args:
            job_id: The job ID to cancel
            cancelled_by: Admin user who requested cancellation

        Returns:
            Updated job document

        Raises:
            ValueError: If job not found or in invalid state for cancel
        """
        # Read job
        try:
            job_doc = self.jobs.read_item(
                item=job_id, partition_key=job_id
            )
        except Exception as e:
            logger.error(
                "Job not found for cancellation",
                job_id=job_id,
                error=str(e)
            )
            raise ValueError(f"Job {job_id} not found")

        # Validate state
        current_status = job_doc["status"]
        if current_status not in [JobStatus.QUEUED.value]:
            raise ValueError(
                f"Cannot cancel job in {current_status} status. "
                "Only queued jobs can be cancelled."
            )

        # Update to cancelled
        job_doc["status"] = JobStatus.CANCELLED.value
        job_doc["end_time"] = datetime.now(timezone.utc).isoformat()
        job_doc["error_log"].append({
            "doc_id": "job_level",
            "error": f"Job cancelled by {cancelled_by}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Save
        try:
            self.jobs.upsert_item(body=job_doc)
            logger.info(
                "Reanalysis job cancelled",
                job_id=job_id,
                cancelled_by=cancelled_by
            )
        except Exception as e:
            logger.error(
                "Failed to cancel job",
                job_id=job_id,
                error=str(e)
            )
            raise

        return job_doc
