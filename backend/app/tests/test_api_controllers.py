"""
Integration tests for API controllers
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from dependency_injector import containers, providers

from app.main import app
from app.core.container import Container
from app.dto.ingredient_dto import IngredientResponseDto
from app.dto.category_dto import CategoryResponseDto
from app.dto.menu_item_dto import MenuItemResponseDto
from app.dto.restaurant_dto import RestaurantResponseDto


@pytest.fixture
def mock_ingredient_service():
    """Mock ingredient service for testing"""
    service = AsyncMock()
    from datetime import datetime
    now = datetime.now()
    
    service.create.return_value = IngredientResponseDto(
        id=1,
        name="Test Ingredient",
        description="Test description",
        is_allergen=False,
        allergen_type=None,
        is_optional=False,
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_id.return_value = IngredientResponseDto(
        id=1,
        name="Test Ingredient",
        description="Test description",
        is_allergen=False,
        allergen_type=None,
        is_optional=False,
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_restaurant.return_value = [
        IngredientResponseDto(
            id=1,
            name="Test Ingredient",
            description="Test description",
            is_allergen=False,
            allergen_type=None,
            is_optional=False,
            restaurant_id=1,
            created_at=now,
            updated_at=now
        )
    ]
    service.update.return_value = IngredientResponseDto(
        id=1,
        name="Updated Ingredient",
        description="Updated description",
        is_allergen=False,
        allergen_type=None,
        is_optional=False,
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.delete.return_value = True
    return service


@pytest.fixture
def mock_category_service():
    """Mock category service for testing"""
    service = AsyncMock()
    from datetime import datetime
    now = datetime.now()
    
    service.create.return_value = CategoryResponseDto(
        id=1,
        name="Test Category",
        description="Test description",
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_id.return_value = CategoryResponseDto(
        id=1,
        name="Test Category",
        description="Test description",
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_restaurant.return_value = [
        CategoryResponseDto(
            id=1,
            name="Test Category",
            description="Test description",
            restaurant_id=1,
            created_at=now,
            updated_at=now
        )
    ]
    service.update.return_value = CategoryResponseDto(
        id=1,
        name="Updated Category",
        description="Updated description",
        restaurant_id=1,
        created_at=now,
        updated_at=now
    )
    service.delete.return_value = True
    return service


@pytest.fixture
def mock_menu_item_service():
    """Mock menu item service for testing"""
    service = AsyncMock()
    from datetime import datetime
    now = datetime.now()
    
    service.create.return_value = MenuItemResponseDto(
        id=1,
        name="Test Menu Item",
        description="Test description",
        price=9.99,
        image_url="https://example.com/image.jpg",
        category_id=1,
        restaurant_id=1,
        is_available=True,
        is_upsell=False,
        is_special=False,
        prep_time_minutes=5,
        display_order=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_id.return_value = MenuItemResponseDto(
        id=1,
        name="Test Menu Item",
        description="Test description",
        price=9.99,
        image_url="https://example.com/image.jpg",
        category_id=1,
        restaurant_id=1,
        is_available=True,
        is_upsell=False,
        is_special=False,
        prep_time_minutes=5,
        display_order=1,
        created_at=now,
        updated_at=now
    )
    service.get_by_restaurant.return_value = [
        MenuItemResponseDto(
            id=1,
            name="Test Menu Item",
            description="Test description",
            price=9.99,
            image_url="https://example.com/image.jpg",
            category_id=1,
            restaurant_id=1,
            is_available=True,
            is_upsell=False,
            is_special=False,
            prep_time_minutes=5,
            display_order=1,
            created_at=now,
            updated_at=now
        )
    ]
    service.get_by_category.return_value = [
        MenuItemResponseDto(
            id=1,
            name="Test Menu Item",
            description="Test description",
            price=9.99,
            image_url="https://example.com/image.jpg",
            category_id=1,
            restaurant_id=1,
            is_available=True,
            is_upsell=False,
            is_special=False,
            prep_time_minutes=5,
            display_order=1,
            created_at=now,
            updated_at=now
        )
    ]
    service.update.return_value = MenuItemResponseDto(
        id=1,
        name="Updated Menu Item",
        description="Updated description",
        price=12.99,
        image_url="https://example.com/image.jpg",
        category_id=1,
        restaurant_id=1,
        is_available=True,
        is_upsell=False,
        is_special=False,
        prep_time_minutes=5,
        display_order=1,
        created_at=now,
        updated_at=now
    )
    service.delete.return_value = True
    return service


@pytest.fixture
def mock_restaurant_service():
    """Mock restaurant service for testing"""
    service = AsyncMock()
    from datetime import datetime
    now = datetime.now()
    
    service.create.return_value = RestaurantResponseDto(
        id=1,
        name="Test Restaurant",
        address="123 Test St",
        phone="555-123-4567",
        primary_color="#FF6B35",
        secondary_color="#F7931E",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    service.get_by_id.return_value = RestaurantResponseDto(
        id=1,
        name="Test Restaurant",
        address="123 Test St",
        phone="555-123-4567",
        primary_color="#FF6B35",
        secondary_color="#F7931E",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    service.get_all.return_value = [
        RestaurantResponseDto(
            id=1,
            name="Test Restaurant",
            address="123 Test St",
            phone="555-123-4567",
            primary_color="#FF6B35",
            secondary_color="#F7931E",
            is_active=True,
            created_at=now,
            updated_at=now
        )
    ]
    service.update.return_value = RestaurantResponseDto(
        id=1,
        name="Updated Restaurant",
        address="456 Updated Ave",
        phone="555-987-6543",
        primary_color="#FF6B35",
        secondary_color="#F7931E",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    service.delete.return_value = True
    return service


@pytest.fixture
def test_container(mock_restaurant_service, mock_ingredient_service, mock_category_service, mock_menu_item_service):
    """Test container with mocked services"""
    container = Container()
    container.restaurant_service.override(providers.Object(mock_restaurant_service))
    container.ingredient_service.override(providers.Object(mock_ingredient_service))
    container.category_service.override(providers.Object(mock_category_service))
    container.menu_item_service.override(providers.Object(mock_menu_item_service))
    return container


@pytest.fixture
def client(test_container):
    """Test client with mocked dependencies"""
    # Override the container in the app
    app.container = test_container
    
    # Wire the container
    test_container.wire(modules=[
        "app.api.restaurants_controller",
        "app.api.ingredients_controller",
        "app.api.categories_controller", 
        "app.api.menu_items_controller"
    ])
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Unwire after test
    test_container.unwire()


class TestRestaurantsController:
    """Test restaurants API controller"""

    def test_create_restaurant(self, client):
        """Test creating a restaurant"""
        data = {
            "name": "Test Restaurant",
            "address": "123 Test St",
            "phone": "555-123-4567"
        }
        
        response = client.post("/api/restaurants/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test Restaurant"
        assert result["address"] == "123 Test St"

    def test_get_restaurant(self, client):
        """Test getting a restaurant by ID"""
        response = client.get("/api/restaurants/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 1
        assert result["name"] == "Test Restaurant"

    def test_get_restaurants(self, client):
        """Test getting all restaurants"""
        response = client.get("/api/restaurants/")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_count"] == 1
        assert len(result["restaurants"]) == 1
        assert result["restaurants"][0]["name"] == "Test Restaurant"

    def test_update_restaurant(self, client):
        """Test updating a restaurant"""
        data = {
            "name": "Updated Restaurant",
            "address": "456 Updated Ave"
        }
        
        response = client.put("/api/restaurants/1", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Restaurant"
        assert result["address"] == "456 Updated Ave"

    def test_delete_restaurant(self, client):
        """Test deleting a restaurant"""
        response = client.delete("/api/restaurants/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["restaurant_id"] == 1


class TestIngredientsController:
    """Test ingredients API controller"""

    def test_create_ingredient(self, client):
        """Test creating an ingredient"""
        data = {
            "name": "Test Ingredient",
            "description": "Test description",
            "restaurant_id": 1
        }
        
        response = client.post("/api/ingredients/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test Ingredient"
        assert result["restaurant_id"] == 1

    def test_get_ingredient(self, client):
        """Test getting an ingredient by ID"""
        response = client.get("/api/ingredients/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 1
        assert result["name"] == "Test Ingredient"

    def test_get_ingredients_by_restaurant(self, client):
        """Test getting ingredients by restaurant"""
        response = client.get("/api/ingredients/?restaurant_id=1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_count"] == 1
        assert len(result["ingredients"]) == 1
        assert result["restaurant_id"] == 1

    def test_update_ingredient(self, client):
        """Test updating an ingredient"""
        data = {
            "name": "Updated Ingredient",
            "description": "Updated description"
        }
        
        response = client.put("/api/ingredients/1", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Ingredient"

    def test_delete_ingredient(self, client):
        """Test deleting an ingredient"""
        response = client.delete("/api/ingredients/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["ingredient_id"] == 1


class TestCategoriesController:
    """Test categories API controller"""

    def test_create_category(self, client):
        """Test creating a category"""
        data = {
            "name": "Test Category",
            "description": "Test description",
            "restaurant_id": 1
        }
        
        response = client.post("/api/categories/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test Category"
        assert result["restaurant_id"] == 1

    def test_get_category(self, client):
        """Test getting a category by ID"""
        response = client.get("/api/categories/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 1
        assert result["name"] == "Test Category"

    def test_get_categories_by_restaurant(self, client):
        """Test getting categories by restaurant"""
        response = client.get("/api/categories/?restaurant_id=1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_count"] == 1
        assert len(result["categories"]) == 1
        assert result["restaurant_id"] == 1

    def test_update_category(self, client):
        """Test updating a category"""
        data = {
            "name": "Updated Category",
            "description": "Updated description"
        }
        
        response = client.put("/api/categories/1", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Category"

    def test_delete_category(self, client):
        """Test deleting a category"""
        response = client.delete("/api/categories/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["category_id"] == 1


class TestMenuItemsController:
    """Test menu items API controller"""

    def test_create_menu_item(self, client):
        """Test creating a menu item"""
        data = {
            "name": "Test Menu Item",
            "description": "Test description",
            "price": 9.99,
            "image_url": "https://example.com/image.jpg",
            "category_id": 1,
            "restaurant_id": 1,
            "is_available": True,
            "is_upsell": False,
            "is_special": False,
            "prep_time_minutes": 5,
            "display_order": 1
        }
        
        response = client.post("/api/menu-items/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test Menu Item"
        assert result["price"] == "9.99"
        assert result["restaurant_id"] == 1

    def test_get_menu_item(self, client):
        """Test getting a menu item by ID"""
        response = client.get("/api/menu-items/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 1
        assert result["name"] == "Test Menu Item"

    def test_get_menu_items_by_restaurant(self, client):
        """Test getting menu items by restaurant"""
        response = client.get("/api/menu-items/?restaurant_id=1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_count"] == 1
        assert len(result["menu_items"]) == 1
        assert result["restaurant_id"] == 1

    def test_get_menu_items_by_category(self, client):
        """Test getting menu items by category"""
        response = client.get("/api/menu-items/?restaurant_id=1&category_id=1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["total_count"] == 1
        assert result["category_id"] == 1

    def test_update_menu_item(self, client):
        """Test updating a menu item"""
        data = {
            "name": "Updated Menu Item",
            "price": 12.99
        }
        
        response = client.put("/api/menu-items/1", json=data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Menu Item"
        assert result["price"] == "12.99"

    def test_delete_menu_item(self, client):
        """Test deleting a menu item"""
        response = client.delete("/api/menu-items/1")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["menu_item_id"] == 1
