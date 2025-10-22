/**
 * ArchiveConfirmationDialog Component
 * 
 * Glass-themed confirmation dialog for archiving tools
 */
import { useState } from 'react';
import { api } from '../services/api';

interface Tool {
  id: string;
  name: string;
}

interface ArchiveConfirmationDialogProps {
  tool: Tool | null;
  adminToken: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const ArchiveConfirmationDialog = ({
  tool,
  adminToken,
  onClose,
  onSuccess,
}: ArchiveConfirmationDialogProps) => {
  const [isArchiving, setIsArchiving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!tool) return null;

  const handleArchive = async () => {
    setError(null);
    setIsArchiving(true);

    try {
      await api.archiveTool(tool.id, adminToken);
      onSuccess();
      onClose();
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Failed to archive tool';
      setError(message);
    } finally {
      setIsArchiving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-md w-full">
        <div className="p-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="text-4xl">📦</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white mb-2">Archive Tool</h2>
              <p className="text-gray-300 text-sm">
                Are you sure you want to archive <strong className="text-white">"{tool.name}"</strong>?
              </p>
            </div>
          </div>

          {error && (
            <div className="p-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Archive Information */}
          <div className="mb-6 p-4 bg-dark-elevated/50 border border-glass-border rounded-lg">
            <p className="text-gray-300 text-sm mb-2">
              Archiving this tool will:
            </p>
            <ul className="text-xs text-gray-400 space-y-1 list-disc list-inside">
              <li>Remove it from the active tools list</li>
              <li>Preserve all historical sentiment data</li>
              <li>Allow you to restore it later if needed</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleArchive}
              disabled={isArchiving}
              className="flex-1 glass-button bg-yellow-900/40 border-yellow-700/50 text-yellow-300 hover:bg-yellow-900/60 hover:border-yellow-600/60 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isArchiving ? 'Archiving...' : 'Archive Tool'}
            </button>
            <button
              onClick={onClose}
              disabled={isArchiving}
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
