/**
 * AdminReanalysisPanel Component
 * 
 * Form to manually trigger reanalysis jobs for backfilling
 * tool categorization in sentiment data.
 * 
 * Features:
 * - Date range selection (optional)
 * - Tool ID filtering (optional)
 * - Batch size configuration
 * - Job submission with admin authentication
 */
import { useState, FormEvent } from 'react';
import { api } from '../services/api';
import { ReanalysisJobResponse } from '../types/reanalysis';

interface AdminReanalysisPanelProps {
  adminToken: string;
  onJobCreated?: (jobResponse: ReanalysisJobResponse) => void;
}

export function AdminReanalysisPanel({ 
  adminToken, 
  onJobCreated 
}: AdminReanalysisPanelProps) {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [toolIds, setToolIds] = useState<string>('');
  const [batchSize, setBatchSize] = useState<number>(100);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      // Build request
      const request: {
        date_range?: { start?: string; end?: string };
        tool_ids?: string[];
        batch_size: number;
      } = {
        batch_size: batchSize
      };

      // Add date range if provided
      if (startDate || endDate) {
        request.date_range = {};
        if (startDate) {
          request.date_range.start = new Date(startDate).toISOString();
        }
        if (endDate) {
          request.date_range.end = new Date(endDate).toISOString();
        }
      }

      // Add tool IDs if provided (comma-separated)
      if (toolIds.trim()) {
        request.tool_ids = toolIds
          .split(',')
          .map(id => id.trim())
          .filter(id => id.length > 0);
      }

      // Trigger reanalysis
      const response = await api.triggerReanalysis(request, adminToken);
      
      setSuccess(
        `Reanalysis job created successfully! ` +
        `Job ID: ${response.job_id}, ` +
        `Estimated documents: ${response.estimated_docs}`
      );

      // Notify parent component
      if (onJobCreated) {
        onJobCreated(response);
      }

      // Reset form
      setStartDate('');
      setEndDate('');
      setToolIds('');
      setBatchSize(100);

    } catch (err) {
      const message = err instanceof Error 
        ? err.message 
        : 'Failed to trigger reanalysis job';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-2xl font-bold text-white mb-4">
        Trigger Reanalysis Job
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        Manually trigger a reanalysis job to backfill tool categorization 
        in historical sentiment data. Leave filters empty to process all data.
      </p>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-4">
          <p className="text-sm">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-4 py-3 rounded-lg mb-4">
          <p className="text-sm">
            <strong>Success:</strong> {success}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Date Range Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">
            Date Range (Optional)
          </h3>
          <p className="text-sm text-gray-400 -mt-2">
            Filter sentiment data by creation date. Leave empty to process all dates.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label 
                htmlFor="start-date" 
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Start Date
              </label>
              <input
                id="start-date"
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <div>
              <label 
                htmlFor="end-date" 
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                End Date
              </label>
              <input
                id="end-date"
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Tool IDs Section */}
        <div className="space-y-2">
          <label 
            htmlFor="tool-ids" 
            className="block text-sm font-medium text-gray-300"
          >
            Tool IDs (Optional)
          </label>
          <p className="text-xs text-gray-400">
            Comma-separated list of tool IDs to filter by. Leave empty to detect all tools.
          </p>
          <input
            id="tool-ids"
            type="text"
            value={toolIds}
            onChange={(e) => setToolIds(e.target.value)}
            placeholder="e.g., tool-uuid-1, tool-uuid-2"
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {/* Batch Size Section */}
        <div className="space-y-2">
          <label 
            htmlFor="batch-size" 
            className="block text-sm font-medium text-gray-300"
          >
            Batch Size
          </label>
          <p className="text-xs text-gray-400">
            Number of documents to process per batch. Higher values = faster processing but more memory usage.
          </p>
          <input
            id="batch-size"
            type="number"
            value={batchSize}
            onChange={(e) => setBatchSize(parseInt(e.target.value) || 100)}
            min={10}
            max={500}
            step={10}
            className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          <p className="text-xs text-gray-500">
            Recommended: 100-200 for balanced performance
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-3 bg-primary hover:bg-primary-dark text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Creating Job...' : 'Trigger Reanalysis'}
          </button>
        </div>
      </form>
    </div>
  );
}
