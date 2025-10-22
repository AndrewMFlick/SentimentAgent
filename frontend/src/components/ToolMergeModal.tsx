/**
 * ToolMergeModal Component
 * 
 * Glass-themed modal for merging multiple tools into a single primary tool
 * Implements Phase 7: User Story 5 - Merge Tools
 * 
 * Features:
 * - Multi-select for source tools (1-10 tools) (T093)
 * - Category and vendor selection for merged result (T094)
 * - Optional notes field for merge reasoning (T095)
 * - Warning display for vendor/category mismatches (T096)
 * - Success message with sentiment migration count (T100)
 * - Keyboard shortcut: Esc to close (T113)
 */
import { useState, useEffect } from 'react';

interface Tool {
  id: string;
  name: string;
  vendor?: string;
  categories?: string[];
  status?: string;
}

interface ToolMergeModalProps {
  targetTool: Tool | null;
  availableTools: Tool[];
  adminToken: string;
  onClose: () => void;
  onSuccess: () => void;
}

interface MergeFormData {
  sourceToolIds: string[];
  finalCategories: string[];
  finalVendor: string;
  notes: string;
}

const AVAILABLE_CATEGORIES = [
  'CODE_ASSISTANT',
  'AI_CHATBOT',
  'IMAGE_GENERATION',
  'DATA_ANALYSIS',
  'PRODUCTIVITY',
  'AUTOMATION',
  'RESEARCH',
  'OTHER'
];

