/**
 * MergeHistoryModal Component
 * 
 * Glass-themed modal for viewing merge history of a tool
 * Implements Phase 7 Task 108: Optional merge history viewer
 * 
 * Features:
 * - Shows all merge operations where tool was target
 * - Displays source tools, sentiment counts, and timestamps
 * - Pagination for large histories
 * - Admin notes and metadata changes
 */
import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface Tool {
  id: string;
  name: string;
}

interface MergeRecord {
  id: string;
  target_tool_id: string;
  source_tool_ids: string[];
  merged_at: string;
  merged_by: string;
  sentiment_count: number;
  target_categories_before: string[];
  target_categories_after: string[];
  target_vendor_before: string;
  target_vendor_after: string;
  source_tools_metadata: Array<{
    id: string;
    name: string;
    vendor: string;
    categories: string[];
    sentiment_count: number;
  }>;
  notes?: string;
}

interface MergeHistoryModalProps {
  tool: Tool | null;
  adminToken: string;
  onClose: () => void;
}

export const MergeHistoryModal = ({
  tool,
  adminToken,
  onClose,
}: MergeHistoryModalProps) => {
  const [mergeRecords, setMergeRecords] = useState<MergeRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    if (!tool) return;

    const fetchMergeHistory = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await api.getMergeHistory(tool.id, adminToken, page, 10);
        setMergeRecords(result.merge_records);
        setTotal(result.total);
        setHasMore(result.has_more);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load merge history';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMergeHistory();
  }, [tool, adminToken, page]);

  if (!tool) return null;

  const formatDate = (isoDate: string) => {
    return new Date(isoDate).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start gap-4 mb-6">
            <div className="text-4xl">📜</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white mb-2">Merge History</h2>
              <p className="text-gray-300 text-sm">
                Viewing merge operations for <strong>{tool.name}</strong>
              </p>
              {total > 0 && (
                <p className="text-gray-400 text-xs mt-1">
                  {total} merge operation{total !== 1 ? 's' : ''} total
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
              title="Close"
            >
              ✕
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-gray-400">Loading merge history...</div>
            </div>
          )}

          {/* No Records */}
          {!isLoading && !error && mergeRecords.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔗</div>
              <p className="text-gray-400 text-lg">No merge operations found</p>
              <p className="text-gray-500 text-sm mt-2">
                This tool has not been the target of any merge operations.
              </p>
            </div>
          )}

          {/* Merge Records */}
          {!isLoading && mergeRecords.length > 0 && (
            <div className="space-y-4">
              {mergeRecords.map((record) => (
                <div
                  key={record.id}
                  className="p-4 bg-dark-elevated/50 border border-glass-border rounded-lg"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="text-sm font-medium text-white">
                        Merged {record.source_tools_metadata.length} tool
                        {record.source_tools_metadata.length !== 1 ? 's' : ''}
                      </div>
                      <div className="text-xs text-gray-400">
                        {formatDate(record.merged_at)} by {record.merged_by}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-accent-primary">
                        {record.sentiment_count.toLocaleString()} records
                      </div>
                      <div className="text-xs text-gray-400">migrated</div>
                    </div>
                  </div>

                  {/* Source Tools */}
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-400 mb-2">
                      Source Tools:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {record.source_tools_metadata.map((source) => (
                        <div
                          key={source.id}
                          className="px-3 py-1.5 bg-purple-900/20 border border-purple-700/30 rounded-lg text-xs"
                        >
                          <div className="font-medium text-purple-300">
                            {source.name}
                          </div>
                          <div className="text-purple-400/70">
                            {source.vendor} • {source.sentiment_count.toLocaleString()} records
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metadata Changes */}
                  {(record.target_vendor_before !== record.target_vendor_after ||
                    JSON.stringify(record.target_categories_before) !==
                      JSON.stringify(record.target_categories_after)) && (
                    <div className="mb-3 p-3 bg-blue-900/10 border border-blue-700/20 rounded-lg">
                      <div className="text-xs font-medium text-blue-300 mb-2">
                        Metadata Changes:
                      </div>
                      {record.target_vendor_before !== record.target_vendor_after && (
                        <div className="text-xs text-gray-300 mb-1">
                          <span className="text-gray-400">Vendor:</span>{' '}
                          <span className="line-through text-gray-500">
                            {record.target_vendor_before}
                          </span>{' '}
                          → <span className="text-white">{record.target_vendor_after}</span>
                        </div>
                      )}
                      {JSON.stringify(record.target_categories_before) !==
                        JSON.stringify(record.target_categories_after) && (
                        <div className="text-xs text-gray-300">
                          <span className="text-gray-400">Categories:</span>{' '}
                          <span className="line-through text-gray-500">
                            {record.target_categories_before.join(', ')}
                          </span>{' '}
                          → <span className="text-white">{record.target_categories_after.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Notes */}
                  {record.notes && (
                    <div className="p-3 bg-gray-900/30 border border-gray-700/30 rounded-lg">
                      <div className="text-xs font-medium text-gray-400 mb-1">
                        Notes:
                      </div>
                      <div className="text-sm text-gray-300">{record.notes}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {!isLoading && total > 10 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-glass-border">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 glass-button disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Previous
              </button>
              <div className="text-sm text-gray-400">
                Page {page} of {Math.ceil(total / 10)}
              </div>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasMore}
                className="px-4 py-2 glass-button disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next →
              </button>
            </div>
          )}

          {/* Close Button */}
          <div className="mt-6">
            <button
              onClick={onClose}
              className="w-full glass-button"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
