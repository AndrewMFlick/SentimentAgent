/**
 * AdminToolApproval Component
 * 
 * Admin panel for reviewing and approving/rejecting auto-detected AI tools
 */
import { useState } from 'react';
import { usePendingTools, useApproveTool, useRejectTool } from '../services/toolApi';
import { ToolTable } from './ToolTable';
import { ToolEditModal } from './ToolEditModal';
import { DeleteConfirmationDialog } from './DeleteConfirmationDialog';

interface Tool {
  id: string;
  name: string;
  vendor: string;
  category: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export const AdminToolApproval = () => {
  const [adminToken, setAdminToken] = useState<string>('');
  const [isTokenSet, setIsTokenSet] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  
  // Active tab state
  const [activeTab, setActiveTab] = useState<'pending' | 'manage'>('pending');
  
  // Tool management state
  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  const [deletingTool, setDeletingTool] = useState<Tool | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Fetch pending tools (only if token is set)
  const {
    data: pendingData,
    isLoading: isLoadingPending,
    error: pendingError,
    refetch: refetchPending
  } = usePendingTools(isTokenSet ? adminToken : null);

  // Approval/rejection hooks
  const { approveTool, isLoading: isApproving } = useApproveTool(adminToken);
  const { rejectTool, isLoading: isRejecting } = useRejectTool(adminToken);

  const handleSetToken = (e: React.FormEvent) => {
    e.preventDefault();
    if (adminToken.trim()) {
      setIsTokenSet(true);
      setActionError(null);
      setActionSuccess(null);
    } else {
      setActionError('Please enter an admin token');
    }
  };

  const handleApprove = async (toolId: string, toolName: string) => {
    setActionError(null);
    setActionSuccess(null);
    
    try {
      await approveTool(toolId);
      setActionSuccess(`Successfully approved "${toolName}"`);
      // Refetch pending tools after successful approval
      await refetchPending();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to approve tool';
      setActionError(message);
    }
  };

  const handleReject = async (toolId: string, toolName: string) => {
    setActionError(null);
    setActionSuccess(null);
    
    try {
      await rejectTool(toolId);
      setActionSuccess(`Successfully rejected "${toolName}"`);
      // Refetch pending tools after successful rejection
      await refetchPending();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to reject tool';
      setActionError(message);
    }
  };

  const handleClearToken = () => {
    setAdminToken('');
    setIsTokenSet(false);
    setActionError(null);
    setActionSuccess(null);
  };

  // Tool management handlers
  const handleEditTool = (tool: Tool) => {
    setEditingTool(tool);
    setActionError(null);
    setActionSuccess(null);
  };

  const handleDeleteTool = (tool: Tool) => {
    setDeletingTool(tool);
    setActionError(null);
    setActionSuccess(null);
  };

  const handleEditSuccess = () => {
    setActionSuccess('Tool updated successfully');
    setRefreshTrigger(prev => prev + 1);
  };

  const handleDeleteSuccess = () => {
    setActionSuccess('Tool deleted successfully');
    setRefreshTrigger(prev => prev + 1);
  };

  // Token input form
  if (!isTokenSet) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg p-5">
        <div className="max-w-screen-xl mx-auto">
          <div className="glass-card p-8">
            <h1 className="text-4xl mb-3 text-white font-bold">Admin Tool Approval</h1>
            <p className="text-gray-400 text-sm mb-6">
              Enter your admin token to view and manage pending AI tool approvals
            </p>

            <form onSubmit={handleSetToken} className="flex flex-col gap-4 max-w-md">
              <label htmlFor="admin-token" className="text-sm font-bold text-gray-200">
                Admin Token
              </label>
              <input
                id="admin-token"
                type="password"
                value={adminToken}
                onChange={(e) => setAdminToken(e.target.value)}
                placeholder="Enter admin token"
                className="glass-input"
                autoFocus
              />
              <button
                type="submit"
                className="glass-button bg-blue-600/30 border-blue-500/50 hover:bg-blue-600/40 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!adminToken.trim()}
              >
                Authenticate
              </button>
            </form>

            {actionError && (
              <div className="p-4 mt-6 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
                <strong>Error:</strong> {actionError}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoadingPending) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg p-5">
        <div className="max-w-screen-xl mx-auto">
          <div className="glass-card p-8">
            <h1 className="text-4xl mb-3 text-white font-bold">Admin Tool Approval</h1>
            <div className="flex flex-col items-center py-16 gap-4">
              <div className="border-4 border-dark-elevated border-t-blue-500 rounded-full w-12 h-12 animate-spin"></div>
              <p className="text-gray-300">Loading pending tools...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (pendingError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg p-5">
        <div className="max-w-screen-xl mx-auto">
          <div className="glass-card p-8">
            <h1 className="text-4xl mb-3 text-white font-bold">Admin Tool Approval</h1>
            <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 mb-6">
              <strong>Error loading pending tools:</strong>{' '}
              {pendingError instanceof Error ? pendingError.message : 'Unknown error'}
            </div>
            <button onClick={handleClearToken} className="glass-button">
              Clear Token & Re-authenticate
            </button>
          </div>
        </div>
      </div>
    );
  }

  const pendingTools = pendingData?.tools || [];

  // Main admin panel
  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-bg via-dark-surface to-dark-bg p-5">
      <div className="max-w-screen-xl mx-auto">
        <div className="glass-card p-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-4xl mb-3 text-white font-bold">Admin Tool Management</h1>
              <p className="text-gray-400 text-sm">
                {activeTab === 'pending' 
                  ? `Review and approve auto-detected AI tools (${pendingTools.length} pending)`
                  : 'Manage all AI tools in the system'}
              </p>
            </div>
            <button onClick={handleClearToken} className="glass-button">
              Logout
            </button>
          </div>

          {/* Action feedback */}
          {actionSuccess && (
            <div className="p-4 bg-emerald-900/30 border border-emerald-700/50 rounded-lg text-emerald-300 mb-4">
              <strong>Success:</strong> {actionSuccess}
            </div>
          )}
          {actionError && (
            <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 mb-4">
              <strong>Error:</strong> {actionError}
            </div>
          )}

          {/* Tab Navigation */}
          <div className="flex gap-2 border-b border-glass-border mb-6">
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-6 py-3 font-bold text-sm transition-all ${
                activeTab === 'pending'
                  ? 'border-b-2 border-blue-500 text-blue-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Pending Approvals {pendingTools.length > 0 && `(${pendingTools.length})`}
            </button>
            <button
              onClick={() => setActiveTab('manage')}
              className={`px-6 py-3 font-bold text-sm transition-all ${
                activeTab === 'manage'
                  ? 'border-b-2 border-blue-500 text-blue-400'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              Manage Tools
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'pending' && (
            <>
              {/* Pending tools table */}
              {pendingTools.length === 0 ? (
                <div className="text-center py-20 px-5">
                  <p className="text-xl text-gray-300 mb-2">No pending tools</p>
                  <p className="text-sm text-gray-500">
                    All auto-detected tools have been reviewed
                  </p>
                </div>
              ) : (
            <div className="overflow-x-auto mt-6">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">Tool Name</th>
                    <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">Vendor</th>
                    <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">7-Day Mentions</th>
                    <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">First Detected</th>
                    <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingTools.map((tool) => (
                    <tr key={tool.id} className="border-b border-glass-border hover:bg-dark-elevated/30 transition-colors">
                      <td className="p-4 text-sm text-gray-200">
                        <strong className="text-white">{tool.name}</strong>
                        {tool.description && (
                          <div className="text-xs text-gray-500 mt-1">{tool.description}</div>
                        )}
                      </td>
                      <td className="p-4 text-sm text-gray-300">{tool.vendor || 'Unknown'}</td>
                      <td className="p-4 text-sm text-gray-300">
                        <span className="inline-block px-3 py-1 bg-blue-900/40 border border-blue-700/50 rounded-full text-xs font-bold text-blue-300">
                          {tool.mention_count_7d || 0} mentions
                        </span>
                      </td>
                      <td className="p-4 text-sm text-gray-300">
                        {tool.first_detected
                          ? new Date(tool.first_detected).toLocaleDateString()
                          : 'Unknown'}
                      </td>
                      <td className="p-4 text-sm text-gray-300">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleApprove(tool.id, tool.name)}
                            disabled={isApproving || isRejecting}
                            className="px-3 py-1.5 text-xs font-bold bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 rounded-lg transition-all hover:bg-emerald-900/60 hover:border-emerald-600/60 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Approve this tool"
                          >
                            {isApproving ? '⏳' : '✓'} Approve
                          </button>
                          <button
                            onClick={() => handleReject(tool.id, tool.name)}
                            disabled={isApproving || isRejecting}
                            className="px-3 py-1.5 text-xs font-bold bg-red-900/40 text-red-300 border border-red-700/50 rounded-lg transition-all hover:bg-red-900/60 hover:border-red-600/60 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Reject this tool"
                          >
                            {isRejecting ? '⏳' : '✗'} Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="mt-8 p-5 bg-dark-elevated/50 border border-glass-border rounded-lg">
            <p className="text-xs text-gray-400 m-0">
              <strong className="text-gray-300">Note:</strong> Tools with 50+ mentions in the last 7 days are
              automatically queued for approval. Approved tools will appear in the public
              dashboard.
            </p>
          </div>
            </>
          )}

          {/* Manage Tools Tab */}
          {activeTab === 'manage' && (
            <ToolTable
              adminToken={adminToken}
              onEdit={handleEditTool}
              onDelete={handleDeleteTool}
              refreshTrigger={refreshTrigger}
            />
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {editingTool && (
        <ToolEditModal
          tool={editingTool}
          adminToken={adminToken}
          onClose={() => setEditingTool(null)}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deletingTool && (
        <DeleteConfirmationDialog
          tool={deletingTool}
          adminToken={adminToken}
          onClose={() => setDeletingTool(null)}
          onSuccess={handleDeleteSuccess}
        />
      )}
    </div>
  );
};

