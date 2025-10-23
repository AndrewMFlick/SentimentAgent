import React from 'react';
import { HotTopic } from '../types/hot-topics';

interface HotTopicCardProps {
  topic: HotTopic;
  rank: number;
  onClick?: () => void;
}

export const HotTopicCard: React.FC<HotTopicCardProps> = ({ topic, rank, onClick }) => {
  const { 
    tool_name, 
    engagement_score, 
    total_mentions, 
    total_comments, 
    total_upvotes,
    sentiment_distribution 
  } = topic;

  // Determine dominant sentiment for border color
  const getDominantSentiment = () => {
    const { positive_percent, negative_percent, neutral_percent } = sentiment_distribution;
    const max = Math.max(positive_percent, negative_percent, neutral_percent);
    
    if (positive_percent === max && positive_percent > 40) return 'positive';
    if (negative_percent === max && negative_percent > 40) return 'negative';
    return 'neutral';
  };

  const sentimentType = getDominantSentiment();

  const borderColorClass = {
    positive: 'border-l-emerald-500 bg-emerald-900/10',
    negative: 'border-l-red-500 bg-red-900/10',
    neutral: 'border-l-amber-500 bg-amber-900/10'
  }[sentimentType];

  return (
    <article
      className={`glass-card border-l-4 ${borderColorClass} p-6 rounded-lg shadow-md hover:scale-[1.02] transition-transform cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-bg`}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${tool_name}, ranked #${rank} with ${engagement_score} engagement score`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* Header with rank and tool name */}
          <div className="flex items-center gap-4 mb-3">
            <span className="text-3xl font-bold text-gray-400">#{rank}</span>
            <h2 className="text-2xl font-bold text-white">{tool_name}</h2>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            {/* Engagement Score */}
            <div>
              <p className="text-sm text-gray-400">Engagement Score</p>
              <p className="text-2xl font-bold text-emerald-400">
                {engagement_score.toLocaleString()}
              </p>
            </div>

            {/* Total Mentions */}
            <div>
              <p className="text-sm text-gray-400">Mentions</p>
              <p className="text-xl font-semibold text-gray-200">
                {total_mentions.toLocaleString()}
              </p>
            </div>

            {/* Total Comments */}
            <div>
              <p className="text-sm text-gray-400">Comments</p>
              <p className="text-xl font-semibold text-gray-200">
                {total_comments.toLocaleString()}
              </p>
            </div>

            {/* Total Upvotes */}
            <div>
              <p className="text-sm text-gray-400">Upvotes</p>
              <p className="text-xl font-semibold text-gray-200">
                {total_upvotes.toLocaleString()}
              </p>
            </div>
          </div>

          {/* Sentiment Distribution */}
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-sm text-gray-400 mb-2">Sentiment Distribution</p>
            <div className="flex gap-4" role="list" aria-label="Sentiment breakdown">
              {/* Positive */}
              <div className="flex items-center gap-2" role="listitem">
                <div 
                  className="w-3 h-3 rounded-full bg-emerald-500"
                  aria-hidden="true"
                ></div>
                <span className="text-emerald-400 font-semibold" aria-label={`Positive: ${sentiment_distribution.positive_percent.toFixed(1)} percent`}>
                  {sentiment_distribution.positive_percent.toFixed(1)}%
                </span>
                <span className="text-gray-500 text-sm" aria-label={`${sentiment_distribution.positive_count} positive mentions`}>
                  ({sentiment_distribution.positive_count})
                </span>
              </div>

              {/* Negative */}
              <div className="flex items-center gap-2" role="listitem">
                <div 
                  className="w-3 h-3 rounded-full bg-red-500"
                  aria-hidden="true"
                ></div>
                <span className="text-red-400 font-semibold" aria-label={`Negative: ${sentiment_distribution.negative_percent.toFixed(1)} percent`}>
                  {sentiment_distribution.negative_percent.toFixed(1)}%
                </span>
                <span className="text-gray-500 text-sm" aria-label={`${sentiment_distribution.negative_count} negative mentions`}>
                  ({sentiment_distribution.negative_count})
                </span>
              </div>

              {/* Neutral */}
              <div className="flex items-center gap-2" role="listitem">
                <div 
                  className="w-3 h-3 rounded-full bg-gray-500"
                  aria-hidden="true"
                ></div>
                <span className="text-gray-400 font-semibold" aria-label={`Neutral: ${sentiment_distribution.neutral_percent.toFixed(1)} percent`}>
                  {sentiment_distribution.neutral_percent.toFixed(1)}%
                </span>
                <span className="text-gray-500 text-sm" aria-label={`${sentiment_distribution.neutral_count} neutral mentions`}>
                  ({sentiment_distribution.neutral_count})
                </span>
              </div>
            </div>

            {/* Sentiment Bar */}
            <div 
              className="mt-3 h-2 bg-gray-800 rounded-full overflow-hidden flex"
              role="img"
              aria-label={`Sentiment distribution: ${sentiment_distribution.positive_percent.toFixed(1)}% positive, ${sentiment_distribution.negative_percent.toFixed(1)}% negative, ${sentiment_distribution.neutral_percent.toFixed(1)}% neutral`}
            >
              <div
                className="bg-emerald-500"
                style={{ width: `${sentiment_distribution.positive_percent}%` }}
              ></div>
              <div
                className="bg-red-500"
                style={{ width: `${sentiment_distribution.negative_percent}%` }}
              ></div>
              <div
                className="bg-gray-500"
                style={{ width: `${sentiment_distribution.neutral_percent}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};
