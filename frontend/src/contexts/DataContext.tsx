'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Restaurant, MenuCategory } from '@/types/restaurant';
import { apiClient } from '@/lib/api';

interface DataContextType {
  restaurant: Restaurant | null;
  menu: MenuCategory[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

// Cache for restaurant data to avoid multiple API calls
let restaurantCache: Restaurant | null = null;
let menuCache: MenuCategory[] = [];
let cacheTimestamp: number = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [restaurant, setRestaurant] = useState<Restaurant | null>(restaurantCache);
  const [menu, setMenu] = useState<MenuCategory[]>(menuCache);
  const [isLoading, setIsLoading] = useState(!restaurantCache);
  const [error, setError] = useState<string | null>(null);

  const fetchRestaurantData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const restaurantId = parseInt(process.env.NEXT_PUBLIC_RESTAURANT_ID || '1');
      
      const data = await apiClient.getRestaurantMenu(restaurantId);
      
      // Use menu as-is (already sorted by display_order from API)
      const sortedMenu = data.menu;
      
      // Update cache
      restaurantCache = data.restaurant;
      menuCache = sortedMenu;
      cacheTimestamp = Date.now();
      
      setRestaurant(data.restaurant);
      setMenu(sortedMenu);
    } catch (err) {
      console.error('Error fetching restaurant data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load restaurant data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check if we have valid cached data
    const now = Date.now();
    if (restaurantCache && (now - cacheTimestamp) < CACHE_DURATION) {
      setRestaurant(restaurantCache);
      setMenu(menuCache);
      setIsLoading(false);
      return;
    }

    // Fetch fresh data immediately
    fetchRestaurantData();
  }, []);

  const refetch = async () => {
    // Clear cache and fetch fresh data
    restaurantCache = null;
    menuCache = [];
    cacheTimestamp = 0;
    await fetchRestaurantData();
  };

  return (
    <DataContext.Provider value={{ restaurant, menu, isLoading, error, refetch }}>
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}
