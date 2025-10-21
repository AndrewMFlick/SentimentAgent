/**
 * AliasLinkModal Component
 * 
 * Modal dialog for linking a tool as an alias of another primary tool
 */
import { useState } from 'react';
import { AITool } from '../types';

interface AliasLinkModalProps {
  aliasToolName: string;
  aliasToolId: string;
  tools: AITool[];
  onLink: (primaryToolId: string) => Promise<void>;
  onClose: () => void;
}

export const AliasLinkModal = ({
  aliasToolName,
  aliasToolId,
  tools,
  onLink,
  onClose
}: AliasLinkModalProps) => {
  const [selectedPrimaryId, setSelectedPrimaryId] = useState<string>('');
  const [isLinking, setIsLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter out the alias tool itself from the list of potential primary tools
  const availablePrimaryTools = tools.filter(tool => tool.id !== aliasToolId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedPrimaryId) {
      setError('Please select a primary tool');
      return;
    }

    setIsLinking(true);
    setError(null);

    try {
      await onLink(selectedPrimaryId);
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to link alias';
      setError(message);
    } finally {
      setIsLinking(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="glass-card w-full max-w-md p-6 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          aria-label="Close modal"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Modal header */}
        <h2 className="text-2xl font-bold text-white mb-2">Link Tool Alias</h2>
        <p className="text-sm text-gray-400 mb-6">
          Set <strong className="text-white">{aliasToolName}</strong> as an alias of another primary tool.
          Sentiment data will be consolidated under the primary tool.
        </p>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="primary-tool" className="block text-sm font-bold text-gray-200 mb-2">
              Primary Tool
            </label>
            <select
              id="primary-tool"
              value={selectedPrimaryId}
              onChange={(e) => setSelectedPrimaryId(e.target.value)}
              className="glass-input w-full"
              disabled={isLinking}
              autoFocus
            >
              <option value="">Select a primary tool...</option>
              {availablePrimaryTools.map((tool) => (
                <option key={tool.id} value={tool.id}>
                  {tool.name} ({tool.vendor})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Choose the primary tool that this alias should point to
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="glass-button px-4 py-2 text-sm"
              disabled={isLinking}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="glass-button bg-blue-600/30 border-blue-500/50 hover:bg-blue-600/40 px-4 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLinking || !selectedPrimaryId}
            >
              {isLinking ? 'Linking...' : 'Link Alias'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
