/**
 * Hot Topics data models for frontend.
 * 
 * These interfaces match the Pydantic models in backend/src/models/hot_topics.py
 * Used for type-safe API communication and component props.
 */

/**
 * Sentiment distribution breakdown for a tool.
 * Represents positive/negative/neutral counts and percentages.
 */
export interface SentimentDistribution {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_percent: number;  // 0-100
  negative_percent: number;  // 0-100
  neutral_percent: number;   // 0-100
}

/**
 * Hot topic representing a trending developer tool.
 * Calculated entity - not stored in database.
 */
export interface HotTopic {
  tool_id: string;
  tool_name: string;
  tool_slug: string;
  engagement_score: number;
  total_mentions: number;
  total_comments: number;
  total_upvotes: number;
  sentiment_distribution: SentimentDistribution;
}

/**
 * Reddit post related to a specific tool.
 * Includes engagement metrics and deep link to Reddit.
 */
export interface RelatedPost {
  post_id: string;
  title: string;
  excerpt: string;  // Max 200 characters
  author: string;
  subreddit: string;
  created_utc: string;  // ISO 8601 datetime
  reddit_url: string;   // Direct link to Reddit post
  comment_count: number;
  upvotes: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  engagement_score: number;
}

/**
 * API response for GET /api/hot-topics
 */
export interface HotTopicsResponse {
  hot_topics: HotTopic[];
  generated_at: string;  // ISO 8601 datetime
  time_range: '24h' | '7d' | '30d';
}

/**
 * API response for GET /api/hot-topics/{tool_id}/posts
 */
export interface RelatedPostsResponse {
  posts: RelatedPost[];
  total: number;
  has_more: boolean;
  offset: number;
  limit: number;
}

/**
 * Time range filter options for hot topics and related posts.
 */
export type TimeRange = '24h' | '7d' | '30d';

/**
 * Query parameters for GET /api/hot-topics
 */
export interface HotTopicsParams {
  time_range?: TimeRange;
  limit?: number;  // 1-50, default 10
}

/**
 * Query parameters for GET /api/hot-topics/{tool_id}/posts
 */
export interface RelatedPostsParams {
  time_range?: TimeRange;
  offset?: number;  // Default 0
  limit?: number;   // 1-100, default 20
}
