import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

interface AuditRecord {
  id: string;
  tool_id: string;
  action_type: string;
  admin_user: string;
  timestamp: string;
  ip_address?: string;
  changes?: {
    before?: any;
    after?: any;
  };
  notes?: string;
}

interface AuditLogViewerProps {
  toolId: string;
  toolName: string;
  isOpen: boolean;
  onClose: () => void;
  adminToken: string;
}

export default function AuditLogViewer({
  toolId,
  toolName,
  isOpen,
  onClose,
  adminToken
}: AuditLogViewerProps) {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState<string>('');
  const limit = 20;

  // Reset to page 1 when filter changes
  useEffect(() => {
    setPage(1);
  }, [actionFilter]);

  // Fetch audit log
  const { data, isLoading, error } = useQuery({
    queryKey: ['audit-log', toolId, page, actionFilter],
    queryFn: () => api.getAuditLog(toolId, adminToken, page, limit, actionFilter || undefined),
    enabled: isOpen && !!toolId && !!adminToken
  });

  // Close on Esc key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getActionBadgeColor = (actionType: string) => {
    const colors: Record<string, string> = {
      created: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      edited: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      archived: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      unarchived: 'bg-green-500/20 text-green-300 border-green-500/30',
      deleted: 'bg-red-500/20 text-red-300 border-red-500/30',
      merged: 'bg-purple-500/20 text-purple-300 border-purple-500/30'
    };
    return colors[actionType] || 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="glass-card w-full max-w-4xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <div>
              <h2 className="text-2xl font-bold text-white">Audit Log</h2>
              <p className="text-sm text-white/60 mt-1">{toolName}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/60 hover:text-white transition-colors"
              aria-label="Close audit log"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Filter */}
          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-4">
              <label htmlFor="action-filter" className="text-sm text-white/60">Filter by action:</label>
              <select
                id="action-filter"
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <option value="">All actions</option>
                <option value="created">Created</option>
                <option value="edited">Edited</option>
                <option value="archived">Archived</option>
                <option value="unarchived">Unarchived</option>
                <option value="deleted">Deleted</option>
                <option value="merged">Merged</option>
              </select>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {isLoading && (
              <div className="text-center py-12">
                <div className="inline-block w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
                <p className="text-white/60 mt-4">Loading audit log...</p>
              </div>
            )}

            {error && (
              <div className="text-center py-12">
                <p className="text-red-400">Failed to load audit log</p>
                <p className="text-white/60 text-sm mt-2">
                  {error instanceof Error ? error.message : 'Unknown error'}
                </p>
              </div>
            )}

            {!isLoading && !error && data && (
              <>
                {data.audit_records.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-white/60">No audit records found</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {data.audit_records.map((record: AuditRecord) => (
                      <div
                        key={record.id}
                        className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <span
                              className={`px-3 py-1 text-xs font-medium rounded-full border ${getActionBadgeColor(
                                record.action_type
                              )}`}
                            >
                              {record.action_type}
                            </span>
                            <span className="text-white/60 text-sm">
                              by {record.admin_user}
                            </span>
                          </div>
                          <span className="text-white/40 text-sm">
                            {formatTimestamp(record.timestamp)}
                          </span>
                        </div>

                        {record.changes && (
                          <div className="mt-3 p-3 bg-black/20 rounded border border-white/5">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              {record.changes.before && (
                                <div>
                                  <p className="text-white/40 mb-1 text-xs">Before:</p>
                                  <pre className="text-white/60 text-xs overflow-x-auto">
                                    {JSON.stringify(record.changes.before, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {record.changes.after && (
                                <div>
                                  <p className="text-white/40 mb-1 text-xs">After:</p>
                                  <pre className="text-white/60 text-xs overflow-x-auto">
                                    {JSON.stringify(record.changes.after, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {record.notes && (
                          <p className="mt-2 text-white/60 text-sm italic">
                            Note: {record.notes}
                          </p>
                        )}

                        {record.ip_address && (
                          <p className="mt-2 text-white/40 text-xs">
                            IP: {record.ip_address}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Pagination */}
                {data.total > limit && (
                  <div className="flex items-center justify-between mt-6 pt-6 border-t border-white/10">
                    <p className="text-sm text-white/60">
                      Showing {((page - 1) * limit) + 1}-{Math.min(page * limit, data.total)} of{' '}
                      {data.total} records
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setPage(Math.max(1, page - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
                      >
                        Previous
                      </button>
                      <span className="text-white/60 px-4">Page {page}</span>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={!data.has_more}
                        className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10 transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-white/10 flex justify-end">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
