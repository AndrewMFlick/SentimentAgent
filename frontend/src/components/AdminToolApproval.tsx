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
      <div style={styles.container}>
        <div style={styles.card}>
          <h1 style={styles.title}>Admin Tool Approval</h1>
          <p style={styles.subtitle}>
            Enter your admin token to view and manage pending AI tool approvals
          </p>

          <form onSubmit={handleSetToken} style={styles.form}>
            <label htmlFor="admin-token" style={styles.label}>
              Admin Token
            </label>
            <input
              id="admin-token"
              type="password"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="Enter admin token"
              style={styles.input}
              autoFocus
            />
            <button
              type="submit"
              style={styles.primaryButton}
              disabled={!adminToken.trim()}
            >
              Authenticate
            </button>
          </form>

          {actionError && (
            <div style={styles.errorAlert}>
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
      <div style={styles.container}>
        <div style={styles.card}>
          <h1 style={styles.title}>Admin Tool Approval</h1>
          <div style={styles.loadingContainer}>
            <div style={styles.spinner}></div>
            <p>Loading pending tools...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (pendingError) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h1 style={styles.title}>Admin Tool Approval</h1>
          <div style={styles.errorAlert}>
            <strong>Error loading pending tools:</strong>{' '}
            {pendingError instanceof Error ? pendingError.message : 'Unknown error'}
          </div>
          <button onClick={handleClearToken} style={styles.secondaryButton}>
            Clear Token & Re-authenticate
          </button>
        </div>
      </div>
    );
  }

  const pendingTools = pendingData?.tools || [];

  // Main admin panel
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Admin Tool Approval</h1>
            <p style={styles.subtitle}>
              Review and approve auto-detected AI tools ({pendingTools.length} pending)
            </p>
          </div>
          <button onClick={handleClearToken} style={styles.secondaryButton}>
            Logout
          </button>
        </div>

        {/* Action feedback */}
        {actionSuccess && (
          <div style={styles.successAlert}>
            <strong>Success:</strong> {actionSuccess}
          </div>
        )}
        {actionError && (
          <div style={styles.errorAlert}>
            <strong>Error:</strong> {actionError}
          </div>
        )}

        {/* Pending tools table */}
        {pendingTools.length === 0 ? (
          <div style={styles.emptyState}>
            <p style={styles.emptyText}>No pending tools</p>
            <p style={styles.emptySubtext}>
              All auto-detected tools have been reviewed
            </p>
          </div>
        ) : (
          <div style={styles.tableContainer}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Tool Name</th>
                  <th style={styles.th}>Vendor</th>
                  <th style={styles.th}>7-Day Mentions</th>
                  <th style={styles.th}>First Detected</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingTools.map((tool) => (
                  <tr key={tool.id} style={styles.tr}>
                    <td style={styles.td}>
                      <strong>{tool.name}</strong>
                      {tool.description && (
                        <div style={styles.description}>{tool.description}</div>
                      )}
                    </td>
                    <td style={styles.td}>{tool.vendor || 'Unknown'}</td>
                    <td style={styles.td}>
                      <span style={styles.badge}>
                        {tool.mention_count_7d || 0} mentions
                      </span>
                    </td>
                    <td style={styles.td}>
                      {tool.first_detected
                        ? new Date(tool.first_detected).toLocaleDateString()
                        : 'Unknown'}
                    </td>
                    <td style={styles.td}>
                      <div style={styles.actionButtons}>
                        <button
                          onClick={() => handleApprove(tool.id, tool.name)}
                          disabled={isApproving || isRejecting}
                          style={styles.approveButton}
                          title="Approve this tool"
                        >
                          {isApproving ? '⏳' : '✓'} Approve
                        </button>
                        <button
                          onClick={() => handleReject(tool.id, tool.name)}
                          disabled={isApproving || isRejecting}
                          style={styles.rejectButton}
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

        <div style={styles.footer}>
          <p style={styles.footerText}>
            <strong>Note:</strong> Tools with 50+ mentions in the last 7 days are
            automatically queued for approval. Approved tools will appear in the public
            dashboard.
          </p>
        </div>
      </div>
    </div>
  );
};

// Styles
const styles = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
  } as React.CSSProperties,

  card: {
    backgroundColor: '#1e1e1e',
    borderRadius: '8px',
    padding: '24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
  } as React.CSSProperties,

  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '20px',
  } as React.CSSProperties,

  title: {
    fontSize: '28px',
    marginBottom: '8px',
    color: '#ffffff',
  } as React.CSSProperties,

  subtitle: {
    color: '#a0a0a0',
    fontSize: '14px',
    marginBottom: '20px',
  } as React.CSSProperties,

  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
    maxWidth: '400px',
  } as React.CSSProperties,

  label: {
    fontSize: '14px',
    fontWeight: 'bold' as const,
    color: '#e0e0e0',
  } as React.CSSProperties,

  input: {
    padding: '10px 12px',
    fontSize: '14px',
    borderRadius: '4px',
    border: '1px solid #444',
    backgroundColor: '#2a2a2a',
    color: '#ffffff',
  } as React.CSSProperties,

  primaryButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: 'bold' as const,
    backgroundColor: '#0066cc',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  } as React.CSSProperties,

  secondaryButton: {
    padding: '8px 16px',
    fontSize: '14px',
    backgroundColor: '#444',
    color: '#ffffff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  } as React.CSSProperties,

  loadingContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    padding: '40px',
    gap: '16px',
  } as React.CSSProperties,

  spinner: {
    border: '4px solid #333',
    borderTop: '4px solid #0066cc',
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    animation: 'spin 1s linear infinite',
  } as React.CSSProperties,

  successAlert: {
    padding: '12px 16px',
    backgroundColor: '#1a4d2e',
    border: '1px solid #2d7a4f',
    borderRadius: '4px',
    marginBottom: '16px',
    color: '#a8e6a1',
  } as React.CSSProperties,

  errorAlert: {
    padding: '12px 16px',
    backgroundColor: '#4d1a1a',
    border: '1px solid #7a2d2d',
    borderRadius: '4px',
    marginBottom: '16px',
    color: '#e6a1a1',
  } as React.CSSProperties,

  emptyState: {
    textAlign: 'center' as const,
    padding: '60px 20px',
  } as React.CSSProperties,

  emptyText: {
    fontSize: '18px',
    color: '#a0a0a0',
    marginBottom: '8px',
  } as React.CSSProperties,

  emptySubtext: {
    fontSize: '14px',
    color: '#707070',
  } as React.CSSProperties,

  tableContainer: {
    overflowX: 'auto' as const,
    marginTop: '20px',
  } as React.CSSProperties,

  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
  } as React.CSSProperties,

  th: {
    textAlign: 'left' as const,
    padding: '12px',
    backgroundColor: '#2a2a2a',
    borderBottom: '2px solid #444',
    fontSize: '13px',
    fontWeight: 'bold' as const,
    color: '#e0e0e0',
  } as React.CSSProperties,

  tr: {
    borderBottom: '1px solid #333',
  } as React.CSSProperties,

  td: {
    padding: '12px',
    fontSize: '14px',
    color: '#d0d0d0',
  } as React.CSSProperties,

  description: {
    fontSize: '12px',
    color: '#888',
    marginTop: '4px',
  } as React.CSSProperties,

  badge: {
    display: 'inline-block',
    padding: '4px 8px',
    backgroundColor: '#2a4a7a',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold' as const,
    color: '#a0c0ff',
  } as React.CSSProperties,

  actionButtons: {
    display: 'flex',
    gap: '8px',
  } as React.CSSProperties,

  approveButton: {
    padding: '6px 12px',
    fontSize: '13px',
    fontWeight: 'bold' as const,
    backgroundColor: '#1a4d2e',
    color: '#a8e6a1',
    border: '1px solid #2d7a4f',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  } as React.CSSProperties,

  rejectButton: {
    padding: '6px 12px',
    fontSize: '13px',
    fontWeight: 'bold' as const,
    backgroundColor: '#4d1a1a',
    color: '#e6a1a1',
    border: '1px solid #7a2d2d',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  } as React.CSSProperties,

  footer: {
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#2a2a2a',
    borderRadius: '4px',
  } as React.CSSProperties,

  footerText: {
    fontSize: '13px',
    color: '#a0a0a0',
    margin: 0,
  } as React.CSSProperties,
};
