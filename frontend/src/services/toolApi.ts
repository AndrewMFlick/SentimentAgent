// AI Tools API hooks using react-query
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from './api';

/**
 * Hook to fetch list of approved AI tools
 */
export const useTools = () => {
  return useQuery({
    queryKey: ['tools'],
    queryFn: api.getTools,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: false
  });
};

/**
 * Hook to fetch sentiment data for a specific tool
 * 
 * @param toolId - Tool identifier
 * @param options - Query options (hours, startDate, endDate)
 */
export const useToolSentiment = (
  toolId: string | null,
  options?: {
    hours?: number;
    startDate?: string;
    endDate?: string;
  }
) => {
  return useQuery({
    queryKey: ['toolSentiment', toolId, options],
    queryFn: () => {
      if (!toolId) throw new Error('Tool ID is required');
      return api.getToolSentiment(toolId, options);
    },
    enabled: !!toolId,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000 // Poll every 60 seconds
  });
};

/**
 * Hook to compare sentiment data for multiple tools
 * 
 * @param toolIds - Array of tool identifiers to compare
 * @param options - Query options (hours, startDate, endDate)
 */
export const useToolComparison = (
  toolIds: string[],
  options?: {
    hours?: number;
    startDate?: string;
    endDate?: string;
  }
) => {
  return useQuery({
    queryKey: ['toolComparison', toolIds, options],
    queryFn: () => api.compareTools(toolIds, options),
    enabled: toolIds.length >= 2,
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000 // Poll every 60 seconds
  });
};

/**
 * Hook to fetch time series data for a specific tool
 * 
 * @param toolId - Tool identifier
 * @param startDate - Start date (YYYY-MM-DD)
 * @param endDate - End date (YYYY-MM-DD)
 * @param granularity - Time granularity (default: 'daily')
 */
export const useTimeSeries = (
  toolId: string | null,
  startDate: string,
  endDate: string,
  granularity: string = 'daily'
) => {
  return useQuery({
    queryKey: ['timeSeries', toolId, startDate, endDate, granularity],
    queryFn: () => {
      if (!toolId) throw new Error('Tool ID is required');
      return api.getToolTimeSeries(
        toolId,
        startDate,
        endDate,
        granularity
      );
    },
    enabled: !!toolId && !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes (data is historical)
    refetchInterval: false // Don't auto-refetch for historical data
  });
};

/**
 * Hook to manage time range state across dashboard components
 * Returns time range value and setter function
 */
export type TimeRangePreset = '24h' | '7d' | '30d' | '90d' | 'custom';

export interface TimeRangeValue {
  preset: TimeRangePreset;
  startDate?: string;
  endDate?: string;
  hours?: number;
}

export const useTimeRange = (
  initialPreset: TimeRangePreset = '24h'
) => {
  const [timeRange, setTimeRange] = useState<TimeRangeValue>({
    preset: initialPreset,
    hours: initialPreset === '24h' ? 24 : undefined
  });

  return {
    timeRange,
    setTimeRange
  };
};

/**
 * Hook to check for data updates
 * Polls the last_updated endpoint every 60 seconds
 */
export const useLastUpdated = () => {
  return useQuery({
    queryKey: ['lastUpdated'],
    queryFn: api.getLastUpdated,
    staleTime: 0, // Always refetch
    refetchInterval: 60 * 1000 // Poll every 60 seconds
  });
};

// ============================================================================
// ADMIN HOOKS
// ============================================================================

/**
 * Hook to fetch pending tools awaiting admin approval
 * 
 * @param adminToken - Admin authentication token
 */
export const usePendingTools = (adminToken: string | null) => {
  return useQuery({
    queryKey: ['pendingTools', adminToken],
    queryFn: () => {
      if (!adminToken) throw new Error('Admin token is required');
      return api.getPendingTools(adminToken);
    },
    enabled: !!adminToken,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000 // Poll every 30 seconds
  });
};

/**
 * Hook to approve a pending tool
 * 
 * @param adminToken - Admin authentication token
 */
export const useApproveTool = (adminToken: string | null) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const approveTool = async (toolId: string) => {
    if (!adminToken) {
      setError('Admin token is required');
      return null;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.approveTool(toolId, adminToken);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to approve tool';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { approveTool, isLoading, error };
};

/**
 * Hook to reject a pending tool
 * 
 * @param adminToken - Admin authentication token
 */
export const useRejectTool = (adminToken: string | null) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const rejectTool = async (toolId: string) => {
    if (!adminToken) {
      setError('Admin token is required');
      return null;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.rejectTool(toolId, adminToken);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reject tool';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { rejectTool, isLoading, error };
};

/**
 * Hook to link a tool as an alias of another primary tool
 * 
 * @param adminToken - Admin authentication token
 */
export const useLinkAlias = (adminToken: string | null) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const linkAlias = async (aliasToolId: string, primaryToolId: string) => {
    if (!adminToken) {
      setError('Admin token is required');
      return null;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.linkAlias(aliasToolId, primaryToolId, adminToken);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to link alias';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { linkAlias, isLoading, error };
};

/**
 * Hook to unlink a tool alias
 * 
 * @param adminToken - Admin authentication token
 */
export const useUnlinkAlias = (adminToken: string | null) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const unlinkAlias = async (aliasToolId: string) => {
    if (!adminToken) {
      setError('Admin token is required');
      return null;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.unlinkAlias(aliasToolId, adminToken);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to unlink alias';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };
  
  return { unlinkAlias, isLoading, error };
};

/**
 * Hook to fetch all tools for admin management
 * 
 * @param adminToken - Admin authentication token
 */
export const useAllToolsAdmin = (adminToken: string | null) => {
  return useQuery({
    queryKey: ['allToolsAdmin', adminToken],
    queryFn: () => {
      if (!adminToken) throw new Error('Admin token is required');
      return api.getAllToolsAdmin(adminToken);
    },
    enabled: !!adminToken,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: false
  });
};
