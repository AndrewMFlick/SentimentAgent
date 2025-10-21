import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { api } from '../services/api';
import { DashboardData, AITool } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ToolSentimentCard } from './ToolSentimentCard';
import { ToolComparison } from './ToolComparison';
import { SentimentTimeSeries } from './SentimentTimeSeries';
import { TimeRangeFilter } from './TimeRangeFilter';
import { useTools, useToolSentiment, useToolComparison, useTimeSeries, TimeRangeValue } from '../services/toolApi';

// Create a client
const queryClient = new QueryClient();

const COLORS = {
  positive: '#4ade80',
  negative: '#f87171',
  neutral: '#94a3b8'
};

// Time series section with tool selector and date range
const TimeSeriesSection: React.FC<{
  tools: AITool[];
}> = ({ tools }) => {
  const [selectedToolId, setSelectedToolId] = useState<string>('');
  const [showChart, setShowChart] = useState(false);
  
  // Default to last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(today.getDate() - 30);
  
  const [startDate, setStartDate] = useState(
    thirtyDaysAgo.toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(
    today.toISOString().split('T')[0]
  );

  const { data, isLoading, error } = useTimeSeries(
    showChart ? selectedToolId : null,
    startDate,
    endDate
  );

  const handleShowChart = () => {
    if (selectedToolId) {
      setShowChart(true);
    }
  };

  const handleReset = () => {
    setSelectedToolId('');
    setShowChart(false);
  };

  if (tools.length === 0) {
    return null;
  }

  return (
    <div className="mt-12 glass-card p-8">
      <h2 className="text-3xl font-bold text-white mb-6">
        Sentiment Trends Over Time
      </h2>

      {/* Tool and date selector */}
      <div className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label
              htmlFor="timeseries-tool-select"
              className="block text-sm font-medium mb-2 text-gray-200"
            >
              Select Tool
            </label>
            <select
              id="timeseries-tool-select"
              value={selectedToolId}
              onChange={(e) => setSelectedToolId(e.target.value)}
              className="glass-input w-full"
            >
              <option value="" className="bg-dark-surface text-gray-300">Choose a tool...</option>
              {tools.map((tool) => (
                <option className="bg-dark-surface text-gray-200" key={tool.id} value={tool.id}>
                  {tool.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="timeseries-start-date"
              className="block text-sm font-medium mb-2 text-gray-200"
            >
              Start Date
            </label>
            <input
              id="timeseries-start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="glass-input w-full"
            />
          </div>

          <div>
            <label
              htmlFor="timeseries-end-date"
              className="block text-sm font-medium mb-2 text-gray-200"
            >
              End Date
            </label>
            <input
              id="timeseries-end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="glass-input w-full"
            />
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleShowChart}
              disabled={!selectedToolId}
              className={`glass-button px-6 py-2 rounded-lg font-semibold ${
                selectedToolId
                  ? 'bg-emerald-600/40 border-emerald-500/60 hover:bg-emerald-600/60'
                  : 'opacity-50 cursor-not-allowed'
              }`}
            >
              View Trends
            </button>
            {showChart && (
              <button
                onClick={handleReset}
                className="glass-button px-6 py-2 rounded-lg bg-gray-600/30 border-gray-500/50 hover:bg-gray-600/40"
              >
                Reset
              </button>
            )}
          </div>
        </div>

        <p className="text-sm text-gray-400">
          View daily sentiment trends for up to 90 days
        </p>
      </div>

      {/* Time series chart */}
      {showChart && (
        <SentimentTimeSeries
          timeSeries={data || null}
          loading={isLoading}
          error={
            error ? 'Failed to load time series data' : null
          }
        />
      )}
    </div>
  );
};

// Tool comparison section with multi-select
const ToolComparisonSection: React.FC<{
  tools: AITool[];
  timeRange: TimeRangeValue;
}> = ({ tools, timeRange }) => {
  const [selectedToolIds, setSelectedToolIds] = useState<string[]>([]);
  const [showComparison, setShowComparison] = useState(false);

  const { data, isLoading, error } = useToolComparison(
    selectedToolIds,
    {
      hours: timeRange.hours,
      startDate: timeRange.startDate,
      endDate: timeRange.endDate
    }
  );

  const handleToolToggle = (toolId: string) => {
    setSelectedToolIds((prev) =>
      prev.includes(toolId)
        ? prev.filter((id) => id !== toolId)
        : [...prev, toolId]
    );
  };

  const handleCompare = () => {
    if (selectedToolIds.length >= 2) {
      setShowComparison(true);
    }
  };

  const handleReset = () => {
    setSelectedToolIds([]);
    setShowComparison(false);
  };

  if (tools.length < 2) {
    return null;
  }

  return (
    <div className="mt-12 glass-card p-8">
      <h2 className="text-3xl font-bold text-white mb-6">Compare AI Tools</h2>

      {/* Tool selector */}
      <div className="mb-6">
        <p className="text-sm text-gray-300 mb-3">
          Select 2 or more tools to compare sentiment:
        </p>
        <div className="flex flex-wrap gap-2 mb-4">
          {tools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => handleToolToggle(tool.id)}
              className={`px-4 py-2 rounded-lg border transition-all ${
                selectedToolIds.includes(tool.id)
                  ? 'glass-button bg-emerald-600/40 border-emerald-500/60 text-white'
                  : 'glass-button bg-dark-elevated/60 text-gray-200 border-glass-border hover:bg-dark-elevated/80'
              }`}
            >
              {tool.name}
            </button>
          ))}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleCompare}
            disabled={selectedToolIds.length < 2}
            className={`glass-button px-6 py-2 rounded-lg font-semibold ${
              selectedToolIds.length >= 2
                ? 'bg-emerald-600/40 border-emerald-500/60 hover:bg-emerald-600/60'
                : 'opacity-50 cursor-not-allowed'
            }`}
          >
            Compare ({selectedToolIds.length} selected)
          </button>
          {showComparison && (
            <button
              onClick={handleReset}
              className="glass-button px-6 py-2 rounded-lg bg-gray-600/30 border-gray-500/50 hover:bg-gray-600/40"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Comparison results */}
      {showComparison && (
        <div className="glass-card p-8">
          {isLoading && (
            <div className="text-center py-8 text-gray-300">
              Loading comparison...
            </div>
          )}

          {error && (
            <div className="text-red-400 text-center py-8">
              Failed to load comparison data
            </div>
          )}

          {data && <ToolComparison comparison={data} />}
        </div>
      )}
    </div>
  );
};

const DashboardContent: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>('all');
  const [subreddits, setSubreddits] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Time range state
  const [timeRange, setTimeRange] = useState<TimeRangeValue>({
    preset: '24h',
    hours: 24
  });

  // Fetch AI tools
  const { data: toolsData, isLoading: toolsLoading, error: toolsError } = useTools();

  useEffect(() => {
    loadSubreddits();
  }, []);

  useEffect(() => {
    loadData();
    // Refresh every 5 minutes
    const interval = setInterval(loadData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [selectedSubreddit, timeRange]);

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
      const hours = timeRange.hours || 24;
      const result = await api.getSentimentStats(subreddit, hours);
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
        <div className="text-xl text-gray-300">Loading dashboard...</div>
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
    <div className="container mx-auto px-6 py-12">
      <h1 className="text-5xl font-bold mb-10 bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
        Reddit Sentiment Analysis Dashboard
      </h1>

      {/* Filters */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="subreddit-select" className="block text-sm font-medium mb-2 text-gray-200">Subreddit</label>
          <select
            id="subreddit-select"
            value={selectedSubreddit}
            onChange={(e) => setSelectedSubreddit(e.target.value)}
            className="glass-input w-full"
          >
            <option value="all" className="bg-dark-surface text-gray-300">All Subreddits</option>
            {subreddits.map(sub => (
              <option className="bg-dark-surface text-gray-200" key={sub} value={sub}>r/{sub}</option>
            ))}
          </select>
        </div>
        
        <TimeRangeFilter
          value={timeRange}
          onChange={setTimeRange}
          maxDays={90}
        />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-card p-8">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Total Analyzed</h3>
          <p className="text-3xl font-bold">{data.statistics.total}</p>
        </div>
        
        <div className="glass-card p-8 bg-emerald-900/20 border-emerald-700/50">
          <h3 className="text-sm font-medium text-gray-600 mb-2">Positive</h3>
          <p className="text-3xl font-bold text-green-600">{data.statistics.positive}</p>
        </div>
        
        <div className="glass-card p-8 bg-red-900/20 border-red-700/50">
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
        <div className="glass-card p-8">
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
        <div className="glass-card p-8">
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
      <div className="mt-8 glass-card p-8">
        <h2 className="text-2xl font-semibold mb-6 text-white">Average Sentiment Score</h2>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="bg-dark-elevated/50 rounded-full h-8">
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
          <div className="text-sm text-gray-300">
            Range: -1 (negative) to +1 (positive)
          </div>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-4 text-sm text-gray-400 text-right">
        Last updated: {new Date(data.timestamp).toLocaleString()}
      </div>

      {/* AI Tools Sentiment Section */}
      <div className="mt-12">
        <h2 className="text-3xl font-bold text-white mb-6">AI Developer Tools Sentiment</h2>
        
        {toolsLoading && (
          <div className="text-center py-8">Loading AI tools...</div>
        )}
        
        {toolsError && (
          <div className="text-red-400 text-center py-8">
            Failed to load AI tools
          </div>
        )}
        
        {toolsData && toolsData.tools && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {toolsData.tools.map((tool) => (
              <ToolSentimentCardWrapper
                key={tool.id}
                toolId={tool.id}
                timeRange={timeRange}
              />
            ))}
          </div>
        )}
      </div>

      {/* Tool Comparison Section */}
      <ToolComparisonSection
        tools={toolsData?.tools || []}
        timeRange={timeRange}
      />

      {/* Time Series Section */}
      <TimeSeriesSection tools={toolsData?.tools || []} />
    </div>
  );
};

// Wrapper component for individual tool sentiment cards
const ToolSentimentCardWrapper: React.FC<{
  toolId: string;
  timeRange: TimeRangeValue;
}> = ({ toolId, timeRange }) => {
  const { data, isLoading, error } = useToolSentiment(toolId, {
    hours: timeRange.hours,
    startDate: timeRange.startDate,
    endDate: timeRange.endDate
  });
  
  return (
    <ToolSentimentCard
      sentiment={data || null}
      loading={isLoading}
      error={error ? 'Failed to load sentiment data' : null}
    />
  );
};

// Main Dashboard component wrapped with QueryClientProvider
export const Dashboard: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardContent />
    </QueryClientProvider>
  );
};
