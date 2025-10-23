"""Hot Topics service for aggregating engagement and sentiment data.

This service calculates hot topics (trending tools) and related posts
by aggregating data from multiple CosmosDB containers:
- sentiment_scores (tool mentions, sentiment analysis)
- reddit_posts (post metadata, engagement metrics)
- reddit_comments (comment activity for timeline filtering)
- Tools (tool metadata)

All entities are derived/calculated - nothing stored in database.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

import structlog
from azure.cosmos import ContainerProxy

from ..models.hot_topics import (
    HotTopic,
    HotTopicsResponse,
    RelatedPost,
    RelatedPostsResponse,
    SentimentDistribution,
)

logger = structlog.get_logger(__name__)


class HotTopicsService:
    """Service for calculating hot topics and related posts.
    
    Methods are placeholders for Phase 3+ implementation.
    Phase 2 establishes service structure and helper functions.
    """

    def __init__(
        self,
        sentiment_scores_container: ContainerProxy,
        reddit_posts_container: ContainerProxy,
        reddit_comments_container: ContainerProxy,
        tools_container: ContainerProxy,
    ):
        """Initialize service with database containers.
        
        Args:
            sentiment_scores_container: Container with detected_tool_ids
            reddit_posts_container: Container with post data
            reddit_comments_container: Container with comment data
            tools_container: Container with tool metadata
        """
        self.sentiment_scores = sentiment_scores_container
        self.reddit_posts = reddit_posts_container
        self.reddit_comments = reddit_comments_container
        self.tools = tools_container
        self._logger = logger.bind(service="hot_topics")

    def _calculate_cutoff_timestamp(self, time_range: str) -> int:
        """Calculate Unix timestamp cutoff for time range filtering.
        
        Args:
            time_range: One of "24h", "7d", "30d"
        
        Returns:
            Unix timestamp (seconds since epoch) marking the cutoff.
            Posts/comments with _ts >= cutoff are included.
        
        Raises:
            ValueError: If time_range is invalid
        
        Example:
            >>> service._calculate_cutoff_timestamp("7d")
            1705776000  # 7 days ago from now
        """
        now = datetime.now(timezone.utc)

        if time_range == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_range == "7d":
            cutoff = now - timedelta(days=7)
        elif time_range == "30d":
            cutoff = now - timedelta(days=30)
        else:
            raise ValueError(
                f"Invalid time_range: {time_range}. Must be '24h', '7d', or '30d'"
            )

        # CosmosDB _ts field is Unix timestamp (seconds since epoch)
        timestamp = int(cutoff.timestamp())
        
        self._logger.debug(
            "Calculated cutoff timestamp",
            time_range=time_range,
            cutoff_iso=cutoff.isoformat(),
            cutoff_ts=timestamp,
        )
        
        return timestamp

    def calculate_engagement_score(
        self,
        mentions: int,
        comments: int,
        upvotes: int,
    ) -> int:
        """Calculate engagement score for a tool.
        
        Formula: (mentions × 10) + (comments × 2) + upvotes
        
        Args:
            mentions: Number of posts/comments mentioning the tool
            comments: Sum of comment counts on related posts
            upvotes: Sum of upvotes on related posts
        
        Returns:
            Integer engagement score (higher is more engaged)
        
        Example:
            >>> service.calculate_engagement_score(5, 20, 100)
            190  # (5 × 10) + (20 × 2) + 100
        """
        return (mentions * 10) + (comments * 2) + upvotes

    def _aggregate_sentiment_distribution(
        self,
        sentiment_scores: List[Dict],
    ) -> SentimentDistribution:
        """Aggregate sentiment distribution from sentiment scores.
        
        Args:
            sentiment_scores: List of sentiment score documents
        
        Returns:
            SentimentDistribution with counts and percentages
        """
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for score in sentiment_scores:
            sentiment = score.get("sentiment", "neutral")
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
        
        total = positive_count + negative_count + neutral_count
        
        if total == 0:
            return SentimentDistribution(
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                positive_percent=0.0,
                negative_percent=0.0,
                neutral_percent=0.0,
            )
        
        return SentimentDistribution(
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            positive_percent=round((positive_count / total) * 100, 2),
            negative_percent=round((negative_count / total) * 100, 2),
            neutral_percent=round((neutral_count / total) * 100, 2),
        )

    async def get_hot_topics(
        self,
        time_range: str = "7d",
        limit: int = 10,
    ) -> HotTopicsResponse:
        """Get hot topics ranked by engagement within time range.
        
        Algorithm:
        1. Query sentiment_scores for tool mentions within time range
        2. Calculate engagement score per tool: (mentions × 10) + (comments × 2) + upvotes
        3. Calculate sentiment distribution per tool
        4. Rank by engagement_score DESC
        5. Return top N tools
        
        Args:
            time_range: Filter by "24h", "7d", or "30d" (default: "7d")
            limit: Maximum number of hot topics to return (1-50)
        
        Returns:
            HotTopicsResponse with ranked hot topics list
        
        Raises:
            ValueError: If time_range is invalid or limit out of range
        """
        self._logger.info(
            "get_hot_topics called",
            time_range=time_range,
            limit=limit,
        )
        
        # Validate parameters
        if limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50")
        
        cutoff_ts = self._calculate_cutoff_timestamp(time_range)
        
        # Get all active tools
        tools_query = "SELECT * FROM c WHERE c.status = 'active' AND c.partitionKey = 'tool'"
        tools = list(self.tools.query_items(
            query=tools_query,
            enable_cross_partition_query=False
        ))
        
        self._logger.debug(f"Found {len(tools)} active tools")
        
        # For each tool, calculate engagement metrics
        hot_topics = []
        
        for tool in tools:
            tool_id = tool["id"]
            tool_name = tool["name"]
            tool_slug = tool.get("slug", tool_name.lower().replace(" ", "-"))
            
            # Query sentiment scores for this tool within time range
            # Use ARRAY_CONTAINS to find posts mentioning this tool
            sentiment_query = f"""
                SELECT * FROM c 
                WHERE ARRAY_CONTAINS(c.detected_tool_ids, @tool_id)
                AND c._ts >= @cutoff_ts
            """
            
            sentiment_scores = list(self.sentiment_scores.query_items(
                query=sentiment_query,
                parameters=[
                    {"name": "@tool_id", "value": tool_id},
                    {"name": "@cutoff_ts", "value": cutoff_ts}
                ],
                enable_cross_partition_query=True
            ))
            
            mentions = len(sentiment_scores)
            
            # Skip tools with fewer than 3 mentions (threshold)
            if mentions < 3:
                continue
            
            # Get post IDs to calculate engagement metrics
            post_ids = [score["post_id"] for score in sentiment_scores]
            
            # Query reddit posts for comment counts and upvotes
            total_comments = 0
            total_upvotes = 0
            
            if post_ids:
                # Query in batches to avoid parameter limits
                batch_size = 100
                for i in range(0, len(post_ids), batch_size):
                    batch_ids = post_ids[i:i+batch_size]
                    
                    # Use IN clause for batch querying
                    placeholders = ", ".join([f"@post_id_{j}" for j in range(len(batch_ids))])
                    posts_query = f"SELECT c.num_comments, c.score FROM c WHERE c.id IN ({placeholders})"
                    
                    parameters = [
                        {"name": f"@post_id_{j}", "value": post_id}
                        for j, post_id in enumerate(batch_ids)
                    ]
                    
                    posts = list(self.reddit_posts.query_items(
                        query=posts_query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    for post in posts:
                        total_comments += post.get("num_comments", 0)
                        total_upvotes += post.get("score", 0)
            
            # Calculate engagement score
            engagement_score = self.calculate_engagement_score(
                mentions, total_comments, total_upvotes
            )
            
            # Calculate sentiment distribution
            sentiment_distribution = self._aggregate_sentiment_distribution(sentiment_scores)
            
            hot_topics.append(HotTopic(
                tool_id=tool_id,
                tool_name=tool_name,
                tool_slug=tool_slug,
                engagement_score=engagement_score,
                total_mentions=mentions,
                total_comments=total_comments,
                total_upvotes=total_upvotes,
                sentiment_distribution=sentiment_distribution,
            ))
        
        # Sort by engagement score descending
        hot_topics.sort(key=lambda x: x.engagement_score, reverse=True)
        
        # Limit results
        hot_topics = hot_topics[:limit]
        
        self._logger.info(
            "Hot topics calculated",
            count=len(hot_topics),
            time_range=time_range,
        )
        
        return HotTopicsResponse(
            hot_topics=hot_topics,
            generated_at=datetime.now(timezone.utc),
            time_range=time_range,
        )

    async def get_related_posts(
        self,
        tool_id: str,
        time_range: str = "7d",
        offset: int = 0,
        limit: int = 20,
    ) -> RelatedPostsResponse:
        """Get paginated related posts for a specific tool.
        
        Placeholder for Phase 4 (US2) implementation.
        Will query reddit_posts filtered by tool mentions.
        
        Algorithm (to be implemented in Phase 4):
        1. Query sentiment_scores for posts mentioning tool_id within time_range
        2. Get post details from reddit_posts
        3. Calculate engagement_score = comment_count + upvotes
        4. Sort by engagement_score DESC
        5. Apply offset/limit pagination
        6. Format with reddit_url for deep links
        
        Args:
            tool_id: Tool identifier to find related posts for
            time_range: Filter by "24h", "7d", or "30d" (default: "7d")
            offset: Number of posts to skip (for pagination)
            limit: Maximum posts to return (1-100, default: 20)
        
        Returns:
            RelatedPostsResponse with paginated posts and metadata
        
        Raises:
            ValueError: If parameters are invalid
        """
        self._logger.info(
            "get_related_posts called (placeholder)",
            tool_id=tool_id,
            time_range=time_range,
            offset=offset,
            limit=limit,
        )
        
        # Validate parameters
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be >= 0")
        
        cutoff_ts = self._calculate_cutoff_timestamp(time_range)
        
        # TODO (Phase 4 - T023): Implement related posts query
        # - Query sentiment_scores WHERE tool_id IN detected_tool_ids AND _ts >= cutoff
        # - Join with reddit_posts for full post data
        # - Calculate engagement scores
        # - Sort by engagement DESC
        # - Apply offset/limit pagination
        # - Generate reddit URLs: f"https://reddit.com/r/{subreddit}/comments/{post_id}"
        
        return RelatedPostsResponse(
            posts=[],
            total=0,
            has_more=False,
            offset=offset,
            limit=limit,
        )
