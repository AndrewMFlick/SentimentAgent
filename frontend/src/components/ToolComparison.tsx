// Tool Comparison Component - Side-by-side sentiment comparison
import { ToolComparison as ToolComparisonType } from '../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ToolComparisonProps {
  comparison: ToolComparisonType;
}

interface DeltaHighlightsProps {
  deltas: ToolComparisonType['deltas'];
}

/**
 * DeltaHighlights sub-component
 * Visually emphasizes differences > 10%
 */
const DeltaHighlights = ({ deltas }: DeltaHighlightsProps) => {
  const significantDeltas = deltas.filter(
    (delta) =>
      Math.abs(delta.positive_delta) > 10 ||
      Math.abs(delta.negative_delta) > 10
  );

  if (significantDeltas.length === 0) {
    return (
      <div className="delta-highlights">
        <p className="text-sm text-gray-500">
          No significant differences (&gt;10%) between tools
        </p>
      </div>
    );
  }

  return (
    <div className="delta-highlights">
      <h4 className="text-sm font-semibold mb-2">
        Significant Differences (&gt;10%)
      </h4>
      <div className="space-y-2">
        {significantDeltas.map((delta, idx) => (
          <div
            key={idx}
            className="p-2 bg-gray-50 rounded border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {delta.tool_a_id} vs {delta.tool_b_id}
              </span>
            </div>
            <div className="mt-1 space-y-1">
              {Math.abs(delta.positive_delta) > 10 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">
                    Positive:
                  </span>
                  <span
                    className={`text-xs font-semibold ${
                      delta.positive_delta > 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {delta.positive_delta > 0 ? '↑' : '↓'}{' '}
                    {Math.abs(delta.positive_delta).toFixed(1)}%
                  </span>
                </div>
              )}
              {Math.abs(delta.negative_delta) > 10 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-600">
                    Negative:
                  </span>
                  <span
                    className={`text-xs font-semibold ${
                      delta.negative_delta > 0
                        ? 'text-red-600'
                        : 'text-green-600'
                    }`}
                  >
                    {delta.negative_delta > 0 ? '↑' : '↓'}{' '}
                    {Math.abs(delta.negative_delta).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * ToolComparison component
 * Displays side-by-side sentiment comparison with grouped bar chart
 */
export const ToolComparison = ({
  comparison
}: ToolComparisonProps) => {
  // Transform data for grouped bar chart
  const chartData = comparison.tools.map((tool) => ({
    name: tool.tool_name,
    Positive: tool.positive_percentage,
    Negative: tool.negative_percentage,
    Neutral: tool.neutral_percentage,
    mentions: tool.total_mentions
  }));

  const colors = {
    Positive: '#10b981',
    Negative: '#ef4444',
    Neutral: '#6b7280'
  };

  return (
    <div className="tool-comparison">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Tool Sentiment Comparison
        </h3>

        {/* Grouped Bar Chart */}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis label={{ value: 'Percentage (%)', angle: -90 }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white p-3 border rounded shadow">
                      <p className="font-semibold mb-1">
                        {data.name}
                      </p>
                      <p className="text-sm text-gray-600 mb-2">
                        {data.mentions} mentions
                      </p>
                      {payload.map((entry: any) => {
                        const colorClass =
                          entry.dataKey === 'Positive'
                            ? 'text-green-600'
                            : entry.dataKey === 'Negative'
                            ? 'text-red-600'
                            : 'text-gray-600';
                        return (
                          <p
                            key={entry.dataKey}
                            className={`text-sm ${colorClass}`}
                          >
                            {entry.dataKey}: {entry.value.toFixed(1)}%
                          </p>
                        );
                      })}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Bar dataKey="Positive" fill={colors.Positive} />
            <Bar dataKey="Negative" fill={colors.Negative} />
            <Bar dataKey="Neutral" fill={colors.Neutral} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Side-by-side sentiment cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {comparison.tools.map((tool) => (
          <div
            key={tool.tool_id}
            className="p-4 border rounded-lg bg-white shadow-sm"
          >
            <h4 className="font-semibold mb-2">{tool.tool_name}</h4>
            <div className="text-sm text-gray-600 mb-3">
              {tool.total_mentions} mentions
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm">Positive:</span>
                <span className="font-semibold text-green-600">
                  {tool.positive_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Negative:</span>
                <span className="font-semibold text-red-600">
                  {tool.negative_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Neutral:</span>
                <span className="font-semibold text-gray-600">
                  {tool.neutral_percentage.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-sm">Avg Sentiment:</span>
                <span className="font-semibold">
                  {tool.avg_sentiment.toFixed(3)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Delta Highlights */}
      <DeltaHighlights deltas={comparison.deltas} />
    </div>
  );
};
