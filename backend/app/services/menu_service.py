"""
Menu Service with fuzzy search for menu items and ingredients

This service provides fuzzy search capabilities for both menu items and ingredients.
For menu items, it can load their associated ingredients using prefetch_related.
Uses Redis cache first, PostgreSQL fallback.
"""

import logging
from typing import List, Optional, Dict, Any
from rapidfuzz import fuzz, process
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient
from app.dto import (
    MenuItemResponseDto,
    IngredientResponseDto,
    MenuItemListResponseDto,
    IngredientListResponseDto
)

logger = logging.getLogger(__name__)


class MenuService:
    """
    Service for fuzzy searching menu items and ingredients with related data.
    Uses Redis cache first, PostgreSQL fallback.
    """
    
    def __init__(self, menu_cache_service=None):
        """
        Initialize with optional cache service
        
        Args:
            menu_cache_service: MenuCacheService for Redis caching
        """
        self.cache_service = menu_cache_service
    
    async def get_menu_items(self, restaurant_id: int) -> List[Dict[str, Any]]:
        """
        Get all menu items for a restaurant (for STT context).
        Uses cache service if available, otherwise falls back to PostgreSQL.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            List of menu items with basic info
        """
        try:
            # Try cache service first if available
            if self.cache_service:
                cached_items = await self.cache_service.get_cached_menu_items(restaurant_id)
                if cached_items:
                    # Convert cached items to the format expected by STT
                    return [
                        {
                            "name": item.get("name", ""),
                            "description": item.get("description", ""),
                            "ingredients": item.get("ingredients", [])
                        }
                        for item in cached_items
                    ]
            
            # Fallback to PostgreSQL - get all items directly
            menu_items = await MenuItem.filter(
                restaurant_id=restaurant_id,
                is_available=True
            ).order_by('display_order').all()
            
            return [
                {
                    "name": item.name,
                    "description": item.description or "",
                    "ingredients": []
                }
                for item in menu_items
            ]
            
        except Exception as e:
            logger.error(f"Error getting menu items for restaurant {restaurant_id}: {e}")
            return []
    
    async def fuzzy_search_menu_items(
        self, 
        restaurant_id: int, 
        search_term: str, 
        limit: int = 5,
        include_ingredients: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for menu items using rapidfuzz.
        Uses Redis cache first, PostgreSQL fallback.
        
        Args:
            restaurant_id: Restaurant ID to search within
            search_term: User's search term (e.g., "pizza", "burger")
            limit: Maximum number of results to return
            include_ingredients: Whether to load associated ingredients
            
        Returns:
            List of menu item dictionaries with match scores and optional ingredients
        """
        # Try Redis cache first if available
        if self.cache_service:
            try:
                cached_results = await self.cache_service.fuzzy_search_menu_items_cached(
                    restaurant_id, search_term, limit
                )
                if cached_results:
                    return cached_results
            except Exception as e:
                print(f"Cache search failed, falling back to PostgreSQL: {e}")
        
        # Fallback to PostgreSQL
        return await self._fuzzy_search_menu_items_postgres(restaurant_id, search_term, limit, include_ingredients)
    
    async def _fuzzy_search_menu_items_postgres(
        self, 
        restaurant_id: int, 
        search_term: str, 
        limit: int = 5,
        include_ingredients: bool = True
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL fallback for fuzzy search menu items
        
        Args:
            restaurant_id: Restaurant ID to search within
            search_term: User's search term (e.g., "pizza", "burger")
            limit: Maximum number of results to return
            include_ingredients: Whether to load associated ingredients
            
        Returns:
            List of menu item dictionaries with match scores and optional ingredients
        """
        try:
            # Get all available menu items for the restaurant
            menu_items = await MenuItem.filter(
                restaurant_id=restaurant_id,
                is_available=True
            ).order_by('display_order').all()
            
            if not menu_items:
                return []
            
            # Prepare menu item names for fuzzy matching
            menu_names = [item.name for item in menu_items]
            
            # DEBUG: Log available menu items
            logger.info(f"DEBUG FUZZY SEARCH: Available menu items for restaurant {restaurant_id}:")
            for i, name in enumerate(menu_names):
                logger.info(f"  {i+1}. '{name}'")
            
            # Use rapidfuzz to find best matches (case-insensitive)
            matches = process.extract(
                search_term.lower(),
                [name.lower() for name in menu_names],
                scorer=fuzz.WRatio,  # Use weighted ratio for better matching
                limit=limit
            )
            
            # DEBUG: Log all matches before filtering
            logger.info(f"DEBUG FUZZY SEARCH: '{search_term}' -> {len(matches)} raw matches")
            for i, (name, score, index) in enumerate(matches):
                logger.info(f"  Raw match {i+1}: '{name}' (score: {score:.1f}, index: {index})")
            
            # Filter out matches with very low scores (less than 60)
            matches = [(name, score, index) for name, score, index in matches if score >= 60]
            
            # DEBUG: Log filtered matches
            logger.info(f"DEBUG FUZZY SEARCH: After filtering (score >= 60): {len(matches)} matches")
            for i, (name, score, index) in enumerate(matches):
                logger.info(f"  Filtered match {i+1}: '{name}' (score: {score:.1f})")
            
            # Convert matches to structured results
            results = []
            for match_name, score, index in matches:
                menu_item = menu_items[index]
                # Use original case name from the menu item
                original_name = menu_item.name
                
                result = {
                    "id": menu_item.id,  # Changed from menu_item_id
                    "name": menu_item.name,  # Changed from menu_item_name
                    "menu_item_id": menu_item.id,  # Keep both for compatibility
                    "menu_item_name": menu_item.name,  # Keep both for compatibility
                    "description": menu_item.description,
                    "price": float(menu_item.price),
                    "image_url": menu_item.image_url,
                    "category_id": menu_item.category_id,
                    "is_special": menu_item.is_special,
                    "is_upsell": menu_item.is_upsell,
                    "prep_time_minutes": menu_item.prep_time_minutes,
                    "match_score": score
                }
                
                # Load ingredients if requested
                if include_ingredients:
                    ingredients = await self._get_menu_item_ingredients(menu_item.id)
                    result["ingredients"] = ingredients
                
                results.append(result)
            
            return results
        
        except Exception as e:
            print(f"Error in fuzzy_search_menu_items: {e}")
            return []
    
    async def fuzzy_search_ingredients(
        self, 
        restaurant_id: int, 
        search_term: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy search for ingredients using rapidfuzz.
        Uses Redis cache first, PostgreSQL fallback.
        
        Args:
            restaurant_id: Restaurant ID to search within
            search_term: User's search term (e.g., "cheese", "onions")
            limit: Maximum number of results to return
            
        Returns:
            List of ingredient dictionaries with match scores
        """
        # Try Redis cache first if available
        if self.cache_service:
            try:
                cached_results = await self.cache_service.fuzzy_search_ingredients_cached(
                    restaurant_id, search_term, limit
                )
                if cached_results:
                    return cached_results
            except Exception as e:
                print(f"Cache search failed, falling back to PostgreSQL: {e}")
        
        # Fallback to PostgreSQL
        return await self._fuzzy_search_ingredients_postgres(restaurant_id, search_term, limit)
    
    async def _fuzzy_search_ingredients_postgres(
        self, 
        restaurant_id: int, 
        search_term: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        PostgreSQL fallback for fuzzy search ingredients
        
        Args:
            restaurant_id: Restaurant ID to search within
            search_term: User's search term (e.g., "cheese", "onions")
            limit: Maximum number of results to return
            
        Returns:
            List of ingredient dictionaries with match scores
        """
        try:
            # Get all ingredients for the restaurant
            ingredients = await Ingredient.filter(
                restaurant_id=restaurant_id
            ).order_by('name').all()
            
            if not ingredients:
                return []
            
            # Prepare ingredient names for fuzzy matching
            ingredient_names = [ingredient.name for ingredient in ingredients]
            
            # Use rapidfuzz to find best matches (case-insensitive)
            matches = process.extract(
                search_term.lower(),
                [name.lower() for name in ingredient_names],
                scorer=fuzz.WRatio,  # Use weighted ratio for better matching
                limit=limit
            )
            
            # Filter out matches with very low scores (less than 60)
            matches = [(name, score, index) for name, score, index in matches if score >= 60]
            
            # Convert matches to structured results
            results = []
            for match_name, score, index in matches:
                ingredient = ingredients[index]
                # Use original case name from the ingredient
                original_name = ingredient.name
                
                results.append({
                    "ingredient_id": ingredient.id,
                    "ingredient_name": ingredient.name,
                    "description": ingredient.description,
                    "is_allergen": ingredient.is_allergen,
                    "allergen_type": ingredient.allergen_type,
                    "is_optional": ingredient.is_optional,
                    "match_score": score
                })
            
            return results
        
        except Exception as e:
            print(f"Error in fuzzy_search_ingredients: {e}")
            return []
    
    async def get_menu_item_with_ingredients(
        self, 
        restaurant_id: int, 
        menu_item_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific menu item with its ingredients loaded.
        
        Args:
            restaurant_id: Restaurant ID
            menu_item_id: Menu item ID
            
        Returns:
            Menu item dictionary with ingredients or None if not found
        """
        try:
            menu_item = await MenuItem.get_or_none(
                id=menu_item_id,
                restaurant_id=restaurant_id,
                is_available=True
            )
            
            if not menu_item:
                return None
            
            # Get ingredients for this menu item
            ingredients = await self._get_menu_item_ingredients(menu_item.id)
            
            return {
                "menu_item_id": menu_item.id,
                "menu_item_name": menu_item.name,
                "description": menu_item.description,
                "price": float(menu_item.price),
                "image_url": menu_item.image_url,
                "category_id": menu_item.category_id,
                "is_special": menu_item.is_special,
                "is_upsell": menu_item.is_upsell,
                "prep_time_minutes": menu_item.prep_time_minutes,
                "ingredients": ingredients
            }
        
        except Exception as e:
            print(f"Error in get_menu_item_with_ingredients: {e}")
            return None
    
    async def search_menu_items_by_ingredient(
        self, 
        restaurant_id: int, 
        ingredient_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find menu items that contain a specific ingredient.
        
        Args:
            restaurant_id: Restaurant ID
            ingredient_name: Name of the ingredient to search for
            limit: Maximum number of results to return
            
        Returns:
            List of menu items that contain the ingredient
        """
        try:
            # First, find the ingredient(s) that match the name
            ingredient_matches = await self.fuzzy_search_ingredients(
                restaurant_id, ingredient_name, limit=5
            )
            
            if not ingredient_matches:
                return []
            
            # Get menu items that contain any of the matching ingredients
            menu_items = []
            for ingredient_match in ingredient_matches:
                ingredient_id = ingredient_match["ingredient_id"]
                
                # Find menu items that use this ingredient
                menu_item_ingredients = await MenuItemIngredient.filter(
                    ingredient_id=ingredient_id
                ).prefetch_related('menu_item').all()
                
                for menu_item_ingredient in menu_item_ingredients:
                    menu_item = menu_item_ingredient.menu_item
                    
                    # Only include items from the correct restaurant and available
                    if (menu_item.restaurant_id == restaurant_id and 
                        menu_item.is_available):
                        
                        menu_items.append({
                            "menu_item_id": menu_item.id,
                            "menu_item_name": menu_item.name,
                            "description": menu_item.description,
                            "price": float(menu_item.price),
                            "image_url": menu_item.image_url,
                            "category_id": menu_item.category_id,
                            "is_special": menu_item.is_special,
                            "is_upsell": menu_item.is_upsell,
                            "prep_time_minutes": menu_item.prep_time_minutes,
                            "matching_ingredient": ingredient_match["ingredient_name"],
                            "ingredient_match_score": ingredient_match["match_score"]
                        })
            
            # Remove duplicates and limit results
            seen_ids = set()
            unique_items = []
            for item in menu_items:
                if item["menu_item_id"] not in seen_ids:
                    seen_ids.add(item["menu_item_id"])
                    unique_items.append(item)
                    if len(unique_items) >= limit:
                        break
            
            return unique_items
        
        except Exception as e:
            print(f"Error in search_menu_items_by_ingredient: {e}")
            return []
    
    async def _get_menu_item_ingredients(self, menu_item_id: int) -> List[Dict[str, Any]]:
        """
        Helper method to get ingredients for a menu item.
        
        Args:
            menu_item_id: Menu item ID
            
        Returns:
            List of ingredient dictionaries
        """
        try:
            menu_item_ingredients = await MenuItemIngredient.filter(
                menu_item_id=menu_item_id
            ).prefetch_related('ingredient').all()
            
            ingredients = []
            for menu_item_ingredient in menu_item_ingredients:
                ingredient = menu_item_ingredient.ingredient
                ingredients.append({
                    "ingredient_id": ingredient.id,
                    "ingredient_name": ingredient.name,
                    "description": ingredient.description,
                    "is_allergen": ingredient.is_allergen,
                    "allergen_type": ingredient.allergen_type,
                    "is_optional": ingredient.is_optional,
                    "quantity": float(menu_item_ingredient.quantity),
                    "unit": menu_item_ingredient.unit,
                    "additional_cost": float(menu_item_ingredient.additional_cost)
                })
            
            return ingredients
        
        except Exception as e:
            print(f"Error in _get_menu_item_ingredients: {e}")
            return []
