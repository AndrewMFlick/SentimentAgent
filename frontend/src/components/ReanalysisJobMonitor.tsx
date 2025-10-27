/**
 * ReanalysisJobMonitor Component
 * 
 * Displays a table of reanalysis jobs with:
 * - Job status (color-coded badges)
 * - Progress bars for running jobs
 * - Statistics and error counts
 * - Auto-refresh for active jobs
 * - Navigation to job details
 * 
 * Features auto-polling when jobs are active (queued/running).
 */
import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  ReanalysisJob, 
  JobStatus, 
  ReanalysisJobList 
} from '../types/reanalysis';

interface ReanalysisJobMonitorProps {
  adminToken: string;
  refreshTrigger?: number;  // External trigger to force refresh
}

export function ReanalysisJobMonitor({ 
  adminToken, 
  refreshTrigger 
}: ReanalysisJobMonitorProps) {
  const [jobs, setJobs] = useState<ReanalysisJob[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);

  const fetchJobs = async () => {
    try {
      setError(null);
      const params: {
        limit: number;
        offset: number;
        status?: string;
      } = { limit, offset };
      
      if (statusFilter) {
        params.status = statusFilter;
      }

      const response: ReanalysisJobList = await api.listReanalysisJobs(
        adminToken, 
        params
      );
      
      setJobs(response.jobs);
      setTotalCount(response.total_count);
    } catch (err) {
      const message = err instanceof Error 
        ? err.message 
        : 'Failed to fetch reanalysis jobs';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load and refresh on filter/offset/trigger change
  useEffect(() => {
    fetchJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, offset, refreshTrigger]);

  // Auto-refresh every 5 seconds if there are active jobs
  useEffect(() => {
    const hasActiveJobs = jobs.some(
      job => job.status === JobStatus.QUEUED || job.status === JobStatus.RUNNING
    );

    if (!hasActiveJobs) {
      return;
    }

    const intervalId = setInterval(() => {
      fetchJobs();
    }, 5000); // 5 seconds

    return () => clearInterval(intervalId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobs]);

  const getStatusBadgeClass = (status: JobStatus): string => {
    switch (status) {
      case JobStatus.QUEUED:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case JobStatus.RUNNING:
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case JobStatus.COMPLETED:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case JobStatus.FAILED:
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case JobStatus.CANCELLED:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const formatDuration = (seconds: number | null): string => {
    if (seconds === null) return 'N/A';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (mins === 0) {
      return `${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  const formatDate = (isoString: string | null): string => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString();
  };

  if (isLoading && jobs.length === 0) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-2xl font-bold text-white mb-4">
          Reanalysis Jobs
        </h2>
        <p className="text-gray-400">Loading jobs...</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">
          Reanalysis Jobs
        </h2>
        <button
          onClick={fetchJobs}
          disabled={isLoading}
          className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Status Filter */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Filter by Status
        </label>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setOffset(0); // Reset to first page
          }}
          className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
        >
          <option value="">All Statuses</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg mb-4">
          <p className="text-sm">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

      {/* Jobs Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                Job ID
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                Status
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                Progress
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                Trigger
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                Created
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">
                ETA
              </th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  No reanalysis jobs found
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr
                  key={job.id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="py-3 px-4">
                    <span className="text-sm text-white font-mono">
                      {job.id.substring(0, 8)}...
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-3 py-1 text-xs font-semibold rounded-full border ${getStatusBadgeClass(
                        job.status
                      )}`}
                    >
                      {job.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-white/10 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-primary h-full transition-all"
                            style={{ width: `${job.progress.percentage}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 min-w-[3rem]">
                          {job.progress.percentage.toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">
                        {job.progress.processed_count} / {
                          typeof job.progress.total_count === 'object' 
                            ? (job.progress.total_count as any).count || 0
                            : job.progress.total_count
                        }
                      </p>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-300">
                      {job.trigger_type === 'manual' ? 'Manual' : 'Automatic'}
                    </span>
                    {job.reason && (
                      <p className="text-xs text-gray-500 mt-1">
                        {job.reason}
                      </p>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-400">
                      {formatDate(job.created_at)}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-400">
                      {job.status === JobStatus.RUNNING
                        ? formatDuration(job.progress.estimated_time_remaining)
                        : '-'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalCount > limit && (
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-white/10">
          <p className="text-sm text-gray-400">
            Showing {offset + 1} - {Math.min(offset + limit, totalCount)} of{' '}
            {totalCount}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= totalCount}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
