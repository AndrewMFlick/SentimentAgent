// Sentiment Time Series Component - Line chart visualization
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { ToolTimeSeries } from '../types';

interface SentimentTimeSeriesProps {
  timeSeries: ToolTimeSeries | null;
  loading?: boolean;
  error?: string | null;
}

/**
 * Custom tooltip for time series chart
 * Shows detailed stats on hover
 */
const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    
    return (
      <div className="bg-white p-3 border rounded shadow-lg">
        <p className="font-semibold mb-2">{data.date}</p>
        <div className="space-y-1">
          <p className="text-sm text-gray-600">
            Total Mentions:{' '}
            <span className="font-semibold">
              {data.total_mentions}
            </span>
          </p>
          <p className="text-sm text-green-600">
            Positive:{' '}
            <span className="font-semibold">
              {data.positive_count}
            </span>
          </p>
          <p className="text-sm text-red-600">
            Negative:{' '}
            <span className="font-semibold">
              {data.negative_count}
            </span>
          </p>
          <p className="text-sm text-gray-600">
            Neutral:{' '}
            <span className="font-semibold">
              {data.neutral_count}
            </span>
          </p>
          <p className="text-sm text-blue-600 pt-2 border-t">
            Avg Sentiment:{' '}
            <span className="font-semibold">
              {data.avg_sentiment?.toFixed(3) || 'N/A'}
            </span>
          </p>
        </div>
      </div>
    );
  }
  
  return null;
};

/**
 * Detect extreme sentiment shifts (> 0.3 change day-over-day)
 */
const detectSentimentShifts = (dataPoints: any[]) => {
  const shifts: Array<{date: string; change: number; direction: 'up' | 'down'}> = [];
  
  for (let i = 1; i < dataPoints.length; i++) {
    const prev = dataPoints[i - 1].avg_sentiment;
    const curr = dataPoints[i].avg_sentiment;
    const change = curr - prev;
    
    // Consider a shift "extreme" if > 0.3 change
    if (Math.abs(change) > 0.3) {
      shifts.push({
        date: dataPoints[i].date,
        change: change,
        direction: change > 0 ? 'up' : 'down'
      });
    }
  }
  
  return shifts;
};

/**
 * SentimentTimeSeries component
 * Displays sentiment trends over time with daily granularity
 */
export const SentimentTimeSeries = ({
  timeSeries,
  loading,
  error
}: SentimentTimeSeriesProps) => {
  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center py-8 text-gray-500">
          Loading time series data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center py-8 text-red-600">
          {error}
        </div>
      </div>
    );
  }

  if (!timeSeries || !timeSeries.data_points.length) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="text-center py-8 text-gray-500">
          No time series data available for the selected period
        </div>
      </div>
    );
  }

  // Detect extreme sentiment shifts
  const sentimentShifts = detectSentimentShifts(timeSeries.data_points);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">
          {timeSeries.tool_name} - Sentiment Trends
        </h3>
        <p className="text-sm text-gray-600">
          {timeSeries.time_period.start} to{' '}
          {timeSeries.time_period.end} (
          {timeSeries.data_points.length} days)
        </p>
        
        {/* Show sentiment shift alerts */}
        {sentimentShifts.length > 0 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm font-semibold text-yellow-800 mb-2">
              ⚠️ Extreme Sentiment Shifts Detected
            </p>
            <div className="space-y-1">
              {sentimentShifts.map((shift, idx) => (
                <p key={idx} className="text-xs text-yellow-700">
                  {shift.date}: {shift.direction === 'up' ? '📈' : '📉'}{' '}
                  {shift.change > 0 ? '+' : ''}{shift.change.toFixed(2)} sentiment change
                </p>
              ))}
            </div>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={timeSeries.data_points}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            yAxisId="left"
            label={{
              value: 'Mention Count',
              angle: -90,
              position: 'insideLeft'
            }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[-1, 1]}
            label={{
              value: 'Avg Sentiment',
              angle: 90,
              position: 'insideRight'
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Mention count lines */}
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="positive_count"
            stroke="#10b981"
            name="Positive"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="negative_count"
            stroke="#ef4444"
            name="Negative"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="neutral_count"
            stroke="#6b7280"
            name="Neutral"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
          
          {/* Average sentiment line */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="avg_sentiment"
            stroke="#3b82f6"
            name="Avg Sentiment"
            strokeWidth={3}
            strokeDasharray="5 5"
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Summary stats */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-sm text-gray-600">Total Mentions</p>
          <p className="text-xl font-bold">
            {timeSeries.data_points.reduce(
              (sum, p) => sum + p.total_mentions,
              0
            )}
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">Avg Positive</p>
          <p className="text-xl font-bold text-green-600">
            {(
              (timeSeries.data_points.reduce(
                (sum, p) => sum + p.positive_count,
                0
              ) /
                timeSeries.data_points.reduce(
                  (sum, p) => sum + p.total_mentions,
                  0
                )) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">Avg Negative</p>
          <p className="text-xl font-bold text-red-600">
            {(
              (timeSeries.data_points.reduce(
                (sum, p) => sum + p.negative_count,
                0
              ) /
                timeSeries.data_points.reduce(
                  (sum, p) => sum + p.total_mentions,
                  0
                )) *
              100
            ).toFixed(1)}
            %
          </p>
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-600">Avg Sentiment</p>
          <p className="text-xl font-bold text-blue-600">
            {(
              timeSeries.data_points.reduce(
                (sum, p) => sum + (p.avg_sentiment || 0),
                0
              ) / timeSeries.data_points.length
            ).toFixed(3)}
          </p>
        </div>
      </div>
    </div>
  );
};
