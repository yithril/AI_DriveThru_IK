"""
Startup Service - Handles application initialization and menu preloading
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class StartupService:
    """
    Service for handling application startup tasks like menu preloading
    """
    
    def __init__(self, menu_cache_service, restaurant_service):
        """
        Initialize with required services
        
        Args:
            menu_cache_service: MenuCacheService for preloading menu data
            restaurant_service: RestaurantService for getting restaurant list
        """
        self.menu_cache_service = menu_cache_service
        self.restaurant_service = restaurant_service
    
    async def preload_all_restaurant_menus(self) -> bool:
        """
        Preload menu data for all restaurants into Redis cache
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting menu preload for all restaurants")
            
            # Get all restaurants
            restaurants = await self.restaurant_service.get_all()
            if not restaurants:
                logger.warning("No restaurants found to preload menus")
                return True  # Not an error, just no data
            
            success_count = 0
            total_count = len(restaurants)
            
            for restaurant in restaurants:
                try:
                    success = await self.menu_cache_service.preload_restaurant_menu(restaurant.id)
                    if success:
                        success_count += 1
                        logger.info(f"Preloaded menu for restaurant {restaurant.id} ({restaurant.name})")
                    else:
                        logger.error(f"Failed to preload menu for restaurant {restaurant.id} ({restaurant.name})")
                except Exception as e:
                    logger.error(f"Error preloading menu for restaurant {restaurant.id}: {e}")
            
            logger.info(f"Menu preload completed: {success_count}/{total_count} restaurants successful")
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"Error during menu preload: {e}")
            return False
    
    async def preload_restaurant_menu(self, restaurant_id: int) -> bool:
        """
        Preload menu data for a specific restaurant
        
        Args:
            restaurant_id: Restaurant ID to preload menu for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Preloading menu for restaurant {restaurant_id}")
            
            success = await self.menu_cache_service.preload_restaurant_menu(restaurant_id)
            
            if success:
                logger.info(f"Successfully preloaded menu for restaurant {restaurant_id}")
            else:
                logger.error(f"Failed to preload menu for restaurant {restaurant_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error preloading menu for restaurant {restaurant_id}: {e}")
            return False
    
    async def refresh_restaurant_menu(self, restaurant_id: int) -> bool:
        """
        Refresh menu data for a specific restaurant (invalidates cache and reloads)
        
        Args:
            restaurant_id: Restaurant ID to refresh menu for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Refreshing menu for restaurant {restaurant_id}")
            
            # Invalidate existing cache
            await self.menu_cache_service.invalidate_cache(restaurant_id)
            
            # Reload menu data
            success = await self.menu_cache_service.preload_restaurant_menu(restaurant_id)
            
            if success:
                logger.info(f"Successfully refreshed menu for restaurant {restaurant_id}")
            else:
                logger.error(f"Failed to refresh menu for restaurant {restaurant_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error refreshing menu for restaurant {restaurant_id}: {e}")
            return False
    
    async def check_cache_health(self) -> dict:
        """
        Check the health of the menu cache
        
        Returns:
            dict: Cache health status
        """
        try:
            # Check if Redis is available
            redis_available = await self.menu_cache_service.is_redis_available()
            
            if not redis_available:
                return {
                    "status": "unhealthy",
                    "reason": "Redis not available",
                    "cached_restaurants": []
                }
            
            # Get all restaurants and check cache status
            restaurants = await self.restaurant_service.get_all()
            cached_restaurants = []
            uncached_restaurants = []
            
            for restaurant in restaurants:
                cached_items = await self.menu_cache_service.get_cached_menu_items(restaurant.id)
                if cached_items:
                    cached_restaurants.append({
                        "id": restaurant.id,
                        "name": restaurant.name,
                        "cached_items": len(cached_items)
                    })
                else:
                    uncached_restaurants.append({
                        "id": restaurant.id,
                        "name": restaurant.name
                    })
            
            return {
                "status": "healthy" if uncached_restaurants else "partial",
                "redis_available": redis_available,
                "total_restaurants": len(restaurants),
                "cached_restaurants": cached_restaurants,
                "uncached_restaurants": uncached_restaurants
            }
            
        except Exception as e:
            logger.error(f"Error checking cache health: {e}")
            return {
                "status": "error",
                "reason": str(e),
                "cached_restaurants": []
            }
