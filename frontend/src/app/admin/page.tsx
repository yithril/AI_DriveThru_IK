'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'

export default function AdminDashboard() {
  const restaurantId = useRestaurantId()
  const [stats, setStats] = useState([
    {
      name: 'Menu Items',
      value: '0',
      href: '/admin/menu-items',
      icon: '🍽️',
      description: 'Manage menu items and their details'
    },
    {
      name: 'Ingredients',
      value: '0',
      href: '/admin/ingredients',
      icon: '🥬',
      description: 'Manage ingredients and allergens'
    },
    {
      name: 'Categories',
      value: '0',
      href: '/admin/categories',
      icon: '📁',
      description: 'Organize menu categories'
    },
    {
      name: 'Restaurants',
      value: '0',
      href: '/admin/restaurants',
      icon: '🏪',
      description: 'Manage restaurant settings'
    }
  ])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [restaurantId])

  const fetchStats = async () => {
    try {
      const [menuItems, ingredients, categories, restaurants] = await Promise.all([
        apiClient.getMenuItems(restaurantId, undefined, false), // Get all items, not just available
        apiClient.getIngredients(restaurantId),
        apiClient.getCategories(restaurantId),
        apiClient.getRestaurants()
      ])

      setStats(prev => prev.map(stat => {
        if (stat.name === 'Menu Items') {
          return { ...stat, value: menuItems.length.toString() }
        }
        if (stat.name === 'Ingredients') {
          return { ...stat, value: ingredients.length.toString() }
        }
        if (stat.name === 'Categories') {
          return { ...stat, value: categories.filter(cat => cat.is_active).length.toString() }
        }
        if (stat.name === 'Restaurants') {
          return { ...stat, value: restaurants.filter(rest => rest.is_active).length.toString() }
        }
        return stat
      }))
    } catch (err) {
      console.error('Error fetching stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const quickActions = [
    {
      name: 'Create Restaurant',
      href: '/admin/restaurants',
      icon: '🏪',
      description: 'Set up a new restaurant'
    },
    {
      name: 'Create Menu Item',
      href: '/admin/menu-items/new',
      icon: '➕',
      description: 'Add a new menu item with ingredients'
    },
    {
      name: 'Add Ingredient',
      href: '/admin/ingredients/new',
      icon: '🥕',
      description: 'Create a new ingredient'
    },
    {
      name: 'Import Data',
      href: '/admin/import',
      icon: '📥',
      description: 'Import restaurant data from Excel'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage your restaurant menu, ingredients, and orders
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Link
            key={stat.name}
            href={stat.href}
            className="relative bg-white pt-5 px-4 pb-12 sm:pt-6 sm:px-6 shadow rounded-lg overflow-hidden hover:shadow-md transition-shadow"
          >
            <dt>
              <div className="absolute bg-indigo-500 rounded-md p-3">
                <span className="text-2xl">{stat.icon}</span>
              </div>
              <p className="ml-16 text-sm font-medium text-gray-500 truncate">
                {stat.name}
              </p>
            </dt>
            <dd className="ml-16 pb-6 flex items-baseline sm:pb-7">
              <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              <p className="ml-2 flex items-baseline text-sm font-semibold text-indigo-600">
                <span className="sr-only">View {stat.name}</span>
              </p>
            </dd>
            <div className="absolute bottom-0 left-0 right-0 bg-gray-50 px-4 py-3">
              <p className="text-xs text-gray-600">{stat.description}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              href={action.href}
              className="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-indigo-500 rounded-lg hover:shadow-md transition-shadow"
            >
              <div>
                <span className="rounded-lg inline-flex p-3 bg-indigo-50 text-indigo-700 ring-4 ring-white text-2xl">
                  {action.icon}
                </span>
              </div>
              <div className="mt-4">
                <h3 className="text-lg font-medium text-gray-900 group-hover:text-indigo-600">
                  {action.name}
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  {action.description}
                </p>
              </div>
              <span
                className="pointer-events-none absolute top-6 right-6 text-gray-300 group-hover:text-gray-400"
                aria-hidden="true"
              >
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20 4h1a1 1 0 00-1-1v1zm-1 12a1 1 0 102 0h-2zM8 3a1 1 0 000 2V3zM3.293 19.293a1 1 0 101.414 1.414l-1.414-1.414zM19 4v12h2V4h-2zm1-1H8v2h12V3zm-.707.293l-16 16 1.414 1.414 16-16-1.414-1.414z" />
                </svg>
              </span>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Recent Activity
          </h3>
          <div className="mt-5">
            <div className="text-center py-6">
              <div className="text-4xl mb-2">📊</div>
              <p className="text-gray-500">No recent activity</p>
              <p className="text-sm text-gray-400 mt-1">
                Start by creating menu items or importing data
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
