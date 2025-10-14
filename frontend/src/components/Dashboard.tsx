import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardData } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = {
  positive: '#4ade80',
  negative: '#f87171',
  neutral: '#94a3b8'
};

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>('all');
  const [subreddits, setSubreddits] = useState<string[]>([]);
  const [timeWindow, setTimeWindow] = useState<number>(24);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSubreddits();
  }, []);

  useEffect(() => {
    loadData();
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [selectedSubreddit, timeWindow]);

  const loadSubreddits = async () => {
    try {
      const result = await api.getMonitoredSubreddits();
      setSubreddits(result.subreddits);
    } catch (err) {
      console.error('Failed to load subreddits:', err);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const subreddit = selectedSubreddit === 'all' ? undefined : selectedSubreddit;
      const result = await api.getSentimentStats(subreddit, timeWindow);
      setData(result);
    } catch (err) {
      setError('Failed to load sentiment data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const sentimentData = [
    { name: 'Positive', value: data.statistics.positive, color: COLORS.positive },
    { name: 'Negative', value: data.statistics.negative, color: COLORS.negative },
    { name: 'Neutral', value: data.statistics.neutral, color: COLORS.neutral }
  ];

  const barData = [
    {
      name: 'Sentiment Distribution',
      Positive: data.statistics.positive,
      Negative: data.statistics.negative,
      Neutral: data.statistics.neutral
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Reddit Sentiment Analysis Dashboard</h1>

      {/* Filters */}
      <div className="mb-8 flex gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Subreddit</label>
          <select
            value={selectedSubreddit}
            onChange={(e) => setSelectedSubreddit(e.target.value)}
            className="border rounded px-4 py-2"
          >
            <option value="all">All Subreddits</option>
            {subreddits.map(sub => (
              <option key={sub} value={sub}>r/{sub}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Time Window</label>
          <select
            value={timeWindow}
            onChange={(e) => setTimeWindow(Number(e.target.value))}
            className="border rounded px-4 py-2"
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Total Analyzed</h3>
          <p className="text-3xl font-bold">{data.statistics.total}</p>
        </div>
        
        <div className="bg-green-50 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Positive</h3>
          <p className="text-3xl font-bold text-green-600">{data.statistics.positive}</p>
        </div>
        
        <div className="bg-red-50 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Negative</h3>
          <p className="text-3xl font-bold text-red-600">{data.statistics.negative}</p>
        </div>
        
        <div className="bg-gray-50 p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Neutral</h3>
          <p className="text-3xl font-bold text-gray-600">{data.statistics.neutral}</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Pie Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Sentiment Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Sentiment Counts</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Positive" fill={COLORS.positive} />
              <Bar dataKey="Negative" fill={COLORS.negative} />
              <Bar dataKey="Neutral" fill={COLORS.neutral} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Average Sentiment */}
      <div className="mt-8 bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Average Sentiment Score</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="bg-gray-200 rounded-full h-8">
              <div
                className={`h-8 rounded-full flex items-center justify-center text-white font-bold ${
                  data.statistics.avg_sentiment >= 0 ? 'bg-green-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.abs(data.statistics.avg_sentiment) * 50 + 50}%` }}
              >
                {data.statistics.avg_sentiment.toFixed(3)}
              </div>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            Range: -1 (negative) to +1 (positive)
          </div>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-4 text-sm text-gray-500 text-right">
        Last updated: {new Date(data.timestamp).toLocaleString()}
      </div>
    </div>
  );
};
