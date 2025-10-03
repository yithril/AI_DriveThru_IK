"""
Unit tests for Menu Service fuzzy search functionality
"""

import pytest
from decimal import Decimal
from app.services.menu_service import MenuService
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item_ingredient import MenuItemIngredient


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
async def sample_menu_items(db, sample_restaurant, sample_category):
    """Create sample menu items for testing"""
    pizza = await MenuItem.create(
        name="Margherita Pizza",
        description="Classic pizza with tomato and mozzarella",
        price=Decimal("14.99"),
        category=sample_category,
        restaurant=sample_restaurant,
        is_available=True
    )
    
    burger = await MenuItem.create(
        name="Cheeseburger",
        description="Beef burger with cheese and lettuce",
        price=Decimal("12.99"),
        category=sample_category,
        restaurant=sample_restaurant,
        is_available=True
    )
    
    pasta = await MenuItem.create(
        name="Spaghetti Carbonara",
        description="Creamy pasta with bacon and parmesan",
        price=Decimal("16.99"),
        category=sample_category,
        restaurant=sample_restaurant,
        is_available=True
    )
    
    return [pizza, burger, pasta]


@pytest.fixture
async def sample_ingredients(db, sample_restaurant):
    """Create sample ingredients for testing"""
    cheese = await Ingredient.create(
        name="Mozzarella Cheese",
        description="Fresh mozzarella",
        is_allergen=True,
        allergen_type="dairy",
        restaurant=sample_restaurant
    )
    
    tomato = await Ingredient.create(
        name="Fresh Tomatoes",
        description="Ripe tomatoes",
        is_allergen=False,
        restaurant=sample_restaurant
    )
    
    beef = await Ingredient.create(
        name="Ground Beef Patty",
        description="100% beef patty",
        is_allergen=False,
        restaurant=sample_restaurant
    )
    
    return [cheese, tomato, beef]


@pytest.fixture
async def sample_menu_item_ingredients(db, sample_menu_items, sample_ingredients):
    """Create menu item ingredient relationships"""
    pizza, burger, pasta = sample_menu_items
    cheese, tomato, beef = sample_ingredients
    
    # Pizza ingredients
    await MenuItemIngredient.create(
        menu_item=pizza,
        ingredient=cheese,
        quantity=1.0,
        unit="slice"
    )
    await MenuItemIngredient.create(
        menu_item=pizza,
        ingredient=tomato,
        quantity=2.0,
        unit="pieces"
    )
    
    # Burger ingredients
    await MenuItemIngredient.create(
        menu_item=burger,
        ingredient=beef,
        quantity=1.0,
        unit="patty"
    )
    await MenuItemIngredient.create(
        menu_item=burger,
        ingredient=cheese,
        quantity=1.0,
        unit="slice"
    )
    
    return [(pizza, [cheese, tomato]), (burger, [beef, cheese])]


@pytest.fixture
def menu_service(db):
    return MenuService()


