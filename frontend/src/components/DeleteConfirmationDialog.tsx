/**
 * DeleteConfirmationDialog Component
 * 
 * Glass-themed confirmation dialog for deleting tools
 */
import { useState } from 'react';

interface Tool {
  id: string;
  name: string;
}

interface DeleteConfirmationDialogProps {
  tool: Tool | null;
  adminToken: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const DeleteConfirmationDialog = ({
  tool,
  adminToken,
  onClose,
  onSuccess,
}: DeleteConfirmationDialogProps) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [hardDelete, setHardDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!tool) return null;

  const handleDelete = async () => {
    setError(null);
    setIsDeleting(true);

    try {
      const params = new URLSearchParams();
      if (hardDelete) {
        params.append('hard_delete', 'true');
      }

      const response = await fetch(
        `http://localhost:8000/api/admin/tools/${tool.id}?${params.toString()}`,
        {
          method: 'DELETE',
          headers: {
            'X-Admin-Token': adminToken,
          },
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete tool');
      }

      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete tool';
      setError(message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-md w-full">
        <div className="p-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="text-4xl">⚠️</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white mb-2">Delete Tool</h2>
              <p className="text-gray-300 text-sm">
                Are you sure you want to delete <strong className="text-white">"{tool.name}"</strong>?
              </p>
            </div>
          </div>

          {error && (
            <div className="p-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Delete Type Selection */}
          <div className="mb-6 p-4 bg-dark-elevated/50 border border-glass-border rounded-lg space-y-3">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="deleteType"
                checked={!hardDelete}
                onChange={() => setHardDelete(false)}
                className="mt-1"
              />
              <div>
                <div className="font-bold text-gray-200 text-sm">Soft Delete (Recommended)</div>
                <div className="text-xs text-gray-400 mt-1">
                  Marks tool as deleted but preserves data. Can be restored later.
                </div>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="deleteType"
                checked={hardDelete}
                onChange={() => setHardDelete(true)}
                className="mt-1"
              />
              <div>
                <div className="font-bold text-red-300 text-sm">Permanent Delete</div>
                <div className="text-xs text-gray-400 mt-1">
                  Permanently removes tool and all related data. Cannot be undone.
                </div>
              </div>
            </label>
          </div>

          {/* Warning for Hard Delete */}
          {hardDelete && (
            <div className="p-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg">
              <p className="text-red-300 text-xs font-bold">
                ⚠️ WARNING: This action is irreversible. All historical sentiment data and
                mentions for this tool will be permanently lost.
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className={`flex-1 glass-button ${
                hardDelete
                  ? 'bg-red-900/40 border-red-700/50 text-red-300 hover:bg-red-900/60 hover:border-red-600/60'
                  : 'bg-yellow-900/40 border-yellow-700/50 text-yellow-300 hover:bg-yellow-900/60 hover:border-yellow-600/60'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isDeleting ? 'Deleting...' : hardDelete ? 'Delete Permanently' : 'Soft Delete'}
            </button>
            <button
              onClick={onClose}
              disabled={isDeleting}
              className="flex-1 glass-button disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
