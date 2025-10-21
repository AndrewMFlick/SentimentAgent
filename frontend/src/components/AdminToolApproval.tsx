/**
 * AdminToolApproval Component
 * 
 * Admin panel for reviewing and approving/rejecting auto-detected AI tools
 */
import { useState } from 'react';
import { usePendingTools, useApproveTool, useRejectTool } from '../services/toolApi';

export const AdminToolApproval = () => {
  const [adminToken, setAdminToken] = useState<string>('');
  const [isTokenSet, setIsTokenSet] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

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

  // Token input form
  if (!isTokenSet) {
    return (
      <div className="p-5 max-w-screen-xl mx-auto">
        <div className="glass-card p-6">
          <h1 className="text-3xl mb-2 text-white">Admin Tool Approval</h1>
          <p className="text-gray-400 text-sm mb-5">
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
              className="glass-button bg-blue-600/20 border-blue-500/50 hover:bg-blue-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!adminToken.trim()}
            >
              Authenticate
            </button>
          </form>

          {actionError && (
            <div className="p-3 px-4 bg-red-900/40 border border-red-700/50 rounded text-red-300 mb-4 mt-4">
              <strong>Error:</strong> {actionError}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoadingPending) {
    return (
      <div className="p-5 max-w-screen-xl mx-auto">
        <div className="glass-card p-6">
          <h1 className="text-3xl mb-2 text-white">Admin Tool Approval</h1>
          <div className="flex flex-col items-center p-10 gap-4">
            <div className="border-4 border-gray-700 border-t-blue-600 rounded-full w-10 h-10 animate-spin"></div>
            <p className="text-gray-300">Loading pending tools...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (pendingError) {
    return (
      <div className="p-5 max-w-screen-xl mx-auto">
        <div className="glass-card p-6">
          <h1 className="text-3xl mb-2 text-white">Admin Tool Approval</h1>
          <div className="p-3 px-4 bg-red-900/40 border border-red-700/50 rounded text-red-300 mb-4">
            <strong>Error loading pending tools:</strong>{' '}
            {pendingError instanceof Error ? pendingError.message : 'Unknown error'}
          </div>
          <button onClick={handleClearToken} className="glass-button bg-gray-700/50">
            Clear Token & Re-authenticate
          </button>
        </div>
      </div>
    );
  }

  const pendingTools = pendingData?.tools || [];

  // Main admin panel
  return (
    <div className="p-5 max-w-screen-xl mx-auto">
      <div className="glass-card p-6">
        <div className="flex justify-between items-start mb-5">
          <div>
            <h1 className="text-3xl mb-2 text-white">Admin Tool Approval</h1>
            <p className="text-gray-400 text-sm mb-5">
              Review and approve auto-detected AI tools ({pendingTools.length} pending)
            </p>
          </div>
          <button onClick={handleClearToken} className="glass-button bg-gray-700/50">
            Logout
          </button>
        </div>

        {/* Action feedback */}
        {actionSuccess && (
          <div className="p-3 px-4 bg-emerald-900/40 border border-emerald-700/50 rounded text-emerald-300 mb-4">
            <strong>Success:</strong> {actionSuccess}
          </div>
        )}
        {actionError && (
          <div className="p-3 px-4 bg-red-900/40 border border-red-700/50 rounded text-red-300 mb-4">
            <strong>Error:</strong> {actionError}
          </div>
        )}

        {/* Pending tools table */}
        {pendingTools.length === 0 ? (
          <div className="text-center py-16 px-5">
            <p className="text-lg text-gray-400 mb-2">No pending tools</p>
            <p className="text-sm text-gray-500">
              All auto-detected tools have been reviewed
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto mt-5">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left p-3 bg-gray-800/50 border-b-2 border-gray-700 text-sm font-bold text-gray-200">Tool Name</th>
                  <th className="text-left p-3 bg-gray-800/50 border-b-2 border-gray-700 text-sm font-bold text-gray-200">Vendor</th>
                  <th className="text-left p-3 bg-gray-800/50 border-b-2 border-gray-700 text-sm font-bold text-gray-200">7-Day Mentions</th>
                  <th className="text-left p-3 bg-gray-800/50 border-b-2 border-gray-700 text-sm font-bold text-gray-200">First Detected</th>
                  <th className="text-left p-3 bg-gray-800/50 border-b-2 border-gray-700 text-sm font-bold text-gray-200">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingTools.map((tool) => (
                  <tr key={tool.id} className="border-b border-gray-700">
                    <td className="p-3 text-sm text-gray-300">
                      <strong>{tool.name}</strong>
                      {tool.description && (
                        <div className="text-xs text-gray-500 mt-1">{tool.description}</div>
                      )}
                    </td>
                    <td className="p-3 text-sm text-gray-300">{tool.vendor || 'Unknown'}</td>
                    <td className="p-3 text-sm text-gray-300">
                      <span className="inline-block px-2 py-1 bg-blue-900/40 rounded-full text-xs font-bold text-blue-300">
                        {tool.mention_count_7d || 0} mentions
                      </span>
                    </td>
                    <td className="p-3 text-sm text-gray-300">
                      {tool.first_detected
                        ? new Date(tool.first_detected).toLocaleDateString()
                        : 'Unknown'}
                    </td>
                    <td className="p-3 text-sm text-gray-300">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApprove(tool.id, tool.name)}
                          disabled={isApproving || isRejecting}
                          className="px-3 py-1.5 text-xs font-bold bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 rounded transition-all hover:bg-emerald-900/60 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Approve this tool"
                        >
                          {isApproving ? '⏳' : '✓'} Approve
                        </button>
                        <button
                          onClick={() => handleReject(tool.id, tool.name)}
                          disabled={isApproving || isRejecting}
                          className="px-3 py-1.5 text-xs font-bold bg-red-900/40 text-red-300 border border-red-700/50 rounded transition-all hover:bg-red-900/60 disabled:opacity-50 disabled:cursor-not-allowed"
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

        <div className="mt-6 p-4 bg-gray-800/50 rounded">
          <p className="text-xs text-gray-400 m-0">
            <strong>Note:</strong> Tools with 50+ mentions in the last 7 days are
            automatically queued for approval. Approved tools will appear in the public
            dashboard.
          </p>
        </div>
      </div>
    </div>
  );
};

