'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { apiClient } from '@/lib/api'
import { useRestaurantId } from '@/hooks/useRestaurantId'
import MenuItemIngredientManager from '@/components/MenuItemIngredientManager'

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

interface MenuItemIngredient {
  id: number
  menu_item_id: number
  ingredient_id: number
  quantity: number
  unit: string
  is_optional: boolean
  additional_cost: number
  ingredient: {
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
}

export default function MenuItemIngredientsPage() {
  const params = useParams()
  const router = useRouter()
  const restaurantId = useRestaurantId()
  const menuItemId = parseInt(params.id as string)

  const [menuItem, setMenuItem] = useState<MenuItem | null>(null)
  const [ingredients, setIngredients] = useState<MenuItemIngredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (menuItemId) {
      fetchMenuItem()
    }
  }, [menuItemId])

  const fetchMenuItem = async () => {
    try {
      setLoading(true)
      // For now, we'll get menu item from the list - in a real app, you'd have a specific endpoint
      const menuItems = await apiClient.getMenuItems(restaurantId)
      const item = menuItems.find(item => item.id === menuItemId)
      
      if (item) {
        setMenuItem(item)
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

  const handleIngredientsChange = (newIngredients: MenuItemIngredient[]) => {
    setIngredients(newIngredients)
  }

  const getTotalCost = () => {
    return ingredients.reduce((total, itemIngredient) => {
      const baseCost = itemIngredient.ingredient.unit_cost * itemIngredient.quantity
      const additionalCost = itemIngredient.additional_cost
      return total + baseCost + additionalCost
    }, 0)
  }

  const getCostBreakdown = () => {
    const breakdown = ingredients.map(itemIngredient => {
      const baseCost = itemIngredient.ingredient.unit_cost * itemIngredient.quantity
      const additionalCost = itemIngredient.additional_cost
      const totalCost = baseCost + additionalCost
      
      return {
        name: itemIngredient.ingredient.name,
        quantity: itemIngredient.quantity,
        unit: itemIngredient.unit,
        unitCost: itemIngredient.ingredient.unit_cost,
        baseCost,
        additionalCost,
        totalCost,
        isOptional: itemIngredient.is_optional
      }
    })

    return breakdown.sort((a, b) => b.totalCost - a.totalCost)
  }

  const getProfitMargin = () => {
    if (!menuItem) return 0
    const totalCost = getTotalCost()
    const sellingPrice = menuItem.price
    const profit = sellingPrice - totalCost
    return totalCost > 0 ? (profit / totalCost) * 100 : 0
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

  const costBreakdown = getCostBreakdown()
  const totalCost = getTotalCost()
  const profitMargin = getProfitMargin()

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
            <span>Ingredients</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{menuItem.name}</h1>
          <p className="mt-1 text-sm text-gray-600">
            Manage ingredients and calculate costs for this menu item
          </p>
        </div>
        <Link
          href="/admin/menu-items"
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          ← Back to Menu Items
        </Link>
      </div>

      {/* Menu Item Info */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-start space-x-4">
          {menuItem.image_url && (
            <img
              src={menuItem.image_url}
              alt={menuItem.name}
              className="w-24 h-24 object-cover rounded-lg"
            />
          )}
          <div className="flex-1">
            <h2 className="text-lg font-medium text-gray-900">{menuItem.name}</h2>
            {menuItem.description && (
              <p className="text-gray-600 mt-1">{menuItem.description}</p>
            )}
            <div className="mt-2 flex items-center space-x-4">
              <span className="text-2xl font-bold text-green-600">
                ${menuItem.price.toFixed(2)}
              </span>
              <span className="text-sm text-gray-500">selling price</span>
            </div>
            <div className="mt-2 flex items-center space-x-4">
              <span className="text-lg font-semibold text-red-600">
                ${totalCost.toFixed(2)}
              </span>
              <span className="text-sm text-gray-500">total cost</span>
              <span className={`text-sm font-medium ${profitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {profitMargin >= 0 ? '+' : ''}{profitMargin.toFixed(1)}% margin
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      {ingredients.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Cost Breakdown</h3>
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-300">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ingredient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unit Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Base Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Additional
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {costBreakdown.map((item, index) => (
                  <tr key={index} className={item.isOptional ? 'bg-yellow-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">
                          {item.name}
                        </div>
                        {item.isOptional && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Optional
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.quantity} {item.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${item.unitCost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${item.baseCost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${item.additionalCost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      ${item.totalCost.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan={5} className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                    Total Cost:
                  </td>
                  <td className="px-6 py-3 whitespace-nowrap text-sm font-bold text-gray-900">
                    ${totalCost.toFixed(2)}
                  </td>
                </tr>
                <tr>
                  <td colSpan={5} className="px-6 py-3 text-right text-sm font-medium text-gray-900">
                    Profit:
                  </td>
                  <td className={`px-6 py-3 whitespace-nowrap text-sm font-bold ${profitMargin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${(menuItem.price - totalCost).toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Ingredient Manager */}
      <div className="bg-white shadow rounded-lg p-6">
        <MenuItemIngredientManager
          menuItemId={menuItemId}
          onIngredientsChange={handleIngredientsChange}
        />
      </div>
    </div>
  )
}
