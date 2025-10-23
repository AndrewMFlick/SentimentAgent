import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { RelatedPostCard } from './RelatedPostCard';
import { SimpleTimeRangeFilter } from './SimpleTimeRangeFilter';
import { TimeRange, RelatedPost, RelatedPostsResponse } from '../types/hot-topics';
import { ToastContainer } from './Toast';
import { useToast } from '../hooks/useToast';

interface RelatedPostsListProps {
  toolId: string;
  toolName: string;
  onBack?: () => void;
}

/**
 * RelatedPostsList Component
 * Displays paginated list of related posts for a tool with "Load More" functionality
 * User Story 2 implementation
 */
export const RelatedPostsList: React.FC<RelatedPostsListProps> = ({
  toolId,
  toolName,
  onBack,
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [offset, setOffset] = useState(0);
  const [allPosts, setAllPosts] = useState<RelatedPost[]>([]);
  const limit = 20;
  const toast = useToast();

  // Fetch related posts
  const {
    data,
    isLoading,
    error,
    isFetching,
    refetch,
  } = useQuery<RelatedPostsResponse>({
    queryKey: ['related-posts', toolId, timeRange, offset],
    queryFn: () => api.getRelatedPosts(toolId, {
      time_range: timeRange,
      offset: offset,
      limit: limit,
    }),
    retry: 2,
  });

  // Show error toasts
  useEffect(() => {
    if (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      
      if (errorMessage.includes('404')) {
        toast.warning('Related posts endpoint not found. Please check the API configuration.');
      } else if (errorMessage.includes('Network') || errorMessage.includes('timeout')) {
        toast.error('Network error. Please check your internet connection and try again.');
      } else if (errorMessage.includes('500')) {
        toast.error('Server error. The service is experiencing issues. Please try again later.');
      } else {
        toast.error(`Failed to load related posts: ${errorMessage}`);
      }
    }
  }, [error, toast]);

  // Update allPosts when data changes
  useEffect(() => {
    if (data) {
      if (offset === 0) {
        // First page - replace all posts
        setAllPosts(data.posts);
      } else {
        // Subsequent pages - append posts
        setAllPosts(prev => [...prev, ...data.posts]);
      }
    }
  }, [data, offset]);

  // Handle time range change - reset pagination
  const handleTimeRangeChange = (newTimeRange: TimeRange) => {
    setTimeRange(newTimeRange);
    setOffset(0);
    setAllPosts([]);
  };

  // Handle Load More
  const handleLoadMore = () => {
    if (data?.has_more) {
      setOffset(prev => prev + limit);
    }
  };

  // Loading skeleton
  const renderSkeleton = () => (
    <div className="space-y-6">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="glass-card p-6 rounded-lg animate-pulse"
        >
          <div className="h-6 bg-gray-700 rounded w-3/4 mb-3"></div>
          <div className="h-4 bg-gray-700 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-2/3 mb-4"></div>
          <div className="flex gap-4">
            <div className="h-4 bg-gray-700 rounded w-24"></div>
            <div className="h-4 bg-gray-700 rounded w-24"></div>
            <div className="h-4 bg-gray-700 rounded w-24"></div>
          </div>
        </div>
      ))}
    </div>
  );

  // Error state
  if (error && !data) {
    return (
      <div className="container mx-auto px-6 py-12">
        <ToastContainer toasts={toast.toasts} onRemove={toast.removeToast} />
        
        {onBack && (
          <button
            onClick={onBack}
            className="mb-6 inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none rounded-md px-2 py-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Hot Topics
          </button>
        )}
        
        <div className="glass-card p-8 text-center">
          <div className="text-red-400 text-xl mb-4">
            Failed to load related posts
          </div>
          <p className="text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => refetch()}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
            >
              Retry
            </button>
            {onBack && (
              <button
                onClick={onBack}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:outline-none"
              >
                Go Back
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (data && data.total === 0 && !isLoading) {
    return (
      <div className="container mx-auto px-6 py-12">
        {onBack && (
          <button
            onClick={onBack}
            className="mb-6 inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Hot Topics
          </button>
        )}

        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
          Related Posts: {toolName}
        </h1>

        <div className="mb-8">
          <SimpleTimeRangeFilter
            value={timeRange}
            onChange={handleTimeRangeChange}
          />
        </div>

        <div className="glass-card p-8 text-center">
          <p className="text-gray-400">
            No posts found for this tool in the selected time range.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12">
      <ToastContainer toasts={toast.toasts} onRemove={toast.removeToast} />
      
      {/* Back button */}
      {onBack && (
        <button
          onClick={onBack}
          className="mb-6 inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Hot Topics
        </button>
      )}

      {/* Header */}
      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
          Related Posts: {toolName}
        </h1>
        <p className="text-gray-400 text-lg">
          Reddit posts mentioning this tool, sorted by engagement
        </p>
      </div>

      {/* Time Range Filter and Stats */}
      <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
        <SimpleTimeRangeFilter
          value={timeRange}
          onChange={handleTimeRangeChange}
        />
        
        {data && (
          <div className="text-sm text-gray-400">
            Showing {allPosts.length} of {data.total} posts
            {isFetching && offset > 0 && (
              <span className="ml-2 text-emerald-400">Loading...</span>
            )}
          </div>
        )}
      </div>

      {/* Posts List */}
      {isLoading && offset === 0 ? (
        renderSkeleton()
      ) : (
        <>
          <div className="space-y-6">
            {allPosts.map((post) => (
              <RelatedPostCard key={post.post_id} post={post} />
            ))}
          </div>

          {/* Load More Button */}
          {data?.has_more && (
            <div className="mt-8 text-center">
              <button
                onClick={handleLoadMore}
                disabled={isFetching}
                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors inline-flex items-center gap-2"
              >
                {isFetching && offset > 0 ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading...
                  </>
                ) : (
                  <>
                    Load More
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          )}

          {/* End of results message */}
          {data && !data.has_more && allPosts.length > 0 && (
            <div className="mt-8 text-center text-gray-400 text-sm">
              You've reached the end of the list
            </div>
          )}
        </>
      )}
    </div>
  );
};
