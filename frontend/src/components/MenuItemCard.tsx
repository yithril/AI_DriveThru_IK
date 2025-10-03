'use client';

import React from 'react';
import { MenuItem, ThemeColors } from '@/types/restaurant';
import { getImageUrl } from '@/lib/s3-utils';

interface MenuItemCardProps {
  item: MenuItem;
  theme: ThemeColors;
  restaurantId?: number;
}

// Function to get different colors for price badges based on price
const getPriceBadgeColor = (price: number, isEnd: boolean = false): string => {
  if (price < 5) {
    return isEnd ? '#10B981' : '#34D399'; // Green gradient for cheap items
  } else if (price < 10) {
    return isEnd ? '#F59E0B' : '#FBBF24'; // Orange gradient for medium items
  } else {
    return isEnd ? '#EF4444' : '#F87171'; // Red gradient for expensive items
  }
};

export default function MenuItemCard({ item, theme, restaurantId }: MenuItemCardProps) {
  const fullImageUrl = item.image_url ? getImageUrl(item.image_url, restaurantId || 20) : '/placeholder-image.png';

  return (
    <div 
      className="rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden"
      style={{ 
        background: 'transparent',
        border: `1px solid ${theme.border.primary}`,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = theme.border.secondary;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = theme.border.primary;
      }}
    >
      {/* Image at the top */}
      {fullImageUrl && (
        <div className="relative h-48 w-full overflow-hidden">
          <img 
            src={fullImageUrl} 
            alt={item.name}
            className="w-full h-full object-cover object-center transition-transform duration-300 hover:scale-105"
            onError={(e) => {
              // Fallback to a placeholder if image fails to load
              e.currentTarget.style.display = 'none';
            }}
          />
          {/* Price badge overlay */}
          <div className="absolute top-3 right-3">
            <span 
              className="px-3 py-1 text-sm font-bold text-white rounded-full shadow-lg"
              style={{ 
                background: `linear-gradient(135deg, ${getPriceBadgeColor(Number(item.price))} 0%, ${getPriceBadgeColor(Number(item.price), true)} 100%)`
              }}
            >
              ${Number(item.price).toFixed(2)}
            </span>
          </div>
        </div>
      )}

      {/* Content at the bottom */}
      <div className="p-4">
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h3 
              className="font-semibold text-lg mb-1"
              style={{ color: theme.text.primary }}
            >
              {item.name}
            </h3>
            {item.description && (
              <p 
                className="text-sm leading-relaxed"
                style={{ color: theme.text.secondary }}
              >
                {item.description}
              </p>
            )}
          </div>
          {/* Price display when no image */}
          {!fullImageUrl && (
            <div className="text-right ml-4">
              <span 
                className="text-xl font-bold px-3 py-1 rounded-full text-white"
                style={{ 
                  background: `linear-gradient(135deg, ${getPriceBadgeColor(Number(item.price))} 0%, ${getPriceBadgeColor(Number(item.price), true)} 100%)`
                }}
              >
                ${Number(item.price).toFixed(2)}
              </span>
            </div>
          )}
        </div>

        {/* Tags */}
        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {item.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 text-xs font-medium rounded-full text-white"
                style={{ backgroundColor: tag.color }}
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
