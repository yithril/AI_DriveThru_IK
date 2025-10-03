"""
Test database fixtures and helpers for integration tests

Provides in-memory SQLite database with test data that can be reused across tests.
"""

import pytest
from tortoise import Tortoise
from tortoise.contrib.test import initializer, finalizer
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient


@pytest.fixture(scope="function")
async def test_db():
    """
    Initialize in-memory SQLite database for testing.
    Creates a fresh database for each test function.
    """
    # Initialize Tortoise with in-memory SQLite
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": [
            "app.models.restaurant",
            "app.models.category",
            "app.models.menu_item",
            "app.models.ingredient",
            "app.models.menu_item_ingredient",
            "app.models.user",
            "app.models.order",
            "app.models.order_item"
        ]}
    )
    
    # Generate schemas
    await Tortoise.generate_schemas()
    
    yield  # Test runs here
    
    # Cleanup
    await Tortoise.close_connections()


@pytest.fixture(scope="function")
async def test_restaurant(test_db):
    """Create a test restaurant with basic info"""
    restaurant = await Restaurant.create(
        name="Cosmic Burgers",
        description="Out of this world burgers and fries",
        address="123 Galaxy Way, Space City, SC 12345",
        phone="555-COSMIC",
        hours="Mon-Sun: 10 AM - 10 PM",
        primary_color="#FF6B35",
        secondary_color="#F7931E",
        is_active=True
    )
    return restaurant


@pytest.fixture(scope="function")
async def test_categories(test_restaurant):
    """Create test categories for the restaurant"""
    categories = []
    
    burger_cat = await Category.create(
        name="Burgers",
        description="Juicy space burgers",
        restaurant_id=test_restaurant.id,
        display_order=1
    )
    categories.append(burger_cat)
    
    sides_cat = await Category.create(
        name="Sides",
        description="Cosmic side dishes",
        restaurant_id=test_restaurant.id,
        display_order=2
    )
    categories.append(sides_cat)
    
    drinks_cat = await Category.create(
        name="Drinks",
        description="Refreshing beverages",
        restaurant_id=test_restaurant.id,
        display_order=3
    )
    categories.append(drinks_cat)
    
    return categories


@pytest.fixture(scope="function")
async def test_ingredients(test_restaurant):
    """Create test ingredients for the restaurant"""
    ingredients = []
    
    # Burger ingredients
    beef = await Ingredient.create(
        name="Beef Patty",
        description="100% Angus beef",
        restaurant_id=test_restaurant.id,
        is_allergen=False,
        is_optional=False
    )
    ingredients.append(beef)
    
    cheese = await Ingredient.create(
        name="Cheddar Cheese",
        description="Aged cheddar",
        restaurant_id=test_restaurant.id,
        is_allergen=True,
        allergen_type="dairy",
        is_optional=True
    )
    ingredients.append(cheese)
    
    lettuce = await Ingredient.create(
        name="Lettuce",
        description="Fresh iceberg lettuce",
        restaurant_id=test_restaurant.id,
        is_allergen=False,
        is_optional=True
    )
    ingredients.append(lettuce)
    
    tomato = await Ingredient.create(
        name="Tomato",
        description="Sliced tomato",
        restaurant_id=test_restaurant.id,
        is_allergen=False,
        is_optional=True
    )
    ingredients.append(tomato)
    
    pickles = await Ingredient.create(
        name="Pickles",
        description="Dill pickles",
        restaurant_id=test_restaurant.id,
        is_allergen=False,
        is_optional=True
    )
    ingredients.append(pickles)
    
    # Allergen for testing
    peanuts = await Ingredient.create(
        name="Peanuts",
        description="Roasted peanuts",
        restaurant_id=test_restaurant.id,
        is_allergen=True,
        allergen_type="nuts",
        is_optional=True
    )
    ingredients.append(peanuts)
    
    return ingredients


@pytest.fixture(scope="function")
async def test_menu_items(test_restaurant, test_categories, test_ingredients):
    """Create test menu items with ingredients"""
    menu_items = []
    burger_cat = test_categories[0]
    sides_cat = test_categories[1]
    drinks_cat = test_categories[2]
    
    # Cosmic Burger
    cosmic_burger = await MenuItem.create(
        name="Cosmic Burger",
        description="Our signature burger with special cosmic sauce",
        price=12.99,
        category_id=burger_cat.id,
        restaurant_id=test_restaurant.id,
        is_available=True,
        is_special=True,
        prep_time_minutes=10,
        display_order=1
    )
    menu_items.append(cosmic_burger)
    
    # Add ingredients to Cosmic Burger
    await MenuItemIngredient.create(
        menu_item_id=cosmic_burger.id,
        ingredient_id=test_ingredients[0].id,  # Beef
        quantity=1.0,
        unit="patty",
        is_optional=False
    )
    await MenuItemIngredient.create(
        menu_item_id=cosmic_burger.id,
        ingredient_id=test_ingredients[1].id,  # Cheese
        quantity=1.0,
        unit="slice",
        is_optional=True
    )
    await MenuItemIngredient.create(
        menu_item_id=cosmic_burger.id,
        ingredient_id=test_ingredients[2].id,  # Lettuce
        quantity=1.0,
        unit="leaf",
        is_optional=True
    )
    
    # Galaxy Fries
    fries = await MenuItem.create(
        name="Galaxy Fries",
        description="Crispy golden fries",
        price=4.99,
        category_id=sides_cat.id,
        restaurant_id=test_restaurant.id,
        is_available=True,
        prep_time_minutes=5,
        display_order=1
    )
    menu_items.append(fries)
    
    # Meteor Milkshake
    milkshake = await MenuItem.create(
        name="Meteor Milkshake",
        description="Chocolate milkshake",
        price=5.99,
        category_id=drinks_cat.id,
        restaurant_id=test_restaurant.id,
        is_available=True,
        prep_time_minutes=3,
        display_order=1
    )
    menu_items.append(milkshake)
    
    # Add peanut allergen to milkshake
    await MenuItemIngredient.create(
        menu_item_id=milkshake.id,
        ingredient_id=test_ingredients[5].id,  # Peanuts
        quantity=0.5,
        unit="oz",
        is_optional=False
    )
    
    return menu_items


@pytest.fixture(scope="function")
async def test_services(test_restaurant):
    """Create real service instances for testing"""
    from app.services.menu_service import MenuService
    from app.services.ingredient_service import IngredientService
    from app.services.restaurant_service import RestaurantService
    
    return {
        "menu_service": MenuService(),
        "ingredient_service": IngredientService(),
        "restaurant_service": RestaurantService(),
        "restaurant_id": test_restaurant.id
    }

