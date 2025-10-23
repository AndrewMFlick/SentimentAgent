import React from 'react';
import { TimeRange } from '../types/hot-topics';

interface SimpleTimeRangeFilterProps {
  value: TimeRange;
  onChange: (timeRange: TimeRange) => void;
  className?: string;
}

/**
 * Simple time range filter for Hot Topics
 * Provides 3 preset options: 24h, 7d, 30d
 */
export const SimpleTimeRangeFilter: React.FC<SimpleTimeRangeFilterProps> = ({
  value,
  onChange,
  className = ''
}) => {
  const options: { value: TimeRange; label: string }[] = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
  ];

  return (
    <div className={`flex gap-2 ${className}`}>
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={`
            px-4 py-2 rounded-lg font-medium transition-all
            ${
              value === option.value
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'glass-card text-gray-300 hover:bg-white/10'
            }
          `}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
};
