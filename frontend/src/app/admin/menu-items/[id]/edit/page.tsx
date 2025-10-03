'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'
import ImageUpload from '@/components/ImageUpload'

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

export default function EditMenuItemPage() {
  const params = useParams()
  const router = useRouter()
  const restaurantId = useRestaurantId()
  const menuItemId = parseInt(params.id as string)

  const [menuItem, setMenuItem] = useState<MenuItem | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category_id: 1,
    restaurant_id: restaurantId,
    image_url: '',
    is_available: true,
    is_upsell: false,
    is_special: false,
    prep_time_minutes: 5,
    display_order: 0
  })

  useEffect(() => {
    if (menuItemId) {
      fetchMenuItem()
    }
  }, [menuItemId])

  const fetchMenuItem = async () => {
    try {
      setLoading(true)
      // Get all menu items and find the one we're editing
      const menuItems = await apiClient.getMenuItems(restaurantId)
      const item = menuItems.find(item => item.id === menuItemId)
      
      if (item) {
        setMenuItem(item)
        setFormData({
          name: item.name,
          description: item.description || '',
          price: item.price.toString(),
          category_id: item.category_id,
          restaurant_id: item.restaurant_id,
          image_url: item.image_url || '',
          is_available: item.is_available,
          is_upsell: item.is_upsell,
          is_special: item.is_special,
          prep_time_minutes: item.prep_time_minutes,
          display_order: item.display_order
        })
        if (item.image_url) {
          setSelectedImageUrl(item.image_url)
        }
      } else {
        setError('Menu item not found')
      }
    } catch (err) {
      setError('Error fetching menu item')
      console.error('Error fetching menu item:', err)
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
    
    if (!menuItem) return

    try {
      setSaving(true)
      setError(null)

      await apiClient.updateMenuItem(menuItem.id, {
        name: formData.name,
        description: formData.description || undefined,
        price: parseFloat(formData.price),
        category_id: formData.category_id,
        image_url: formData.image_url || undefined,
        is_available: formData.is_available,
        is_upsell: formData.is_upsell,
        is_special: formData.is_special,
        prep_time_minutes: formData.prep_time_minutes,
        display_order: formData.display_order
      })

      // Redirect back to menu items page
      router.push('/admin/menu-items')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error updating menu item')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading menu item...</div>
      </div>
    )
  }

  if (error || !menuItem) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-600">{error || 'Menu item not found'}</div>
        </div>
        <Link
          href="/admin/menu-items"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
        >
          ← Back to Menu Items
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
            <Link href="/admin/menu-items" className="hover:text-gray-700">
              Menu Items
            </Link>
            <span>→</span>
            <span>Edit</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Edit Menu Item</h1>
          <p className="mt-1 text-sm text-gray-600">
            Update the details for {menuItem.name}
          </p>
        </div>
        <Link
          href="/admin/menu-items"
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          ← Back to Menu Items
        </Link>
      </div>

      {/* Edit Form */}
      <div className="bg-white shadow rounded-lg p-6">
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
              {menuItem.image_url && !selectedImageUrl && (
                <div className="mt-2">
                  <p className="text-sm text-gray-600 mb-2">Current image:</p>
                  <img
                    src={menuItem.image_url}
                    alt={menuItem.name}
                    className="w-32 h-32 object-cover rounded-lg"
                  />
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

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-600">{error}</div>
            </div>
          )}

          {/* Submit */}
          <div className="flex justify-end space-x-3">
            <Link
              href="/admin/menu-items"
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
