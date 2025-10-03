'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'
import IngredientTypeahead from './IngredientTypeahead'

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

interface MenuItemIngredient {
  id: number
  menu_item_id: number
  ingredient_id: number
  quantity: number
  unit: string
  is_optional: boolean
  additional_cost: number
  ingredient: Ingredient
}

interface MenuItemIngredientManagerProps {
  menuItemId: number
  onIngredientsChange?: (ingredients: MenuItemIngredient[]) => void
}

export default function MenuItemIngredientManager({
  menuItemId,
  onIngredientsChange
}: MenuItemIngredientManagerProps) {
  const restaurantId = useRestaurantId()
  const [ingredients, setIngredients] = useState<MenuItemIngredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [batchMode, setBatchMode] = useState(false)
  const [selectedIngredients, setSelectedIngredients] = useState<Set<number>>(new Set())

  // Form state for adding new ingredient
  const [newIngredient, setNewIngredient] = useState<Ingredient | null>(null)
  const [quantity, setQuantity] = useState('1')
  const [unit, setUnit] = useState('piece')
  const [isOptional, setIsOptional] = useState(false)
  const [additionalCost, setAdditionalCost] = useState('0')

  useEffect(() => {
    if (menuItemId) {
      fetchIngredients()
    }
  }, [menuItemId])

  const fetchIngredients = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getMenuItemIngredients(menuItemId)
      setIngredients(data)
      onIngredientsChange?.(data)
    } catch (err) {
      setError('Error fetching ingredients')
      console.error('Error fetching ingredients:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddIngredient = async () => {
    if (!newIngredient) return

    try {
      const ingredientData = await apiClient.addIngredientToMenuItem(menuItemId, {
        ingredient_id: newIngredient.id,
        quantity: parseFloat(quantity),
        unit: unit,
        is_optional: isOptional,
        additional_cost: parseFloat(additionalCost)
      })

      setIngredients(prev => [...prev, ingredientData])
      onIngredientsChange?.([...ingredients, ingredientData])
      
      // Reset form
      setNewIngredient(null)
      setQuantity('1')
      setUnit('piece')
      setIsOptional(false)
      setAdditionalCost('0')
      setShowAddForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error adding ingredient')
    }
  }

  const handleRemoveIngredient = async (ingredientId: number) => {
    if (!confirm('Remove this ingredient from the menu item?')) return

    try {
      await apiClient.removeIngredientFromMenuItem(menuItemId, ingredientId)
      setIngredients(prev => prev.filter(ing => ing.ingredient_id !== ingredientId))
      onIngredientsChange?.(ingredients.filter(ing => ing.ingredient_id !== ingredientId))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error removing ingredient')
    }
  }

  const handleBatchRemove = async () => {
    if (selectedIngredients.size === 0) return

    if (!confirm(`Remove ${selectedIngredients.size} ingredients from this menu item?`)) return

    try {
      const promises = Array.from(selectedIngredients).map(ingredientId =>
        apiClient.removeIngredientFromMenuItem(menuItemId, ingredientId)
      )
      
      await Promise.all(promises)
      
      setIngredients(prev => prev.filter(ing => !selectedIngredients.has(ing.ingredient_id)))
      onIngredientsChange?.(ingredients.filter(ing => !selectedIngredients.has(ing.ingredient_id)))
      setSelectedIngredients(new Set())
      setBatchMode(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error removing ingredients')
    }
  }

  const handleSelectIngredient = (ingredient: Ingredient) => {
    setNewIngredient(ingredient)
  }

  const toggleBatchSelection = (ingredientId: number) => {
    const newSelected = new Set(selectedIngredients)
    if (newSelected.has(ingredientId)) {
      newSelected.delete(ingredientId)
    } else {
      newSelected.add(ingredientId)
    }
    setSelectedIngredients(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedIngredients.size === ingredients.length) {
      setSelectedIngredients(new Set())
    } else {
      setSelectedIngredients(new Set(ingredients.map(ing => ing.ingredient_id)))
    }
  }

  const getExcludedIngredientIds = () => {
    return ingredients.map(ing => ing.ingredient_id)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-600">Loading ingredients...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Ingredients ({ingredients.length})
        </h3>
        <div className="flex space-x-2">
          {ingredients.length > 0 && (
            <button
              onClick={() => setBatchMode(!batchMode)}
              className={`px-3 py-1 text-sm rounded-md ${
                batchMode
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {batchMode ? 'Exit Batch' : 'Batch Mode'}
            </button>
          )}
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Add Ingredient
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <div className="text-sm text-red-600">{error}</div>
        </div>
      )}

      {/* Batch Actions */}
      {batchMode && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={toggleSelectAll}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                {selectedIngredients.size === ingredients.length ? 'Deselect All' : 'Select All'}
              </button>
              <span className="text-sm text-blue-600">
                {selectedIngredients.size} selected
              </span>
            </div>
            {selectedIngredients.size > 0 && (
              <button
                onClick={handleBatchRemove}
                className="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Remove Selected ({selectedIngredients.size})
              </button>
            )}
          </div>
        </div>
      )}

      {/* Add Ingredient Form */}
      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
          <h4 className="text-md font-medium text-gray-900 mb-3">Add New Ingredient</h4>
          <div className="space-y-4">
            {/* Ingredient Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Ingredient
              </label>
              <IngredientTypeahead
                onSelect={handleSelectIngredient}
                placeholder="Type to search ingredients..."
                excludeIds={getExcludedIngredientIds()}
              />
              {newIngredient && (
                <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
                  <div className="text-sm text-green-800">
                    Selected: <strong>{newIngredient.name}</strong>
                    {newIngredient.is_allergen && (
                      <span className="ml-2 text-red-600">
                        (Allergen: {newIngredient.allergen_type})
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>

            {newIngredient && (
              <>
                {/* Quantity and Unit */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      placeholder="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Unit
                    </label>
                    <select
                      value={unit}
                      onChange={(e) => setUnit(e.target.value)}
                      className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    >
                      <option value="piece">piece</option>
                      <option value="cup">cup</option>
                      <option value="tbsp">tablespoon</option>
                      <option value="tsp">teaspoon</option>
                      <option value="oz">ounce</option>
                      <option value="lb">pound</option>
                      <option value="g">gram</option>
                      <option value="kg">kilogram</option>
                      <option value="ml">milliliter</option>
                      <option value="l">liter</option>
                      <option value="slice">slice</option>
                      <option value="clove">clove</option>
                      <option value="dash">dash</option>
                      <option value="pinch">pinch</option>
                    </select>
                  </div>
                </div>

                {/* Additional Cost */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Additional Cost (per serving)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={additionalCost}
                    onChange={(e) => setAdditionalCost(e.target.value)}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="0.00"
                  />
                </div>

                {/* Options */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="isOptional"
                    checked={isOptional}
                    onChange={(e) => setIsOptional(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="isOptional" className="ml-2 block text-sm text-gray-700">
                    This ingredient is optional
                  </label>
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleAddIngredient}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                  >
                    Add Ingredient
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Ingredients List */}
      {ingredients.length === 0 ? (
        <div className="text-center py-6 bg-gray-50 rounded-md">
          <div className="text-4xl mb-2">🥬</div>
          <p className="text-gray-500">No ingredients added yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Add ingredients to define what goes into this menu item
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {ingredients.map((itemIngredient) => (
            <div
              key={itemIngredient.id}
              className={`flex items-center justify-between p-3 border rounded-md ${
                batchMode && selectedIngredients.has(itemIngredient.ingredient_id)
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-center space-x-3">
                {batchMode && (
                  <input
                    type="checkbox"
                    checked={selectedIngredients.has(itemIngredient.ingredient_id)}
                    onChange={() => toggleBatchSelection(itemIngredient.ingredient_id)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                )}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      {itemIngredient.ingredient.name}
                    </span>
                    {itemIngredient.ingredient.is_allergen && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {itemIngredient.ingredient.allergen_type || 'Allergen'}
                      </span>
                    )}
                    {itemIngredient.is_optional && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Optional
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {itemIngredient.quantity} {itemIngredient.unit}
                    {itemIngredient.additional_cost > 0 && (
                      <span className="ml-2">
                        (+${itemIngredient.additional_cost.toFixed(2)})
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    ${itemIngredient.ingredient.unit_cost.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500">per unit</div>
                </div>
                {!batchMode && (
                  <button
                    onClick={() => handleRemoveIngredient(itemIngredient.ingredient_id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
