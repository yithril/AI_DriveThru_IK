'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api'

interface Restaurant {
  id: number
  name: string
  description: string | null
  address: string | null
  phone: string | null
  hours: string | null
  logo_url: string | null
  primary_color: string
  secondary_color: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export default function RestaurantDashboard() {
  const params = useParams()
  const router = useRouter()
  const restaurantId = parseInt(params.id as string)
  
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchRestaurant()
  }, [restaurantId])

  const fetchRestaurant = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getRestaurant(restaurantId)
      setRestaurant(data)
    } catch (err) {
      setError('Error fetching restaurant')
      console.error('Error fetching restaurant:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-6">Loading restaurant...</div>
  if (error) return <div className="p-6 text-red-500">{error}</div>
  if (!restaurant) return <div className="p-6">Restaurant not found</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900 mb-4"
          >
            ← Back to Restaurants
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{restaurant.name}</h1>
          {restaurant.description && (
            <p className="text-gray-600 mt-2">{restaurant.description}</p>
          )}
        </div>

        {/* Restaurant Info Card */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Restaurant Information</h2>
          </div>
          <div className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Status</h3>
                <div className="mt-1 flex items-center">
                  <div 
                    className={`w-3 h-3 rounded-full mr-2 ${restaurant.is_active ? 'bg-green-500' : 'bg-red-500'}`}
                  />
                  <span className="text-sm text-gray-900">
                    {restaurant.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              
              {restaurant.phone && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Phone</h3>
                  <p className="mt-1 text-sm text-gray-900">{restaurant.phone}</p>
                </div>
              )}
              
              {restaurant.address && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Address</h3>
                  <p className="mt-1 text-sm text-gray-900">{restaurant.address}</p>
                </div>
              )}
              
              {restaurant.hours && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Hours</h3>
                  <p className="mt-1 text-sm text-gray-900">{restaurant.hours}</p>
                </div>
              )}
              
              <div>
                <h3 className="text-sm font-medium text-gray-500">Brand Colors</h3>
                <div className="mt-1 flex items-center space-x-2">
                  <div 
                    className="w-6 h-6 rounded border border-gray-300"
                    style={{ backgroundColor: restaurant.primary_color }}
                    title="Primary Color"
                  />
                  <div 
                    className="w-6 h-6 rounded border border-gray-300"
                    style={{ backgroundColor: restaurant.secondary_color }}
                    title="Secondary Color"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Management Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Menu Items */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Menu Items</h3>
              <p className="text-sm text-gray-500">Manage the restaurant's menu items</p>
            </div>
            <div className="px-6 py-4">
              <button
                onClick={() => router.push(`/admin/menu-items?restaurant_id=${restaurantId}`)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                Manage Menu Items
              </button>
            </div>
          </div>

          {/* Categories */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Categories</h3>
              <p className="text-sm text-gray-500">Organize menu items into categories</p>
            </div>
            <div className="px-6 py-4">
              <button
                onClick={() => router.push(`/admin/categories?restaurant_id=${restaurantId}`)}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                Manage Categories
              </button>
            </div>
          </div>

          {/* Ingredients */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Ingredients</h3>
              <p className="text-sm text-gray-500">Manage available ingredients</p>
            </div>
            <div className="px-6 py-4">
              <button
                onClick={() => router.push(`/admin/ingredients?restaurant_id=${restaurantId}`)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                Manage Ingredients
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}