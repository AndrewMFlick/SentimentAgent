/**
 * ToolEditModal Component
 * 
 * Glass-themed modal for editing tool details with multi-category support
 */
import { useState, useEffect } from 'react';
import { Tool, ToolCategory } from '../types';

interface ToolEditModalProps {
  tool: Tool | null;
  adminToken: string;
  onClose: () => void;
  onSuccess: (message?: string) => void;
  onConflict?: (message: string) => void;
  onValidationError?: (errors: Record<string, string>) => void;
}

export interface ToolUpdateData {
  name?: string;
  vendor?: string;
  categories?: string[];
  description?: string;
}

const CATEGORY_OPTIONS = [
  { value: 'code_assistant', label: 'Code Assistant' },
  { value: 'autonomous_agent', label: 'Autonomous Agent' },
  { value: 'code_review', label: 'Code Review' },
  { value: 'testing', label: 'Testing' },
  { value: 'devops', label: 'DevOps' },
  { value: 'project_management', label: 'Project Management' },
  { value: 'collaboration', label: 'Collaboration' },
  { value: 'other', label: 'Other' },
];

export const ToolEditModal = ({
  tool,
  adminToken,
  onClose,
  onSuccess,
  onConflict,
  onValidationError,
}: ToolEditModalProps) => {
  const [formData, setFormData] = useState<ToolUpdateData>({
    name: '',
    vendor: '',
    categories: [],
    description: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Populate form when tool changes
  useEffect(() => {
    if (tool) {
      setFormData({
        name: tool.name,
        vendor: tool.vendor,
        categories: tool.categories,
        description: tool.description || '',
      });
      setError(null);
      setErrors({});
    }
  }, [tool]);

  if (!tool) return null;

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      newErrors.name = 'Tool name is required';
    }

    if (!formData.vendor?.trim()) {
      newErrors.vendor = 'Vendor is required';
    }

    if (!formData.categories || formData.categories.length === 0) {
      newErrors.categories = 'At least 1 category is required';
    } else if (formData.categories.length > 5) {
      newErrors.categories = 'Maximum 5 categories allowed';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      // Get ETag from tool metadata if available
      const etag = (tool as any)._etag || undefined;
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Admin-Token': adminToken,
      };

      if (etag) {
        headers['If-Match'] = etag;
      }

      const response = await fetch(
        `http://localhost:8000/api/v1/admin/tools/${tool.id}`,
        {
          method: 'PUT',
          headers,
          body: JSON.stringify(formData),
        }
      );

      if (!response.ok) {
        if (response.status === 409) {
          // Conflict - concurrent modification
          const data = await response.json();
          const message = data.detail || 'Concurrent modification detected';
          setError(message);
          if (onConflict) {
            onConflict(message);
          }
          return;
        } else if (response.status === 400) {
          // Validation error
          const data = await response.json();
          const message = data.detail || 'Validation error';
          setError(message);
          if (onValidationError) {
            // Try to parse field-specific errors
            const fieldErrors: Record<string, string> = {};
            fieldErrors.general = message;
            setErrors(fieldErrors);
            onValidationError(fieldErrors);
          }
          return;
        } else {
          const data = await response.json();
          throw new Error(data.detail || 'Failed to update tool');
        }
      }

      const data = await response.json();
      onSuccess(data.message || 'Tool updated successfully');
      onClose();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to update tool';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const toggleCategory = (category: string) => {
    const categories = formData.categories || [];
    const isSelected = categories.includes(category);

    if (isSelected) {
      // Remove category
      setFormData({
        ...formData,
        categories: categories.filter((c) => c !== category),
      });
    } else {
      // Add category (max 5)
      if (categories.length < 5) {
        setFormData({
          ...formData,
          categories: [...categories, category],
        });
      }
    }
  };

  const isCategorySelected = (category: string): boolean => {
    return (formData.categories || []).includes(category);
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
              <label className="block text-sm font-bold text-gray-200 mb-2">
                Categories *{' '}
                <span className="text-gray-500 font-normal text-xs">
                  (Select 1-5)
                </span>
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {CATEGORY_OPTIONS.map((option) => {
                  const isSelected = isCategorySelected(option.value);
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => toggleCategory(option.value)}
                      disabled={
                        isSubmitting ||
                        (!isSelected &&
                          (formData.categories?.length || 0) >= 5)
                      }
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        isSelected
                          ? 'bg-blue-500/20 border-blue-500 text-blue-300'
                          : 'bg-white/5 border-white/10 text-gray-400 hover:border-white/30 hover:text-gray-300'
                      } border disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
              {errors.categories && (
                <p className="mt-2 text-sm text-red-400">
                  {errors.categories}
                </p>
              )}
              <p className="mt-2 text-xs text-gray-500">
                Selected: {formData.categories?.length || 0} / 5
              </p>
            </div>

            <div>
              <label htmlFor="edit-description" className="block text-sm font-bold text-gray-200 mb-2">
                Description
              </label>
              <textarea
                id="edit-description"
                name="description"
                value={formData.description || ''}
                onChange={handleChange}
                maxLength={1000}
                rows={4}
                disabled={isSubmitting}
                className="glass-input w-full resize-none"
                placeholder="Optional description of the tool..."
              />
              <div className="text-xs text-gray-500 mt-1">
                {(formData.description || '').length}/1000 characters
              </div>
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
