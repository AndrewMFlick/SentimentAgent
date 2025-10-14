import axios from 'axios';
import { DashboardData, RedditPost, TrendingTopic } from '../types';

const API_BASE_URL = '/api/v1';

export const api = {
  // Sentiment endpoints
  getSentimentStats: async (subreddit?: string, hours: number = 24): Promise<DashboardData> => {
    const params = new URLSearchParams();
    if (subreddit) params.append('subreddit', subreddit);
    params.append('hours', hours.toString());
    
    const response = await axios.get(`${API_BASE_URL}/sentiment/stats?${params}`);
    return response.data;
  },

  getSentimentTrends: async (subreddit?: string, hours: number = 168): Promise<DashboardData> => {
    const params = new URLSearchParams();
    if (subreddit) params.append('subreddit', subreddit);
    params.append('hours', hours.toString());
    
    const response = await axios.get(`${API_BASE_URL}/sentiment/trends?${params}`);
    return response.data;
  },

  // Posts endpoints
  getRecentPosts: async (subreddit?: string, hours: number = 24, limit: number = 100): Promise<RedditPost[]> => {
    const params = new URLSearchParams();
    if (subreddit) params.append('subreddit', subreddit);
    params.append('hours', hours.toString());
    params.append('limit', limit.toString());
    
    const response = await axios.get(`${API_BASE_URL}/posts/recent?${params}`);
    return response.data;
  },

  // Trending endpoints
  getTrendingTopics: async (limit: number = 20): Promise<TrendingTopic[]> => {
    const response = await axios.get(`${API_BASE_URL}/trending?limit=${limit}`);
    return response.data;
  },

  // Subreddits
  getMonitoredSubreddits: async (): Promise<{ subreddits: string[]; count: number }> => {
    const response = await axios.get(`${API_BASE_URL}/subreddits`);
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  }
};
