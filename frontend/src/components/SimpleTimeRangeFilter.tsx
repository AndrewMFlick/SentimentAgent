import React, { useCallback, useEffect, useRef } from 'react';
import { TimeRange } from '../types/hot-topics';

interface SimpleTimeRangeFilterProps {
  value: TimeRange;
  onChange: (timeRange: TimeRange) => void;
  className?: string;
  isLoading?: boolean;
}

/**
 * Simple time range filter for Hot Topics
 * Provides 3 preset options: 24h, 7d, 30d
 * Features: Active state styling, keyboard navigation, loading indicator
 */
export const SimpleTimeRangeFilter: React.FC<SimpleTimeRangeFilterProps> = ({
  value,
  onChange,
  className = '',
  isLoading = false
}) => {
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);
  
  const options: { value: TimeRange; label: string }[] = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
  ];

  // Debounced onChange (300ms) to avoid rapid API calls
  const handleChange = useCallback((newValue: TimeRange) => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    
    debounceTimer.current = setTimeout(() => {
      onChange(newValue);
    }, 300);
  }, [onChange]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return (
    <div className={`flex gap-2 ${className}`} role="radiogroup" aria-label="Time range filter">
      {options.map((option, index) => (
        <button
          key={option.value}
          onClick={() => handleChange(option.value)}
          disabled={isLoading}
          role="radio"
          aria-checked={value === option.value ? "true" : "false"}
          aria-label={`Filter by ${option.label.toLowerCase()}`}
          tabIndex={value === option.value ? 0 : -1}
          onKeyDown={(e) => {
            // Keyboard navigation: Arrow keys
            if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
              e.preventDefault();
              const nextIndex = (index + 1) % options.length;
              handleChange(options[nextIndex].value);
              (e.currentTarget.parentElement?.children[nextIndex] as HTMLElement)?.focus();
            } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
              e.preventDefault();
              const prevIndex = (index - 1 + options.length) % options.length;
              handleChange(options[prevIndex].value);
              (e.currentTarget.parentElement?.children[prevIndex] as HTMLElement)?.focus();
            } else if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleChange(option.value);
            }
          }}
          className={`
            px-4 py-2 rounded-lg font-medium transition-all
            focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-dark-bg
            ${
              value === option.value
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'glass-card text-gray-300 hover:bg-white/10'
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          {option.label}
          {isLoading && value === option.value && (
            <span className="ml-2 inline-block animate-spin">⏳</span>
          )}
        </button>
      ))}
    </div>
  );
};
