import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { ToolTable } from './ToolTable';
import { ToolEditModal } from './ToolEditModal';
import { ArchiveConfirmationDialog } from './ArchiveConfirmationDialog';
import { DeleteConfirmationDialog } from './DeleteConfirmationDialog';
import { ToolMergeModal } from './ToolMergeModal';
import { MergeHistoryModal } from './MergeHistoryModal';
import AuditLogViewer from './AuditLogViewer';
import { Tool } from '../types';

interface AdminToolManagementProps {
  adminToken: string;
  onToolCreated?: () => void;
}

export const AdminToolManagement: React.FC<AdminToolManagementProps> = ({ 
  adminToken,
  onToolCreated 
}) => {
  const queryClient = useQueryClient();
  
  // View state
  const [activeView, setActiveView] = useState<'list' | 'create'>('list');
  
  // Edit modal state
  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  
  // Archive modal state
  const [archivingTool, setArchivingTool] = useState<Tool | null>(null);
  
  // Delete modal state
  const [deletingTool, setDeletingTool] = useState<Tool | null>(null);
  
  // Merge modal state
  const [mergingTool, setMergingTool] = useState<Tool | null>(null);
  const [availableTools, setAvailableTools] = useState<Tool[]>([]);
  
  // Merge history modal state
  const [historyTool, setHistoryTool] = useState<Tool | null>(null);
  
  // Audit log modal state
  const [auditLogTool, setAuditLogTool] = useState<Tool | null>(null);
  
  // Form state
  const [toolName, setToolName] = useState('');
  const [vendor, setVendor] = useState('');
  const [categories, setCategories] = useState<string[]>(['code_assistant']);
  const [description, setDescription] = useState('');
  
  // UI state
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Create tool mutation
  const createToolMutation = useMutation({
    mutationFn: async (toolData: {
      name: string;
      vendor: string;
      categories: string[];
      description?: string;
    }) => {
      return await api.createTool(toolData, adminToken);
    },
    onSuccess: (response) => {
      setMessage(`✓ ${response.message}`);
      setMessageType('success');

      // Reset form
      setToolName('');
      setVendor('');
      setCategories(['code_assistant']);
      setDescription('');

      // Invalidate and refetch tools query
      queryClient.invalidateQueries({ queryKey: ['admin-tools'] });

      // Refresh trigger for ToolTable
      setRefreshTrigger(prev => prev + 1);

      // Notify parent component
      if (onToolCreated) {
        onToolCreated();
      }

      // Switch back to list view
      setTimeout(() => {
        setActiveView('list');
        setMessage('');
      }, 2000);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create tool';
      setMessage(`✗ ${errorMessage}`);
      setMessageType('error');
    },
  });

  // Edit handler
  const handleEdit = (tool: Tool) => {
    setEditingTool(tool);
    setMessage(''); // Clear any existing messages
  };

  // Edit conflict handler
  const handleEditConflict = (conflictMessage: string) => {
    setMessage(`⚠️ ${conflictMessage}`);
    setMessageType('error');
    
    // Refresh the tools list to get latest data
    queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
    setRefreshTrigger(prev => prev + 1);
  };

  // Handle edit validation error (400)
  const handleEditValidationError = (errors: Record<string, string>) => {
    const errorMsg = Object.values(errors).join(', ');
    setMessage(`⚠️ Validation error: ${errorMsg}`);
    setMessageType('error');
  };

  const handleDelete = (tool: Tool) => {
    // T073: Show DeleteConfirmationDialog
    setDeletingTool(tool);
    setMessage(''); // Clear any existing messages
  };

  // T076, T077: Handle successful deletion
  const handleDeleteSuccess = () => {
    // T076: Invalidate cache and refresh list
    queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
    setRefreshTrigger(prev => prev + 1);
    
    // T077: Success message will be shown by the dialog
    // We'll show a message here after the dialog closes
    setMessage(`✓ Tool permanently deleted`);
    setMessageType('success');
    
    // Clear message after 3 seconds
    setTimeout(() => {
      setMessage('');
    }, 3000);
  };

  // Archive handler
  const handleArchive = (tool: Tool) => {
    setArchivingTool(tool);
    setMessage(''); // Clear any existing messages
  };

  // Unarchive handler
  const handleUnarchive = async (tool: Tool) => {
    setMessage('');
    
    try {
      await api.unarchiveTool(tool.id, adminToken);
      setMessage(`✓ Tool "${tool.name}" has been unarchived successfully`);
      setMessageType('success');
      
      // Invalidate and refetch tools query
      queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
      setRefreshTrigger(prev => prev + 1);
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to unarchive tool';
      setMessage(`✗ ${errorMessage}`);
      setMessageType('error');
    }
  };

  // Archive success callback
  const handleArchiveSuccess = () => {
    setMessage(`✓ Tool has been archived successfully`);
    setMessageType('success');
    
    // Invalidate and refetch tools query
    queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
    setRefreshTrigger(prev => prev + 1);
    
    // Clear message after 3 seconds
    setTimeout(() => setMessage(''), 3000);
  };

  // Merge handler
  const handleMerge = async (tool: Tool, allTools: Tool[]) => {
    setMergingTool(tool);
    setAvailableTools(allTools);
    setMessage(''); // Clear any existing messages
  };

  // Merge success callback
  const handleMergeSuccess = () => {
    setMessage(`✓ Tools merged successfully`);
    setMessageType('success');
    
    // Invalidate and refetch tools query
    queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
    setRefreshTrigger(prev => prev + 1);
    
    // Clear message after 3 seconds
    setTimeout(() => setMessage(''), 3000);
  };

  // View history handler
  const handleViewHistory = (tool: Tool) => {
    setHistoryTool(tool);
  };

  // View audit log handler
  const handleViewAuditLog = (tool: Tool) => {
    setAuditLogTool(tool);
  };

  // Category toggle handler
  const toggleCategory = (category: string) => {
    setCategories(prev => {
      if (prev.includes(category)) {
        // Don't allow removing the last category
        if (prev.length === 1) return prev;
        return prev.filter(c => c !== category);
      } else {
        // Don't allow more than 5 categories
        if (prev.length >= 5) return prev;
        return [...prev, category];
      }
    });
  };

  // Form validation
  const isFormValid = () => {
    return toolName.trim().length > 0 && 
           vendor.trim().length > 0 && 
           categories.length > 0 && 
           categories.length <= 5;
  };

  // Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isFormValid()) {
      setMessage('Please fill in all required fields (1-5 categories)');
      setMessageType('error');
      return;
    }

    setMessage('');

    createToolMutation.mutate({
      name: toolName,
      vendor: vendor,
      categories: categories,
      description: description || undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* View Toggle */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setActiveView('list')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
            activeView === 'list'
              ? 'bg-blue-600/30 border-2 border-blue-500/50 text-white'
              : 'bg-dark-elevated/50 border-2 border-transparent text-gray-400 hover:bg-dark-elevated hover:text-gray-200'
          }`}
        >
          📋 View All Tools
        </button>
        <button
          onClick={() => setActiveView('create')}
          className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 ${
            activeView === 'create'
              ? 'bg-blue-600/30 border-2 border-blue-500/50 text-white'
              : 'bg-dark-elevated/50 border-2 border-transparent text-gray-400 hover:bg-dark-elevated hover:text-gray-200'
          }`}
        >
          ➕ Add New Tool
        </button>
      </div>

      {/* List View */}
      {activeView === 'list' && (
        <div className="glass-card p-6">
          <h2 className="text-2xl font-bold text-white mb-6">All AI Tools</h2>
          <ToolTable
            adminToken={adminToken}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onArchive={handleArchive}
            onUnarchive={handleUnarchive}
            onMerge={handleMerge}
            onViewHistory={handleViewHistory}
            onViewAuditLog={handleViewAuditLog}
            refreshTrigger={refreshTrigger}
          />
        </div>
      )}

      {/* Create View */}
      {activeView === 'create' && (
        <div className="glass-card p-6">
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
            disabled={createToolMutation.isPending}
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
            disabled={createToolMutation.isPending}
          />
        </div>

        {/* Categories (Multi-select) */}
        <div>
          <label className="block text-sm font-medium mb-2 text-gray-200">
            Categories <span className="text-red-400">*</span>
            <span className="text-xs text-gray-400 ml-2">(Select 1-5 categories)</span>
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[
              { value: 'code_assistant', label: 'Code Assistant' },
              { value: 'autonomous_agent', label: 'Autonomous Agent' },
              { value: 'code_review', label: 'Code Review' },
              { value: 'testing', label: 'Testing' },
              { value: 'devops', label: 'DevOps' },
              { value: 'project_management', label: 'Project Management' },
              { value: 'collaboration', label: 'Collaboration' },
              { value: 'other', label: 'Other' },
            ].map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => toggleCategory(cat.value)}
                disabled={createToolMutation.isPending}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  categories.includes(cat.value)
                    ? 'bg-blue-600/30 border-2 border-blue-500/50 text-white'
                    : 'bg-dark-elevated/50 border-2 border-transparent text-gray-400 hover:bg-dark-elevated hover:text-gray-200'
                } ${createToolMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {categories.includes(cat.value) && '✓ '}
                {cat.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Selected: {categories.length} / 5
          </p>
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
            disabled={createToolMutation.isPending}
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
            disabled={!isFormValid() || createToolMutation.isPending}
            className={`
              px-6 py-3 rounded-lg font-semibold
              transition-all duration-200
              ${
                isFormValid() && !createToolMutation.isPending
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                  : 'bg-gray-600/50 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {createToolMutation.isPending ? (
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
      )}

      {/* Edit Modal */}
      <ToolEditModal
        tool={editingTool}
        adminToken={adminToken}
        onClose={() => {
          setEditingTool(null);
        }}
        onSuccess={(message) => {
          setMessage(`✓ ${message || 'Tool updated successfully'}`);
          setMessageType('success');
          setEditingTool(null);
          queryClient.invalidateQueries({ queryKey: ['admin-tools'] });
          setRefreshTrigger(prev => prev + 1);
          setTimeout(() => setMessage(''), 3000);
        }}
        onConflict={handleEditConflict}
        onValidationError={handleEditValidationError}
      />

      {/* Archive Confirmation Dialog */}
      <ArchiveConfirmationDialog
        tool={archivingTool}
        adminToken={adminToken}
        onClose={() => setArchivingTool(null)}
        onSuccess={handleArchiveSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmationDialog
        tool={deletingTool}
        adminToken={adminToken}
        onClose={() => {
          setDeletingTool(null);
        }}
        onSuccess={handleDeleteSuccess}
      />

      {/* Merge Tools Modal */}
      <ToolMergeModal
        targetTool={mergingTool}
        availableTools={availableTools}
        adminToken={adminToken}
        onClose={() => {
          setMergingTool(null);
          setAvailableTools([]);
        }}
        onSuccess={handleMergeSuccess}
      />

      {/* Merge History Modal */}
      <MergeHistoryModal
        tool={historyTool}
        adminToken={adminToken}
        onClose={() => setHistoryTool(null)}
      />

      {/* Audit Log Viewer */}
      <AuditLogViewer
        toolId={auditLogTool?.id || ''}
        toolName={auditLogTool?.name || ''}
        isOpen={!!auditLogTool}
        onClose={() => setAuditLogTool(null)}
        adminToken={adminToken}
      />
    </div>
  );
};
