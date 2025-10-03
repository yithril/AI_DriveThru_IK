'use client';

import Link from 'next/link';
import { useTheme } from '@/contexts/ThemeContext';

export default function NotFound() {
  const { theme } = useTheme();
  
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 
            className="text-6xl font-bold mb-4"
            style={{ color: theme.text.primary }}
          >
            404
          </h1>
          <h2 
            className="text-2xl font-semibold mb-2"
            style={{ color: theme.text.primary }}
          >
            Page Not Found
          </h2>
          <p style={{ color: theme.text.secondary }}>
            Sorry, we couldn&apos;t find the page you&apos;re looking for.
          </p>
        </div>
        
        <div className="space-y-4">
          <Link 
            href="/"
            className="inline-block text-white font-medium py-3 px-6 rounded-lg transition-colors"
            style={{ backgroundColor: theme.button.primary }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primaryHover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primary;
            }}
          >
            Go Back Home
          </Link>
          
          <div 
            className="text-sm"
            style={{ color: theme.text.muted }}
          >
            <p>If you think this is an error, please contact support.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
