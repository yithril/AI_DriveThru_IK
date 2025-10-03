'use client'

import { useState, useEffect } from 'react'
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

export default function RestaurantsPage() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    address: '',
    phone: '',
    hours: 'Mon-Sun: 6:00 AM - 10:00 PM',
    primary_color: '#FF6B35',
    secondary_color: '#F7931E',
    is_active: true
  })

  useEffect(() => {
    fetchRestaurants()
  }, [])

  const fetchRestaurants = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getRestaurants()
      // The API returns { restaurants: [...], total_count: number }
      setRestaurants(data.restaurants || [])
    } catch (err) {
      setError('Error fetching restaurants')
      console.error('Error fetching restaurants:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newRestaurant = await apiClient.createRestaurant({
        name: formData.name,
        description: formData.description || undefined,
        address: formData.address || undefined,
        phone: formData.phone || undefined,
        hours: formData.hours || undefined,
        primary_color: formData.primary_color,
        secondary_color: formData.secondary_color,
        is_active: formData.is_active
      })

      setRestaurants(prev => [...prev, newRestaurant])
      setShowCreateForm(false)
      setFormData({
        name: '',
        description: '',
        address: '',
        phone: '',
        hours: 'Mon-Sun: 6:00 AM - 10:00 PM',
        primary_color: '#FF6B35',
        secondary_color: '#F7931E',
        is_active: true
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating restaurant')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading restaurants...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Restaurants</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your restaurant information and settings
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {showCreateForm ? 'Cancel' : 'Add Restaurant'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-sm text-red-600">{error}</div>
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Restaurant</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Restaurant Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="e.g., Demo Restaurant"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={2}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Brief description of your restaurant..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Address
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="123 Main St, City, State 12345"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Hours
              </label>
              <input
                type="text"
                value={formData.hours}
                onChange={(e) => setFormData(prev => ({ ...prev, hours: e.target.value }))}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                placeholder="Mon-Sun: 6:00 AM - 10:00 PM"
              />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Primary Color
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <input
                    type="color"
                    value={formData.primary_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, primary_color: e.target.value }))}
                    className="h-10 w-16 border border-gray-300 rounded-md"
                  />
                  <input
                    type="text"
                    value={formData.primary_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, primary_color: e.target.value }))}
                    className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="#FF6B35"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Secondary Color
                </label>
                <div className="mt-1 flex items-center space-x-2">
                  <input
                    type="color"
                    value={formData.secondary_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, secondary_color: e.target.value }))}
                    className="h-10 w-16 border border-gray-300 rounded-md"
                  />
                  <input
                    type="text"
                    value={formData.secondary_color}
                    onChange={(e) => setFormData(prev => ({ ...prev, secondary_color: e.target.value }))}
                    className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="#F7931E"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700">
                Active (visible to customers)
              </label>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Create Restaurant
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Restaurants List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Restaurants ({restaurants.length})
          </h3>
          
          {restaurants.length === 0 ? (
            <div className="text-center py-6">
              <div className="text-4xl mb-2">🏪</div>
              <p className="text-gray-500">No restaurants found</p>
              <p className="text-sm text-gray-400 mt-1">
                Create your first restaurant to get started
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {restaurants.map((restaurant) => (
                <div key={restaurant.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{restaurant.name}</h4>
                        {!restaurant.is_active && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      {restaurant.description && (
                        <p className="text-sm text-gray-600 mt-1">{restaurant.description}</p>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <div 
                        className="w-4 h-4 rounded-full border border-gray-300"
                        style={{ backgroundColor: restaurant.primary_color }}
                        title="Primary Color"
                      />
                      <div 
                        className="w-4 h-4 rounded-full border border-gray-300"
                        style={{ backgroundColor: restaurant.secondary_color }}
                        title="Secondary Color"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm text-gray-600">
                    {restaurant.phone && (
                      <div>📞 {restaurant.phone}</div>
                    )}
                    {restaurant.address && (
                      <div>📍 {restaurant.address}</div>
                    )}
                    {restaurant.hours && (
                      <div>🕒 {restaurant.hours}</div>
                    )}
                  </div>
                  
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <div className="text-xs text-gray-500">
                        ID: {restaurant.id} • Created: {new Date(restaurant.created_at).toLocaleDateString()}
                      </div>
                      <button
                        onClick={() => window.location.href = `/admin/restaurants/${restaurant.id}`}
                        className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium py-1 px-3 rounded-md transition-colors"
                      >
                        Manage
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
