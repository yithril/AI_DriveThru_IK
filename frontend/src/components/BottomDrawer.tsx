'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import FloatingMicrophone from './FloatingMicrophone';

interface BottomDrawerProps {
  orderComponentRef?: React.RefObject<{ refreshOrder: () => void }>;
}

export default function BottomDrawer({ orderComponentRef }: BottomDrawerProps) {
  const { theme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);


  const toggleDrawer = () => {
    setIsAnimating(true);
    setIsOpen(!isOpen);
    setTimeout(() => {
      setIsAnimating(false);
    }, 300); // Match animation duration
  };

  return (
    <>
      {/* Visual Handle/Tab */}
      <div 
        className="fixed bottom-0 left-1/2 transform -translate-x-1/2 z-50 cursor-pointer"
        onClick={toggleDrawer}
        style={{
          width: '60px',
          height: '20px',
          backgroundColor: theme.primary,
          borderRadius: '10px 10px 0 0',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.2s ease'
        }}
      >
        {/* Handle grip lines */}
        <div className="flex justify-center items-center h-full">
          <div className="flex space-x-1">
            <div 
              className="w-1 h-1 rounded-full"
              style={{ backgroundColor: 'rgba(255, 255, 255, 0.6)' }}
            />
            <div 
              className="w-1 h-1 rounded-full"
              style={{ backgroundColor: 'rgba(255, 255, 255, 0.6)' }}
            />
            <div 
              className="w-1 h-1 rounded-full"
              style={{ backgroundColor: 'rgba(255, 255, 255, 0.6)' }}
            />
          </div>
        </div>
      </div>
      
      
      {/* Sliding Drawer Panel */}
      <div 
        className={`fixed left-0 right-0 z-40 transition-all duration-300 ease-out ${
          isOpen ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{
          bottom: isOpen ? '0' : '-100%',
          backgroundColor: theme.surface,
          borderTop: `2px solid ${theme.primary}`,
          boxShadow: isOpen ? '0 -10px 25px rgba(0, 0, 0, 0.15)' : 'none'
        }}
      >
        {/* Drawer Content */}
        <div className="p-6">
          <div className="text-center mb-4">
            <h3 
              className="text-xl font-bold mb-2"
              style={{ color: theme.text.primary }}
            >
              Voice Order
            </h3>
            <p 
              className="text-sm"
              style={{ color: theme.text.secondary }}
            >
              Click the microphone to start recording your order
            </p>
          </div>
          
          {/* FloatingMicrophone Component - positioned in lower-right of drawer */}
          <div className="relative">
            <div className="absolute bottom-0 right-0">
              <FloatingMicrophone orderComponentRef={orderComponentRef} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
