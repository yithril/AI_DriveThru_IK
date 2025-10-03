'use client';

import React, { createContext, useContext, useMemo } from 'react';
import { ThemeColors } from '@/types/restaurant';
import { useData } from './DataContext';

interface ThemeContextType {
  theme: ThemeColors;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const defaultTheme: ThemeColors = {
  primary: '#7c3aed', // Cosmic purple
  secondary: '#1e1b4b', // Deep cosmic blue
  background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #0a0a0a 100%)',
  surface: '#1f2937', // gray-800
  surfaceHover: '#374151', // gray-700
  text: {
    primary: '#ffffff',
    secondary: '#d1d5db', // gray-300
    muted: '#9ca3af', // gray-400
    accent: '#a855f7', // Cosmic purple accent
  },
  border: {
    primary: '#374151', // gray-700
    secondary: '#4b5563', // gray-600
  },
  button: {
    primary: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 25%, #4c1d95 50%, #7c3aed 75%, #a855f7 100%)', // Cosmic purple gradient
    primaryHover: 'linear-gradient(135deg, #312e81 0%, #4c1d95 25%, #7c3aed 50%, #a855f7 75%, #c084fc 100%)', // Brighter cosmic gradient
    secondary: '#4b5563', // gray-600
    secondaryHover: '#6b7280', // gray-500
  },
  error: {
    background: '#fee2e2',
    text: '#dc2626',
    border: '#fca5a5',
  },
};

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Try to get restaurant data, but don't fail if DataProvider is not available
  let restaurant = null;
  try {
    const data = useData();
    restaurant = data.restaurant;
  } catch (error) {
    // DataProvider not available (e.g., on admin pages), use default theme
    console.log('ThemeProvider: No DataProvider available, using default theme');
  }

  const theme: ThemeColors = useMemo(() => {
    return restaurant ? {
      ...defaultTheme,
      primary: restaurant.primary_color,
      secondary: restaurant.secondary_color,
      text: {
        ...defaultTheme.text,
        accent: restaurant.primary_color,
      },
      button: {
        ...defaultTheme.button,
        primary: restaurant.primary_color,
        primaryHover: restaurant.primary_color + 'cc', // Add transparency for hover
      },
    } : defaultTheme;
  }, [restaurant]);

  return (
    <ThemeContext.Provider value={{ theme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}