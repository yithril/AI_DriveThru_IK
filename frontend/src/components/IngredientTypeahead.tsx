'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
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

interface IngredientTypeaheadProps {
  onSelect: (ingredient: Ingredient) => void
  placeholder?: string
  disabled?: boolean
  excludeIds?: number[] // Ingredients to exclude from results
  className?: string
}

export default function IngredientTypeahead({
  onSelect,
  placeholder = "Search ingredients...",
  disabled = false,
  excludeIds = [],
  className = ""
}: IngredientTypeaheadProps) {
  const restaurantId = useRestaurantId()
  const [query, setQuery] = useState('')
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [filteredIngredients, setFilteredIngredients] = useState<Ingredient[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length > 0) {
        searchIngredients(query)
      } else {
        setFilteredIngredients([])
      }
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [query])

  // Filter ingredients based on query and exclusions
  useEffect(() => {
    if (query.length === 0) {
      setFilteredIngredients([])
      return
    }

    const filtered = ingredients.filter(ingredient => {
      // Check if ingredient should be excluded
      if (excludeIds.includes(ingredient.id)) {
        return false
      }

      // Check if query matches ingredient name or description
      const nameMatch = ingredient.name.toLowerCase().includes(query.toLowerCase())
      const descriptionMatch = ingredient.description?.toLowerCase().includes(query.toLowerCase()) || false
      
      return nameMatch || descriptionMatch
    })

    // Sort by relevance (exact matches first, then partial matches)
    filtered.sort((a, b) => {
      const aExact = a.name.toLowerCase() === query.toLowerCase()
      const bExact = b.name.toLowerCase() === query.toLowerCase()
      
      if (aExact && !bExact) return -1
      if (!aExact && bExact) return 1
      
      const aStartsWith = a.name.toLowerCase().startsWith(query.toLowerCase())
      const bStartsWith = b.name.toLowerCase().startsWith(query.toLowerCase())
      
      if (aStartsWith && !bStartsWith) return -1
      if (!aStartsWith && bStartsWith) return 1
      
      return a.name.localeCompare(b.name)
    })

    setFilteredIngredients(filtered)
    setSelectedIndex(-1)
  }, [query, ingredients, excludeIds])

  const searchIngredients = async (searchQuery: string) => {
    if (searchQuery.length < 2) return

    setLoading(true)
    try {
      const results = await apiClient.getIngredients(restaurantId, searchQuery)
      setIngredients(results)
    } catch (error) {
      console.error('Error searching ingredients:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setQuery(value)
    setIsOpen(true)
  }

  const handleInputFocus = () => {
    setIsOpen(true)
  }

  const handleInputBlur = (e: React.FocusEvent) => {
    // Don't close if clicking on dropdown
    if (dropdownRef.current?.contains(e.relatedTarget as Node)) {
      return
    }
    setIsOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown') {
        setIsOpen(true)
        return
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < filteredIngredients.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : filteredIngredients.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < filteredIngredients.length) {
          handleSelect(filteredIngredients[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelect = useCallback((ingredient: Ingredient) => {
    onSelect(ingredient)
    setQuery('')
    setIsOpen(false)
    setSelectedIndex(-1)
    inputRef.current?.focus()
  }, [onSelect])

  const handleClickOutside = useCallback((event: MouseEvent) => {
    if (
      inputRef.current && 
      !inputRef.current.contains(event.target as Node) &&
      dropdownRef.current &&
      !dropdownRef.current.contains(event.target as Node)
    ) {
      setIsOpen(false)
    }
  }, [])

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [handleClickOutside])

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        />
        {loading && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
          </div>
        )}
      </div>

      {isOpen && filteredIngredients.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {filteredIngredients.map((ingredient, index) => (
            <div
              key={ingredient.id}
              onClick={() => handleSelect(ingredient)}
              className={`px-4 py-2 cursor-pointer border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex
                  ? 'bg-indigo-50 text-indigo-900'
                  : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      {ingredient.name}
                    </span>
                    {ingredient.is_allergen && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                        {ingredient.allergen_type || 'Allergen'}
                      </span>
                    )}
                  </div>
                  {ingredient.description && (
                    <p className="text-sm text-gray-500 mt-1">
                      {ingredient.description}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">
                    ${ingredient.unit_cost.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500">
                    per unit
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && query.length > 0 && filteredIngredients.length === 0 && !loading && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="px-4 py-3 text-sm text-gray-500 text-center">
            No ingredients found for "{query}"
          </div>
        </div>
      )}
    </div>
  )
}
