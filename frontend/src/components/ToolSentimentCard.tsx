// Tool Sentiment Card Component
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { ToolSentiment } from '../types';

interface ToolSentimentCardProps {
  sentiment: ToolSentiment | null;
  loading?: boolean;
  error?: string | null;
}

const COLORS = {
  positive: '#10b981', // green
  negative: '#ef4444', // red
  neutral: '#6b7280'   // gray
};

export const ToolSentimentCard: React.FC<ToolSentimentCardProps> = ({
  sentiment,
  loading = false,
  error = null
}) => {
  if (loading) {
    return (
      <div className="tool-sentiment-card loading">
        <div className="spinner"></div>
        <p>Loading sentiment data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tool-sentiment-card error">
        <p className="error-message">❌ {error}</p>
      </div>
    );
  }

  if (!sentiment || sentiment.total_mentions === 0) {
    return (
      <div className="tool-sentiment-card no-data">
        <h3>{sentiment?.tool_name || 'Tool'}</h3>
        <p className="no-data-message">No data available</p>
        <small>Try selecting a different time range</small>
      </div>
    );
  }

  // Prepare chart data
  const chartData = [
    {
      name: 'Positive',
      value: sentiment.positive_count,
      percentage: sentiment.positive_percentage
    },
    {
      name: 'Negative',
      value: sentiment.negative_count,
      percentage: sentiment.negative_percentage
    },
    {
      name: 'Neutral',
      value: sentiment.neutral_count,
      percentage: sentiment.neutral_percentage
    }
  ];

  // Show low sample size warning
  const isLowSampleSize = sentiment.total_mentions < 10;

  return (
    <div className="tool-sentiment-card">
      <div className="card-header">
        <h3>{sentiment.tool_name}</h3>
        {isLowSampleSize && (
          <span className="badge low-sample">Low sample size</span>
        )}
      </div>

      <div className="sentiment-stats">
        <div className="stat-item">
          <span className="stat-label">Total Mentions</span>
          <span className="stat-value">{sentiment.total_mentions}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Avg Sentiment</span>
          <span className={`stat-value sentiment-${sentiment.avg_sentiment >= 0 ? 'positive' : 'negative'}`}>
            {sentiment.avg_sentiment.toFixed(2)}
          </span>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.name.toLowerCase() as keyof typeof COLORS]}
                />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value} mentions`,
                name
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="sentiment-breakdown">
        <div className="breakdown-item positive">
          <span className="label">Positive</span>
          <div className="bar">
            <div
              className="fill"
              style={{ width: `${sentiment.positive_percentage}%` }}
            ></div>
          </div>
          <span className="percentage">{sentiment.positive_percentage.toFixed(1)}%</span>
        </div>

        <div className="breakdown-item negative">
          <span className="label">Negative</span>
          <div className="bar">
            <div
              className="fill"
              style={{ width: `${sentiment.negative_percentage}%` }}
            ></div>
          </div>
          <span className="percentage">{sentiment.negative_percentage.toFixed(1)}%</span>
        </div>

        <div className="breakdown-item neutral">
          <span className="label">Neutral</span>
          <div className="bar">
            <div
              className="fill"
              style={{ width: `${sentiment.neutral_percentage}%` }}
            ></div>
          </div>
          <span className="percentage">{sentiment.neutral_percentage.toFixed(1)}%</span>
        </div>
      </div>

      <div className="time-period">
        <small>
          Data from {new Date(sentiment.time_period.start).toLocaleDateString()} to{' '}
          {new Date(sentiment.time_period.end).toLocaleDateString()}
        </small>
      </div>
    </div>
  );
};
