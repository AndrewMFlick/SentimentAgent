// Time Range Filter Component - Preset and custom date range selection
import React, { useState } from 'react';

export type TimeRangePreset = '24h' | '7d' | '30d' | '90d' | 'custom';

interface TimeRangeValue {
  preset: TimeRangePreset;
  startDate?: string;
  endDate?: string;
  hours?: number;
}

interface TimeRangeFilterProps {
  value: TimeRangeValue;
  onChange: (value: TimeRangeValue) => void;
  maxDays?: number;
}

/**
 * TimeRangeFilter component
 * Provides preset options (24h, 7d, 30d, 90d) and custom date picker
 */
export const TimeRangeFilter: React.FC<TimeRangeFilterProps> = ({
  value,
  onChange,
  maxDays = 90
}) => {
  const [showCustom, setShowCustom] = useState(
    value.preset === 'custom'
  );
  const [customStartDate, setCustomStartDate] = useState(
    value.startDate || ''
  );
  const [customEndDate, setCustomEndDate] = useState(
    value.endDate || ''
  );
  const [validationError, setValidationError] = useState<
    string | null
  >(null);

  const presetOptions: {
    value: TimeRangePreset;
    label: string;
    hours: number;
  }[] = [
    { value: '24h', label: 'Last 24 Hours', hours: 24 },
    { value: '7d', label: 'Last 7 Days', hours: 168 },
    { value: '30d', label: 'Last 30 Days', hours: 720 },
    { value: '90d', label: 'Last 90 Days', hours: 2160 }
  ];

  const handlePresetChange = (preset: TimeRangePreset) => {
    if (preset === 'custom') {
      setShowCustom(true);
      setValidationError(null);
    } else {
      setShowCustom(false);
      setValidationError(null);
      const option = presetOptions.find((o) => o.value === preset);
      if (option) {
        onChange({
          preset,
          hours: option.hours,
          startDate: undefined,
          endDate: undefined
        });
      }
    }
  };

  const handleCustomDateChange = () => {
    if (!customStartDate || !customEndDate) {
      setValidationError('Both start and end dates are required');
      return;
    }

    try {
      const start = new Date(customStartDate);
      const end = new Date(customEndDate);
      const today = new Date();

      // Validation: start must be before end
      if (start > end) {
        setValidationError('Start date must be before end date');
        return;
      }

      // Validation: end date cannot be in the future
      if (end > today) {
        setValidationError('End date cannot be in the future');
        return;
      }

      // Validation: date range must be within max days
      const daysDiff = Math.ceil(
        (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
      );
      if (daysDiff > maxDays) {
        setValidationError(
          `Date range cannot exceed ${maxDays} days`
        );
        return;
      }

      // Validation: must be within retention period
      const retentionDate = new Date(today);
      retentionDate.setDate(today.getDate() - maxDays);
      if (start < retentionDate) {
        setValidationError(
          `Start date must be within last ${maxDays} days`
        );
        return;
      }

      setValidationError(null);
      onChange({
        preset: 'custom',
        startDate: customStartDate,
        endDate: customEndDate,
        hours: undefined
      });
    } catch (error) {
      setValidationError('Invalid date format');
    }
  };

  const handleReset = () => {
    setShowCustom(false);
    setCustomStartDate('');
    setCustomEndDate('');
    setValidationError(null);
    onChange({
      preset: '24h',
      hours: 24,
      startDate: undefined,
      endDate: undefined
    });
  };

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold mb-4 text-white">Time Range</h3>

      {/* Preset buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {presetOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => handlePresetChange(option.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              value.preset === option.value && !showCustom
                ? 'glass-button bg-emerald-600/40 border-emerald-500/60 text-white'
                : 'glass-button bg-dark-elevated/60 text-gray-200 hover:bg-dark-elevated/80'
            }`}
          >
            {option.label}
          </button>
        ))}
        <button
          onClick={() => handlePresetChange('custom')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            showCustom
              ? 'glass-button bg-emerald-600/40 border-emerald-500/60 text-white'
              : 'glass-button bg-dark-elevated/60 text-gray-200 hover:bg-dark-elevated/80'
          }`}
        >
          Custom Range
        </button>
      </div>

      {/* Custom date picker */}
      {showCustom && (
        <div className="mt-4 p-4 glass-card-light">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div>
              <label
                htmlFor="custom-start-date"
                className="block text-xs font-medium text-gray-200 mb-1"
              >
                Start Date
              </label>
              <input
                id="custom-start-date"
                type="date"
                value={customStartDate}
                onChange={(e) => setCustomStartDate(e.target.value)}
                className="glass-input w-full text-sm"
                max={customEndDate || undefined}
              />
            </div>
            <div>
              <label
                htmlFor="custom-end-date"
                className="block text-xs font-medium text-gray-200 mb-1"
              >
                End Date
              </label>
              <input
                id="custom-end-date"
                type="date"
                value={customEndDate}
                onChange={(e) => setCustomEndDate(e.target.value)}
                className="glass-input w-full text-sm"
                min={customStartDate || undefined}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>

          {validationError && (
            <div className="mb-3 p-2 bg-red-900/30 border border-red-700/50 rounded text-xs text-red-300">
              {validationError}
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleCustomDateChange}
              disabled={!customStartDate || !customEndDate}
              className={`glass-button px-4 py-2 text-sm font-medium ${
                customStartDate && customEndDate
                  ? 'bg-emerald-600/40 border-emerald-500/60 hover:bg-emerald-600/60'
                  : 'opacity-50 cursor-not-allowed'
              }`}
            >
              Apply
            </button>
            <button
              onClick={handleReset}
              className="glass-button px-4 py-2 text-sm font-medium"
            >
              Reset
            </button>
          </div>

          <p className="mt-2 text-xs text-gray-400">
            Maximum range: {maxDays} days
          </p>
        </div>
      )}
    </div>
  );
};
