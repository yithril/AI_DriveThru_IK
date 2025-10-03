"""
Unit tests for Ingredient Service
"""

import pytest
from app.services.ingredient_service import IngredientService
from app.models.ingredient import Ingredient
from app.models.restaurant import Restaurant
from app.dto import IngredientCreateDto, IngredientUpdateDto


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
def ingredient_service(db):
    return IngredientService()


class TestIngredientService:
    """Test Ingredient Service CRUD operations"""
    
    async def test_create_ingredient(self, db, ingredient_service, sample_restaurant):
        """Test creating an ingredient"""
        data = IngredientCreateDto(
            name="Cheese",
            description="Fresh mozzarella cheese",
            is_allergen=True,
            allergen_type="dairy",
            is_optional=False,
            restaurant_id=sample_restaurant.id
        )
        
        ingredient = await ingredient_service.create(data)
        
        assert ingredient.id is not None
        assert ingredient.name == "Cheese"
        assert ingredient.description == "Fresh mozzarella cheese"
        assert ingredient.is_allergen is True
        assert ingredient.allergen_type == "dairy"
        assert ingredient.is_optional is False
        assert ingredient.restaurant_id == sample_restaurant.id
    
    async def test_create_ingredient_non_allergen(self, db, ingredient_service, sample_restaurant):
        """Test creating a non-allergen ingredient"""
        data = IngredientCreateDto(
            name="Lettuce",
            description="Fresh iceberg lettuce",
            is_allergen=False,
            is_optional=True,
            restaurant_id=sample_restaurant.id
        )
        
        ingredient = await ingredient_service.create(data)
        
        assert ingredient.id is not None
        assert ingredient.name == "Lettuce"
        assert ingredient.is_allergen is False
        assert ingredient.allergen_type is None
        assert ingredient.is_optional is True
    
    async def test_get_by_id(self, db, ingredient_service, sample_restaurant):
        """Test getting ingredient by ID"""
        # Create an ingredient first
        created_ingredient = await Ingredient.create(
            name="Tomato",
            description="Fresh tomatoes",
            restaurant=sample_restaurant
        )
        
        # Get by ID
        found_ingredient = await ingredient_service.get_by_id(created_ingredient.id)
        
        assert found_ingredient is not None
        assert found_ingredient.name == "Tomato"
        assert found_ingredient.description == "Fresh tomatoes"
        assert found_ingredient.restaurant_id == sample_restaurant.id
    
    async def test_get_by_id_not_found(self, db, ingredient_service):
        """Test getting non-existent ingredient"""
        result = await ingredient_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_restaurant(self, db, ingredient_service, sample_restaurant):
        """Test getting ingredients by restaurant"""
        # Create multiple ingredients for the restaurant
        await Ingredient.create(
            name="Bacon",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Avocado",
            restaurant=sample_restaurant
        )
        
        # Get ingredients for restaurant
        result = await ingredient_service.get_by_restaurant(sample_restaurant.id)
        
        assert result.total == 2
        assert len(result.ingredients) == 2
        # Should be ordered by name
        assert result.ingredients[0].name == "Avocado"
        assert result.ingredients[1].name == "Bacon"
    
    async def test_get_allergens(self, db, ingredient_service, sample_restaurant):
        """Test getting allergen ingredients"""
        # Create allergen and non-allergen ingredients
        await Ingredient.create(
            name="Peanuts",
            is_allergen=True,
            allergen_type="nuts",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Onions",
            is_allergen=False,
            restaurant=sample_restaurant
        )
        
        # Get allergen ingredients
        result = await ingredient_service.get_allergens(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "Peanuts"
        assert result.ingredients[0].is_allergen is True
        assert result.ingredients[0].allergen_type == "nuts"
    
    async def test_get_non_allergens(self, db, ingredient_service, sample_restaurant):
        """Test getting non-allergen ingredients"""
        # Create allergen and non-allergen ingredients
        await Ingredient.create(
            name="Gluten",
            is_allergen=True,
            allergen_type="gluten",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Bell Peppers",
            is_allergen=False,
            restaurant=sample_restaurant
        )
        
        # Get non-allergen ingredients
        result = await ingredient_service.get_non_allergens(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "Bell Peppers"
        assert result.ingredients[0].is_allergen is False
    
    async def test_get_optional_ingredients(self, db, ingredient_service, sample_restaurant):
        """Test getting optional ingredients"""
        # Create optional and required ingredients
        await Ingredient.create(
            name="Extra Cheese",
            is_optional=True,
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Bun",
            is_optional=False,
            restaurant=sample_restaurant
        )
        
        # Get optional ingredients
        result = await ingredient_service.get_optional_ingredients(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "Extra Cheese"
        assert result.ingredients[0].is_optional is True
    
    async def test_get_required_ingredients(self, db, ingredient_service, sample_restaurant):
        """Test getting required ingredients"""
        # Create optional and required ingredients
        await Ingredient.create(
            name="Pickles",
            is_optional=True,
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Meat Patty",
            is_optional=False,
            restaurant=sample_restaurant
        )
        
        # Get required ingredients
        result = await ingredient_service.get_required_ingredients(sample_restaurant.id)
        
        assert result.total == 1
        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "Meat Patty"
        assert result.ingredients[0].is_optional is False
    
    async def test_search_by_name(self, db, ingredient_service, sample_restaurant):
        """Test searching ingredients by name"""
        # Create ingredients with similar names
        await Ingredient.create(
            name="Cheddar Cheese",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Swiss Cheese",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Lettuce",
            restaurant=sample_restaurant
        )
        
        # Search for cheese
        result = await ingredient_service.search_by_name(sample_restaurant.id, "cheese")
        
        assert result.total == 2
        assert len(result.ingredients) == 2
        assert result.ingredients[0].name == "Cheddar Cheese"
        assert result.ingredients[1].name == "Swiss Cheese"
    
    async def test_get_by_allergen_type(self, db, ingredient_service, sample_restaurant):
        """Test getting ingredients by allergen type"""
        # Create ingredients with different allergen types
        await Ingredient.create(
            name="Milk",
            is_allergen=True,
            allergen_type="dairy",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Yogurt",
            is_allergen=True,
            allergen_type="dairy",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="Wheat",
            is_allergen=True,
            allergen_type="gluten",
            restaurant=sample_restaurant
        )
        
        # Get dairy allergens
        result = await ingredient_service.get_by_allergen_type(sample_restaurant.id, "dairy")
        
        assert result.total == 2
        assert len(result.ingredients) == 2
        assert result.ingredients[0].name == "Milk"
        assert result.ingredients[1].name == "Yogurt"
    
    async def test_get_all(self, db, ingredient_service, sample_restaurant):
        """Test getting all ingredients"""
        # Create multiple ingredients
        await Ingredient.create(
            name="All Ingredient 1",
            restaurant=sample_restaurant
        )
        await Ingredient.create(
            name="All Ingredient 2",
            restaurant=sample_restaurant
        )
        
        # Get all ingredients
        result = await ingredient_service.get_all()
        
        assert result.total == 2
        assert len(result.ingredients) == 2
    
    async def test_update_ingredient(self, db, ingredient_service, sample_restaurant):
        """Test updating an ingredient"""
        # Create an ingredient
        created_ingredient = await Ingredient.create(
            name="Original Name",
            description="Original description",
            is_allergen=False,
            restaurant=sample_restaurant
        )
        
        # Update it
        update_data = IngredientUpdateDto(
            name="Updated Name",
            description="Updated description",
            is_allergen=True,
            allergen_type="nuts"
        )
        
        updated = await ingredient_service.update(created_ingredient.id, update_data)
        
        assert updated is not None
        assert updated.id == created_ingredient.id
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.is_allergen is True
        assert updated.allergen_type == "nuts"
    
    async def test_update_ingredient_not_found(self, db, ingredient_service):
        """Test updating non-existent ingredient"""
        update_data = IngredientUpdateDto(name="New Name")
        result = await ingredient_service.update(999, update_data)
        assert result is None
    
    async def test_delete_ingredient(self, db, ingredient_service, sample_restaurant):
        """Test deleting an ingredient"""
        # Create an ingredient
        created_ingredient = await Ingredient.create(
            name="Delete Ingredient",
            restaurant=sample_restaurant
        )
        
        # Delete it
        result = await ingredient_service.delete(created_ingredient.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_ingredient = await ingredient_service.get_by_id(created_ingredient.id)
        assert deleted_ingredient is None
    
    async def test_delete_ingredient_not_found(self, db, ingredient_service):
        """Test deleting non-existent ingredient"""
        result = await ingredient_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
