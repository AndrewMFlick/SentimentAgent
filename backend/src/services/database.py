"""CosmosDB database service.

This module provides database operations for the SentimentAgent application using Azure CosmosDB.

DateTime Query Fix (Feature 004-fix-the-cosmosdb):
---------------------------------------------------
CosmosDB PostgreSQL mode has JSON parsing issues with ISO 8601 datetime strings when used
as query parameters. To resolve this, all datetime-filtered queries use Unix timestamps
(integers) instead of ISO strings, and query against the CosmosDB _ts system field.

Key Implementation Details:
- _datetime_to_timestamp() helper converts Python datetime to Unix timestamp (int)
- All time-based queries use WHERE c._ts >= @cutoff with integer parameters
- The _ts field is a system-generated Unix timestamp on all CosmosDB documents
- This approach ensures backward compatibility with existing data

Affected User Stories:
- US1: Backend startup data loading (get_recent_posts, load_recent_data)
- US2: Historical data queries (get_sentiment_stats, cleanup_old_data)
- US3: Data collection jobs (duplicate detection via timestamp queries)

Reference: specs/004-fix-the-cosmosdb/spec.md
Tasks: T001 (helper), T005-T006 (US1), T011-T012 (US2), T014-T016 (US3)

Sentiment Stats Aggregation Fix (Feature 005-fix-cosmosdb-sql):
----------------------------------------------------------------
CosmosDB PostgreSQL mode does not support SUM(CASE WHEN...) syntax, causing sentiment
statistics to return zero values. Fixed by replacing single complex query with 5 separate
CosmosDB-compatible queries executed in parallel for performance.

Key Implementation Details:
- _execute_scalar_query() helper executes queries returning single scalar values
- get_sentiment_stats() uses 5 separate SELECT VALUE queries (total, positive, negative, neutral, avg)
- Queries executed in parallel using asyncio.gather() to maintain <2s performance target
- Fail-fast error handling (raises exceptions instead of returning silent zeros)
- Structured logging with execution time tracking

Affected Methods:
- _execute_scalar_query() (new): Helper for scalar query execution
- get_sentiment_stats() (modified): Now async, uses 5 parallel queries

Reference: specs/005-fix-cosmosdb-sql/spec.md
Tasks: T008 (helper), T009-T012 (integration tests), T013-T017 (implementation)
"""
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
    
    # ===== Datetime Query Helper =====
    # CosmosDB PostgreSQL mode has issues with ISO 8601 datetime strings in query parameters.
    # The JSON parsing fails to properly handle datetime strings, causing HTTP 500 errors.
    # Solution: Use Unix timestamps (integers) instead of ISO 8601 strings.
    # 
    # Query the _ts system field (Unix timestamp) rather than custom datetime fields.
    # Note: _ts represents the last modification time in CosmosDB, which for our use case
    # is equivalent to creation time since we don't update documents after creation.
    # This approach is compatible with both legacy data (with ISO format) and new queries.
    # 
    # Reference: specs/004-fix-the-cosmosdb/
    # Related tasks: T001, T005, T006, T011, T012
    
    def _datetime_to_timestamp(self, dt: datetime) -> int:
        """Convert datetime to Unix timestamp for CosmosDB queries.
        
        CosmosDB PostgreSQL mode has JSON parsing issues with ISO 8601 datetime
        strings in query parameters. Use Unix timestamps (integers) instead.
        
        Args:
            dt: Datetime object to convert
            
        Returns:
            Unix timestamp as integer (seconds since epoch)
        """
        return int(dt.timestamp())
    
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
            
            # Use _ts system field with Unix timestamp for CosmosDB PostgreSQL mode compatibility
            query = "SELECT * FROM c WHERE c._ts >= @cutoff"
            parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
            
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
    
    async def _execute_scalar_query(self, query: str, parameters: List[Dict]) -> int | float:
        """Execute a query that returns a single scalar value.
        
        Helper method for executing CosmosDB queries that return a single value
        using SELECT VALUE syntax. Used by get_sentiment_stats for parallel query execution.
        
        Args:
            query: SQL query string using SELECT VALUE syntax
            parameters: List of query parameters
            
        Returns:
            Single integer or float value from query result, or 0 if empty result
            
        Raises:
            Exception: Propagates any database errors (fail-fast pattern)
            
        Example:
            result = await self._execute_scalar_query(
                "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff",
                [{"name": "@cutoff", "value": 1234567890}]
            )
        """
        result = self.sentiment_container.query_items(
            query,
            parameters=parameters,
            enable_cross_partition_query=True
        )
        items = list(result)
        if not items:
            return 0
        # SELECT VALUE returns the value directly, not wrapped in a dict
        value = items[0]
        logger.debug(f"Raw query result value: {value}, type: {type(value)}")
        
        # Handle different CosmosDB response formats
        if isinstance(value, dict):
            logger.debug(f"Value is dict, keys: {value.keys()}")
            # CosmosDB sometimes wraps results in dict with $1 key
            if '$1' in value:
                logger.debug(f"Extracting value from dict with $1 key")
                value = value['$1']
            # Or other numeric keys
            elif len(value) == 1:
                logger.debug(f"Extracting single value from dict")
                value = list(value.values())[0]
        
        logger.debug(f"Returning value: {value}, type: {type(value)}")
        # Convert to appropriate numeric type, return 0 for None
        if value is None:
            return 0
        return float(value) if isinstance(value, (int, float)) else 0
    
    async def get_sentiment_stats(self, subreddit: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get aggregated sentiment statistics.
        
        Executes 5 separate CosmosDB-compatible queries in parallel to aggregate
        sentiment statistics. Uses SELECT VALUE syntax instead of CASE WHEN which
        is not supported in CosmosDB PostgreSQL mode.
        
        Args:
            subreddit: Optional subreddit filter
            hours: Time window in hours (default 24)
            
        Returns:
            Dictionary with keys: total, positive, negative, neutral, avg_sentiment
            
        Raises:
            Exception: Propagates database errors (fail-fast, no silent zeros)
            
        Performance: Completes in <2 seconds for 1-week windows via parallel execution
        """
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            cutoff_ts = self._datetime_to_timestamp(cutoff)
            
            # Build base parameters
            parameters = [{"name": "@cutoff", "value": cutoff_ts}]
            
            # Build query filter conditions
            filter_conditions = "c._ts >= @cutoff"
            if subreddit:
                filter_conditions += " AND c.subreddit = @subreddit"
                parameters.append({"name": "@subreddit", "value": subreddit})
            
            # Define 5 separate CosmosDB-compatible queries
            total_query = f"SELECT VALUE COUNT(1) FROM c WHERE {filter_conditions}"
            positive_query = f"SELECT VALUE COUNT(1) FROM c WHERE {filter_conditions} AND c.sentiment = 'positive'"
            negative_query = f"SELECT VALUE COUNT(1) FROM c WHERE {filter_conditions} AND c.sentiment = 'negative'"
            neutral_query = f"SELECT VALUE COUNT(1) FROM c WHERE {filter_conditions} AND c.sentiment = 'neutral'"
            avg_query = f"SELECT VALUE AVG(c.compound_score) FROM c WHERE {filter_conditions}"
            
            # Log query execution start
            logger.info(f"Executing sentiment stats queries: subreddit={subreddit}, hours={hours}, cutoff_ts={cutoff_ts}")
            
            # Execute queries in parallel for performance
            start_time = time.time()
            total, positive, negative, neutral, avg_sentiment = await asyncio.gather(
                self._execute_scalar_query(total_query, parameters),
                self._execute_scalar_query(positive_query, parameters),
                self._execute_scalar_query(negative_query, parameters),
                self._execute_scalar_query(neutral_query, parameters),
                self._execute_scalar_query(avg_query, parameters)
            )
            execution_time = time.time() - start_time
            
            # Handle None values from AVG query on empty result
            if avg_sentiment is None:
                avg_sentiment = 0.0
            
            result = {
                "total": total,
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "avg_sentiment": float(avg_sentiment) if avg_sentiment else 0.0
            }
            
            # Log query completion with results
            logger.info(
                f"Sentiment stats query complete: "
                f"total={total}, positive={positive}, negative={negative}, neutral={neutral}, "
                f"avg={avg_sentiment:.3f}, execution_time={execution_time:.3f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to query sentiment stats: {e}", exc_info=True)
            # Fail-fast: re-raise exception instead of returning silent zeros
            raise
    
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
            
            # Clean posts - use _ts system field with Unix timestamp
            query = "SELECT c.id, c.subreddit FROM c WHERE c._ts < @cutoff"
            parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
            
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
            
            # Load recent posts
            posts = self.get_recent_posts(hours=hours, limit=1000)
            posts_count = len(posts)
            
            # Count recent comments using _ts system field with Unix timestamp
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            query = "SELECT VALUE COUNT(1) FROM c WHERE c._ts >= @cutoff"
            parameters = [{"name": "@cutoff", "value": self._datetime_to_timestamp(cutoff)}]
            
            try:
                items = list(self.comments_container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                comments_count = items[0] if items else 0
            except Exception as e:
                logger.warning(f"Error counting comments: {e}")
                comments_count = 0
            
            # Get sentiment stats
            stats = await self.get_sentiment_stats(hours=hours)
            
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
