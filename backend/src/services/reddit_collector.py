"""Reddit data collector service."""
import logging
from datetime import datetime
from typing import List
import praw
from praw.models import Submission, Comment

from ..config import settings
from ..models import RedditPost, RedditComment

logger = logging.getLogger(__name__)


class RedditCollector:
    """Collects data from Reddit using PRAW."""
    
    def __init__(self):
        """Initialize Reddit API client."""
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent
        )
        logger.info("Reddit collector initialized")
    
    def collect_posts(self, subreddit_name: str, limit: int = 100) -> List[RedditPost]:
        """
        Collect recent posts from a subreddit.
        
        Args:
            subreddit_name: Name of the subreddit
            limit: Maximum number of posts to collect
            
        Returns:
            List of RedditPost objects
        """
        posts = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for submission in subreddit.new(limit=limit):
                try:
                    post = self._submission_to_post(submission, subreddit_name)
                    posts.append(post)
                except Exception as e:
                    logger.error(f"Error processing post {submission.id}: {e}")
                    continue
            
            logger.info(f"Collected {len(posts)} posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error collecting from r/{subreddit_name}: {e}")
        
        return posts
    
    def collect_comments(self, post_id: str, limit: int = 100) -> List[RedditComment]:
        """
        Collect comments from a post.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to collect
            
        Returns:
            List of RedditComment objects
        """
        comments = []
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove MoreComments objects
            
            for comment in submission.comments.list()[:limit]:
                try:
                    comment_obj = self._comment_to_model(comment, post_id)
                    comments.append(comment_obj)
                except Exception as e:
                    logger.error(f"Error processing comment {comment.id}: {e}")
                    continue
            
            logger.debug(f"Collected {len(comments)} comments from post {post_id}")
            
        except Exception as e:
            logger.error(f"Error collecting comments for post {post_id}: {e}")
        
        return comments
    
    def _submission_to_post(self, submission: Submission, subreddit_name: str) -> RedditPost:
        """Convert PRAW submission to RedditPost."""
        return RedditPost(
            id=submission.id,
            subreddit=subreddit_name,
            author=str(submission.author) if submission.author else "[deleted]",
            title=submission.title,
            content=submission.selftext or "",
            url=submission.url,
            created_utc=datetime.fromtimestamp(submission.created_utc),
            upvotes=submission.score,
            comment_count=submission.num_comments,
        )
    
    def _comment_to_model(self, comment: Comment, post_id: str) -> RedditComment:
        """Convert PRAW comment to RedditComment."""
        parent_id = None
        if hasattr(comment, 'parent_id') and not comment.parent_id.startswith('t3_'):
            parent_id = comment.parent_id.replace('t1_', '')
        
        return RedditComment(
            id=comment.id,
            post_id=post_id,
            parent_id=parent_id,
            author=str(comment.author) if comment.author else "[deleted]",
            content=comment.body,
            created_utc=datetime.fromtimestamp(comment.created_utc),
            upvotes=comment.score,
        )
