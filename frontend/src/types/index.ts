// TypeScript type definitions

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

// AI Tools Feature Types
export interface AITool {
  id: string;
  name: string;
  vendor: string;
  category: string;
  aliases: string[];
  status: 'pending' | 'approved' | 'rejected';
  detection_threshold: number;
  approved_by?: string;
  approved_at?: string;
  rejected_by?: string;
  rejected_at?: string;
  created_at: string;
}

export interface ToolSentiment {
  tool_id: string;
  tool_name: string;
  total_mentions: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  avg_sentiment: number;
  time_period: {
    start: string;
    end: string;
  };
}

export interface ToolComparison {
  tools: ToolSentiment[];
  deltas: {
    tool_a_id: string;
    tool_b_id: string;
    positive_delta: number;
    negative_delta: number;
    sentiment_delta: number;
  }[];
}

export interface TimeSeriesPoint {
  date: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  avg_sentiment: number;
  total_mentions: number;
}

export interface ToolTimeSeries {
  tool_id: string;
  tool_name: string;
  time_period: {
    start: string;
    end: string;
  };
  granularity: 'daily' | 'weekly' | 'monthly';
  data_points: TimeSeriesPoint[];
}

export interface PendingTool extends AITool {
  description?: string;
  mention_count_7d: number;
  first_detected: string;
  sample_mentions?: string[];
}

export interface LastUpdated {
  last_aggregation: string;
  last_detection: string;
}

// Tool Management Feature Types (Admin)
export enum ToolCategory {
  CODE_ASSISTANT = 'code_assistant',
  CHATBOT = 'chatbot',
  IMAGE_GENERATION = 'image_generation',
  WRITING = 'writing',
  PRODUCTIVITY = 'productivity',
  OTHER = 'other'
}

export enum ToolStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  DELETED = 'deleted'
}

export interface Tool {
  id: string;
  partitionKey: string;
  name: string;
  slug: string;
  vendor: string;
  category: ToolCategory;
  description: string;
  status: ToolStatus;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ToolAlias {
  id: string;
  partitionKey: string;
  alias_tool_id: string;
  primary_tool_id: string;
  created_at: string;
  created_by: string;
}

export interface ToolCreateRequest {
  name: string;
  vendor: string;
  category: ToolCategory;
  description?: string;
  metadata?: Record<string, any>;
}

export interface ToolUpdateRequest {
  name?: string;
  vendor?: string;
  category?: ToolCategory;
  description?: string;
  status?: ToolStatus;
  metadata?: Record<string, any>;
}

export interface AliasLinkRequest {
  alias_tool_id: string;
  primary_tool_id: string;
}

export interface ToolResponse {
  tool: Tool;
  aliases: ToolAlias[];
}

export interface ToolListResponse {
  tools: Tool[];
  total: number;
  page: number;
  limit: number;
}
