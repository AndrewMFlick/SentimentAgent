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
from typing import Any, Dict, List

import structlog
from azure.cosmos import ContainerProxy

from ..models.hot_topics import (
    HotTopic,
    HotTopicsResponse,
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
        sentiment_scores: List[Dict[str, Any]],
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
            sentiment_query = """
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

    async def _get_posts_with_engagement(
        self,
        cutoff_ts: int,
    ) -> set[str]:
        """Get post IDs that have engagement within the time range.
        
        A post is considered engaged if:
        - The post itself was created within the time range (post._ts >= cutoff), OR
        - The post has comments created within the time range
        
        Args:
            cutoff_ts: Unix timestamp cutoff for time range filtering
        
        Returns:
            Set of post IDs with engagement activity
        """
        # Query posts created within time range
        posts_query = "SELECT c.id FROM c WHERE c._ts >= @cutoff_ts"
        posts_in_range = list(self.reddit_posts.query_items(
            query=posts_query,
            parameters=[{"name": "@cutoff_ts", "value": cutoff_ts}],
            enable_cross_partition_query=True
        ))
        post_ids_from_posts = {p["id"] for p in posts_in_range}
        
        # Query comments within time range to find posts with recent comments
        comments_query = "SELECT DISTINCT c.post_id FROM c WHERE c._ts >= @cutoff_ts"
        comments_in_range = list(self.reddit_comments.query_items(
            query=comments_query,
            parameters=[{"name": "@cutoff_ts", "value": cutoff_ts}],
            enable_cross_partition_query=True
        ))
        post_ids_from_comments = {c["post_id"] for c in comments_in_range}
        
        # Combine both sets (posts created in range OR posts with comments in range)
        engaged_post_ids = post_ids_from_posts | post_ids_from_comments
        
        self._logger.debug(
            "Found engaged posts",
            posts_in_range=len(post_ids_from_posts),
            posts_with_recent_comments=len(post_ids_from_comments),
            total_engaged=len(engaged_post_ids),
        )
        
        return engaged_post_ids

    async def get_related_posts(
        self,
        tool_id: str,
        time_range: str = "7d",
        offset: int = 0,
        limit: int = 20,
    ) -> RelatedPostsResponse:
        """Get paginated related posts for a specific tool.
        
        Returns Reddit posts that mention the specified tool, filtered by
        engagement within the time range, sorted by engagement score.
        
        Algorithm:
        1. Calculate cutoff timestamp from time_range
        2. Get engaged post IDs (posts created or commented on within range)
        3. Query sentiment_scores for posts mentioning tool_id
        4. Filter by engaged post IDs
        5. Get full post details from reddit_posts
        6. Calculate engagement_score = comment_count + upvotes
        7. Sort by engagement_score DESC
        8. Apply offset/limit pagination
        9. Format with reddit URLs and excerpts
        
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
            "get_related_posts called",
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
        
        # Calculate cutoff timestamp
        cutoff_ts = self._calculate_cutoff_timestamp(time_range)
        
        # Get engaged post IDs (posts created or commented on within time range)
        engaged_post_ids = await self._get_posts_with_engagement(cutoff_ts)
        
        # Query sentiment_scores for posts mentioning this tool
        # Filter by content_type = 'post' to only get post-level sentiment
        sentiment_query = """
            SELECT c.content_id, c.sentiment, c.subreddit
            FROM c 
            WHERE ARRAY_CONTAINS(c.detected_tool_ids, @tool_id)
            AND c.content_type = 'post'
        """
        
        sentiment_scores = list(self.sentiment_scores.query_items(
            query=sentiment_query,
            parameters=[{"name": "@tool_id", "value": tool_id}],
            enable_cross_partition_query=True
        ))
        
        # Filter sentiment scores to only engaged posts
        engaged_sentiment_scores = [
            s for s in sentiment_scores 
            if s["content_id"] in engaged_post_ids
        ]
        
        if not engaged_sentiment_scores:
            return RelatedPostsResponse(
                posts=[],
                total=0,
                has_more=False,
                offset=offset,
                limit=limit,
            )
        
        # Get unique post IDs
        post_ids = list({s["content_id"] for s in engaged_sentiment_scores})
        
        # Create a mapping from post_id to sentiment
        sentiment_map = {s["content_id"]: s["sentiment"] for s in engaged_sentiment_scores}
        
        # Query reddit_posts for full post details
        # Process in batches to avoid parameter limits
        all_posts = []
        batch_size = 100
        
        for i in range(0, len(post_ids), batch_size):
            batch_ids = post_ids[i:i+batch_size]
            
            # Use IN clause for batch querying
            placeholders = ", ".join([f"@post_id_{j}" for j in range(len(batch_ids))])
            posts_query = f"""
                SELECT c.id, c.title, c.content, c.author, c.subreddit, 
                       c.created_utc, c.url, c.comment_count, c.upvotes
                FROM c 
                WHERE c.id IN ({placeholders})
            """
            
            parameters = [
                {"name": f"@post_id_{j}", "value": post_id}
                for j, post_id in enumerate(batch_ids)
            ]
            
            batch_posts = list(self.reddit_posts.query_items(
                query=posts_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            all_posts.extend(batch_posts)
        
        # Build RelatedPost objects with engagement scores
        from ..models.hot_topics import RelatedPost
        
        related_posts = []
        for post in all_posts:
            post_id = post["id"]
            
            # Calculate engagement score
            comment_count = post.get("comment_count", 0)
            upvotes = post.get("upvotes", 0)
            engagement_score = comment_count + upvotes
            
            # Generate excerpt (first 150 characters of content)
            content = post.get("content", "")
            excerpt = content[:150] if len(content) > 150 else content
            
            # Generate Reddit URL
            subreddit = post.get("subreddit", "")
            reddit_url = f"https://reddit.com/r/{subreddit}/comments/{post_id}"
            
            # Get sentiment from mapping
            sentiment = sentiment_map.get(post_id, "neutral")
            
            # Parse created_utc - it might be stored as string or datetime
            created_utc = post.get("created_utc")
            if isinstance(created_utc, str):
                from datetime import datetime
                created_utc = datetime.fromisoformat(created_utc.replace('Z', '+00:00'))
            
            related_posts.append(RelatedPost(
                post_id=post_id,
                title=post.get("title", ""),
                excerpt=excerpt,
                author=post.get("author", ""),
                subreddit=subreddit,
                created_utc=created_utc,
                reddit_url=reddit_url,
                comment_count=comment_count,
                upvotes=upvotes,
                sentiment=sentiment,
                engagement_score=engagement_score,
            ))
        
        # Sort by engagement score descending
        related_posts.sort(key=lambda p: p.engagement_score, reverse=True)
        
        # Calculate pagination
        total = len(related_posts)
        has_more = (offset + limit) < total
        
        # Apply offset and limit
        paginated_posts = related_posts[offset:offset+limit]
        
        self._logger.info(
            "Related posts retrieved",
            tool_id=tool_id,
            total=total,
            returned=len(paginated_posts),
            offset=offset,
            limit=limit,
            has_more=has_more,
        )
        
        return RelatedPostsResponse(
            posts=paginated_posts,
            total=total,
            has_more=has_more,
            offset=offset,
            limit=limit,
        )
