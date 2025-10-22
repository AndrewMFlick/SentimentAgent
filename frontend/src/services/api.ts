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
  },

  // =========================================================================
  // Admin Tool Management endpoints
  // =========================================================================

  /**
   * Create a new AI tool
   * @param toolData - Tool creation data
   * @param adminToken - Admin authentication token
   */
  createTool: async (toolData: any, adminToken: string): Promise<{ tool: any; message: string }> => {
    const response = await axios.post(
      `${API_BASE_URL}/admin/tools`,
      toolData,
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * List all tools with pagination and filtering
   * @param options - Query parameters for filtering and pagination
   * @param adminToken - Admin authentication token
   */
  listAdminTools: async (
    options: {
      page?: number;
      limit?: number;
      search?: string;
      status?: string;
      category?: string[];
      vendor?: string;
      sort_by?: string;
      sort_order?: 'asc' | 'desc';
    } = {},
    adminToken: string
  ): Promise<{
    tools: any[];
    pagination: {
      page: number;
      limit: number;
      total_items: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    };
    filters_applied: {
      status?: string;
      categories?: string[];
      vendor?: string;
      search?: string;
      sort_by?: string;
      sort_order?: string;
    };
  }> => {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.search) params.append('search', options.search);
    if (options.status) params.append('status', options.status);
    if (options.category && options.category.length > 0) {
      params.append('category', options.category.join(','));
    }
    if (options.vendor) params.append('vendor', options.vendor);
    if (options.sort_by) params.append('sort_by', options.sort_by);
    if (options.sort_order) params.append('sort_order', options.sort_order);

    const response = await axios.get(
      `${API_BASE_URL}/admin/tools?${params}`,
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * Get tool details
   * @param toolId - Tool identifier
   * @param adminToken - Admin authentication token
   */
  getToolDetails: async (toolId: string, adminToken: string): Promise<any> => {
    const response = await axios.get(
      `${API_BASE_URL}/admin/tools/${toolId}`,
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * Update a tool with optimistic concurrency control
   * @param toolId - Tool identifier
   * @param updates - Fields to update
   * @param adminToken - Admin authentication token
   * @param etag - Optional ETag for optimistic concurrency (If-Match header)
   */
  updateTool: async (
    toolId: string,
    updates: any,
    adminToken: string,
    etag?: string
  ): Promise<{ tool: any; message: string }> => {
    const headers: Record<string, string> = {
      'X-Admin-Token': adminToken
    };

    // Add ETag header if provided for optimistic concurrency control
    if (etag) {
      headers['If-Match'] = etag;
    }

    const response = await axios.put(
      `${API_BASE_URL}/admin/tools/${toolId}`,
      updates,
      {
        headers
      }
    );
    return response.data;
  },

  /**
   * Delete a tool (soft delete)
   * @param toolId - Tool identifier
   * @param adminToken - Admin authentication token
   */
  deleteTool: async (toolId: string, adminToken: string): Promise<{ message: string }> => {
    const response = await axios.delete(
      `${API_BASE_URL}/admin/tools/${toolId}`,
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * Link a tool as an alias to another tool
   * @param aliasToolId - Tool ID to set as alias
   * @param primaryToolId - Primary tool ID
   * @param adminToken - Admin authentication token
   */
  linkAlias: async (aliasToolId: string, primaryToolId: string, adminToken: string): Promise<{ alias: any; message: string }> => {
    const response = await axios.put(
      `${API_BASE_URL}/admin/tools/${aliasToolId}/alias`,
      { primary_tool_id: primaryToolId },
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  },

  /**
   * Remove alias relationship
   * @param aliasToolId - Alias tool ID
   * @param adminToken - Admin authentication token
   */
  unlinkAlias: async (aliasToolId: string, adminToken: string): Promise<{ message: string }> => {
    const response = await axios.delete(
      `${API_BASE_URL}/admin/tools/${aliasToolId}/alias`,
      {
        headers: {
          'X-Admin-Token': adminToken
        }
      }
    );
    return response.data;
  }
};
