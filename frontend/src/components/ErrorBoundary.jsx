import React from 'react';

/**
 * ErrorBoundary - React Error Boundary Component
 * 
 * Catches JavaScript errors in child components
 * and displays a user-friendly error message.
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ errorInfo });
        
        // Error logging service integration can be added here
        console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen w-full flex items-center justify-center bg-[var(--bg-dark)] p-8">
                    <div className="max-w-lg w-full card p-8 text-center">
                        {/* Error Icon */}
                        <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-red-500/10 flex items-center justify-center">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <line x1="12" y1="8" x2="12" y2="12"></line>
                                <line x1="12" y1="16" x2="12.01" y2="16"></line>
                            </svg>
                        </div>
                        
                        <h1 className="text-2xl font-bold text-[var(--text-main)] mb-2">
                            Something Went Wrong
                        </h1>
                        <p className="text-[var(--text-muted)] mb-6">
                            An unexpected error occurred. Please refresh the page or try again later.
                        </p>
                        
                        {/* Error Details (Development only) */}
                        {import.meta.env.DEV && this.state.error && (
                            <details className="text-left bg-[var(--bg-dark)] rounded p-4 mb-6 text-xs">
                                <summary className="cursor-pointer text-[var(--text-muted)] mb-2">
                                    Technical Details
                                </summary>
                                <pre className="overflow-auto text-red-400 font-mono">
                                    {this.state.error.toString()}
                                    {this.state.errorInfo?.componentStack}
                                </pre>
                            </details>
                        )}
                        
                        <div className="flex gap-4 justify-center">
                            <button
                                onClick={() => window.location.reload()}
                                className="btn btn-primary"
                            >
                                Refresh Page
                            </button>
                            <button
                                onClick={this.handleReset}
                                className="btn border border-[var(--border)] hover:bg-[var(--bg-card-hover)]"
                            >
                                Try Again
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
