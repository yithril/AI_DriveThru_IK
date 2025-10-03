'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'

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

export default function IngredientsPage() {
  const restaurantId = useRestaurantId()
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterAllergens, setFilterAllergens] = useState<boolean | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    restaurant_id: restaurantId,
    is_allergen: false,
    allergen_type: '',
    unit_cost: 0.0
  })

  useEffect(() => {
    fetchIngredients()
  }, [])

  const fetchIngredients = async () => {
    try {
      const data = await apiClient.getIngredients(restaurantId, searchTerm, filterAllergens || undefined)
      setIngredients(data)
    } catch (err) {
      setError('Error fetching ingredients')
      console.error('Error fetching ingredients:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIngredients()
  }, [searchTerm, filterAllergens])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newIngredient = await apiClient.createIngredient({
        ...formData,
        restaurant_id: restaurantId,
        unit_cost: parseFloat(formData.unit_cost.toString()),
        allergen_type: formData.is_allergen ? formData.allergen_type : undefined,
      })

      setIngredients(prev => [...prev, newIngredient])
      setShowCreateForm(false)
      setFormData({
        name: '',
        description: '',
        restaurant_id: restaurantId,
        is_allergen: false,
        allergen_type: '',
        unit_cost: 0.0
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creating ingredient')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this ingredient?')) return

    try {
      await apiClient.deleteIngredient(id)
      setIngredients(prev => prev.filter(ing => ing.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error deleting ingredient')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading ingredients...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ingredients</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage ingredients, allergens, and costs for your menu items
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {showCreateForm ? 'Cancel' : 'Add Ingredient'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-sm text-red-600">{error}</div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search ingredients
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name..."
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filter by allergens
            </label>
            <select
              value={filterAllergens === null ? '' : filterAllergens.toString()}
              onChange={(e) => setFilterAllergens(e.target.value === '' ? null : e.target.value === 'true')}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            >
              <option value="">All ingredients</option>
              <option value="true">Allergens only</option>
              <option value="false">Non-allergens only</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchIngredients}
              className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Ingredient</h2>
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
                  placeholder="e.g., Beef Patty"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Unit Cost *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.unit_cost}
                  onChange={(e) => setFormData(prev => ({ ...prev, unit_cost: parseFloat(e.target.value) }))}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="0.00"
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
                placeholder="Describe this ingredient..."
              />
            </div>

            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_allergen}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_allergen: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">This ingredient is an allergen</span>
              </label>

              {formData.is_allergen && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Allergen Type
                  </label>
                  <select
                    value={formData.allergen_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, allergen_type: e.target.value }))}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    <option value="">Select allergen type</option>
                    <option value="dairy">Dairy</option>
                    <option value="nuts">Nuts</option>
                    <option value="gluten">Gluten</option>
                    <option value="eggs">Eggs</option>
                    <option value="soy">Soy</option>
                    <option value="fish">Fish</option>
                    <option value="shellfish">Shellfish</option>
                    <option value="sesame">Sesame</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              )}
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
                Add Ingredient
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Ingredients List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Ingredients ({ingredients.length})
          </h3>
          
          {ingredients.length === 0 ? (
            <div className="text-center py-6">
              <div className="text-4xl mb-2">🥬</div>
              <p className="text-gray-500">No ingredients found</p>
              <p className="text-sm text-gray-400 mt-1">
                Add your first ingredient to get started
              </p>
            </div>
          ) : (
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit Cost
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Allergen
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {ingredients.map((ingredient) => (
                    <tr key={ingredient.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {ingredient.name}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600 max-w-xs truncate">
                          {ingredient.description || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          ${ingredient.unit_cost.toFixed(2)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {ingredient.is_allergen ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {ingredient.allergen_type || 'Allergen'}
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Safe
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleDelete(ingredient.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
