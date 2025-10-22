/**
 * ErrorBoundary Component
 * 
 * Glass-themed error boundary to catch React errors and display fallback UI
 * Implements Phase 8 Task 109: Error Boundary Component
 * 
 * Features:
 * - Catches JavaScript errors anywhere in child component tree
 * - Logs error details to console
 * - Displays user-friendly error message with glass design
 * - Provides "Try Again" button to reset error state
 * - Shows error details in development mode
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Update state with error info
    this.setState({
      error,
      errorInfo,
    });

    // In production, you could send error to error tracking service
    // e.g., Sentry, LogRocket, etc.
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
          <div className="glass-card max-w-2xl w-full p-8">
            {/* Error Icon and Title */}
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold text-white mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-gray-300">
                We encountered an unexpected error. Please try again.
              </p>
            </div>

            {/* Error Details (Development Only) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-red-900/20 border border-red-700/30 rounded-lg">
                <h2 className="text-sm font-bold text-red-300 mb-2">
                  Error Details (Development Mode):
                </h2>
                <div className="text-xs text-red-200 font-mono mb-2">
                  <strong>Error:</strong> {this.state.error.toString()}
                </div>
                {this.state.errorInfo && (
                  <details className="text-xs text-red-200">
                    <summary className="cursor-pointer text-red-300 font-semibold mb-2">
                      Component Stack
                    </summary>
                    <pre className="whitespace-pre-wrap overflow-auto max-h-48 p-2 bg-black/30 rounded">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={this.handleReset}
                className="flex-1 glass-button bg-blue-600/20 border-blue-500/30 text-blue-300 hover:bg-blue-600/30 hover:border-blue-500/50"
              >
                ↻ Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 glass-button"
              >
                🏠 Go Home
              </button>
            </div>

            {/* Help Text */}
            <div className="mt-6 p-4 bg-blue-900/10 border border-blue-700/20 rounded-lg">
              <p className="text-xs text-blue-300">
                💡 <strong>Tip:</strong> If this error persists, try:
              </p>
              <ul className="text-xs text-blue-200 mt-2 ml-4 space-y-1">
                <li>• Refreshing the page (Ctrl/Cmd + R)</li>
                <li>• Clearing your browser cache</li>
                <li>• Checking your internet connection</li>
                <li>• Contacting support if the problem continues</li>
              </ul>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
