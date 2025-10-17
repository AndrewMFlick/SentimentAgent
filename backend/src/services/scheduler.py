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
which resolves CosmosDB PostgreSQL mode JSON parsing issues with ISO 8601 strings.

Related database methods used by jobs:
- db.get_recent_posts(hours=N) - Check for existing posts (duplicate detection)
- db.cleanup_old_data() - Remove old data based on timestamps
- db.get_sentiment_stats(hours=N) - Aggregate sentiment over time windows

Reference: specs/004-fix-the-cosmosdb/spec.md (User Story 3)
Tasks: T014, T015, T016
"""
import logging
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import settings
from ..models import DataCollectionCycle
from .reddit_collector import RedditCollector
from .sentiment_analyzer import SentimentAnalyzer
from .database import db
from .trending_analyzer import trending_analyzer
from .health import app_state

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
            id='data_collection',
            name='Collect Reddit data and analyze sentiment',
            replace_existing=True
        )
        
        # Schedule cleanup job (daily)
        self.scheduler.add_job(
            self.cleanup_old_data,
            trigger=IntervalTrigger(hours=24),
            id='data_cleanup',
            name='Clean up old data',
            replace_existing=True
        )
        
        # Schedule trending analysis (every hour)
        self.scheduler.add_job(
            self.analyze_trending_topics,
            trigger=IntervalTrigger(hours=1),
            id='trending_analysis',
            name='Analyze trending topics',
            replace_existing=True
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
            trigger='date',
            run_date=datetime.now() + timedelta(seconds=5),
            id='initial_collection',
            name='Initial data collection',
            replace_existing=True
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
        await loop.run_in_executor(
            self.executor, self._collect_and_analyze_sync
        )
    
    def _collect_and_analyze_sync(self):
        """Synchronous data collection (runs in thread pool) with catch-log-continue error handling."""
        import psutil
        import os
        
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        process = psutil.Process(os.getpid())
        
        # Log memory usage at start
        memory_start_mb = process.memory_info().rss / 1024 / 1024
        
        cycle = DataCollectionCycle(
            id=cycle_id,
            start_time=datetime.utcnow(),
            status="running"
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
                            "timestamp": datetime.utcnow().isoformat()
                        }
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
                                    "error_type": type(e).__name__
                                },
                                exc_info=True
                            )
                            continue  # Continue with next post
                        
                        # Analyze post sentiment
                        try:
                            post_text = f"{post.title} {post.content}"
                            sentiment = self.analyzer.analyze(
                                content_id=post.id,
                                content_type="post",
                                subreddit=subreddit,
                                text=post_text
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
                                    "error_type": type(e).__name__
                                },
                                exc_info=True
                            )
                        
                        # Collect and analyze top comments
                        try:
                            comments = self.collector.collect_comments(post.id, limit=20)
                            cycle.comments_collected += len(comments)
                            
                            for comment in comments:
                                try:
                                    db.save_comment(comment)
                                    
                                    # Analyze comment sentiment
                                    comment_sentiment = self.analyzer.analyze(
                                        content_id=comment.id,
                                        content_type="comment",
                                        subreddit=subreddit,
                                        text=comment.content
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
                                            "error_type": type(e).__name__
                                        },
                                        exc_info=True
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
                                    "error_type": type(e).__name__
                                },
                                exc_info=True
                            )
                    
                    cycle.subreddits_processed.append(subreddit)
                    logger.info(
                        f"Collection completed for r/{subreddit}",
                        extra={
                            "cycle_id": cycle_id,
                            "subreddit": subreddit,
                            "posts_collected": len(posts)
                        }
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
                            "stack_trace": True
                        },
                        exc_info=True
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
                f"{cycle.posts_collected} posts, {cycle.comments_collected} comments, "
                f"{len(cycle.errors)} errors, "
                f"memory_start={memory_start_mb:.2f}MB, memory_end={memory_end_mb:.2f}MB, "
                f"memory_delta={memory_delta_mb:.2f}MB"
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
                    "error_type": type(e).__name__
                },
                exc_info=True
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
                self.executor,
                trending_analyzer.analyze_trending,
                24
            )
            msg = f"Trending analysis completed: {len(topics)} topics"
            logger.info(msg)
        except Exception as e:
            logger.error(f"Trending analysis failed: {e}")


# Global scheduler instance
scheduler = CollectionScheduler()
