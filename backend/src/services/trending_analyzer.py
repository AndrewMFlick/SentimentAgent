"""Trending topics analyzer."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict

from ..models import RedditPost, TrendingTopic
from .database import db

logger = logging.getLogger(__name__)


class TrendingAnalyzer:
    """Analyzes and identifies trending topics."""
    
    def analyze_trending(self, hours: int = 24) -> List[TrendingTopic]:
        """
        Identify trending topics from recent posts.
        
        Args:
            hours: Time window to analyze (default: 24)
            
        Returns:
            List of TrendingTopic objects
        """
        try:
            # Get recent posts
            posts = db.get_recent_posts(hours=hours, limit=500)
            
            if not posts:
                logger.info("No posts found for trending analysis")
                return []
            
            # Calculate engagement velocity for each post
            trending_posts = []
            for post in posts:
                velocity = self._calculate_engagement_velocity(post)
                if velocity > 0:
                    trending_posts.append((post, velocity))
            
            # Sort by velocity
            trending_posts.sort(key=lambda x: x[1], reverse=True)
            
            # Group related posts by theme
            topics = self._group_by_theme(trending_posts[:50])  # Top 50 posts
            
            # Create trending topic objects
            trending_topics = []
            for theme, posts_data in topics.items():
                posts_list = [p[0] for p in posts_data]
                topic = self._create_trending_topic(theme, posts_list, posts_data)
                trending_topics.append(topic)
            
            # Sort topics by engagement
            trending_topics.sort(key=lambda x: x.engagement_velocity, reverse=True)
            
            # Save to database
            for topic in trending_topics[:20]:  # Top 20
                db.save_trending_topic(topic)
            
            logger.info(f"Identified {len(trending_topics)} trending topics")
            return trending_topics[:20]
            
        except Exception as e:
            logger.error(f"Error analyzing trending topics: {e}")
            return []
    
    def _calculate_engagement_velocity(self, post: RedditPost) -> float:
        """
        Calculate engagement velocity score.
        
        Factors:
        - Upvotes per hour
        - Comments per hour
        - Recency boost
        """
        try:
            # Calculate age in hours
            age_hours = (datetime.utcnow() - post.created_utc).total_seconds() / 3600
            
            if age_hours <= 0:
                age_hours = 0.1  # Minimum age
            
            # Calculate rates
            upvotes_per_hour = post.upvotes / age_hours
            comments_per_hour = post.comment_count / age_hours
            
            # Weight comments more heavily (they indicate active discussion)
            engagement_score = (upvotes_per_hour * 1.0) + (comments_per_hour * 3.0)
            
            # Recency boost (favor recent posts)
            if age_hours < 6:
                engagement_score *= 1.5
            elif age_hours < 12:
                engagement_score *= 1.2
            
            return engagement_score
            
        except Exception as e:
            logger.error(f"Error calculating velocity for post {post.id}: {e}")
            return 0.0
    
    def _group_by_theme(self, posts_with_velocity: List[tuple]) -> Dict[str, List]:
        """
        Group posts by common themes using simple keyword matching.
        
        In a production system, this would use more sophisticated NLP/clustering.
        """
        themes = defaultdict(list)
        
        # Common themes/keywords for AI developer tools
        theme_keywords = {
            "performance": ["slow", "fast", "speed", "performance", "lag", "responsive"],
            "bugs": ["bug", "error", "crash", "issue", "problem", "broken", "not working"],
            "features": ["feature", "new", "update", "release", "announcement", "added"],
            "pricing": ["price", "cost", "expensive", "cheap", "subscription", "free", "paid"],
            "comparison": ["vs", "versus", "compare", "better than", "alternative"],
            "integration": ["integration", "plugin", "extension", "api", "connect"],
            "productivity": ["productivity", "efficient", "workflow", "time-saving"],
            "documentation": ["documentation", "docs", "tutorial", "guide", "learning"],
            "support": ["support", "help", "question", "how to", "assistance"],
        }
        
        for post, velocity in posts_with_velocity:
            title_lower = post.title.lower()
            content_lower = post.content.lower() if post.content else ""
            text = f"{title_lower} {content_lower}"
            
            # Check for theme matches
            matched_themes = []
            for theme, keywords in theme_keywords.items():
                if any(keyword in text for keyword in keywords):
                    matched_themes.append(theme)
            
            # Assign to theme(s)
            if matched_themes:
                for theme in matched_themes:
                    themes[theme].append((post, velocity))
            else:
                # Use subreddit as theme if no keyword match
                themes[f"r/{post.subreddit}"].append((post, velocity))
        
        return themes
    
    def _create_trending_topic(self, theme: str, posts: List[RedditPost], 
                               posts_with_velocity: List[tuple]) -> TrendingTopic:
        """Create a TrendingTopic object from grouped posts."""
        # Generate topic ID using SHA-256 for better collision resistance
        import hashlib
        topic_id = hashlib.sha256(f"{theme}_{datetime.utcnow().date()}".encode()).hexdigest()[:16]
        
        # Collect post IDs
        post_ids = [post.id for post in posts]
        
        # Extract keywords from titles
        keywords = self._extract_keywords(posts, theme)
        
        # Calculate average velocity
        avg_velocity = sum(v for _, v in posts_with_velocity) / len(posts_with_velocity)
        
        # Get sentiment distribution from database
        # Query actual sentiment scores for these posts
        sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
        try:
            for post in posts[:10]:  # Sample top 10
                # This queries the actual sentiment data
                # In a real implementation, we'd batch query for efficiency
                # For now, we'll use a placeholder since sentiment data may not be available
                pass
            # TODO: Implement batch sentiment lookup for efficiency
            # sentiment_scores = db.get_sentiments_for_posts(post_ids[:10])
            # for score in sentiment_scores:
            #     sentiment_dist[score.sentiment] += 1
        except Exception as e:
            logger.warning(f"Could not fetch sentiment distribution: {e}")
        
        # Find peak time (most recent post time)
        peak_time = max(post.created_utc for post in posts)
        
        return TrendingTopic(
            id=topic_id,
            post_ids=post_ids[:10],  # Top 10 posts
            theme=theme.title(),
            keywords=keywords,
            engagement_velocity=avg_velocity,
            sentiment_distribution=sentiment_dist,
            peak_time=peak_time
        )
    
    def _extract_keywords(self, posts: List[RedditPost], theme: str, max_keywords: int = 5) -> List[str]:
        """Extract key terms from post titles."""
        word_freq = defaultdict(int)
        
        # Common stop words to ignore
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "are", "was", "were", "be", "been", "have", "has",
            "had", "do", "does", "did", "will", "would", "could", "should", "may",
            "can", "this", "that", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "my", "your", "his", "her", "its", "our", "their"
        }
        
        for post in posts[:20]:  # Sample first 20
            words = post.title.lower().split()
            for word in words:
                # Clean word
                word = ''.join(c for c in word if c.isalnum())
                if word and word not in stop_words and len(word) > 3:
                    word_freq[word] += 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_words[:max_keywords]]
        
        # Add theme as a keyword if not present
        if theme.lower() not in [k.lower() for k in keywords]:
            keywords.insert(0, theme.lower())
        
        return keywords[:max_keywords]


# Global trending analyzer instance
trending_analyzer = TrendingAnalyzer()
