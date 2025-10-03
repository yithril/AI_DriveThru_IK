"""
Menu Cache Service - Preloads menu data into Redis for fast access
"""

from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class MenuCacheService:
    """
    Service for caching menu data in Redis for fast access during drive-thru operations.
    Menu data is preloaded on startup and can be refreshed as needed.
    """
    
    def __init__(self, redis_service, menu_service, restaurant_service):
        """
        Initialize with required services
        
        Args:
            redis_service: Redis service instance
            menu_service: MenuService for PostgreSQL fallback
            restaurant_service: RestaurantService for getting restaurant data
        """
        self.redis = redis_service
        self.menu_service = menu_service
        self.restaurant_service = restaurant_service
    
    async def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            await self.redis.get("health_check")
            return True
        except Exception as e:
            logger.error(f"Redis not available: {e}")
            return False
    
    async def preload_restaurant_menu(self, restaurant_id: int, ttl: int = 3600) -> bool:
        """
        Preload all menu data for a restaurant into Redis
        
        Args:
            restaurant_id: Restaurant ID to preload menu for
            ttl: Time to live in seconds (default 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot preload menu")
            return False
        
        try:
            # Get restaurant data
            restaurant = await self.restaurant_service.get_by_id(restaurant_id)
            if not restaurant:
                logger.error(f"Restaurant {restaurant_id} not found")
                return False
            
            # Get all menu items with ingredients
            menu_items = await self.menu_service.get_all_menu_items(restaurant_id)
            
            # Get all ingredients
            ingredients = await self.menu_service.get_all_ingredients(restaurant_id)
            
            # Prepare cache data
            cache_data = {
                "restaurant_id": restaurant_id,
                "restaurant_name": restaurant.name,
                "menu_items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "price": float(item.price),
                        "image_url": item.image_url,
                        "category_id": item.category_id,
                        "is_available": item.is_available,
                        "ingredients": await self._get_menu_item_ingredients(item.id)
                    }
                    for item in menu_items
                ],
                "ingredients": [
                    {
                        "id": ingredient.id,
                        "name": ingredient.name,
                        "description": ingredient.description,
                        "is_allergen": ingredient.is_allergen,
                        "allergen_type": ingredient.allergen_type,
                        "is_optional": ingredient.is_optional
                    }
                    for ingredient in ingredients
                ],
                "cached_at": "2024-01-01T00:00:00"  # Will be set to current time
            }
            
            # Cache the data
            success = await self.redis.set_json(
                f"menu_cache:{restaurant_id}", 
                cache_data, 
                expire=ttl
            )
            
            if success:
                logger.info(f"Preloaded menu data for restaurant {restaurant_id}")
                return True
            else:
                logger.error(f"Failed to cache menu data for restaurant {restaurant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error preloading menu for restaurant {restaurant_id}: {e}")
            return False
    
    async def get_cached_menu_items(self, restaurant_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached menu items for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            list: Cached menu items if available, None otherwise
        """
        if not await self.is_redis_available():
            return None
        
        try:
            cache_data = await self.redis.get_json(f"menu_cache:{restaurant_id}")
            if cache_data and "menu_items" in cache_data:
                return cache_data["menu_items"]
            return None
        except Exception as e:
            logger.error(f"Error getting cached menu items for restaurant {restaurant_id}: {e}")
            return None
    
    async def get_cached_ingredients(self, restaurant_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached ingredients for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            list: Cached ingredients if available, None otherwise
        """
        if not await self.is_redis_available():
            return None
        
        try:
            cache_data = await self.redis.get_json(f"menu_cache:{restaurant_id}")
            if cache_data and "ingredients" in cache_data:
                return cache_data["ingredients"]
            return None
        except Exception as e:
            logger.error(f"Error getting cached ingredients for restaurant {restaurant_id}: {e}")
            return None
    
    async def fuzzy_search_menu_items_cached(
        self, 
        restaurant_id: int, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search menu items using cached data
        
        Args:
            restaurant_id: Restaurant ID
            query: Search query
            limit: Maximum results
            
        Returns:
            list: Search results
        """
        # Try Redis cache first
        cached_items = await self.get_cached_menu_items(restaurant_id)
        if cached_items:
            return await self._fuzzy_search_in_cached_data(cached_items, query, limit)
        
        # Fallback to PostgreSQL
        logger.info(f"Cache miss for restaurant {restaurant_id}, falling back to PostgreSQL")
        return await self.menu_service.fuzzy_search_menu_items(restaurant_id, query, limit)
    
    async def fuzzy_search_ingredients_cached(
        self, 
        restaurant_id: int, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search ingredients using cached data
        
        Args:
            restaurant_id: Restaurant ID
            query: Search query
            limit: Maximum results
            
        Returns:
            list: Search results
        """
        # Try Redis cache first
        cached_ingredients = await self.get_cached_ingredients(restaurant_id)
        if cached_ingredients:
            return await self._fuzzy_search_ingredients_in_cached_data(cached_ingredients, query, limit)
        
        # Fallback to PostgreSQL
        logger.info(f"Cache miss for restaurant {restaurant_id}, falling back to PostgreSQL")
        return await self.menu_service.fuzzy_search_ingredients(restaurant_id, query, limit)
    
    async def invalidate_cache(self, restaurant_id: int) -> bool:
        """
        Invalidate cached menu data for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot invalidate cache")
            return False
        
        try:
            success = await self.redis.delete(f"menu_cache:{restaurant_id}")
            if success:
                logger.info(f"Invalidated menu cache for restaurant {restaurant_id}")
                return True
            else:
                logger.error(f"Failed to invalidate cache for restaurant {restaurant_id}")
                return False
        except Exception as e:
            logger.error(f"Error invalidating cache for restaurant {restaurant_id}: {e}")
            return False
    
    async def _get_menu_item_ingredients(self, menu_item_id: int) -> List[Dict[str, Any]]:
        """
        Get ingredients for a menu item (placeholder - would use MenuItemIngredient model)
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            list: Ingredients for the menu item
        """
        # TODO: Implement using MenuItemIngredient model
        # For now, return empty list
        return []
    
    async def _fuzzy_search_in_cached_data(
        self, 
        cached_items: List[Dict[str, Any]], 
        query: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search in cached menu items
        
        Args:
            cached_items: Cached menu items
            query: Search query
            limit: Maximum results
            
        Returns:
            list: Search results
        """
        from rapidfuzz import fuzz, process
        
        # Extract menu item names for fuzzy matching
        menu_names = [item["name"] for item in cached_items]
        
        # Use rapidfuzz to find best matches (case-insensitive)
        matches = process.extract(
            query.lower(),
            [name.lower() for name in menu_names],
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        # Filter out matches with very low scores (less than 60)
        matches = [(name, score, index) for name, score, index in matches if score >= 60]
        
        # Convert matches to structured results
        results = []
        for match_name, score, index in matches:
            menu_item = cached_items[index]
            results.append({
                "menu_item_id": menu_item["id"],
                "menu_item_name": menu_item["name"],
                "description": menu_item["description"],
                "price": menu_item["price"],
                "image_url": menu_item["image_url"],
                "category_id": menu_item["category_id"],
                "is_available": menu_item["is_available"],
                "ingredients": menu_item["ingredients"],
                "match_score": score
            })
        
        return results
    
    async def _fuzzy_search_ingredients_in_cached_data(
        self, 
        cached_ingredients: List[Dict[str, Any]], 
        query: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Perform fuzzy search in cached ingredients
        
        Args:
            cached_ingredients: Cached ingredients
            query: Search query
            limit: Maximum results
            
        Returns:
            list: Search results
        """
        from rapidfuzz import fuzz, process
        
        # Extract ingredient names for fuzzy matching
        ingredient_names = [ingredient["name"] for ingredient in cached_ingredients]
        
        # Use rapidfuzz to find best matches (case-insensitive)
        matches = process.extract(
            query.lower(),
            [name.lower() for name in ingredient_names],
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        # Filter out matches with very low scores (less than 60)
        matches = [(name, score, index) for name, score, index in matches if score >= 60]
        
        # Convert matches to structured results
        results = []
        for match_name, score, index in matches:
            ingredient = cached_ingredients[index]
            results.append({
                "ingredient_id": ingredient["id"],
                "ingredient_name": ingredient["name"],
                "description": ingredient["description"],
                "is_allergen": ingredient["is_allergen"],
                "allergen_type": ingredient["allergen_type"],
                "is_optional": ingredient["is_optional"],
                "match_score": score
            })
        
        return results
