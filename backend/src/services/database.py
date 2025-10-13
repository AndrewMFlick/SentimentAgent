"""CosmosDB database service."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient, PartitionKey, exceptions

from ..config import settings
from ..models import RedditPost, RedditComment, SentimentScore, TrendingTopic, DataCollectionCycle

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages CosmosDB operations."""
    
    def __init__(self):
        """Initialize CosmosDB client and containers."""
        self.client = CosmosClient(settings.cosmos_endpoint, settings.cosmos_key)
        self.database = self.client.get_database_client(settings.cosmos_database)
        
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
            parameters = [{"name": "@cutoff", "value": cutoff.isoformat()}]
            
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
            parameters = [{"name": "@cutoff", "value": cutoff.isoformat()}]
            
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
            cutoff_str = cutoff.isoformat()
            
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


# Global database instance
db = DatabaseService()
