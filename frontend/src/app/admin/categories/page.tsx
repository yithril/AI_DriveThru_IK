'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'

interface Category {
  id: number
  name: string
  description: string | null
  restaurant_id: number
  display_order: number
  is_active: boolean
  created_at: string
}

export default function CategoriesPage() {
  const restaurantId = useRestaurantId()
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    restaurant_id: restaurantId,
    display_order: 0,
    is_active: true
  })

  useEffect(() => {
    fetchCategories()
  }, [restaurantId])

  const fetchCategories = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getCategories(restaurantId)
      setCategories(data.sort((a, b) => a.display_order - b.display_order))
    } catch (err) {
      setError('Error fetching categories')
      console.error('Error fetching categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newCategory = await apiClient.createCategory({
        ...formData,
        restaurant_id: restaurantId,
        display_order: parseInt(formData.display_order.toString()),
      })

      setCategories(prev => [...prev, newCategory].sort((a, b) => a.display_order - b.display_order))
      setShowCreateForm(false)
      setFormData({
        name: '',
        description: '',
        restaurant_id: restaurantId,
        display_order: categories.length,
        is_active: true
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating category')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this category? This will affect menu items in this category.')) return

    try {
      await apiClient.deleteCategory(id)
      setCategories(prev => prev.filter(cat => cat.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error deleting category')
    }
  }

  const toggleActive = async (category: Category) => {
    try {
      const updated = await apiClient.updateCategory(category.id, {
        is_active: !category.is_active
      })
      setCategories(prev => prev.map(cat => 
        cat.id === category.id ? updated : cat
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error updating category')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading categories...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage menu categories for organizing your items
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {showCreateForm ? 'Cancel' : 'Add Category'}
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
          <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Category</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
                  placeholder="e.g., Burgers, Drinks, Sides"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Display Order
                </label>
                <input
                  type="number"
                  min="0"
                  value={formData.display_order}
                  onChange={(e) => setFormData(prev => ({ ...prev, display_order: parseInt(e.target.value) }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="0"
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
                placeholder="Optional description for this category..."
              />
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
                Create Category
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Categories List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Categories ({categories.length})
          </h3>
          
          {categories.length === 0 ? (
            <div className="text-center py-6">
              <div className="text-4xl mb-2">📁</div>
              <p className="text-gray-500">No categories found</p>
              <p className="text-sm text-gray-400 mt-1">
                Create your first category to organize your menu items
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {categories.map((category) => (
                <div key={category.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h4 className="font-medium text-gray-900">{category.name}</h4>
                        {!category.is_active && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      {category.description && (
                        <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                      )}
                      <div className="mt-2 text-xs text-gray-500">
                        Order: {category.display_order}
                      </div>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => toggleActive(category)}
                        className={`px-2 py-1 text-xs rounded-md ${
                          category.is_active
                            ? 'bg-green-100 text-green-800 hover:bg-green-200'
                            : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        }`}
                      >
                        {category.is_active ? 'Active' : 'Inactive'}
                      </button>
                      <button
                        onClick={() => handleDelete(category.id)}
                        className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-md hover:bg-red-200"
                      >
                        Delete
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
