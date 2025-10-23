import React from 'react';
import { RelatedPost } from '../types/hot-topics';

interface RelatedPostCardProps {
  post: RelatedPost;
}

/**
 * RelatedPostCard Component
 * Displays a single Reddit post with metadata and deep link
 * User Story 2 implementation
 */
export const RelatedPostCard: React.FC<RelatedPostCardProps> = ({ post }) => {
  // Format timestamp
  const formatTimestamp = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return 'less than an hour ago';
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 30) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  // Get sentiment color
  const getSentimentColor = (): string => {
    switch (post.sentiment) {
      case 'positive':
        return 'text-emerald-400';
      case 'negative':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  // Get sentiment icon
  const getSentimentIcon = (): string => {
    switch (post.sentiment) {
      case 'positive':
        return '👍';
      case 'negative':
        return '👎';
      default:
        return '➖';
    }
  };

  return (
    <article className="glass-card p-6 rounded-lg hover:scale-[1.01] transition-transform">
      {/* Header: Title and Sentiment */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="text-lg font-semibold text-white flex-1">
          <a 
            href={post.reddit_url}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-emerald-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-bg rounded"
            aria-label={`Reddit post: ${post.title}`}
          >
            {post.title}
          </a>
        </h3>
        <span 
          className={`${getSentimentColor()} text-2xl flex-shrink-0`} 
          role="img"
          aria-label={`Sentiment: ${post.sentiment}`}
          title={post.sentiment}
        >
          {getSentimentIcon()}
        </span>
      </div>

      {/* Excerpt */}
      {post.excerpt && (
        <p className="text-gray-400 text-sm mb-4 line-clamp-3">
          {post.excerpt}
        </p>
      )}

      {/* Metadata Row */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400">
        {/* Subreddit */}
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">r/</span>
          <span className="text-gray-300">{post.subreddit}</span>
        </div>

        {/* Author */}
        <div className="flex items-center gap-1.5">
          <span className="text-gray-500">by</span>
          <span className="text-gray-300">u/{post.author}</span>
        </div>

        {/* Timestamp */}
        <div className="text-gray-400">
          {formatTimestamp(post.created_utc)}
        </div>

        {/* Engagement metrics */}
        <div className="flex items-center gap-3 ml-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">💬</span>
            <span className="text-gray-300">{post.comment_count}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">⬆️</span>
            <span className="text-gray-300">{post.upvotes}</span>
          </div>
        </div>
      </div>

      {/* Link indicator */}
      <div className="mt-3 pt-3 border-t border-white/10">
        <a
          href={post.reddit_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm text-emerald-400 hover:text-emerald-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-bg rounded"
          aria-label="Open post on Reddit in new tab"
        >
          <span>View on Reddit</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </article>
  );
};