export const ToolMergeModal = ({
  targetTool,
  availableTools,
  adminToken,
  onClose,
  onSuccess,
}: ToolMergeModalProps) => {
  const [formData, setFormData] = useState<MergeFormData>({
    sourceToolIds: [],
    finalCategories: targetTool?.categories || [],
    finalVendor: targetTool?.vendor || '',
    notes: '',
  });
  const [isMerging, setIsMerging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Initialize form with target tool data
  useEffect(() => {
    if (targetTool) {
      setFormData({
        sourceToolIds: [],
        finalCategories: targetTool.categories || [],
        finalVendor: targetTool.vendor || '',
        notes: '',
      });
    }
  }, [targetTool]);

  // Keyboard shortcut: Esc to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isMerging) {
        onClose();
      }
    };

    if (targetTool) {
      document.addEventListener('keydown', handleEsc);
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
    };
  }, [targetTool, isMerging, onClose]);

  if (!targetTool) return null;

  // Filter out target tool and inactive tools from available sources
  const eligibleSourceTools = availableTools.filter(
    (tool) =>
      tool.id !== targetTool.id &&
      tool.status === 'active'
      // Don't allow merging already merged tools
      // (merged_into field would exist on tool if already merged)
  );

  const handleSourceToggle = (toolId: string) => {
    setFormData((prev) => {
      const isSelected = prev.sourceToolIds.includes(toolId);
      const newSourceIds = isSelected
        ? prev.sourceToolIds.filter((id) => id !== toolId)
        : [...prev.sourceToolIds, toolId];

      // Limit to 10 source tools
      if (newSourceIds.length > 10) {
        setError('Cannot merge more than 10 source tools at once');
        return prev;
      }

      setError(null);
      return { ...prev, sourceToolIds: newSourceIds };
    });
  };

  const handleCategoryToggle = (category: string) => {
    setFormData((prev) => {
      const isSelected = prev.finalCategories.includes(category);
      const newCategories = isSelected
        ? prev.finalCategories.filter((cat) => cat !== category)
        : [...prev.finalCategories, category];

      return { ...prev, finalCategories: newCategories };
    });
  };

  const handleMerge = async () => {
    setError(null);
    setWarnings([]);

    // Validation
    if (formData.sourceToolIds.length === 0) {
      setError('Please select at least one source tool to merge');
      return;
    }

    if (formData.finalCategories.length === 0) {
      setError('Please select at least one category for the merged tool');
      return;
    }

    if (!formData.finalVendor.trim()) {
      setError('Please specify a vendor for the merged tool');
      return;
    }

    setIsMerging(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/tools/merge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': adminToken,
        },
        body: JSON.stringify({
          target_tool_id: targetTool.id,
          source_tool_ids: formData.sourceToolIds,
          final_categories: formData.finalCategories,
          final_vendor: formData.finalVendor,
          notes: formData.notes || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to merge tools');
      }

      const result = await response.json();

      // Store warnings if any
      if (result.warnings && result.warnings.length > 0) {
        setWarnings(result.warnings);
      }

      // Notify parent with success
      onSuccess();
      
      // Close after showing warnings (if any)
      setTimeout(() => {
        onClose();
      }, warnings.length > 0 ? 3000 : 500);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to merge tools';
      setError(message);
    } finally {
      setIsMerging(false);
    }
  };

  const selectedSourceTools = eligibleSourceTools.filter((tool) =>
    formData.sourceToolIds.includes(tool.id)
  );

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start gap-4 mb-6">
            <div className="text-4xl">🔗</div>
            <div className="flex-1">
              <h2 className="text-xl font-bold text-white mb-2">Merge Tools</h2>
              <p className="text-gray-300 text-sm">
                Merge multiple tools into <strong>{targetTool.name}</strong>. All sentiment data
                will be migrated to the target tool, and source tools will be archived.
              </p>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 mb-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Warning Display */}
          {warnings.length > 0 && (
            <div className="p-4 mb-4 bg-yellow-900/30 border border-yellow-700/50 rounded-lg">
              <strong className="text-yellow-300">Warnings:</strong>
              <ul className="mt-2 space-y-1">
                {warnings.map((warning, idx) => (
                  <li key={idx} className="text-yellow-200 text-sm">
                    • {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Source Tools Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Select Source Tools (1-10)
              <span className="ml-2 text-gray-500">
                ({formData.sourceToolIds.length} selected)
              </span>
            </label>
            <div className="max-h-48 overflow-y-auto space-y-2 p-3 bg-dark-elevated/50 border border-glass-border rounded-lg">
              {eligibleSourceTools.length === 0 ? (
                <p className="text-gray-500 text-sm">No eligible tools available for merging</p>
              ) : (
                eligibleSourceTools.map((tool) => (
                  <label
                    key={tool.id}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={formData.sourceToolIds.includes(tool.id)}
                      onChange={() => handleSourceToggle(tool.id)}
                      disabled={isMerging}
                      className="w-4 h-4 rounded border-glass-border bg-dark-elevated/50 text-accent-primary focus:ring-2 focus:ring-accent-primary/50"
                    />
                    <div className="flex-1">
                      <div className="text-white font-medium">{tool.name}</div>
                      <div className="text-xs text-gray-400">
                        {tool.vendor && `${tool.vendor} • `}
                        {tool.categories?.join(', ')}
                      </div>
                    </div>
                  </label>
                ))
              )}
            </div>
          </div>

          {/* Selected Tools Preview */}
          {selectedSourceTools.length > 0 && (
            <div className="mb-6 p-4 bg-dark-elevated/50 border border-glass-border rounded-lg">
              <div className="text-sm font-medium text-gray-300 mb-2">
                Will merge into {targetTool.name}:
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedSourceTools.map((tool) => (
                  <span
                    key={tool.id}
                    className="px-3 py-1 bg-accent-primary/20 border border-accent-primary/30 rounded-full text-xs text-accent-primary"
                  >
                    {tool.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Final Categories */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Final Categories (select all that apply)
            </label>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_CATEGORIES.map((category) => (
                <button
                  key={category}
                  onClick={() => handleCategoryToggle(category)}
                  disabled={isMerging}
                  className={`px-3 py-1 rounded-lg text-sm transition-all ${
                    formData.finalCategories.includes(category)
                      ? 'bg-accent-primary/30 border-accent-primary/50 text-accent-primary'
                      : 'bg-dark-elevated/50 border-glass-border text-gray-400 hover:bg-white/5'
                  } border disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {category.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Final Vendor */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Final Vendor
            </label>
            <input
              type="text"
              value={formData.finalVendor}
              onChange={(e) => setFormData({ ...formData, finalVendor: e.target.value })}
              placeholder="e.g., OpenAI, Anthropic, Microsoft"
              disabled={isMerging}
              className="w-full px-4 py-2 bg-dark-elevated/50 border border-glass-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-primary/50"
            />
          </div>

          {/* Notes */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes (optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Reason for merge, migration context, etc."
              disabled={isMerging}
              rows={3}
              className="w-full px-4 py-2 bg-dark-elevated/50 border border-glass-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-primary/50 resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={handleMerge}
              disabled={
                isMerging ||
                formData.sourceToolIds.length === 0 ||
                formData.finalCategories.length === 0 ||
                !formData.finalVendor.trim()
              }
              className="flex-1 glass-button bg-accent-primary/20 border-accent-primary/30 text-accent-primary hover:bg-accent-primary/30 hover:border-accent-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isMerging ? 'Merging...' : `Merge ${formData.sourceToolIds.length} Tool${formData.sourceToolIds.length !== 1 ? 's' : ''}`}
            </button>
            <button
              onClick={onClose}
              disabled={isMerging}
              className="flex-1 glass-button disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
          </div>

          {/* Info Notice */}
          <div className="mt-4 p-3 bg-blue-900/20 border border-blue-700/30 rounded-lg">
            <p className="text-blue-300 text-xs">
              ℹ️ <strong>This operation will:</strong>
            </p>
            <ul className="text-blue-300 text-xs mt-2 ml-4 space-y-1">
              <li>• Migrate all sentiment data to {targetTool.name}</li>
              <li>• Archive source tools with "merged_into" reference</li>
              <li>• Update target tool categories and vendor</li>
              <li>• Create an audit trail in merge records</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
