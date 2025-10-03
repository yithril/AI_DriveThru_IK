'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSession } from '@/contexts/SessionContext';
import { useOrder } from '@/contexts/OrderContext';
import { apiClient } from '@/lib/api';
import { LineItem, SessionData } from '@/types/order';

const OrderComponent = React.forwardRef<{ refreshOrder: () => void }>((props, ref) => {
  const { theme } = useTheme();
  const { sessionId, restaurantId, isLoading: sessionLoading } = useSession();
  const { refreshTrigger } = useOrder();
  const [orderItems, setOrderItems] = useState<LineItem[]>([]);
  const [orderTotals, setOrderTotals] = useState({ subtotal: 0, tax: 0, total: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch order data from current order endpoint
  const fetchOrderData = useCallback(async () => {
    if (!sessionId) {
      setOrderItems([]);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getCurrentOrder();
      
      if (response.success && response.data.order) {
        const order = response.data.order;
        const lineItems = order.items || [];
        
        // Map API data to frontend format
        const mappedItems = lineItems.map(item => {
          // Calculate additional costs from backend-provided modifier costs
          let additionalCost = 0;
          const customizations: string[] = [];
          const additionalCosts: { name: string; cost: number }[] = [];
          
          // Use backend-provided modifier cost breakdown
          if (item.modifier_costs && Array.isArray(item.modifier_costs)) {
            item.modifier_costs.forEach((modifierCost: any) => {
              additionalCost += modifierCost.cost;
              additionalCosts.push({ 
                name: `${modifierCost.action} ${modifierCost.ingredient_name}`, 
                cost: modifierCost.cost 
              });
            });
          }
          
          // Get customizations for display
          if (item.modifications?.ingredient_modifications) {
            customizations.push(...item.modifications.ingredient_modifications.split('; ').filter(mod => mod.trim()));
          }
          
          return {
            id: item.id,
            menu_item_id: item.menu_item_id,
            name: item.menu_item?.name || 'Unknown Item',
            price: item.menu_item?.price || 0,
            quantity: item.quantity || 1,
            additional_cost: additionalCost,
            additional_costs: additionalCosts,
            total_price: (item.menu_item?.price || 0) + additionalCost, // Base price + additional costs
            customizations,
            special_instructions: item.modifications?.special_instructions || item.special_instructions
          };
        });
        
        // Set order totals from backend
        setOrderTotals({
          subtotal: order.subtotal || 0,
          tax: order.tax_amount || 0,
          total: order.total_amount || 0
        });
        
        setOrderItems(mappedItems);
      } else {
        setOrderItems([]);
        setOrderTotals({ subtotal: 0, tax: 0, total: 0 });
      }
    } catch (err: unknown) {
      console.error('Failed to fetch order data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch order data');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Clear order when session changes (new car)
  useEffect(() => {
    if (sessionId) {
      // New session - clear old order data and fetch fresh data
      setOrderItems([]);
      setOrderTotals({ subtotal: 0, tax: 0, total: 0 });
      fetchOrderData();
    } else {
      // No session - clear everything
      setOrderItems([]);
      setOrderTotals({ subtotal: 0, tax: 0, total: 0 });
    }
  }, [sessionId, fetchOrderData]);

  // Auto-refresh when order context triggers refresh
  useEffect(() => {
    if (refreshTrigger > 0 && sessionId) {
      fetchOrderData();
    }
  }, [refreshTrigger, sessionId, fetchOrderData]);

  // Auto-refresh when order changes (this will be called from VoiceOrderComponent)
  const refreshOrder = () => {
    fetchOrderData();
  };

  // Expose refresh function to parent components
  React.useImperativeHandle(ref, () => ({
    refreshOrder
  }));

  // Use backend-calculated totals instead of frontend calculation
  const { subtotal, tax, total } = orderTotals;
  
  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 
          className="text-2xl font-bold mb-2"
          style={{ color: theme.text.primary }}
        >
          Current Order
        </h2>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 mx-auto" style={{ borderColor: theme.text.primary }}></div>
          <p className="mt-2 text-sm" style={{ color: theme.text.secondary }}>Loading order...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8">
          <div className="text-red-500 mb-2">❌ {error}</div>
          <button
            onClick={fetchOrderData}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* No Session State */}
      {!sessionId && !isLoading && (
        <div className="text-center py-12">
          <div 
            className="mb-4"
            style={{ color: theme.text.muted }}
          >
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p style={{ color: theme.text.secondary }}>Ready to take your order</p>
          <p 
            className="text-sm mt-1"
            style={{ color: theme.text.muted }}
          >
            Click "New Car" to start ordering
          </p>
        </div>
      )}

      {/* Empty Order State */}
      {sessionId && !isLoading && !error && orderItems.length === 0 && (
        <div className="text-center py-12">
          <div 
            className="mb-4"
            style={{ color: theme.text.muted }}
          >
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p style={{ color: theme.text.secondary }}>No items in order</p>
          <p 
            className="text-sm mt-1"
            style={{ color: theme.text.muted }}
          >
            Add items from the menu
          </p>
        </div>
      )}

      {/* Order Items */}
      {sessionId && !isLoading && !error && orderItems.length > 0 && (
        <div className="space-y-3">
          {orderItems.map((item, index) => (
            <div 
              key={`${item.menu_item_id}-${item.id}-${index}`} 
              className="rounded-lg p-4 shadow-sm"
              style={{ 
                backgroundColor: theme.surface,
                border: `1px solid ${theme.border.primary}`
              }}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 
                    className="text-lg font-semibold mb-2"
                    style={{ color: theme.text.accent }}
                  >
                    {item.name}
                  </h3>
                  <div className="text-sm space-y-1" style={{ color: theme.text.secondary }}>
                    <div className="font-medium">Base: ${item.price.toFixed(2)} each</div>
                    {item.additional_costs && item.additional_costs.length > 0 && (
                      <div className="space-y-1">
                        {item.additional_costs.map((cost, index) => (
                          <div key={index} className="text-xs" style={{ color: '#8B5CF6' }}>
                            {cost.name} (+${cost.cost.toFixed(2)})
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Only show customizations that aren't already shown in additional_costs */}
                  {item.customizations && item.customizations.length > 0 && (
                    <div className="mt-2">
                      {item.customizations
                        .filter(customization => 
                          !item.additional_costs?.some(cost => 
                            cost.name.toLowerCase().includes(customization.toLowerCase()) ||
                            customization.toLowerCase().includes(cost.name.toLowerCase())
                          )
                        )
                        .map((customization, index) => (
                          <div 
                            key={index}
                            className="text-xs ml-4 py-1"
                            style={{ color: theme.text.muted }}
                          >
                            • {customization}
                          </div>
                        ))}
                    </div>
                  )}
                  
                  {/* Special Instructions */}
                  {item.special_instructions && (
                    <div className="mt-2">
                      <div 
                        className="text-xs ml-4 py-1 italic"
                        style={{ color: theme.text.muted }}
                      >
                        Note: {item.special_instructions}
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span 
                    className="w-8 text-center font-medium"
                    style={{ color: theme.text.primary }}
                  >
                    {item.quantity}
                  </span>
                </div>
              </div>
              <div className="mt-2 text-right">
                <span 
                  className="font-medium"
                  style={{ color: theme.text.primary }}
                >
                  ${(item.total_price * item.quantity).toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {orderItems.length > 0 && (
        <div 
          className="mt-6 pt-4"
          style={{ borderTop: `1px solid ${theme.border.primary}` }}
        >
          <div className="flex justify-between items-center">
            <span 
              className="text-lg font-semibold"
              style={{ color: theme.text.primary }}
            >
              Total:
            </span>
            <span 
              className="text-xl font-bold"
              style={{ color: theme.text.accent }}
            >
              ${total.toFixed(2)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
});

OrderComponent.displayName = 'OrderComponent';

export default OrderComponent;
