"""
Unit tests for MenuCacheService - Redis-based menu caching
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.services.menu_cache_service import MenuCacheService


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing"""
    redis_service = AsyncMock()
    redis_service.get.return_value = None
    redis_service.set.return_value = True
    redis_service.set_json.return_value = True
    redis_service.get_json.return_value = None
    redis_service.delete.return_value = True
    return redis_service


@pytest.fixture
def mock_menu_service():
    """Mock MenuService for testing"""
    menu_service = AsyncMock()
    
    # Mock menu items
    menu_items = [
        Mock(id=1, name="Margherita Pizza", description="Classic pizza", price=12.99, 
             image_url="pizza.jpg", category_id=1, is_available=True),
        Mock(id=2, name="Cheese Burger", description="Beef burger", price=9.99,
             image_url="burger.jpg", category_id=2, is_available=True)
    ]
    
    # Mock ingredients
    ingredients = [
        Mock(id=1, name="Mozzarella Cheese", description="Fresh mozzarella", 
             is_allergen=True, allergen_type="dairy", is_optional=False),
        Mock(id=2, name="Fresh Tomatoes", description="Ripe tomatoes",
             is_allergen=False, allergen_type=None, is_optional=False)
    ]
    
    menu_service.get_all_menu_items.return_value = menu_items
    menu_service.get_all_ingredients.return_value = ingredients
    
    return menu_service


@pytest.fixture
def mock_restaurant_service():
    """Mock RestaurantService for testing"""
    restaurant_service = AsyncMock()
    
    restaurant = Mock()
    restaurant.id = 1
    restaurant.name = "Test Restaurant"
    restaurant_service.get_by_id.return_value = restaurant
    
    return restaurant_service


@pytest.fixture
def menu_cache_service(mock_redis_service, mock_menu_service, mock_restaurant_service):
    """Fixture for MenuCacheService"""
    return MenuCacheService(mock_redis_service, mock_menu_service, mock_restaurant_service)


