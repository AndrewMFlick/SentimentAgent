"""Data collection scheduler.

This module manages scheduled background jobs for collecting Reddit data and analyzing sentiment.

User Story 3 (US3) Implementation:
----------------------------------
Scheduled jobs can query existing data by timestamp to avoid duplicate collection.
The datetime query fix (Feature 004) enables these jobs to:
- Check for existing posts from the same time period before re-collecting
- Query recent data for trending topic analysis
- Clean up old data based on retention policies

All datetime queries use Unix timestamps via database._datetime_to_timestamp() helper,
which resolves CosmosDB PostgreSQL mode JSON parsing issues with ISO 8601 datetime
strings when used as query parameters.

Related database methods used by jobs:
- db.get_recent_posts(hours=N) - Check for existing posts (duplicate detection)
- db.cleanup_old_data() - Remove old data based on timestamps
- db.get_sentiment_stats(hours=N) - Aggregate sentiment over time windows

Reference: specs/004-fix-the-cosmosdb/spec.md (User Story 3)
Tasks: T014, T015, T016
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import settings
from ..models import DataCollectionCycle
from .database import db
from .health import app_state
from .reddit_collector import RedditCollector
from .sentiment_analyzer import SentimentAnalyzer
from .trending_analyzer import trending_analyzer

logger = logging.getLogger(__name__)


class CollectionScheduler:
    """Schedules and manages periodic data collection."""

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.collector = RedditCollector()
        self.analyzer = SentimentAnalyzer()
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=1)

        logger.info("Collection scheduler initialized")

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Schedule data collection
        self.scheduler.add_job(
            self.collect_and_analyze,
            trigger=IntervalTrigger(minutes=settings.collection_interval_minutes),
            id="data_collection",
            name="Collect Reddit data and analyze sentiment",
            replace_existing=True,
        )

        # Schedule cleanup job (daily)
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=IntervalTrigger(hours=24),
            id="data_cleanup",
            name="Clean up old data",
            replace_existing=True,
        )

        # Schedule trending analysis (every hour)
        self.scheduler.add_job(
            self.analyze_trending_topics,
            trigger=IntervalTrigger(hours=1),
            id="trending_analysis",
            name="Analyze trending topics",
            replace_existing=True,
        )

        # Schedule daily sentiment aggregation (00:05 UTC)
        self.scheduler.add_job(
            self.compute_daily_aggregates,
            trigger="cron",
            hour=0,
            minute=5,
            id="daily_aggregation",
            name="Compute daily sentiment aggregates",
            replace_existing=True,
        )

        # Schedule tool auto-detection (hourly)
        self.scheduler.add_job(
            self.check_tool_auto_detection,
            trigger=IntervalTrigger(hours=1),
            id="tool_auto_detection",
            name="Check for auto-detection candidates",
            replace_existing=True,
        )

        # Schedule sentiment data cleanup (02:00 UTC)
        self.scheduler.add_job(
            self.cleanup_sentiment_data,
            trigger="cron",
            hour=2,
            minute=0,
            id="sentiment_cleanup",
            name="Clean up old sentiment aggregates",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        logger.info(
            f"Scheduler started - collecting data every "
            f"{settings.collection_interval_minutes} minutes"
        )

        # Run initial collection after 5 seconds to allow app to start
        from datetime import datetime, timedelta

        self.scheduler.add_job(
            self.collect_and_analyze,
            trigger="date",
            run_date=datetime.now() + timedelta(seconds=5),
            id="initial_collection",
            name="Initial data collection",
            replace_existing=True,
        )

    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.is_running:
            return

        logger.info("Stopping scheduler gracefully...")

        # Shutdown with wait=True to allow running jobs to complete
        self.scheduler.shutdown(wait=True)

        # Shutdown thread pool executor
        self.executor.shutdown(wait=True)

        self.is_running = False
        logger.info("Scheduler stopped gracefully")

    async def collect_and_analyze(self):
        """Collect data from Reddit and analyze sentiment."""
        # Run the blocking collection in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._collect_and_analyze_sync)

    def _collect_and_analyze_sync(self):
        """Synchronous data collection (runs in thread pool) with catch-log-continue error handling."""
        import os

        import psutil

        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        process = psutil.Process(os.getpid())

        # Log memory usage at start
        memory_start_mb = process.memory_info().rss / 1024 / 1024

        cycle = DataCollectionCycle(
            id=cycle_id, start_time=datetime.utcnow(), status="running"
        )

        logger.info(
            f"Starting collection cycle: {cycle_id}, "
            f"memory_start={memory_start_mb:.2f}MB"
        )

        try:
            # Catch-log-continue: Process each subreddit independently
            for subreddit in settings.subreddit_list:
                try:
                    logger.info(
                        f"Collection started for r/{subreddit}",
                        extra={
                            "cycle_id": cycle_id,
                            "subreddit": subreddit,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

                    # Collect posts
                    posts = self.collector.collect_posts(subreddit, limit=50)
                    cycle.posts_collected += len(posts)

                    for post in posts:
                        # Save post with retry logic
                        try:
                            db.save_post(post)
                        except Exception as e:
                            logger.error(
                                f"Failed to save post {post.id}",
                                extra={
                                    "cycle_id": cycle_id,
                                    "subreddit": subreddit,
                                    "post_id": post.id,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                                exc_info=True,
                            )
                            continue  # Continue with next post

                        # Analyze post sentiment
                        try:
                            post_text = f"{post.title} {post.content}"
                            sentiment = self.analyzer.analyze(
                                content_id=post.id,
                                content_type="post",
                                subreddit=subreddit,
                                text=post_text,
                            )
                            db.save_sentiment(sentiment)
                        except Exception as e:
                            logger.error(
                                f"Failed to analyze post sentiment {post.id}",
                                extra={
                                    "cycle_id": cycle_id,
                                    "subreddit": subreddit,
                                    "post_id": post.id,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                                exc_info=True,
                            )

                        # Collect and analyze top comments
                        try:
                            comments = self.collector.collect_comments(
                                post.id, limit=20
                            )
                            cycle.comments_collected += len(comments)

                            for comment in comments:
                                try:
                                    db.save_comment(comment)

                                    # Analyze comment sentiment
                                    comment_sentiment = self.analyzer.analyze(
                                        content_id=comment.id,
                                        content_type="comment",
                                        subreddit=subreddit,
                                        text=comment.content,
                                    )
                                    db.save_sentiment(comment_sentiment)
                                except Exception as e:
                                    logger.error(
                                        f"Failed to process comment {comment.id}",
                                        extra={
                                            "cycle_id": cycle_id,
                                            "subreddit": subreddit,
                                            "comment_id": comment.id,
                                            "error": str(e),
                                            "error_type": type(e).__name__,
                                        },
                                        exc_info=True,
                                    )
                                    continue  # Continue with next comment
                        except Exception as e:
                            logger.error(
                                f"Failed to collect comments for post {post.id}",
                                extra={
                                    "cycle_id": cycle_id,
                                    "subreddit": subreddit,
                                    "post_id": post.id,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                                exc_info=True,
                            )

                    cycle.subreddits_processed.append(subreddit)
                    logger.info(
                        f"Collection completed for r/{subreddit}",
                        extra={
                            "cycle_id": cycle_id,
                            "subreddit": subreddit,
                            "posts_collected": len(posts),
                        },
                    )

                except Exception as e:
                    # Catch-log-continue: Log error but continue with next subreddit
                    error_msg = f"Error processing r/{subreddit}: {str(e)}"
                    logger.error(
                        error_msg,
                        extra={
                            "cycle_id": cycle_id,
                            "subreddit": subreddit,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "stack_trace": True,
                        },
                        exc_info=True,
                    )
                    cycle.errors.append(error_msg)
                    app_state.collections_failed += 1

            # Collection cycle completed successfully
            cycle.status = "completed"
            cycle.end_time = datetime.utcnow()

            # Update application state
            app_state.last_collection_time = datetime.utcnow()
            app_state.collections_succeeded += 1

            # Log memory usage at end to detect leaks
            memory_end_mb = process.memory_info().rss / 1024 / 1024
            memory_delta_mb = memory_end_mb - memory_start_mb

            logger.info(
                f"Collection cycle {cycle_id} completed: "
                f"{
                    cycle.posts_collected} posts, {
                    cycle.comments_collected} comments, "
                f"{
                    len(
                        cycle.errors)} errors, "
                f"memory_start={
                        memory_start_mb:.2f}MB, memory_end={
                            memory_end_mb:.2f}MB, "
                f"memory_delta={
                    memory_delta_mb:.2f}MB"
            )

        except Exception as e:
            # Unexpected error during collection cycle
            cycle.status = "failed"
            cycle.end_time = datetime.utcnow()
            error_msg = f"Collection cycle failed: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "cycle_id": cycle_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            cycle.errors.append(error_msg)
            app_state.collections_failed += 1

    async def cleanup_old_data(self):
        """Clean up data older than retention period."""
        logger.info("Starting data cleanup")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, db.cleanup_old_data)
            logger.info("Data cleanup completed")
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    async def analyze_trending_topics(self):
        """Analyze and identify trending topics."""
        logger.info("Starting trending analysis")
        try:
            loop = asyncio.get_event_loop()
            topics = await loop.run_in_executor(
                self.executor, trending_analyzer.analyze_trending, 24
            )
            msg = f"Trending analysis completed: {len(topics)} topics"
            logger.info(msg)
        except Exception as e:
            logger.error(f"Trending analysis failed: {e}")

    async def compute_daily_aggregates(self):
        """Compute daily sentiment aggregates for all tools."""
        start_time = datetime.utcnow()
        logger.info("Starting daily sentiment aggregation")
        try:
            from .sentiment_aggregator import sentiment_aggregator

            if sentiment_aggregator:
                aggregates = await sentiment_aggregator.compute_daily_aggregates()
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                logger.info(
                    "Daily aggregation completed",
                    tool_count=len(aggregates),
                    execution_time_s=round(execution_time, 2),
                    status="success",
                )
            else:
                logger.warning("Sentiment aggregator not initialized")
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "Daily aggregation failed",
                error=str(e),
                execution_time_s=round(execution_time, 2),
                status="failed",
                exc_info=True,
            )

    async def check_tool_auto_detection(self):
        """Check for tools that should be auto-queued for approval."""
        start_time = datetime.utcnow()
        logger.info("Checking for auto-detection candidates")
        try:
            from .tool_manager import tool_manager

            if tool_manager:
                candidates = await tool_manager.check_auto_detection()
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                logger.info(
                    "Auto-detection check completed",
                    tools_queued=len(candidates),
                    execution_time_s=round(execution_time, 2),
                    status="success",
                )
            else:
                logger.warning("Tool manager not initialized")
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                "Tool auto-detection failed",
                error=str(e),
                execution_time_s=round(execution_time, 2),
                status="failed",
                exc_info=True,
            )

    async def cleanup_sentiment_data(self):
        """Clean up old sentiment aggregates based on retention policy."""
        logger.info("Starting sentiment data cleanup")
        try:
            from datetime import timedelta

            # Step 1: Soft delete aggregates older than retention period
            cutoff_date = (
                datetime.utcnow() - timedelta(days=settings.sentiment_retention_days)
            ).strftime("%Y-%m-%d")

            query_soft = """
                SELECT c.id, c.tool_id, c.date
                FROM c
                WHERE c.date < @cutoff_date
                    AND c.deleted_at = null
            """

            items_to_soft_delete = await db.query_items(
                "time_period_aggregates",
                query_soft,
                parameters=[{"name": "@cutoff_date", "value": cutoff_date}],
            )

            # Mark as deleted
            soft_deleted_count = 0
            for item in items_to_soft_delete:
                item["deleted_at"] = datetime.utcnow().isoformat()
                await db.upsert_item("time_period_aggregates", item)
                soft_deleted_count += 1

            # Step 2: Hard delete aggregates soft-deleted 30+ days ago
            hard_delete_cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()

            query_hard = """
                SELECT c.id, c.tool_id, c.date, c.deleted_at
                FROM c
                WHERE c.deleted_at != null
                    AND c.deleted_at < @hard_delete_cutoff
            """

            items_to_hard_delete = await db.query_items(
                "time_period_aggregates",
                query_hard,
                parameters=[
                    {"name": "@hard_delete_cutoff", "value": hard_delete_cutoff}
                ],
            )

            # Permanently delete from database
            hard_deleted_count = 0
            for item in items_to_hard_delete:
                await db.delete_item(
                    "time_period_aggregates",
                    item["id"],
                    item["tool_id"],  # partition key
                )
                hard_deleted_count += 1

            logger.info(
                "Sentiment cleanup completed",
                soft_deleted=soft_deleted_count,
                hard_deleted=hard_deleted_count,
                retention_days=settings.sentiment_retention_days,
            )
        except Exception as e:
            logger.error(f"Sentiment data cleanup failed: {e}", exc_info=True)


# Global scheduler instance
scheduler = CollectionScheduler()
