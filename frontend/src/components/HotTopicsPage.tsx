import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { HotTopicCard } from './HotTopicCard';
import { RelatedPostsList } from './RelatedPostsList';
import { SimpleTimeRangeFilter } from './SimpleTimeRangeFilter';
import { TimeRange, HotTopic } from '../types/hot-topics';

/**
 * Hot Topics Page Component
 * Displays ranked list of trending developer tools with engagement metrics
 * User Story 1 implementation
 * 
 * Also handles navigation to related posts view (User Story 2)
 */
export const HotTopicsPage: React.FC = () => {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [selectedTool, setSelectedTool] = useState<{ id: string; name: string } | null>(null);

  // Fetch hot topics using React Query
  const {
    data,
    isLoading,
    error,
    isFetching
  } = useQuery({
    queryKey: ['hot-topics', timeRange],
    queryFn: () => api.getHotTopics({ time_range: timeRange, limit: 10 }),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data fresh for 2 minutes
  });

  // Loading skeleton
  const renderSkeleton = () => (
    <div className="space-y-6">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="glass-card border-l-4 border-l-gray-600 p-6 rounded-lg animate-pulse"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-gray-700 rounded"></div>
            <div className="h-8 bg-gray-700 rounded w-48"></div>
          </div>
          <div className="grid grid-cols-4 gap-4">
            <div className="h-16 bg-gray-700 rounded"></div>
            <div className="h-16 bg-gray-700 rounded"></div>
            <div className="h-16 bg-gray-700 rounded"></div>
            <div className="h-16 bg-gray-700 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  );

  // If a tool is selected, show related posts
  if (selectedTool) {
    return (
      <RelatedPostsList
        toolId={selectedTool.id}
        toolName={selectedTool.name}
        onBack={() => setSelectedTool(null)}
      />
    );
  }

  // Error state
  if (error && !data) {
    return (
      <div className="container mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-10 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
          Hot Topics
        </h1>
        <div className="glass-card p-8 text-center">
          <div className="text-red-400 text-xl mb-4">
            Failed to load hot topics
          </div>
          <p className="text-gray-400">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
          Hot Topics
        </h1>
        <p className="text-gray-400 text-lg">
          Trending developer tools ranked by engagement and community sentiment
        </p>
      </div>

      {/* Time Range Filter */}
      <div className="mb-8 flex items-center justify-between">
        <SimpleTimeRangeFilter
          value={timeRange}
          onChange={setTimeRange}
        />
        
        {/* Last updated indicator */}
        {data && (
          <div className="text-sm text-gray-400">
            Generated: {new Date(data.generated_at).toLocaleTimeString()}
            {isFetching && (
              <span className="ml-2 text-emerald-400 animate-pulse">
                • Updating...
              </span>
            )}
          </div>
        )}
      </div>

      {/* Loading state (initial load only) */}
      {isLoading && !data ? (
        renderSkeleton()
      ) : data && data.hot_topics.length > 0 ? (
        // Hot topics list
        <div className="space-y-6 relative">
          {/* Loading overlay for filter changes */}
          {isFetching && (
            <div className="absolute inset-0 bg-dark-bg/50 backdrop-blur-sm z-10 rounded-lg flex items-center justify-center">
              <div className="text-emerald-400 text-lg animate-pulse">
                Loading...
              </div>
            </div>
          )}
          
          {data.hot_topics.map((topic: HotTopic, index: number) => (
            <HotTopicCard
              key={topic.tool_id}
              topic={topic}
              rank={index + 1}
              onClick={() => {
                // Navigate to related posts view
                setSelectedTool({ id: topic.tool_id, name: topic.tool_name });
              }}
            />
          ))}
        </div>
      ) : (
        // Empty state
        <div className="glass-card p-12 text-center">
          <div className="text-gray-400 text-xl mb-2">
            No hot topics found
          </div>
          <p className="text-gray-500">
            {timeRange === '24h' 
              ? 'No trending tools in the last 24 hours. Try a longer time range.'
              : timeRange === '7d'
              ? 'No trending tools in the last 7 days. Check back later.'
              : 'No trending tools in the last 30 days. Check back later.'}
          </p>
        </div>
      )}
    </div>
  );
};
