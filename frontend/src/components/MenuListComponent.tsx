'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { Restaurant, MenuCategory } from '@/types/restaurant';
import MenuItemCard from './MenuItemCard';

interface MenuListComponentProps {
  restaurant: Restaurant | null;
  menu: MenuCategory[];
}

export default function MenuListComponent({ restaurant, menu }: MenuListComponentProps) {
  const { theme } = useTheme();
  const [showImages, setShowImages] = useState(true);

  return (
    <div className="h-full" style={{ background: 'transparent' }}>
      {/* Toggle Button */}
      <div className="p-6 pb-4">
        <div className="flex justify-center">
          <div 
            className="inline-flex rounded-lg p-1"
            style={{ backgroundColor: theme.surface }}
          >
            <button
              onClick={() => setShowImages(true)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                showImages ? 'text-white' : ''
              }`}
              style={{
                backgroundColor: showImages ? theme.primary : 'transparent',
                color: showImages ? 'white' : theme.text.secondary
              }}
            >
              📷 Images
            </button>
            <button
              onClick={() => setShowImages(false)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
                !showImages ? 'text-white' : ''
              }`}
              style={{
                backgroundColor: !showImages ? theme.primary : 'transparent',
                color: !showImages ? 'white' : theme.text.secondary
              }}
            >
              📄 Text Only
            </button>
          </div>
        </div>
      </div>

      {/* Menu Categories */}
      <div className="p-6 pt-2 space-y-8" style={{ background: 'transparent' }}>
        {menu.map((category) => (
          <div key={category.id} className="space-y-4">
            <div 
              className="pb-2"
              style={{ borderBottom: `1px solid ${theme.border.primary}` }}
            >
              <h2 
                className="text-xl font-semibold"
                style={{ color: theme.text.primary }}
              >
                {category.name}
              </h2>
              {category.description && (
                <p 
                  className="text-sm mt-1"
                  style={{ color: theme.text.secondary }}
                >
                  {category.description}
                </p>
              )}
            </div>

            {showImages ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {category.items.map((item) => (
                  <MenuItemCard key={item.id} item={item} theme={theme} restaurantId={restaurant?.id} />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {category.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex justify-between items-center p-3 rounded-lg hover:shadow-sm transition-all duration-200"
                    style={{
                      backgroundColor: theme.surface,
                      border: `1px solid ${theme.border.primary}`
                    }}
                  >
                    <div className="flex-1">
                      <h4 
                        className="font-semibold text-base"
                        style={{ color: theme.text.primary }}
                      >
                        {item.name}
                      </h4>
                      {item.description && (
                        <p 
                          className="text-sm mt-1"
                          style={{ color: theme.text.secondary }}
                        >
                          {item.description}
                        </p>
                      )}
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
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
                    <div className="text-right ml-4">
                      <span 
                        className="text-lg font-bold px-3 py-1 rounded-full text-white"
                        style={{ 
                          background: `linear-gradient(135deg, ${
                            Number(item.price) < 5 ? '#10B981' : 
                            Number(item.price) < 10 ? '#F59E0B' : '#EF4444'
                          } 0%, ${
                            Number(item.price) < 5 ? '#34D399' : 
                            Number(item.price) < 10 ? '#FBBF24' : '#F87171'
                          } 100%)`
                        }}
                      >
                        ${Number(item.price).toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

