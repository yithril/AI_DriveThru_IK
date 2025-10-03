'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import ImageUpload from '@/components/ImageUpload'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'

interface MenuItem {
  id: number
  name: string
  description: string | null
  price: number
  image_url: string | null
  category_id: number
  restaurant_id: number
  is_available: boolean
  is_upsell: boolean
  is_special: boolean
  prep_time_minutes: number
  display_order: number
  created_at: string
  updated_at: string | null
}

interface Ingredient {
  id: number
  name: string
  description: string | null
  restaurant_id: number
  is_allergen: boolean
  allergen_type: string | null
  unit_cost: number
  created_at: string
  updated_at: string | null
}

interface Category {
  id: number
  name: string
  description: string | null
  restaurant_id: number
  display_order: number
  is_active: boolean
  created_at: string
}

export default function MenuItemsPage() {
  const restaurantId = useRestaurantId()
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category_id: 1, // Default to first category
    restaurant_id: restaurantId,
    image_url: '',
    is_available: true,
    is_upsell: false,
    is_special: false,
    prep_time_minutes: 5,
    display_order: 0
  })

  useEffect(() => {
    fetchMenuItems()
    fetchIngredients()
    fetchCategories()
  }, [])

  const fetchMenuItems = async () => {
    try {
      const data = await apiClient.getMenuItems(restaurantId)
      setMenuItems(data)
    } catch (err) {
      setError('Error fetching menu items')
      console.error('Error fetching menu items:', err)
    }
  }

  const fetchIngredients = async () => {
    try {
      const data = await apiClient.getIngredients(restaurantId)
      setIngredients(data)
    } catch (err) {
      console.error('Error fetching ingredients:', err)
    }
  }

  const fetchCategories = async () => {
    try {
      const data = await apiClient.getCategories(restaurantId)
      setCategories(data.filter(cat => cat.is_active))
    } catch (err) {
      console.error('Error fetching categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = (imageUrl: string, fileData: any) => {
    setSelectedImageUrl(imageUrl)
    setFormData(prev => ({ ...prev, image_url: imageUrl }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newMenuItem = await apiClient.createMenuItem({
        ...formData,
        price: parseFloat(formData.price),
        restaurant_id: restaurantId,
      })

      setMenuItems(prev => [...prev, newMenuItem])
      setShowCreateForm(false)
        setFormData({
          name: '',
          description: '',
          price: '',
          category_id: categories.length > 0 ? categories[0].id : 1,
          restaurant_id: restaurantId,
          image_url: '',
          is_available: true,
          is_upsell: false,
          is_special: false,
          prep_time_minutes: 5,
          display_order: 0
        })
      setSelectedImageUrl(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating menu item')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading menu items...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menu Items</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage your restaurant menu items and their ingredients
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {showCreateForm ? 'Cancel' : 'Create Menu Item'}
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
          <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Menu Item</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {/* Basic Info */}
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="e.g., Quantum Cheeseburger"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Category *
                  </label>
                  <select
                    required
                    value={formData.category_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, category_id: parseInt(e.target.value) }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    <option value="">Select a category</option>
                    {categories.map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                  {categories.length === 0 && (
                    <p className="mt-1 text-xs text-gray-500">
                      No categories found. <a href="/admin/categories" className="text-indigo-600 hover:text-indigo-800">Create one first</a>.
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Describe your menu item..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Price *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={formData.price}
                    onChange={(e) => setFormData(prev => ({ ...prev, price: e.target.value }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Prep Time (minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.prep_time_minutes}
                    onChange={(e) => setFormData(prev => ({ ...prev, prep_time_minutes: parseInt(e.target.value) }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  />
                </div>
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Menu Item Image
                </label>
                <ImageUpload
                  onImageUpload={handleImageUpload}
                  restaurantId={restaurantId}
                  className="mb-4"
                />
                {selectedImageUrl && (
                  <div className="text-sm text-green-600">
                    ✓ Image uploaded successfully
                  </div>
                )}
              </div>
            </div>

            {/* Options */}
            <div className="flex space-x-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_available}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_available: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Available for ordering</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_special}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_special: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Special item</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_upsell}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_upsell: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Upsell item</span>
              </label>
            </div>

            {/* Submit */}
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
                Create Menu Item
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Menu Items List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Menu Items ({menuItems.length})
          </h3>
          
          {menuItems.length === 0 ? (
            <div className="text-center py-6">
              <div className="text-4xl mb-2">🍽️</div>
              <p className="text-gray-500">No menu items found</p>
              <p className="text-sm text-gray-400 mt-1">
                Create your first menu item to get started
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {menuItems.map((item) => (
                <div key={item.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  {item.image_url && (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-full h-32 object-cover rounded-md mb-3"
                    />
                  )}
                  <h4 className="font-medium text-gray-900">{item.name}</h4>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{item.description}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-lg font-semibold text-green-600">
                      ${item.price.toFixed(2)}
                    </span>
                    <div className="flex space-x-1">
                      {item.is_special && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Special
                        </span>
                      )}
                      {!item.is_available && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Unavailable
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-3 flex space-x-2">
                    <Link
                      href={`/admin/menu-items/${item.id}/ingredients`}
                      className="flex-1 text-center px-3 py-1 text-xs font-medium text-indigo-600 hover:text-indigo-800 border border-indigo-300 rounded-md hover:bg-indigo-50"
                    >
                      Ingredients
                    </Link>
                    <Link
                      href={`/admin/menu-items/${item.id}/edit`}
                      className="flex-1 text-center px-3 py-1 text-xs font-medium text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Edit
                    </Link>
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
