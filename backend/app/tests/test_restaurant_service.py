"""
Unit tests for Restaurant Service
"""

import pytest
from app.services.restaurant_service import RestaurantService
from app.models.restaurant import Restaurant
from app.dto import RestaurantCreateDto, RestaurantUpdateDto


@pytest.fixture
async def db():
    """Initialize test database"""
    from tortoise import Tortoise
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def restaurant_service():
    """Create restaurant service instance"""
    return RestaurantService()


class TestRestaurantService:
    """Test Restaurant Service CRUD operations"""
    
    async def test_create_restaurant(self, db, restaurant_service):
        """Test creating a restaurant"""
        data = RestaurantCreateDto(
            name="Test Restaurant",
            description="A test restaurant",
            address="123 Test St",
            phone="555-012-3456",
            primary_color="#FF6B35",
            secondary_color="#F7931E"
        )
        
        restaurant = await restaurant_service.create(data)
        
        assert restaurant.id is not None
        assert restaurant.name == "Test Restaurant"
        assert restaurant.address == "123 Test St"
        assert restaurant.phone == "555-012-3456"
        assert restaurant.primary_color == "#FF6B35"
        assert restaurant.secondary_color == "#F7931E"
    
    async def test_get_by_id(self, db, restaurant_service):
        """Test getting restaurant by ID"""
        # Create a restaurant first
        restaurant = await Restaurant.create(
            name="Test Restaurant",
            address="123 Test St",
            phone="555-012-3456"
        )
        
        # Retrieve it
        retrieved = await restaurant_service.get_by_id(restaurant.id)
        
        assert retrieved is not None
        assert retrieved.id == restaurant.id
        assert retrieved.name == "Test Restaurant"
        assert retrieved.address == "123 Test St"
        assert retrieved.phone == "555-012-3456"
    
    async def test_get_by_id_not_found(self, db, restaurant_service):
        """Test getting non-existent restaurant"""
        result = await restaurant_service.get_by_id(999)
        assert result is None
    
    async def test_get_all(self, db, restaurant_service):
        """Test getting all restaurants"""
        # Create multiple restaurants
        await Restaurant.create(name="Restaurant 1", address="123 St", phone="555-0001")
        await Restaurant.create(name="Restaurant 2", address="456 St", phone="555-0002")
        
        result = await restaurant_service.get_all()
        
        assert result.total == 2
        assert len(result.restaurants) == 2
        assert result.restaurants[0].name == "Restaurant 1"
        assert result.restaurants[1].name == "Restaurant 2"
    
    async def test_update_restaurant(self, db, restaurant_service):
        """Test updating a restaurant"""
        # Create a restaurant
        restaurant = await Restaurant.create(
            name="Original Name",
            address="123 Original St",
            phone="555-0001"
        )
        
        # Update it
        update_data = RestaurantUpdateDto(
            name="Updated Name",
            address="456 Updated St",
            phone="555-0002"
        )
        
        updated = await restaurant_service.update(restaurant.id, update_data)
        
        assert updated is not None
        assert updated.id == restaurant.id
        assert updated.name == "Updated Name"
        assert updated.address == "456 Updated St"
        assert updated.phone == "555-0002"
    
    async def test_update_restaurant_not_found(self, db, restaurant_service):
        """Test updating non-existent restaurant"""
        update_data = RestaurantUpdateDto(name="New Name")
        result = await restaurant_service.update(999, update_data)
        assert result is None
    
    async def test_delete_restaurant(self, db, restaurant_service):
        """Test deleting a restaurant"""
        # Create a restaurant
        restaurant = await Restaurant.create(
            name="To Delete",
            address="123 Delete St",
            phone="555-0001"
        )
        
        # Delete it
        result = await restaurant_service.delete(restaurant.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted = await restaurant_service.get_by_id(restaurant.id)
        assert deleted is None
    
    async def test_delete_restaurant_not_found(self, db, restaurant_service):
        """Test deleting non-existent restaurant"""
        result = await restaurant_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