class TestMenuService:
    """Test Menu Service fuzzy search operations"""
    
    async def test_fuzzy_search_menu_items_exact_match(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test fuzzy search with exact match"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "Margherita Pizza", limit=5
        )
        
        assert len(results) == 1
        assert results[0]["menu_item_name"] == "Margherita Pizza"
        assert results[0]["match_score"] == 100  # Exact match
        assert results[0]["price"] == 14.99
    
    async def test_fuzzy_search_menu_items_partial_match(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test fuzzy search with partial match"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "pizza", limit=5
        )
        
        assert len(results) >= 1
        # Should find the pizza item
        pizza_found = any(result["menu_item_name"] == "Margherita Pizza" for result in results)
        assert pizza_found is True
    
    async def test_fuzzy_search_menu_items_with_ingredients(
        self, db, menu_service, sample_restaurant, sample_menu_items, sample_menu_item_ingredients
    ):
        """Test fuzzy search with ingredients loaded"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "Margherita Pizza", limit=5, include_ingredients=True
        )
        
        assert len(results) == 1
        result = results[0]
        assert result["menu_item_name"] == "Margherita Pizza"
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2  # Should have 2 ingredients
    
    async def test_fuzzy_search_menu_items_without_ingredients(
        self, db, menu_service, sample_restaurant, sample_menu_items, sample_menu_item_ingredients
    ):
        """Test fuzzy search without ingredients loaded"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "Margherita Pizza", limit=5, include_ingredients=False
        )
        
        assert len(results) == 1
        result = results[0]
        assert result["menu_item_name"] == "Margherita Pizza"
        assert "ingredients" not in result
    
    async def test_fuzzy_search_menu_items_no_match(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test fuzzy search with no matches"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "nonexistent item", limit=5
        )
        
        assert len(results) == 0
    
    async def test_fuzzy_search_ingredients_exact_match(
        self, db, menu_service, sample_restaurant, sample_ingredients
    ):
        """Test ingredient fuzzy search with exact match"""
        results = await menu_service.fuzzy_search_ingredients(
            sample_restaurant.id, "Mozzarella Cheese", limit=5
        )
        
        assert len(results) == 1
        assert results[0]["ingredient_name"] == "Mozzarella Cheese"
        assert results[0]["match_score"] == 100  # Exact match
        assert results[0]["is_allergen"] is True
        assert results[0]["allergen_type"] == "dairy"
    
    async def test_fuzzy_search_ingredients_partial_match(
        self, db, menu_service, sample_restaurant, sample_ingredients
    ):
        """Test ingredient fuzzy search with partial match"""
        results = await menu_service.fuzzy_search_ingredients(
            sample_restaurant.id, "cheese", limit=5
        )
        
        assert len(results) >= 1
        # Should find the cheese ingredient
        cheese_found = any(result["ingredient_name"] == "Mozzarella Cheese" for result in results)
        assert cheese_found is True
    
    async def test_fuzzy_search_ingredients_no_match(
        self, db, menu_service, sample_restaurant, sample_ingredients
    ):
        """Test ingredient fuzzy search with no matches"""
        results = await menu_service.fuzzy_search_ingredients(
            sample_restaurant.id, "nonexistent ingredient", limit=5
        )
        
        assert len(results) == 0
    
    async def test_get_menu_item_with_ingredients(
        self, db, menu_service, sample_restaurant, sample_menu_items, sample_menu_item_ingredients
    ):
        """Test getting menu item with ingredients loaded"""
        pizza = sample_menu_items[0]  # Margherita Pizza
        
        result = await menu_service.get_menu_item_with_ingredients(
            sample_restaurant.id, pizza.id
        )
        
        assert result is not None
        assert result["menu_item_name"] == "Margherita Pizza"
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
    
    async def test_get_menu_item_with_ingredients_not_found(
        self, db, menu_service, sample_restaurant
    ):
        """Test getting non-existent menu item"""
        result = await menu_service.get_menu_item_with_ingredients(
            sample_restaurant.id, 999
        )
        
        assert result is None
    
    async def test_search_menu_items_by_ingredient(
        self, db, menu_service, sample_restaurant, sample_menu_items, sample_ingredients, sample_menu_item_ingredients
    ):
        """Test finding menu items by ingredient"""
        results = await menu_service.search_menu_items_by_ingredient(
            sample_restaurant.id, "cheese", limit=10
        )
        
        assert len(results) >= 1
        # Should find both pizza and burger (both have cheese)
        menu_names = [result["menu_item_name"] for result in results]
        assert "Margherita Pizza" in menu_names
        assert "Cheeseburger" in menu_names
    
    async def test_search_menu_items_by_ingredient_no_match(
        self, db, menu_service, sample_restaurant, sample_menu_items, sample_ingredients, sample_menu_item_ingredients
    ):
        """Test finding menu items by non-existent ingredient"""
        results = await menu_service.search_menu_items_by_ingredient(
            sample_restaurant.id, "nonexistent ingredient", limit=10
        )
        
        assert len(results) == 0
    
    async def test_fuzzy_search_case_insensitive(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test that fuzzy search is case insensitive"""
        results_upper = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "PIZZA", limit=5
        )
        results_lower = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "pizza", limit=5
        )
        
        assert len(results_upper) == len(results_lower)
        assert results_upper[0]["menu_item_name"] == results_lower[0]["menu_item_name"]
    
    async def test_fuzzy_search_typo_tolerance(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test that fuzzy search handles typos reasonably"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "piza", limit=5  # Missing 'z'
        )
        
        assert len(results) >= 1
        # Should still find the pizza despite the typo
        pizza_found = any(result["menu_item_name"] == "Margherita Pizza" for result in results)
        assert pizza_found is True
    
    async def test_limit_parameter(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test that limit parameter works correctly"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "test", limit=2
        )
        
        assert len(results) <= 2
    
    async def test_empty_search_term(
        self, db, menu_service, sample_restaurant, sample_menu_items
    ):
        """Test fuzzy search with empty search term"""
        results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "", limit=5
        )
        
        # Empty search should return no results or very low scores
        if results:
            # If results are returned, scores should be very low
            for result in results:
                assert result["match_score"] < 50
