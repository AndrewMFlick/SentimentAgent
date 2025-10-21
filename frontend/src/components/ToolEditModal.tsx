/**
 * ToolEditModal Component
 * 
 * Glass-themed modal for editing tool details
 */
import { useState, useEffect } from 'react';

interface Tool {
  id: string;
  name: string;
  vendor: string;
  category: string;
  description: string;
  status: string;
}

interface ToolEditModalProps {
  tool: Tool | null;
  adminToken: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const ToolEditModal = ({ tool, adminToken, onClose, onSuccess }: ToolEditModalProps) => {
  const [formData, setFormData] = useState({
    name: '',
    vendor: '',
    category: '',
    description: '',
    status: 'active',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Populate form when tool changes
  useEffect(() => {
    if (tool) {
      setFormData({
        name: tool.name,
        vendor: tool.vendor,
        category: tool.category,
        description: tool.description,
        status: tool.status,
      });
      setError(null);
    }
  }, [tool]);

  if (!tool) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`http://localhost:8000/api/admin/tools/${tool.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': adminToken,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to update tool');
      }

      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update tool';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-2xl font-bold text-white">Edit Tool</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-2xl leading-none"
              aria-label="Close modal"
            >
              ×
            </button>
          </div>

          {error && (
            <div className="p-4 mb-6 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="edit-name" className="block text-sm font-bold text-gray-200 mb-2">
                Tool Name *
              </label>
              <input
                id="edit-name"
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                maxLength={100}
                className="glass-input w-full"
                placeholder="e.g., GitHub Copilot"
              />
            </div>

            <div>
              <label htmlFor="edit-vendor" className="block text-sm font-bold text-gray-200 mb-2">
                Vendor *
              </label>
              <input
                id="edit-vendor"
                type="text"
                name="vendor"
                value={formData.vendor}
                onChange={handleChange}
                required
                maxLength={100}
                className="glass-input w-full"
                placeholder="e.g., GitHub"
              />
            </div>

            <div>
              <label htmlFor="edit-category" className="block text-sm font-bold text-gray-200 mb-2">
                Category *
              </label>
              <select
                id="edit-category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                required
                className="glass-input w-full"
              >
                <option value="">Select a category</option>
                <option value="code-completion">Code Completion</option>
                <option value="chat">Chat</option>
                <option value="analysis">Analysis</option>
              </select>
            </div>

            <div>
              <label htmlFor="edit-description" className="block text-sm font-bold text-gray-200 mb-2">
                Description
              </label>
              <textarea
                id="edit-description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                maxLength={500}
                rows={3}
                className="glass-input w-full resize-none"
                placeholder="Brief description of the tool..."
              />
              <div className="text-xs text-gray-500 mt-1">
                {formData.description.length}/500 characters
              </div>
            </div>

            <div>
              <label htmlFor="edit-status" className="block text-sm font-bold text-gray-200 mb-2">
                Status *
              </label>
              <select
                id="edit-status"
                name="status"
                value={formData.status}
                onChange={handleChange}
                required
                className="glass-input w-full"
              >
                <option value="active">Active</option>
                <option value="deprecated">Deprecated</option>
                <option value="deleted">Deleted</option>
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 glass-button bg-blue-600/30 border-blue-500/50 hover:bg-blue-600/40 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="flex-1 glass-button disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
