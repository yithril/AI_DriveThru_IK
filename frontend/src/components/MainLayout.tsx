'use client';

import React, { useRef } from 'react';
import { DataProvider, useData } from '@/contexts/DataContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { SessionProvider, useSession } from '@/contexts/SessionContext';
import { SpeakerProvider, useSpeaker } from '@/contexts/SpeakerContext';
import { OrderProvider } from '@/contexts/OrderContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import OrderComponent from '@/components/OrderComponent';
import CarControlComponent from '@/components/CarControlComponent';
import MenuListComponent from '@/components/MenuListComponent';
import RestaurantLogo from '@/components/RestaurantLogo';
import LoadingSpinner from '@/components/LoadingSpinner';
import FloatingMicrophone from '@/components/FloatingMicrophone';
import BottomDrawer from '@/components/BottomDrawer';

function MainLayoutContent() {
  const { restaurant, menu, isLoading, error } = useData();
  const { theme } = useTheme();
  const { sessionId } = useSession();
  const { isAISpeaking } = useSpeaker();
  const orderComponentRef = useRef<{ refreshOrder: () => void }>(null);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p style={{ color: theme.text.secondary }}>Loading restaurant data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-md w-full text-center">
          <div className="mb-8">
            <h1 className="text-6xl font-bold text-red-600 mb-4">⚠️</h1>
            <h2 
              className="text-2xl font-semibold mb-2"
              style={{ color: theme.text.primary }}
            >
              Failed to Load
            </h2>
            <p 
              className="mb-4"
              style={{ color: theme.text.secondary }}
            >
              {error}
            </p>
          </div>
          
          <button
            onClick={() => window.location.reload()}
            className="inline-block text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2 mx-auto"
            style={{ backgroundColor: theme.button.primary }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primaryHover;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.primary;
            }}
          >
            <LoadingSpinner size="sm" color="text-white" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex relative"
      style={{
        '--primary-color': theme.primary,
        '--secondary-color': theme.secondary,
      } as React.CSSProperties}
    >
      {/* Left Panel - Order Management (1/3) */}
      <div 
        className="w-1/3 flex flex-col"
        style={{ 
          backgroundColor: theme.surface,
          borderRight: `1px solid ${theme.border.primary}`
        }}
      >
        {/* Car Controls - Above Order */}
        <div 
          className="p-4"
          style={{ borderBottom: `1px solid ${theme.border.primary}` }}
        >
          <CarControlComponent />
        </div>
        
        {/* Order Component */}
        <div className="flex-1 overflow-y-auto">
          <OrderComponent ref={orderComponentRef} />
        </div>
        
      </div>

      {/* Right Panel - Menu Display (2/3) */}
      <div 
        className="w-2/3"
        style={{ background: 'transparent' }}
      >
        {/* Restaurant Logo */}
        <RestaurantLogo restaurant={restaurant} />
        
        {/* Menu List */}
        <div className="h-full overflow-y-auto">
          <MenuListComponent restaurant={restaurant} menu={menu} />
        </div>
      </div>
      
      {/* Bottom Drawer */}
      <BottomDrawer orderComponentRef={orderComponentRef} />
    </div>
  );
}

export default function MainLayout() {
  // Context providers are now in the customer layout
  // This component only renders the main content
  return <MainLayoutContent />;
}
