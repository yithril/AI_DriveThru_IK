'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

interface OrderContextType {
  refreshTrigger: number;
  triggerOrderRefresh: () => void;
}

const OrderContext = createContext<OrderContextType | undefined>(undefined);

export function OrderProvider({ children }: { children: React.ReactNode }) {
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerOrderRefresh = useCallback(() => {
    console.log('🔄 OrderContext: triggerOrderRefresh called');
    setRefreshTrigger(prev => prev + 1);
  }, []);

  return (
    <OrderContext.Provider value={{ refreshTrigger, triggerOrderRefresh }}>
      {children}
    </OrderContext.Provider>
  );
}

export function useOrder() {
  const context = useContext(OrderContext);
  if (context === undefined) {
    throw new Error('useOrder must be used within an OrderProvider');
  }
  return context;
}
