import React, { useState } from 'react';
import { api } from '../services/api';

interface AdminToolManagementProps {
  adminToken: string;
  onToolCreated?: () => void;
}

export const AdminToolManagement: React.FC<AdminToolManagementProps> = ({ 
  adminToken,
  onToolCreated 
}) => {
  // Form state
  const [toolName, setToolName] = useState('');
  const [vendor, setVendor] = useState('');
  const [category, setCategory] = useState<'code-completion' | 'chat' | 'analysis'>('code-completion');
  const [description, setDescription] = useState('');
  
  // UI state
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form validation
  const isFormValid = () => {
    return toolName.trim().length > 0 && vendor.trim().length > 0;
  };

  // Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isFormValid()) {
      setMessage('Please fill in all required fields');
      setMessageType('error');
      return;
    }

    setIsSubmitting(true);
    setMessage('');

    try {
      const response = await api.createTool(
        {
          name: toolName,
          vendor: vendor,
          category: category,
          description: description || undefined,
        },
        adminToken
      );

      setMessage(`✓ ${response.message}`);
      setMessageType('success');

      // Reset form
      setToolName('');
      setVendor('');
      setCategory('code-completion');
      setDescription('');

      // Notify parent component
      if (onToolCreated) {
        onToolCreated();
      }

      // Clear success message after 5 seconds
      setTimeout(() => {
        setMessage('');
      }, 5000);

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create tool';
      setMessage(`✗ ${errorMessage}`);
      setMessageType('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="glass-card p-6 mb-8">
      <h2 className="text-2xl font-bold text-white mb-6">Add New AI Tool</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Tool Name */}
        <div>
          <label htmlFor="tool-name" className="block text-sm font-medium mb-2 text-gray-200">
            Tool Name <span className="text-red-400">*</span>
          </label>
          <input
            id="tool-name"
            type="text"
            value={toolName}
            onChange={(e) => setToolName(e.target.value)}
            placeholder="e.g., GitHub Copilot"
            className="glass-input w-full"
            maxLength={100}
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Vendor */}
        <div>
          <label htmlFor="vendor" className="block text-sm font-medium mb-2 text-gray-200">
            Vendor <span className="text-red-400">*</span>
          </label>
          <input
            id="vendor"
            type="text"
            value={vendor}
            onChange={(e) => setVendor(e.target.value)}
            placeholder="e.g., GitHub"
            className="glass-input w-full"
            maxLength={100}
            required
            disabled={isSubmitting}
          />
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium mb-2 text-gray-200">
            Category <span className="text-red-400">*</span>
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value as 'code-completion' | 'chat' | 'analysis')}
            className="glass-input w-full"
            required
            disabled={isSubmitting}
          >
            <option value="code-completion" className="bg-dark-surface text-gray-200">
              Code Completion
            </option>
            <option value="chat" className="bg-dark-surface text-gray-200">
              Chat
            </option>
            <option value="analysis" className="bg-dark-surface text-gray-200">
              Analysis
            </option>
          </select>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium mb-2 text-gray-200">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of the tool (optional)"
            className="glass-input w-full resize-none"
            rows={3}
            maxLength={500}
            disabled={isSubmitting}
          />
        </div>

        {/* Message */}
        {message && (
          <div
            className={`p-4 rounded-lg border ${
              messageType === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            }`}
          >
            {message}
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={!isFormValid() || isSubmitting}
            className={`
              px-6 py-3 rounded-lg font-semibold
              transition-all duration-200
              ${
                isFormValid() && !isSubmitting
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                  : 'bg-gray-600/50 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </span>
            ) : (
              'Add Tool'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
