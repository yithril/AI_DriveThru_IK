"""
Unit tests for Menu Resolution Service fuzzy search functionality
"""

import pytest
from decimal import Decimal
from app.services.menu_resolution_service import MenuResolutionService
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.workflow.response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.restaurant import Restaurant
from app.models.category import Category


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
    restaurant = await Restaurant.create(
        name="Test Restaurant",
        address="123 Test St",
        phone="555-0123",
        email="test@restaurant.com"
    )
    return restaurant


@pytest.fixture
async def sample_categories(db, sample_restaurant):
    """Create sample categories"""
    categories = []
    for name in ["Burgers", "Drinks"]:
        category = await Category.create(
            restaurant_id=sample_restaurant.id,
            name=name,
            display_order=1
        )
        categories.append(category)
    return categories


@pytest.fixture
async def sample_menu_items(db, sample_restaurant, sample_categories):
    """Create sample menu items including quantum items"""
    menu_items = []
    
    # Quantum items that should test the fuzzy search
    quantum_items = [
        ("Quantum Cheeseburger", "A delicious quantum-powered cheeseburger", 12.99, sample_categories[0].id),
        ("Quantum Cola", "Refreshing quantum cola drink", 3.99, sample_categories[1].id),
        ("Quantum Fries", "Crispy quantum potato fries", 4.99, sample_categories[0].id),
    ]
    
    for name, description, price, category_id in quantum_items:
        menu_item = await MenuItem.create(
            restaurant_id=sample_restaurant.id,
            category_id=category_id,
            name=name,
            description=description,
            price=Decimal(str(price)),
            is_available=True,
            display_order=1
        )
        menu_items.append(menu_item)
    
    return menu_items


@pytest.fixture
def menu_service():
    return MenuService()


@pytest.fixture
def ingredient_service():
    return IngredientService()


@pytest.fixture
def menu_resolution_service(menu_service, ingredient_service):
    return MenuResolutionService(menu_service, ingredient_service)


class TestMenuResolutionService:
    """Test Menu Resolution Service fuzzy search operations"""
    
    async def test_quantum_burger_fuzzy_search_should_prefer_cheeseburger(
        self, db, menu_resolution_service, sample_restaurant, sample_menu_items
    ):
        """
        Test that 'quantum burger' should match 'Quantum Cheeseburger' 
        with higher confidence than 'Quantum Cola'
        """
        # Create extraction response for "quantum burger"
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="quantum burger",
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9
                )
            ]
        )
        
        # Resolve the item
        resolution_response = await menu_resolution_service.resolve_items(
            extraction_response, 
            sample_restaurant.id
        )
        
        # Debug: Let's see what the fuzzy search actually returned
        print(f"\n=== DEBUG: Fuzzy search results for 'quantum burger' ===")
        menu_service = MenuService()
        fuzzy_results = await menu_service.fuzzy_search_menu_items(
            sample_restaurant.id, "quantum burger", limit=5
        )
        for i, result in enumerate(fuzzy_results):
            print(f"  {i+1}. {result['menu_item_name']} (score: {result['match_score']})")
        print("=" * 60)
        
        # Should not be ambiguous - should prefer cheeseburger over cola
        assert resolution_response.success is True
        assert len(resolution_response.resolved_items) == 1
        
        resolved_item = resolution_response.resolved_items[0]
        
        # Should resolve to Quantum Cheeseburger, not be ambiguous
        assert resolved_item.is_ambiguous is False
        assert resolved_item.resolved_menu_item_name == "Quantum Cheeseburger"
        assert resolved_item.resolved_menu_item_id > 0
        
        # The confidence should be reasonable (not perfect since it's fuzzy)
        assert resolved_item.menu_item_resolution_confidence > 0.7
    
    async def test_quantum_burger_with_multiple_matches_should_choose_best(
        self, db, menu_resolution_service, sample_restaurant, sample_menu_items
    ):
        """
        Test that when multiple quantum items exist, it chooses the best match
        and doesn't ask for clarification if there's a clear winner
        """
        # Create extraction response for "quantum burger" 
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="quantum burger",
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9
                )
            ]
        )
        
        # Resolve the item
        resolution_response = await menu_resolution_service.resolve_items(
            extraction_response, 
            sample_restaurant.id
        )
        
        # Should not need clarification
        assert resolution_response.needs_clarification is False
        assert len(resolution_response.clarification_questions) == 0
        
        # Should resolve to the cheeseburger (best match)
        resolved_item = resolution_response.resolved_items[0]
        assert resolved_item.is_ambiguous is False
        assert "cheeseburger" in resolved_item.resolved_menu_item_name.lower()
    
    async def test_exact_match_should_have_high_confidence(
        self, db, menu_resolution_service, sample_restaurant, sample_menu_items
    ):
        """Test that exact matches have high confidence"""
        # Create extraction response for exact match
        extraction_response = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="Quantum Cheeseburger",  # Exact match
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9
                )
            ]
        )
        
        # Resolve the item
        resolution_response = await menu_resolution_service.resolve_items(
            extraction_response, 
            sample_restaurant.id
        )
        
        assert resolution_response.success is True
        resolved_item = resolution_response.resolved_items[0]
        assert resolved_item.is_ambiguous is False
        assert resolved_item.menu_item_resolution_confidence > 0.9  # High confidence for exact match
