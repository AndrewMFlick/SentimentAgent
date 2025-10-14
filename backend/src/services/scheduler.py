"""Data collection scheduler."""
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
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")
    
    async def collect_and_analyze(self):
        """Collect data from Reddit and analyze sentiment."""
        # Run the blocking collection in a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor, self._collect_and_analyze_sync
        )
    
    def _collect_and_analyze_sync(self):
        """Synchronous data collection (runs in thread pool)."""
        cycle_id = f"cycle_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        cycle = DataCollectionCycle(
            id=cycle_id,
            start_time=datetime.utcnow(),
            status="running"
        )
        
        logger.info(f"Starting collection cycle: {cycle_id}")
        
        try:
            for subreddit in settings.subreddit_list:
                try:
                    logger.info(f"Collecting from r/{subreddit}")
                    
                    # Collect posts
                    posts = self.collector.collect_posts(subreddit, limit=50)
                    cycle.posts_collected += len(posts)
                    
                    for post in posts:
                        # Save post
                        db.save_post(post)
                        
                        # Analyze post sentiment
                        post_text = f"{post.title} {post.content}"
                        sentiment = self.analyzer.analyze(
                            content_id=post.id,
                            content_type="post",
                            subreddit=subreddit,
                            text=post_text
                        )
                        db.save_sentiment(sentiment)
                        
                        # Collect and analyze top comments
                        comments = self.collector.collect_comments(post.id, limit=20)
                        cycle.comments_collected += len(comments)
                        
                        for comment in comments:
                            db.save_comment(comment)
                            
                            # Analyze comment sentiment
                            comment_sentiment = self.analyzer.analyze(
                                content_id=comment.id,
                                content_type="comment",
                                subreddit=subreddit,
                                text=comment.content
                            )
                            db.save_sentiment(comment_sentiment)
                    
                    cycle.subreddits_processed.append(subreddit)
                    
                except Exception as e:
                    error_msg = f"Error processing r/{subreddit}: {str(e)}"
                    logger.error(error_msg)
                    cycle.errors.append(error_msg)
            
            cycle.status = "completed"
            cycle.end_time = datetime.utcnow()
            
            logger.info(
                f"Collection cycle {cycle_id} completed: "
                f"{cycle.posts_collected} posts, {cycle.comments_collected} comments, "
                f"{len(cycle.errors)} errors"
            )
            
        except Exception as e:
            cycle.status = "failed"
            cycle.end_time = datetime.utcnow()
            error_msg = f"Collection cycle failed: {str(e)}"
            logger.error(error_msg)
            cycle.errors.append(error_msg)
    
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
