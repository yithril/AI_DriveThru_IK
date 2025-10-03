'use client';
import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getImageUrl } from '../lib/s3-utils';

interface RestaurantLogoProps {
  restaurant?: {
    id: number;
    name: string;
    logo_url?: string;
  } | null;
}

export default function RestaurantLogo({ restaurant }: RestaurantLogoProps) {
  const { theme } = useTheme();

  return (
    <div 
      className="w-full p-6"
      style={{ 
        background: 'transparent',
        borderBottom: `1px solid ${theme.border.primary}`
      }}
    >
      {restaurant?.logo_url ? (
        <img 
          src={getImageUrl(restaurant.logo_url, restaurant.id)}
          alt={restaurant.name}
          className="w-full h-auto object-fill"
          style={{ width: '100%', height: '256px' }}
          onError={(e) => {
            // Fallback to initial if logo fails to load
            e.currentTarget.style.display = 'none';
            e.currentTarget.nextElementSibling?.classList.remove('hidden');
          }}
        />
      ) : null}
      <div 
        className={`w-full h-32 rounded-lg flex items-center justify-center text-white font-bold text-6xl ${restaurant?.logo_url ? 'hidden' : ''}`}
        style={{ backgroundColor: theme.primary }}
      >
        {restaurant?.name?.charAt(0) || 'R'}
      </div>
    </div>
  );
}
