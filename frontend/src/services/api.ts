import axios from 'axios';
import {
  DashboardData,
  RedditPost,
  TrendingTopic,
  AITool,
  ToolSentiment,
  ToolComparison,
  ToolTimeSeries,
  LastUpdated,
  PendingTool
} from '../types';

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

  // AI Tools endpoints
  getTools: async (): Promise<{ tools: AITool[] }> => {
    const response = await axios.get(`${API_BASE_URL}/tools`);
    return response.data;
  },

  getToolSentiment: async (
    toolId: string,
    options?: {
      hours?: number;
      startDate?: string;
      endDate?: string;
    }
  ): Promise<ToolSentiment> => {
    const params = new URLSearchParams();
    if (options?.hours) {
      params.append('hours', options.hours.toString());
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }
    
    const response = await axios.get(
      `${API_BASE_URL}/tools/${toolId}/sentiment?${params}`
    );
    return response.data;
  },

  compareTools: async (
    toolIds: string[],
    options?: {
      hours?: number;
      startDate?: string;
      endDate?: string;
    }
  ): Promise<ToolComparison> => {
    const params = new URLSearchParams();
    params.append('tool_ids', toolIds.join(','));
    
    if (options?.hours) {
      params.append('hours', options.hours.toString());
    }
    if (options?.startDate) {
      params.append('start_date', options.startDate);
    }
    if (options?.endDate) {
      params.append('end_date', options.endDate);
    }
    
    const response = await axios.get(
      `${API_BASE_URL}/tools/compare?${params}`
    );
    return response.data;
  },

  getToolTimeSeries: async (
    toolId: string,
    startDate: string,
    endDate: string,
    granularity: string = 'daily'
  ): Promise<ToolTimeSeries> => {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    params.append('granularity', granularity);
    
    const response = await axios.get(
      `${API_BASE_URL}/tools/${toolId}/timeseries?${params}`
    );
    return response.data;
  },

  getLastUpdated: async (): Promise<LastUpdated> => {
    const response = await axios.get(`${API_BASE_URL}/tools/last_updated`);
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
  },

  // =========================================================================
  // Admin endpoints
  // =========================================================================

  /**
   * Get pending tools awaiting admin approval
   * @param adminToken - Admin authentication token
   */
  getPendingTools: async (adminToken: string): Promise<{ tools: PendingTool[]; count: number }> => {
    const response = await axios.get(`${API_BASE_URL}/admin/tools/pending`, {
      headers: {
        'X-Admin-Token': adminToken
      }
    });
    return response.data;
  },

  /**
   * Approve a pending tool
   * @param toolId - Tool identifier
   * @param adminToken - Admin authentication token
   */
  approveTool: async (toolId: string, adminToken: string): Promise<{ tool: AITool; message: string }> => {
    const response = await axios.post(
      `${API_BASE_URL}/admin/tools/${toolId}/approve`,
      {},
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * Reject a pending tool
   * @param toolId - Tool identifier
   * @param adminToken - Admin authentication token
   */
  rejectTool: async (toolId: string, adminToken: string): Promise<{ tool: AITool; message: string }> => {
    const response = await axios.post(
      `${API_BASE_URL}/admin/tools/${toolId}/reject`,
      {},
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  }
};
