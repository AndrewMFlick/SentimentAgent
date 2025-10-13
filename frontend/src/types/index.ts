"""TypeScript type definitions."""

export interface RedditPost {
  id: string;
  subreddit: string;
  author: string;
  title: string;
  content: string;
  url: string;
  created_utc: string;
  upvotes: number;
  comment_count: number;
  collected_at: string;
}

export interface SentimentScore {
  content_id: string;
  content_type: 'post' | 'comment';
  subreddit: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence: number;
  compound_score: number;
  positive_score: number;
  negative_score: number;
  neutral_score: number;
  analysis_method: 'VADER' | 'LLM';
  analyzed_at: string;
}

export interface SentimentStats {
  total: number;
  positive: number;
  negative: number;
  neutral: number;
  avg_sentiment: number;
}

export interface TrendingTopic {
  id: string;
  post_ids: string[];
  theme: string;
  keywords: string[];
  engagement_velocity: number;
  sentiment_distribution: {
    [key: string]: number;
  };
  peak_time: string;
  created_at: string;
}

export interface DashboardData {
  subreddit: string;
  time_window_hours: number;
  statistics: SentimentStats;
  timestamp: string;
}