class TestMenuCacheService:
    """Test MenuCacheService operations"""

    async def test_is_redis_available_success(self, menu_cache_service, mock_redis_service):
        """Test Redis availability check when Redis is available"""
        mock_redis_service.get.return_value = "ok"
        
        result = await menu_cache_service.is_redis_available()
        
        assert result is True
        mock_redis_service.get.assert_called_once_with("health_check")

    async def test_is_redis_available_failure(self, menu_cache_service, mock_redis_service):
        """Test Redis availability check when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Connection failed")
        
        result = await menu_cache_service.is_redis_available()
        
        assert result is False

    async def test_preload_restaurant_menu_success(self, menu_cache_service, mock_redis_service, mock_menu_service, mock_restaurant_service):
        """Test successful restaurant menu preloading"""
        mock_redis_service.set_json.return_value = True
        
        result = await menu_cache_service.preload_restaurant_menu(restaurant_id=1)
        
        assert result is True
        
        # Verify Redis call
        mock_redis_service.set_json.assert_called_once()
        
        # Check the cache data structure
        call_args = mock_redis_service.set_json.call_args
        cache_key = call_args[0][0]  # First argument is the key
        cache_data = call_args[0][1]  # Second argument is the data
        
        assert cache_key == "menu_cache:1"
        assert cache_data["restaurant_id"] == 1
        assert cache_data["restaurant_name"] == "Test Restaurant"
        assert len(cache_data["menu_items"]) == 2
        assert len(cache_data["ingredients"]) == 2
        assert "cached_at" in cache_data

    async def test_preload_restaurant_menu_redis_unavailable(self, menu_cache_service, mock_redis_service):
        """Test menu preloading when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Redis unavailable")
        
        result = await menu_cache_service.preload_restaurant_menu(restaurant_id=1)
        
        assert result is False

    async def test_preload_restaurant_menu_restaurant_not_found(self, menu_cache_service, mock_restaurant_service):
        """Test menu preloading when restaurant doesn't exist"""
        mock_restaurant_service.get_by_id.return_value = None
        
        result = await menu_cache_service.preload_restaurant_menu(restaurant_id=999)
        
        assert result is False

    async def test_get_cached_menu_items_success(self, menu_cache_service, mock_redis_service):
        """Test successful cached menu items retrieval"""
        expected_data = {
            "restaurant_id": 1,
            "menu_items": [
                {"id": 1, "name": "Margherita Pizza", "price": 12.99},
                {"id": 2, "name": "Cheese Burger", "price": 9.99}
            ]
        }
        mock_redis_service.get_json.return_value = expected_data
        
        result = await menu_cache_service.get_cached_menu_items(restaurant_id=1)
        
        assert result == expected_data["menu_items"]
        mock_redis_service.get_json.assert_called_once_with("menu_cache:1")

    async def test_get_cached_menu_items_not_found(self, menu_cache_service, mock_redis_service):
        """Test cached menu items retrieval when cache doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await menu_cache_service.get_cached_menu_items(restaurant_id=1)
        
        assert result is None

    async def test_get_cached_ingredients_success(self, menu_cache_service, mock_redis_service):
        """Test successful cached ingredients retrieval"""
        expected_data = {
            "restaurant_id": 1,
            "ingredients": [
                {"id": 1, "name": "Mozzarella Cheese", "is_allergen": True},
                {"id": 2, "name": "Fresh Tomatoes", "is_allergen": False}
            ]
        }
        mock_redis_service.get_json.return_value = expected_data
        
        result = await menu_cache_service.get_cached_ingredients(restaurant_id=1)
        
        assert result == expected_data["ingredients"]
        mock_redis_service.get_json.assert_called_once_with("menu_cache:1")

    async def test_get_cached_ingredients_not_found(self, menu_cache_service, mock_redis_service):
        """Test cached ingredients retrieval when cache doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await menu_cache_service.get_cached_ingredients(restaurant_id=1)
        
        assert result is None

    async def test_fuzzy_search_menu_items_cached_success(self, menu_cache_service, mock_redis_service):
        """Test fuzzy search using cached menu items"""
        cached_items = [
            {"id": 1, "name": "Margherita Pizza", "description": "Classic pizza", "price": 12.99,
             "image_url": "pizza.jpg", "category_id": 1, "is_available": True, "ingredients": []},
            {"id": 2, "name": "Cheese Burger", "description": "Beef burger", "price": 9.99,
             "image_url": "burger.jpg", "category_id": 2, "is_available": True, "ingredients": []}
        ]
        
        # Mock the internal method that would be called
        menu_cache_service.get_cached_menu_items = AsyncMock(return_value=cached_items)
        
        result = await menu_cache_service.fuzzy_search_menu_items_cached(
            restaurant_id=1, query="pizza", limit=5
        )
        
        assert len(result) == 1
        assert result[0]["menu_item_name"] == "Margherita Pizza"
        assert result[0]["match_score"] >= 90.0  # High match score

    async def test_fuzzy_search_menu_items_cached_no_cache_fallback(self, menu_cache_service, mock_menu_service):
        """Test fuzzy search fallback to PostgreSQL when cache miss"""
        menu_cache_service.get_cached_menu_items = AsyncMock(return_value=None)
        mock_menu_service.fuzzy_search_menu_items.return_value = [
            {"menu_item_name": "Margherita Pizza", "match_score": 100.0}
        ]
        
        result = await menu_cache_service.fuzzy_search_menu_items_cached(
            restaurant_id=1, query="pizza", limit=5
        )
        
        assert len(result) == 1
        assert result[0]["menu_item_name"] == "Margherita Pizza"
        mock_menu_service.fuzzy_search_menu_items.assert_called_once_with(1, "pizza", 5)

    async def test_fuzzy_search_ingredients_cached_success(self, menu_cache_service, mock_redis_service):
        """Test fuzzy search using cached ingredients"""
        cached_ingredients = [
            {"id": 1, "name": "Mozzarella Cheese", "description": "Fresh mozzarella", 
             "is_allergen": True, "allergen_type": "dairy", "is_optional": False},
            {"id": 2, "name": "Fresh Tomatoes", "description": "Ripe tomatoes",
             "is_allergen": False, "allergen_type": None, "is_optional": False}
        ]
        
        # Mock the internal method that would be called
        menu_cache_service.get_cached_ingredients = AsyncMock(return_value=cached_ingredients)
        
        result = await menu_cache_service.fuzzy_search_ingredients_cached(
            restaurant_id=1, query="cheese", limit=5
        )
        
        assert len(result) == 1
        assert result[0]["ingredient_name"] == "Mozzarella Cheese"
        assert result[0]["match_score"] >= 90.0  # High match score

    async def test_fuzzy_search_ingredients_cached_no_cache_fallback(self, menu_cache_service, mock_menu_service):
        """Test fuzzy search fallback to PostgreSQL when cache miss"""
        menu_cache_service.get_cached_ingredients = AsyncMock(return_value=None)
        mock_menu_service.fuzzy_search_ingredients.return_value = [
            {"ingredient_name": "Mozzarella Cheese", "match_score": 100.0}
        ]
        
        result = await menu_cache_service.fuzzy_search_ingredients_cached(
            restaurant_id=1, query="cheese", limit=5
        )
        
        assert len(result) == 1
        assert result[0]["ingredient_name"] == "Mozzarella Cheese"
        mock_menu_service.fuzzy_search_ingredients.assert_called_once_with(1, "cheese", 5)

    async def test_invalidate_cache_success(self, menu_cache_service, mock_redis_service):
        """Test successful cache invalidation"""
        mock_redis_service.delete.return_value = True
        
        result = await menu_cache_service.invalidate_cache(restaurant_id=1)
        
        assert result is True
        mock_redis_service.delete.assert_called_once_with("menu_cache:1")

    async def test_invalidate_cache_redis_unavailable(self, menu_cache_service, mock_redis_service):
        """Test cache invalidation when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Redis unavailable")
        
        result = await menu_cache_service.invalidate_cache(restaurant_id=1)
        
        assert result is False

    async def test_fuzzy_search_menu_items_low_score_filtering(self, menu_cache_service):
        """Test that fuzzy search filters out low-score matches"""
        cached_items = [
            {"id": 1, "name": "Margherita Pizza", "description": "Classic pizza", "price": 12.99,
             "image_url": "pizza.jpg", "category_id": 1, "is_available": True, "ingredients": []},
            {"id": 2, "name": "Cheese Burger", "description": "Beef burger", "price": 9.99,
             "image_url": "burger.jpg", "category_id": 2, "is_available": True, "ingredients": []}
        ]
        
        menu_cache_service.get_cached_menu_items = AsyncMock(return_value=cached_items)
        
        # Search for something that should have low match score
        result = await menu_cache_service.fuzzy_search_menu_items_cached(
            restaurant_id=1, query="completely_different_food", limit=5
        )
        
        # Should return empty list due to low match scores
        assert len(result) == 0

    async def test_fuzzy_search_case_insensitive(self, menu_cache_service):
        """Test that fuzzy search is case insensitive"""
        cached_items = [
            {"id": 1, "name": "Margherita Pizza", "description": "Classic pizza", "price": 12.99,
             "image_url": "pizza.jpg", "category_id": 1, "is_available": True, "ingredients": []}
        ]
        
        menu_cache_service.get_cached_menu_items = AsyncMock(return_value=cached_items)
        
        # Search with different case
        result = await menu_cache_service.fuzzy_search_menu_items_cached(
            restaurant_id=1, query="PIZZA", limit=5
        )
        
        assert len(result) == 1
        assert result[0]["menu_item_name"] == "Margherita Pizza"

    async def test_redis_error_handling(self, menu_cache_service, mock_redis_service):
        """Test error handling when Redis operations fail"""
        mock_redis_service.get.side_effect = Exception("Redis error")
        
        # Test various operations that should handle Redis errors gracefully
        assert await menu_cache_service.is_redis_available() is False
        assert await menu_cache_service.preload_restaurant_menu(1) is False
        assert await menu_cache_service.get_cached_menu_items(1) is None
        assert await menu_cache_service.get_cached_ingredients(1) is None
        assert await menu_cache_service.invalidate_cache(1) is False
