"""
Unit tests for Category Service
"""

import pytest
from app.services.category_service import CategoryService
from app.models.category import Category
from app.models.restaurant import Restaurant
from app.dto import CategoryCreateDto, CategoryUpdateDto


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
def category_service(db):
    return CategoryService()


class TestCategoryService:
    """Test Category Service CRUD operations"""
    
    async def test_create_category(self, db, category_service, sample_restaurant):
        """Test creating a category"""
        data = CategoryCreateDto(
            name="Test Category",
            description="A test category",
            restaurant_id=sample_restaurant.id
        )
        
        category = await category_service.create(data)
        
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.description == "A test category"
        assert category.restaurant_id == sample_restaurant.id
    
    async def test_get_by_id(self, db, category_service, sample_restaurant):
        """Test getting category by ID"""
        # Create a category first
        created_category = await Category.create(
            name="Get Category",
            restaurant=sample_restaurant
        )
        
        # Get by ID
        found_category = await category_service.get_by_id(created_category.id)
        
        assert found_category is not None
        assert found_category.name == "Get Category"
        assert found_category.restaurant_id == sample_restaurant.id
    
    async def test_get_by_id_not_found(self, db, category_service):
        """Test getting non-existent category"""
        result = await category_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_restaurant(self, db, category_service, sample_restaurant):
        """Test getting categories by restaurant"""
        # Create multiple categories for the restaurant
        await Category.create(name="Category 1", restaurant=sample_restaurant)
        await Category.create(name="Category 2", restaurant=sample_restaurant)
        
        # Get categories for restaurant
        result = await category_service.get_by_restaurant(sample_restaurant.id)
        
        assert result.total == 2
        assert len(result.categories) == 2
        assert result.categories[0].name == "Category 1"
        assert result.categories[1].name == "Category 2"
    
    async def test_get_all(self, db, category_service, sample_restaurant):
        """Test getting all categories"""
        # Create multiple categories
        await Category.create(name="All Category 1", restaurant=sample_restaurant)
        await Category.create(name="All Category 2", restaurant=sample_restaurant)
        
        # Get all categories
        result = await category_service.get_all()
        
        assert result.total == 2
        assert len(result.categories) == 2
    
    async def test_update_category(self, db, category_service, sample_restaurant):
        """Test updating a category"""
        # Create a category
        created_category = await Category.create(
            name="Original Name",
            restaurant=sample_restaurant
        )
        
        # Update it
        update_data = CategoryUpdateDto(
            name="Updated Name",
            description="Updated description"
        )
        
        updated = await category_service.update(created_category.id, update_data)
        
        assert updated is not None
        assert updated.id == created_category.id
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
    
    async def test_update_category_not_found(self, db, category_service):
        """Test updating non-existent category"""
        update_data = CategoryUpdateDto(name="New Name")
        result = await category_service.update(999, update_data)
        assert result is None
    
    async def test_delete_category(self, db, category_service, sample_restaurant):
        """Test deleting a category"""
        # Create a category
        created_category = await Category.create(
            name="Delete Category",
            restaurant=sample_restaurant
        )
        
        # Delete it
        result = await category_service.delete(created_category.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_category = await category_service.get_by_id(created_category.id)
        assert deleted_category is None
    
    async def test_delete_category_not_found(self, db, category_service):
        """Test deleting non-existent category"""
        result = await category_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
