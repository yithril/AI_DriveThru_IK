'use client'

import { useMemo } from 'react'
import { useSearchParams } from 'next/navigation'

export function useRestaurantId(): number {
  const searchParams = useSearchParams()
  
  return useMemo(() => {
    // First try to get from URL parameters
    const urlRestaurantId = searchParams.get('restaurant_id')
    if (urlRestaurantId) {
      const parsedId = parseInt(urlRestaurantId, 10)
      if (!isNaN(parsedId) && parsedId > 0) {
        return parsedId
      }
    }
    
    // Fallback to environment variable
    const envRestaurantId = process.env.NEXT_PUBLIC_RESTAURANT_ID
    const parsedId = envRestaurantId ? parseInt(envRestaurantId, 10) : 1
    
    if (isNaN(parsedId) || parsedId < 1) {
      console.warn('Invalid restaurant ID, defaulting to 1')
      return 1
    }
    
    return parsedId
  }, [searchParams])
}
