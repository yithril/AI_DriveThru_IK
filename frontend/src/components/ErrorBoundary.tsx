'use client';

import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error!} resetError={this.resetError} />;
      }

      return <ErrorFallback error={this.state.error!} resetError={this.resetError} />;
    }

    return this.props.children;
  }
}

function ErrorFallback({ error, resetError }: { error: Error; resetError: () => void }) {
  const { theme } = useTheme();
  
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-red-600 mb-4">⚠️</h1>
          <h2 
            className="text-2xl font-semibold mb-2"
            style={{ color: theme.text.primary }}
          >
            Something went wrong
          </h2>
          <p 
            className="mb-4"
            style={{ color: theme.text.secondary }}
          >
            An unexpected error occurred. Please try refreshing the page.
          </p>
          {error && (
            <details 
              className="text-left p-4 rounded-lg mb-4"
              style={{ 
                backgroundColor: theme.surface,
                border: `1px solid ${theme.border.primary}`
              }}
            >
              <summary 
                className="cursor-pointer font-medium"
                style={{ color: theme.text.primary }}
              >
                Error Details
              </summary>
              <pre 
                className="mt-2 text-sm whitespace-pre-wrap"
                style={{ color: theme.text.secondary }}
              >
                {error.message}
              </pre>
            </details>
          )}
        </div>
        
        <div className="space-y-4">
          <button
            onClick={resetError}
            className="inline-block text-white font-medium py-3 px-6 rounded-lg transition-colors mr-4"
            style={{ backgroundColor: theme.button.primary }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primaryHover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primary;
            }}
          >
            Try Again
          </button>
          
          <button
            onClick={() => window.location.reload()}
            className="inline-block text-white font-medium py-3 px-6 rounded-lg transition-colors"
            style={{ backgroundColor: theme.button.secondary }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.secondaryHover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.secondary;
            }}
          >
            Refresh Page
          </button>
        </div>
      </div>
    </div>
  );
}
