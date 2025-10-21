import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { TrendingTopic } from '../types';
import { formatDistanceToNow } from 'date-fns';

export const HotTopics: React.FC = () => {
  const [topics, setTopics] = useState<TrendingTopic[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTopics();
    // Refresh every 5 minutes
    const interval = setInterval(loadTopics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadTopics = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getTrendingTopics(20);
      setTopics(result);
    } catch (err) {
      setError('Failed to load trending topics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && topics.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-300">Loading hot topics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-400">{error}</div>
      </div>
    );
  }

  const getSentimentColor = (distribution: { [key: string]: number }) => {
    const total = Object.values(distribution).reduce((sum, val) => sum + val, 0);
    if (total === 0) return 'glass-card bg-gray-800/50 border-l-gray-500';
    
    const positive = (distribution.positive || 0) / total;
    const negative = (distribution.negative || 0) / total;
    
    if (positive > negative * 1.5) return 'glass-card bg-emerald-900/20 border-l-emerald-500';
    if (negative > positive * 1.5) return 'glass-card bg-red-900/20 border-l-red-500';
    return 'glass-card bg-amber-900/20 border-l-amber-500';
  };

  return (
    <div className="container mx-auto px-6 py-12">
      <h1 className="text-4xl font-bold mb-10 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">Hot Topics</h1>

      {topics.length === 0 ? (
        <div className="text-center text-gray-400 mt-12">
          <p className="text-xl">No trending topics found</p>
          <p className="mt-2">Check back later for trending discussions</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {topics.map((topic, index) => (
            <div
              key={topic.id}
              className={`border-l-4 p-6 rounded-lg shadow-md ${getSentimentColor(topic.sentiment_distribution)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-2">
                    <span className="text-2xl font-bold text-gray-200">#{index + 1}</span>
                    <h2 className="text-xl font-bold">{topic.theme}</h2>
                  </div>
                  
                  {topic.keywords.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-2">
                      {topic.keywords.map(keyword => (
                        <span
                          key={keyword}
                          className="bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div>
                      <p className="text-sm text-gray-400">Engagement Score</p>
                      <p className="text-lg font-semibold">{topic.engagement_velocity.toFixed(2)}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-400">Related Posts</p>
                      <p className="text-lg font-semibold">{topic.post_ids.length}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-400">Peak Activity</p>
                      <p className="text-lg font-semibold">
                        {formatDistanceToNow(new Date(topic.peak_time), { addSuffix: true })}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-sm text-gray-400">Sentiment</p>
                      <div className="flex gap-2 mt-1">
                        <span className="text-green-600 font-semibold">
                          👍 {topic.sentiment_distribution.positive || 0}
                        </span>
                        <span className="text-red-600 font-semibold">
                          👎 {topic.sentiment_distribution.negative || 0}
                        </span>
                        <span className="text-gray-400 font-semibold">
                          😐 {topic.sentiment_distribution.neutral || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
