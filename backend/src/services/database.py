"""CosmosDB database service."""
import logging
import os
import json
import time
import asyncio
from typing import List, Optional, Dict, Any
from functools import wraps
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import urllib3
import warnings

from ..config import settings
from ..models import (
    RedditPost, RedditComment, SentimentScore, 
    TrendingTopic, DataCollectionCycle
)

# Disable SSL warnings for local emulator
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)


def retry_db_operation(func):
    """
    Retry decorator for database operations with exponential backoff.
    
    Retries transient CosmosDB errors with exponential backoff.
    Configured via settings: db_retry_max_attempts, db_retry_base_delay
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_attempts = settings.db_retry_max_attempts
        base_delay = settings.db_retry_base_delay
        
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except (
                exceptions.CosmosHttpResponseError,
                exceptions.CosmosClientTimeoutError,
                ConnectionError,
            ) as e:
                if attempt == max_attempts - 1:
                    # Last attempt failed, re-raise
                    logger.error(
                        f"Database operation {func.__name__} failed after {max_attempts} attempts: {e}",
                        exc_info=True
                    )
                    raise
                
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Database operation {func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                    f"retrying in {delay}s: {e}"
                )
                time.sleep(delay)
            except Exception as e:
                # Non-transient errors should not be retried
                logger.error(f"Non-retryable error in {func.__name__}: {e}", exc_info=True)
                raise
        
        # Should not reach here, but for safety
        raise RuntimeError(f"Unexpected retry logic failure in {func.__name__}")
    
    return wrapper


def sanitize_text(text: str) -> str:
    """Sanitize text to avoid Unicode escape sequence issues."""
    if not text:
        return text
    try:
        # Use JSON encoding to properly escape all special characters
        # Encode to JSON string (adds quotes and escapes),
        # then remove the quotes
        sanitized = json.dumps(text)[1:-1]
        return sanitized
    except Exception as e:
        logger.debug(f"Error sanitizing text: {e}")
        return ""


class DatabaseService:
    """Manages CosmosDB operations."""
    
    def __init__(self):
        """Initialize CosmosDB client and containers."""
        # For local emulator, disable SSL verification
        if "localhost" in settings.cosmos_endpoint:
            os.environ['AZURE_COSMOS_DISABLE_SSL_VERIFICATION'] = 'true'
            self.client = CosmosClient(
                settings.cosmos_endpoint, 
                settings.cosmos_key,
                connection_verify=False
            )
        else:
            self.client = CosmosClient(
                settings.cosmos_endpoint,
                settings.cosmos_key
            )
        self.database = self.client.get_database_client(
            settings.cosmos_database
        )
        
        # Container references
        self.posts_container = None
        self.comments_container = None
        self.sentiment_container = None
        self.trending_container = None
        
        logger.info("Database service initialized")
    
    async def initialize(self):
        """Initialize database and containers."""
        try:
            # Create database if not exists
            try:
                self.database = self.client.create_database(settings.cosmos_database)
                logger.info(f"Created database: {settings.cosmos_database}")
            except exceptions.CosmosResourceExistsError:
                logger.info(f"Database already exists: {settings.cosmos_database}")
            
            # Create containers
            self._create_container(settings.cosmos_container_posts, "/subreddit")
            self._create_container(settings.cosmos_container_comments, "/post_id")
            self._create_container(settings.cosmos_container_sentiment, "/subreddit")
            self._create_container(settings.cosmos_container_trending, "/id")
            
            # Get container clients
            self.posts_container = self.database.get_container_client(settings.cosmos_container_posts)
            self.comments_container = self.database.get_container_client(settings.cosmos_container_comments)
            self.sentiment_container = self.database.get_container_client(settings.cosmos_container_sentiment)
            self.trending_container = self.database.get_container_client(settings.cosmos_container_trending)
            
            logger.info("Database containers initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    async def is_connected(self) -> bool:
        """Check if database connection is healthy."""
        try:
            # Try a simple operation to verify connection
            if self.database is None:
                return False
            
            # List containers to verify connection
            list(self.database.list_containers())
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def _create_container(self, container_name: str, partition_key: str):
        """Create a container if it doesn't exist."""
        try:
            self.database.create_container(
                id=container_name,
                partition_key=PartitionKey(path=partition_key)
            )
            logger.info(f"Created container: {container_name}")
        except exceptions.CosmosResourceExistsError:
            logger.debug(f"Container already exists: {container_name}")
    
    # Posts operations
    def save_post(self, post: RedditPost):
        """Save a Reddit post."""
        try:
            item = post.model_dump()
            item['id'] = post.id
            item['created_utc'] = post.created_utc.isoformat()
            item['collected_at'] = post.collected_at.isoformat()
            
            # Sanitize text fields to avoid Unicode issues
            if item.get('title'):
                item['title'] = sanitize_text(item['title'])
            if item.get('content'):
                item['content'] = sanitize_text(item['content'])
            if item.get('url'):
                item['url'] = sanitize_text(item['url'])
            if item.get('author'):
                item['author'] = sanitize_text(item['author'])
            if item.get('subreddit'):
                item['subreddit'] = sanitize_text(item['subreddit'])
            
            self.posts_container.upsert_item(item)
            logger.debug(f"Saved post: {post.id}")
        except Exception as e:
            logger.error(f"Error saving post {post.id}: {e}")
    
    def get_post(self, post_id: str, subreddit: str) -> Optional[RedditPost]:
        """Get a post by ID."""
        try:
            item = self.posts_container.read_item(post_id, partition_key=subreddit)
            return RedditPost(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    def get_recent_posts(self, subreddit: Optional[str] = None, hours: int = 24, limit: int = 100) -> List[RedditPost]:
        """Get recent posts."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            query = "SELECT * FROM c WHERE c.collected_at >= @cutoff"
            # CosmosDB expects ISO 8601 format without microseconds
            parameters = [{"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}]
            
            if subreddit:
                query += " AND c.subreddit = @subreddit"
                parameters.append({"name": "@subreddit", "value": subreddit})
            
            query += f" ORDER BY c.created_utc DESC OFFSET 0 LIMIT {limit}"
            
            items = list(self.posts_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return [RedditPost(**item) for item in items]
        except Exception as e:
            logger.error(f"Error getting recent posts: {e}")
            return []
    
    # Comments operations
    def save_comment(self, comment: RedditComment):
        """Save a Reddit comment."""
        try:
            item = comment.model_dump()
            item['id'] = comment.id
            item['created_utc'] = comment.created_utc.isoformat()
            item['collected_at'] = comment.collected_at.isoformat()
            
            # Sanitize text fields to avoid Unicode issues
            if item.get('content'):
                item['content'] = sanitize_text(item['content'])
            if item.get('author'):
                item['author'] = sanitize_text(item['author'])
            if item.get('post_id'):
                item['post_id'] = sanitize_text(item['post_id'])
            if item.get('parent_id'):
                item['parent_id'] = sanitize_text(item['parent_id'])
            
            self.comments_container.upsert_item(item)
            logger.debug(f"Saved comment: {comment.id}")
        except Exception as e:
            logger.error(f"Error saving comment {comment.id}: {e}")
    
    def get_post_comments(self, post_id: str) -> List[RedditComment]:
        """Get all comments for a post."""
        try:
            query = "SELECT * FROM c WHERE c.post_id = @post_id"
            parameters = [{"name": "@post_id", "value": post_id}]
            
            items = list(self.comments_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=post_id
            ))
            
            return [RedditComment(**item) for item in items]
        except Exception as e:
            logger.error(f"Error getting comments for post {post_id}: {e}")
            return []
    
    # Sentiment operations
    def save_sentiment(self, sentiment: SentimentScore):
        """Save sentiment analysis result."""
        try:
            item = sentiment.model_dump()
            item['id'] = sentiment.content_id
            item['analyzed_at'] = sentiment.analyzed_at.isoformat()
            
            self.sentiment_container.upsert_item(item)
            logger.debug(f"Saved sentiment for: {sentiment.content_id}")
        except Exception as e:
            logger.error(f"Error saving sentiment {sentiment.content_id}: {e}")
    
    def get_sentiment_stats(self, subreddit: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated sentiment statistics."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            query = """
            SELECT 
                COUNT(1) as total,
                SUM(CASE WHEN c.sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN c.sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
                SUM(CASE WHEN c.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral,
                AVG(c.compound_score) as avg_sentiment
            FROM c 
            WHERE c.analyzed_at >= @cutoff
            """
            # CosmosDB expects ISO 8601 format without microseconds
            parameters = [
                {"name": "@cutoff", "value": cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")}
            ]
            
            if subreddit:
                query += " AND c.subreddit = @subreddit"
                parameters.append({"name": "@subreddit", "value": subreddit})
            
            items = list(self.sentiment_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if items:
                return items[0]
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "avg_sentiment": 0.0}
            
        except Exception as e:
            logger.error(f"Error getting sentiment stats: {e}")
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "avg_sentiment": 0.0}
    
    # Trending topics operations
    def save_trending_topic(self, topic: TrendingTopic):
        """Save a trending topic."""
        try:
            item = topic.model_dump()
            item['peak_time'] = topic.peak_time.isoformat()
            item['created_at'] = topic.created_at.isoformat()
            
            self.trending_container.upsert_item(item)
            logger.debug(f"Saved trending topic: {topic.id}")
        except Exception as e:
            logger.error(f"Error saving trending topic {topic.id}: {e}")
    
    def get_trending_topics(self, limit: int = 20) -> List[TrendingTopic]:
        """Get top trending topics."""
        try:
            query = f"""
            SELECT * FROM c 
            ORDER BY c.engagement_velocity DESC 
            OFFSET 0 LIMIT {limit}
            """
            
            items = list(self.trending_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return [TrendingTopic(**item) for item in items]
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []
    # Data cleanup
    def cleanup_old_data(self):
        """Remove data older than retention period."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=settings.data_retention_days)
            # CosmosDB expects ISO 8601 format without microseconds
            cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Clean posts
            query = "SELECT c.id, c.subreddit FROM c WHERE c.collected_at < @cutoff"
            parameters = [{"name": "@cutoff", "value": cutoff_str}]
            
            items = list(self.posts_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            for item in items:
                self.posts_container.delete_item(item['id'], partition_key=item['subreddit'])
            
            logger.info(f"Cleaned up {len(items)} old posts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def load_recent_data(self):
        """
        Load recent data from database on startup.
        
        Queries the last N hours of posts and comments to populate caches
        and ensure data is available immediately.
        """
        start_time = time.time()
        hours = settings.startup_load_hours
        
        try:
            logger.info(f"Loading recent data from last {hours} hours...")
            
            # TODO: Fix datetime query format for CosmosDB PostgreSQL mode
            # Temporarily skip data loading until we resolve the datetime format issue
            logger.warning("Data loading temporarily disabled - datetime format issue with CosmosDB")
            posts_count = 0
            comments_count = 0
            stats = {"total": 0}
            
            elapsed = time.time() - start_time
            logger.info(
                f"Data loading complete: {posts_count} posts, {comments_count} comments, "
                f"{stats.get('total', 0)} sentiment scores loaded in {elapsed:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error loading recent data: {e}", exc_info=True)
            # Don't raise - startup should continue even if data loading fails


# Global database instance
db = DatabaseService()
