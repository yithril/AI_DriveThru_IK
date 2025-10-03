"""
Unit tests for Menu Item Service
"""

import pytest
from decimal import Decimal
from app.services.menu_item_service import MenuItemService
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.dto import MenuItemCreateDto, MenuItemUpdateDto


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
async def sample_restaurant(db):
    """Create a sample restaurant for testing"""
    return await Restaurant.create(
        name="Test Restaurant",
        description="A test restaurant",
        address="123 Test St",
        phone="555-012-3456"
    )


@pytest.fixture
async def sample_category(db, sample_restaurant):
    """Create a sample category for testing"""
    return await Category.create(
        name="Test Category",
        description="A test category",
        restaurant=sample_restaurant
    )


@pytest.fixture
def menu_item_service(db):
    return MenuItemService()


class TestMenuItemService:
    """Test Menu Item Service CRUD operations"""
    
    async def test_create_menu_item(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test creating a menu item"""
        data = MenuItemCreateDto(
            name="Test Pizza",
            description="A delicious test pizza",
            price=Decimal("12.99"),
            image_url="https://example.com/pizza.jpg",
            category_id=sample_category.id,
            restaurant_id=sample_restaurant.id,
            is_available=True,
            is_special=False,
            is_upsell=True,
            prep_time_minutes=15,
            display_order=1
        )
        
        menu_item = await menu_item_service.create(data)
        
        assert menu_item.id is not None
        assert menu_item.name == "Test Pizza"
        assert menu_item.description == "A delicious test pizza"
        assert menu_item.price == Decimal("12.99")
        assert menu_item.image_url == "https://example.com/pizza.jpg"
        assert menu_item.category_id == sample_category.id
        assert menu_item.restaurant_id == sample_restaurant.id
        assert menu_item.is_available is True
        assert menu_item.is_special is False
        assert menu_item.is_upsell is True
        assert menu_item.prep_time_minutes == 15
        assert menu_item.display_order == 1
    
    async def test_get_by_id(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting menu item by ID"""
        # Create a menu item first
        created_item = await MenuItem.create(
            name="Get Test Item",
            price=Decimal("9.99"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        
        # Get by ID
        found_item = await menu_item_service.get_by_id(created_item.id)
        
        assert found_item is not None
        assert found_item.name == "Get Test Item"
        assert found_item.price == Decimal("9.99")
        assert found_item.category_id == sample_category.id
        assert found_item.restaurant_id == sample_restaurant.id
    
    async def test_get_by_id_not_found(self, db, menu_item_service):
        """Test getting non-existent menu item"""
        result = await menu_item_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_restaurant(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting menu items by restaurant"""
        # Create multiple menu items for the restaurant
        await MenuItem.create(
            name="Item 1",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            display_order=1
        )
        await MenuItem.create(
            name="Item 2",
            price=Decimal("15.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            display_order=2
        )
        
        # Get items for restaurant
        result = await menu_item_service.get_by_restaurant(sample_restaurant.id)
        
        assert result.total == 2
        assert len(result.menu_items) == 2
        assert result.menu_items[0].name == "Item 1"
        assert result.menu_items[1].name == "Item 2"
    
    async def test_get_by_category(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting menu items by category"""
        # Create multiple menu items in the category
        await MenuItem.create(
            name="Category Item 1",
            price=Decimal("8.99"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        await MenuItem.create(
            name="Category Item 2",
            price=Decimal("11.99"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        
        # Get items for category
        result = await menu_item_service.get_by_category(sample_category.id)
        
        assert result.total == 2
        assert len(result.menu_items) == 2
        assert result.menu_items[0].name == "Category Item 1"
        assert result.menu_items[1].name == "Category Item 2"
    
    async def test_get_available_by_restaurant(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting available menu items by restaurant"""
        # Create available and unavailable items
        await MenuItem.create(
            name="Available Item",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_available=True
        )
        await MenuItem.create(
            name="Unavailable Item",
            price=Decimal("12.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_available=False
        )
        
        # Get available items for restaurant
        result = await menu_item_service.get_available_by_restaurant(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.menu_items) == 1
        assert result.menu_items[0].name == "Available Item"
    
    async def test_get_special_items(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting special items"""
        # Create special and regular items
        await MenuItem.create(
            name="Special Item",
            price=Decimal("20.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_special=True,
            is_available=True
        )
        await MenuItem.create(
            name="Regular Item",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_special=False,
            is_available=True
        )
        
        # Get special items
        result = await menu_item_service.get_special_items(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.menu_items) == 1
        assert result.menu_items[0].name == "Special Item"
        assert result.menu_items[0].is_special is True
    
    async def test_get_upsell_items(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting upsell items"""
        # Create upsell and regular items
        await MenuItem.create(
            name="Upsell Item",
            price=Decimal("25.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_upsell=True,
            is_available=True
        )
        await MenuItem.create(
            name="Regular Item",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant,
            is_upsell=False,
            is_available=True
        )
        
        # Get upsell items
        result = await menu_item_service.get_upsell_items(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.menu_items) == 1
        assert result.menu_items[0].name == "Upsell Item"
        assert result.menu_items[0].is_upsell is True
    
    async def test_get_all(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test getting all menu items"""
        # Create multiple menu items
        await MenuItem.create(
            name="All Item 1",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        await MenuItem.create(
            name="All Item 2",
            price=Decimal("15.00"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        
        # Get all items
        result = await menu_item_service.get_all()
        
        assert result.total == 2
        assert len(result.menu_items) == 2
    
    async def test_update_menu_item(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test updating a menu item"""
        # Create a menu item
        created_item = await MenuItem.create(
            name="Original Name",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        
        # Update it
        update_data = MenuItemUpdateDto(
            name="Updated Name",
            price=Decimal("12.50"),
            description="Updated description",
            is_special=True
        )
        
        updated = await menu_item_service.update(created_item.id, update_data)
        
        assert updated is not None
        assert updated.id == created_item.id
        assert updated.name == "Updated Name"
        assert updated.price == Decimal("12.50")
        assert updated.description == "Updated description"
        assert updated.is_special is True
    
    async def test_update_menu_item_not_found(self, db, menu_item_service):
        """Test updating non-existent menu item"""
        update_data = MenuItemUpdateDto(name="New Name")
        result = await menu_item_service.update(999, update_data)
        assert result is None
    
    async def test_delete_menu_item(self, db, menu_item_service, sample_restaurant, sample_category):
        """Test deleting a menu item"""
        # Create a menu item
        created_item = await MenuItem.create(
            name="Delete Item",
            price=Decimal("10.00"),
            category=sample_category,
            restaurant=sample_restaurant
        )
        
        # Delete it
        result = await menu_item_service.delete(created_item.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_item = await menu_item_service.get_by_id(created_item.id)
        assert deleted_item is None
    
    async def test_delete_menu_item_not_found(self, db, menu_item_service):
        """Test deleting non-existent menu item"""
        result = await menu_item_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
