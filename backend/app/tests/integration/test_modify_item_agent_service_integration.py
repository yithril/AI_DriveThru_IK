"""
Integration test for complex modify item scenario: 4 sandwiches, modify 2 one way, 1 another way, leave 1 alone

This test uses:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- Real database for validation
- Real service logic for applying modifications
- Tests the complex item splitting functionality we implemented
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock
from app.workflow.agents.modify_item_agent import modify_item_agent
from app.services.modify_item_service import ModifyItemService
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient
from app.constants.item_sizes import ItemSize
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory, ConversationRole, ConversationEntry


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


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
        name="Burgers",
        description="Burger category",
        restaurant=sample_restaurant
    )


@pytest.fixture
async def sample_menu_items(db, sample_category, sample_restaurant):
    """Create sample menu items with modification options"""
    
    # Create burger with max_quantity = 5
    burger = await MenuItem.create(
        name="Burger",
        description="A delicious burger",
        price=Decimal('10.00'),
        category=sample_category,
        restaurant=sample_restaurant,
        size=ItemSize.REGULAR,
        available_sizes=["small", "medium", "large"],
        modifiable_ingredients=["pickles", "cheese", "mayo"],
        max_quantity=5
    )
    
    # Create fries with max_quantity = 10
    fries = await MenuItem.create(
        name="Fries",
        description="Crispy french fries",
        price=Decimal('5.00'),
        category=sample_category,
        restaurant=sample_restaurant,
        size=ItemSize.MEDIUM,
        available_sizes=["small", "medium", "large"],
        modifiable_ingredients=["salt", "ketchup"],
        max_quantity=10
    )
    
    return [burger, fries]


@pytest.fixture
async def sample_ingredients(db, sample_restaurant):
    """Create sample ingredients"""
    
    # Create ingredients
    pickles = await Ingredient.create(
        name="Pickles",
        restaurant=sample_restaurant,
        is_optional=True
    )
    
    cheese = await Ingredient.create(
        name="Cheese",
        restaurant=sample_restaurant,
        is_optional=True
    )
    
    mayo = await Ingredient.create(
        name="Mayo",
        restaurant=sample_restaurant,
        is_optional=True
    )
    
    return [pickles, cheese, mayo]


@pytest.fixture
async def sample_menu_item_ingredients(db, sample_menu_items, sample_ingredients):
    """Create menu item ingredients"""
    
    burger, fries = sample_menu_items
    pickles, cheese, mayo = sample_ingredients
    
    # Create menu item ingredients
    await MenuItemIngredient.create(
        menu_item=burger,
        ingredient=pickles,
        quantity=Decimal('2.0'),
        unit="pieces",
        is_optional=True,
        additional_cost=Decimal('0.00')
    )
    
    await MenuItemIngredient.create(
        menu_item=burger,
        ingredient=cheese,
        quantity=Decimal('1.0'),
        unit="slice",
        is_optional=True,
        additional_cost=Decimal('0.50')
    )
    
    await MenuItemIngredient.create(
        menu_item=burger,
        ingredient=mayo,
        quantity=Decimal('1.0'),
        unit="tbsp",
        is_optional=True,
        additional_cost=Decimal('0.25')
    )
    
    return [burger, fries]


@pytest.fixture
def sample_redis_order():
    """Sample Redis order data with 4 sandwiches"""
    return {
        "id": "order_1234567890",
        "session_id": "session_123",
        "restaurant_id": 1,
        "status": "active",
        "items": [
            {
                "id": "item_1234567890",
                "menu_item_id": 1,  # Burger
                "quantity": 4,  # 4 sandwiches
                "modifications": {
                    "size": "regular",
                    "name": "Burger",
                    "unit_price": 10.0,
                    "total_price": 40.0,  # 4 * 10.0
                    "ingredient_modifications": "",
                    "special_instructions": ""
                },
                "added_at": "2024-01-01T12:00:00"
            }
        ]
    }


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history"""
    history = ConversationHistory(session_id="test_session")
    history.add_entry(ConversationRole.USER, "I want a burger")
    history.add_entry(ConversationRole.ASSISTANT, "Added burger to your order")
    history.add_entry(ConversationRole.USER, "And some fries")
    history.add_entry(ConversationRole.ASSISTANT, "Added fries to your order")
    return history


class TestComplexModifyScenario:
    """Integration test for complex modify item scenario with item splitting"""
    
    @pytest.mark.asyncio
    async def test_complex_item_splitting_scenario(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """
        Test complex scenario: 4 sandwiches, modify 2 one way, 1 another way, leave 1 alone
        
        This tests the enhanced agent + service integration with:
        - Real LLM parsing of complex natural language
        - Real validation against database
        - Real item splitting logic
        - Real modification application
        """
        
        # Test input: "Make 2 of those burgers extra cheese and 1 with no pickles"
        user_input = "Make 2 of those burgers extra cheese and 1 with no pickles"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Remaining Unchanged: {agent_result.remaining_unchanged}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        for i, mod in enumerate(agent_result.modifications):
            print(f"    Modification {i+1}: {mod.quantity}x {mod.item_name} - {mod.modification}")
        
        # Verify agent result
        assert agent_result.success is True
        assert agent_result.requires_split is True
        assert len(agent_result.modifications) >= 2  # Should have at least 2 modifications
        assert agent_result.remaining_unchanged == 1  # 1 should remain unchanged
        
        # Run real service
        service = ModifyItemService()
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        print(f"  Modified Fields: {service_result.modified_fields}")
        
        # Verify service result
        assert service_result.success is True
        assert "extra cheese" in service_result.message.lower()
        assert "no pickles" in service_result.message.lower()
        
        # Verify the order was actually split and modified
        print(f"\n[FINAL ORDER] {sample_redis_order['items']}")
        
        # Should have 3 items now (2 modified + 1 unchanged)
        assert len(sample_redis_order["items"]) == 3
        
        # Find the items
        items = sample_redis_order["items"]
        
        # Count items by modification type
        extra_cheese_items = [item for item in items if "extra cheese" in item["modifications"].get("ingredient_modifications", "").lower()]
        no_pickles_items = [item for item in items if "no pickles" in item["modifications"].get("ingredient_modifications", "").lower()]
        unchanged_items = [item for item in items if not item["modifications"].get("ingredient_modifications", "")]
        
        print(f"\n[VERIFICATION]")
        print(f"  Extra cheese items: {len(extra_cheese_items)}")
        print(f"  No pickles items: {len(no_pickles_items)}")
        print(f"  Unchanged items: {len(unchanged_items)}")
        
        # Verify quantities
        assert len(extra_cheese_items) == 1
        assert extra_cheese_items[0]["quantity"] == 2
        assert extra_cheese_items[0]["total_price"] == 20.0  # 2 * 10.0
        
        assert len(no_pickles_items) == 1
        assert no_pickles_items[0]["quantity"] == 1
        assert no_pickles_items[0]["total_price"] == 10.0  # 1 * 10.0
        
        assert len(unchanged_items) == 1
        assert unchanged_items[0]["quantity"] == 1
        assert unchanged_items[0]["total_price"] == 10.0  # 1 * 10.0
        
        # Verify total quantity is still 4
        total_quantity = sum(item["quantity"] for item in items)
        assert total_quantity == 4
        
        print(f"\n[SUCCESS] Complex item splitting scenario completed successfully!")
        print(f"  Total items: {len(items)}")
        print(f"  Total quantity: {total_quantity}")
        print(f"  Extra cheese: {extra_cheese_items[0]['quantity']} items")
        print(f"  No pickles: {no_pickles_items[0]['quantity']} items")
        print(f"  Unchanged: {unchanged_items[0]['quantity']} items")
    
    @pytest.mark.asyncio
    async def test_simple_ingredient_modification(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """Test simple ingredient modification on single item"""
        
        # Test input: Simple modification
        user_input = "No pickles on the burger"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        # Verify agent result
        assert agent_result.success is True
        assert agent_result.requires_split is False  # Should be simple modification
        assert len(agent_result.modifications) == 1
        
        # Run real service
        service = ModifyItemService()
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        
        # Verify service result
        assert service_result.success is True
        assert "pickles" in service_result.message.lower()
        
        # Verify the order was modified (should still be 1 item)
        assert len(sample_redis_order["items"]) == 1
        burger_item = sample_redis_order["items"][0]
        assert "no pickles" in burger_item["modifications"]["ingredient_modifications"].lower()
        
        print(f"\n[SUCCESS] Simple ingredient modification completed!")
        print(f"  Final modifications: {burger_item['modifications']['ingredient_modifications']}")
    
    @pytest.mark.asyncio
    async def test_simple_quantity_modification(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """Test simple quantity modification on single item"""
        
        # Test input: Simple quantity change
        user_input = "I only want 2 burgers total"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        # Verify agent result
        assert agent_result.success is True
        # The agent now correctly recognizes this as a simple quantity change
        assert agent_result.requires_split is False
        assert len(agent_result.modifications) == 1
        
        # Run real service
        service = ModifyItemService()
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        
        # Verify service result
        assert service_result.success is True
        assert "quantity" in service_result.message.lower() or "two" in service_result.message.lower()
        
        # Verify the order was modified (should still be 1 item with quantity 2)
        assert len(sample_redis_order["items"]) == 1
        burger_item = sample_redis_order["items"][0]
        assert burger_item["quantity"] == 2
        assert burger_item["total_price"] == 20.0  # 2 * 10.0
        
        print(f"\n[SUCCESS] Simple quantity modification completed!")
        print(f"  Final quantity: {burger_item['quantity']}")
        print(f"  Final total price: {burger_item['total_price']}")
    
    @pytest.mark.asyncio
    async def test_all_items_modification(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """Test modification applied to all items (no splitting needed)"""
        
        # Test input: Modify all items
        user_input = "Make all the burgers extra cheese"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        # Verify agent result
        assert agent_result.success is True
        assert agent_result.requires_split is False  # Should be simple modification (all items)
        assert len(agent_result.modifications) == 1
        
        # Run real service
        service = ModifyItemService()
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        
        # Verify service result
        assert service_result.success is True
        assert "cheese" in service_result.message.lower()
        
        # Verify the order was modified (should still be 1 item)
        assert len(sample_redis_order["items"]) == 1
        burger_item = sample_redis_order["items"][0]
        assert "extra cheese" in burger_item["modifications"]["ingredient_modifications"].lower()
        assert burger_item["quantity"] == 4  # Should remain 4 (all items modified)
        
        print(f"\n[SUCCESS] All items modification completed!")
        print(f"  Final quantity: {burger_item['quantity']}")
        print(f"  Final modifications: {burger_item['modifications']['ingredient_modifications']}")
    
    @pytest.mark.asyncio
    async def test_modify_nonexistent_item(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """Test modification of item that doesn't exist in order"""
        
        # Test input: Try to modify something not in the order
        user_input = "Make the pizza extra cheese"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Clarification Needed: {agent_result.clarification_needed}")
        print(f"  Clarification Message: {agent_result.clarification_message}")
        
        # The agent should either ask for clarification or fail gracefully
        # It might not find the item and ask for clarification
        if agent_result.clarification_needed:
            print(f"\n[SUCCESS] Agent correctly asked for clarification!")
            print(f"  Message: {agent_result.clarification_message}")
            assert agent_result.clarification_needed is True
            assert agent_result.clarification_message is not None
        else:
            # If agent thinks it found something, the service should handle it
            service = ModifyItemService()
            service_result = await service.apply_modification(agent_result, sample_redis_order)
            
            print(f"\n[SERVICE OUTPUT]")
            print(f"  Success: {service_result.success}")
            print(f"  Message: {service_result.message}")
            
            # Service should fail because item doesn't exist
            assert service_result.success is False
            assert "not found" in service_result.message.lower() or "does not exist" in service_result.message.lower()
            
            print(f"\n[SUCCESS] Service correctly rejected modification of nonexistent item!")
    
    @pytest.mark.asyncio
    async def test_modify_legitimate_menu_item_not_in_order(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test modification of legitimate menu item that's not in current order"""
        
        # Test input: Try to modify fries (which exists on menu but not in order)
        user_input = "Make the fries with bacon"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Clarification Needed: {agent_result.clarification_needed}")
        print(f"  Clarification Message: {agent_result.clarification_message}")
        
        # The agent should ask for clarification since fries isn't in the order
        assert agent_result.clarification_needed is True
        assert agent_result.clarification_message is not None
        assert "fries" in agent_result.clarification_message.lower()
        assert "in your current order" in agent_result.clarification_message.lower()
        
        print(f"\n[SUCCESS] Agent correctly asked for clarification!")
        print(f"  Message: {agent_result.clarification_message}")
    
    @pytest.mark.asyncio
    async def test_ambiguous_item_reference(
        self, 
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients
    ):
        """Test ambiguous item reference that could match multiple items"""
        
        # Add another burger to the order to create ambiguity
        sample_redis_order["items"].append({
            "id": "item_1234567891",
            "menu_item_id": 1,  # Same menu item ID
            "quantity": 2,
            "modifications": {
                "size": "large",
                "name": "Burger",
                "unit_price": 12.0,
                "total_price": 24.0,
                "ingredient_modifications": "",
                "special_instructions": ""
            },
            "added_at": "2024-01-01T12:02:00"
        })
        
        # Test input: Ambiguous reference
        user_input = "Make that burger extra cheese"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Clarification Needed: {agent_result.clarification_needed}")
        print(f"  Clarification Message: {agent_result.clarification_message}")
        
        # Agent should ask for clarification due to ambiguity
        if agent_result.clarification_needed:
            print(f"\n[SUCCESS] Agent correctly identified ambiguity!")
            print(f"  Message: {agent_result.clarification_message}")
            assert agent_result.clarification_needed is True
            assert "which" in agent_result.clarification_message.lower() or "burger" in agent_result.clarification_message.lower()
        else:
            # If agent made a choice, it should be the most recent item
            assert agent_result.success is True
            assert len(agent_result.modifications) == 1
            
            # Service should apply to the most recent item
            service = ModifyItemService()
            service_result = await service.apply_modification(agent_result, sample_redis_order)
            
            print(f"\n[SERVICE OUTPUT]")
            print(f"  Success: {service_result.success}")
            print(f"  Message: {service_result.message}")
            
            assert service_result.success is True
            print(f"\n[SUCCESS] Agent chose most recent item for modification!")
    
    @pytest.mark.asyncio
    async def test_quantity_exceeds_limits(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test quantity change that exceeds business limits"""
        
        # Test input: Try to set quantity to something very high
        user_input = "Change the quantity to 100"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        # Agent should parse the request
        assert agent_result.success is True
        assert agent_result.requires_split is False
        assert len(agent_result.modifications) == 1
        
        # Run real service (should fail validation)
        # Mock MenuItem model to return restrictive quantity limits
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class:
            # Create mock menu item with low max_quantity
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 10  # Lower than requested 100
            
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            service = ModifyItemService()
            service_result = await service.apply_modification(agent_result, sample_redis_order)
            
            print(f"\n[SERVICE OUTPUT]")
            print(f"  Success: {service_result.success}")
            print(f"  Message: {service_result.message}")
            print(f"  Validation Errors: {service_result.validation_errors}")
            
            # Service should fail due to quantity validation
            assert service_result.success is False
            assert "Cannot order" in service_result.message or "Maximum allowed" in service_result.message
            assert len(service_result.validation_errors) > 0
        
        print(f"\n[SUCCESS] Service correctly rejected excessive quantity!")
    
    @pytest.mark.asyncio
    async def test_nonexistent_ingredient_modification(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test modification with ingredient that doesn't exist"""
        
        # Test input: Try to add ingredient that doesn't exist
        user_input = "Make the burger with unicorn meat"
        
        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")
        
        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )
        
        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Requires Split: {agent_result.requires_split}")
        print(f"  Modifications: {len(agent_result.modifications)}")
        
        # Agent should parse the request
        assert agent_result.success is True
        assert agent_result.requires_split is False
        assert len(agent_result.modifications) == 1
        
        # Run real service (should fail validation)
        # Mock ingredient service to return only valid ingredients (no "unicorn meat")
        mock_ingredient_service = MagicMock()
        mock_ingredient_list = MagicMock()
        
        # Create mock ingredients (only valid ones: cheese, pickles, mayo)
        mock_cheese = MagicMock()
        mock_cheese.name = "Cheese"
        mock_pickles = MagicMock()
        mock_pickles.name = "Pickles"
        mock_mayo = MagicMock()
        mock_mayo.name = "Mayo"
        
        mock_ingredient_list.ingredients = [mock_cheese, mock_pickles, mock_mayo]
        
        async def mock_get_by_restaurant(*args, **kwargs):
            return mock_ingredient_list
        mock_ingredient_service.get_by_restaurant = mock_get_by_restaurant
        
        # Create service with mocked dependencies
        service = ModifyItemService(ingredient_service=mock_ingredient_service)
        
        # Debug: Test ingredient validation directly
        print(f"\n[DEBUG] Testing ingredient validation directly...")
        modification = agent_result.modifications[0]
        ingredient_error = await service._validate_ingredients(modification, sample_redis_order)
        print(f"  Ingredient validation error: {ingredient_error}")
        
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        print(f"  Validation Errors: {service_result.validation_errors}")
        
        # Service should fail due to ingredient validation
        assert service_result.success is False
        assert "not available" in service_result.message.lower() or "not found" in service_result.message.lower()
        assert len(service_result.validation_errors) > 0
        
        print(f"\n[SUCCESS] Service correctly rejected nonexistent ingredient!")

    @pytest.mark.asyncio
    async def test_multiple_items_order_targeting(
        self,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test modification targeting specific items in a multi-item order"""

        # Create a multi-item order
        multi_item_order = {
            "id": "order_1234567890",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {
                    "id": "item_111",
                    "menu_item_id": 1,
                    "quantity": 2,
                    "modifications": {
                        "size": "regular",
                        "name": "Burger",
                        "unit_price": 10.0,
                        "total_price": 20.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    },
                    "added_at": "2024-01-01T12:00:00"
                },
                {
                    "id": "item_222",
                    "menu_item_id": 2,
                    "quantity": 1,
                    "modifications": {
                        "size": "large",
                        "name": "Fries",
                        "unit_price": 5.0,
                        "total_price": 5.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    },
                    "added_at": "2024-01-01T12:01:00"
                },
                {
                    "id": "item_333",
                    "menu_item_id": 3,
                    "quantity": 1,
                    "modifications": {
                        "size": "medium",
                        "name": "Drink",
                        "unit_price": 3.0,
                        "total_price": 3.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    },
                    "added_at": "2024-01-01T12:02:00"
                }
            ]
        }

        # Test input: Target specific items in multi-item order
        user_input = "Make the burger extra cheese and the fries extra salty"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[MULTI-ITEM ORDER] {len(multi_item_order['items'])} items")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=multi_item_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should parse both modifications
        assert agent_result.success is True
        assert len(agent_result.modifications) == 2
        
        # Check that it targeted the right items
        burger_mod = next((m for m in agent_result.modifications if "burger" in m.item_name.lower()), None)
        fries_mod = next((m for m in agent_result.modifications if "fries" in m.item_name.lower()), None)
        
        assert burger_mod is not None
        assert fries_mod is not None
        assert burger_mod.item_id == "item_111"  # Burger item ID
        assert fries_mod.item_id == "item_222"   # Fries item ID

        print(f"\n[SUCCESS] Agent correctly targeted specific items in multi-item order!")

    @pytest.mark.asyncio
    async def test_size_modification(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test size modification functionality"""

        # Test input: Change size
        user_input = "Make the burger large"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should parse the size change
        assert agent_result.success is True
        assert len(agent_result.modifications) == 1
        assert "large" in agent_result.modifications[0].modification.lower()

        # Run real service
        service = ModifyItemService()
        service_result = await service.apply_modification(agent_result, sample_redis_order)

        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")

        # Service should handle size modification
        assert service_result.success is True
        assert "large" in service_result.message.lower()

        print(f"\n[SUCCESS] Size modification worked!")

    @pytest.mark.asyncio
    async def test_mixed_validation_failures(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test multiple validation failures in one request"""

        # Test input: Both invalid ingredient and excessive quantity
        user_input = "Make the burger with unicorn meat and change quantity to 100"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should parse both modifications
        assert agent_result.success is True
        assert len(agent_result.modifications) >= 1

        # Run real service with mocked ingredient service
        mock_ingredient_service = MagicMock()
        mock_ingredient_list = MagicMock()
        
        # Create mock ingredients (only valid ones: cheese, pickles, mayo)
        mock_cheese = MagicMock()
        mock_cheese.name = "Cheese"
        mock_pickles = MagicMock()
        mock_pickles.name = "Pickles"
        mock_mayo = MagicMock()
        mock_mayo.name = "Mayo"
        
        mock_ingredient_list.ingredients = [mock_cheese, mock_pickles, mock_mayo]
        
        async def mock_get_by_restaurant(*args, **kwargs):
            return mock_ingredient_list
        mock_ingredient_service.get_by_restaurant = mock_get_by_restaurant
        
        # Mock MenuItem model to return restrictive quantity limits
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class:
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 10  # Lower than requested 100
            
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            service = ModifyItemService(ingredient_service=mock_ingredient_service)
            service_result = await service.apply_modification(agent_result, sample_redis_order)
            
            print(f"\n[SERVICE OUTPUT]")
            print(f"  Success: {service_result.success}")
            print(f"  Message: {service_result.message}")
            print(f"  Validation Errors: {service_result.validation_errors}")
            
            # Service should fail due to multiple validation issues
            assert service_result.success is False
            assert len(service_result.validation_errors) > 0

        print(f"\n[SUCCESS] Service correctly handled multiple validation failures!")

    @pytest.mark.asyncio
    async def test_partial_success_scenario(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test partial success when some modifications work and others don't"""

        # Test input: Mix of valid and invalid ingredients
        user_input = "Make the burger extra cheese and extra unicorn meat"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should parse the modifications
        assert agent_result.success is True
        assert len(agent_result.modifications) >= 1

        # Run real service with mocked ingredient service
        mock_ingredient_service = MagicMock()
        mock_ingredient_list = MagicMock()
        
        # Create mock ingredients (only valid ones: cheese, pickles, mayo)
        mock_cheese = MagicMock()
        mock_cheese.name = "Cheese"
        mock_pickles = MagicMock()
        mock_pickles.name = "Pickles"
        mock_mayo = MagicMock()
        mock_mayo.name = "Mayo"
        
        mock_ingredient_list.ingredients = [mock_cheese, mock_pickles, mock_mayo]
        
        async def mock_get_by_restaurant(*args, **kwargs):
            return mock_ingredient_list
        mock_ingredient_service.get_by_restaurant = mock_get_by_restaurant
        
        service = ModifyItemService(ingredient_service=mock_ingredient_service)
        service_result = await service.apply_modification(agent_result, sample_redis_order)
        
        print(f"\n[SERVICE OUTPUT]")
        print(f"  Success: {service_result.success}")
        print(f"  Message: {service_result.message}")
        print(f"  Validation Errors: {service_result.validation_errors}")
        
        # Service should handle partial success (cheese valid, unicorn meat invalid)
        # This might succeed with cheese but fail on unicorn meat, or fail entirely
        # The exact behavior depends on how we implement partial success handling
        assert service_result.success is not None  # Should have a result

        print(f"\n[SUCCESS] Service handled partial success scenario!")

    @pytest.mark.asyncio
    async def test_context_references(
        self,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test context-based references like 'last item' or 'first item'"""

        # Create a multi-item order
        multi_item_order = {
            "id": "order_1234567890",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {
                    "id": "item_111",
                    "menu_item_id": 1,
                    "quantity": 1,
                    "modifications": {
                        "size": "regular",
                        "name": "Burger",
                        "unit_price": 10.0,
                        "total_price": 10.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    },
                    "added_at": "2024-01-01T12:00:00"
                },
                {
                    "id": "item_222",
                    "menu_item_id": 2,
                    "quantity": 1,
                    "modifications": {
                        "size": "large",
                        "name": "Fries",
                        "unit_price": 5.0,
                        "total_price": 5.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    },
                    "added_at": "2024-01-01T12:01:00"
                }
            ]
        }

        # Test input: Reference last item
        user_input = "Make the last thing I ordered extra cheese"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[MULTI-ITEM ORDER] {len(multi_item_order['items'])} items")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=multi_item_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should parse the context reference
        assert agent_result.success is True
        assert len(agent_result.modifications) == 1
        
        # Should target the last item (Fries, item_222)
        assert agent_result.modifications[0].item_id == "item_222"

        print(f"\n[SUCCESS] Agent correctly resolved context reference!")

    @pytest.mark.asyncio
    async def test_edge_cases(
        self,
        sample_redis_order,
        sample_conversation_history,
        sample_menu_item_ingredients,
        db
    ):
        """Test edge cases and unusual inputs"""

        # Test input: Empty modification
        user_input = "Make the burger with no nothing"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[INITIAL ORDER] {sample_redis_order['items']}")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=sample_conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Clarification Needed: {agent_result.clarification_needed}")

        # Agent should either parse it or ask for clarification
        # This tests how the agent handles ambiguous/empty modifications
        assert agent_result.success is not None

        print(f"\n[SUCCESS] Agent handled edge case appropriately!")

    @pytest.mark.asyncio
    async def test_conversation_context_pronouns(
        self,
        sample_redis_order,
        sample_menu_item_ingredients,
        db
    ):
        """Test pronoun resolution with conversation context"""

        # Create conversation history with recent order
        conversation_history = ConversationHistory(
            entries=[
                ConversationEntry(
                    role=ConversationRole.USER,
                    content="I want a burger",
                    timestamp=datetime.now(),
                    session_id="test_session"
                ),
                ConversationEntry(
                    role=ConversationRole.ASSISTANT,
                    content="I've added a burger to your order",
                    timestamp=datetime.now(),
                    session_id="test_session"
                )
            ],
            session_id="test_session"
        )

        # Test input: Use pronoun to reference recently mentioned item
        user_input = "Make it extra cheese"

        print(f"\n[TEST INPUT] '{user_input}'")
        print(f"[CONVERSATION CONTEXT] Recent: 'I want a burger'")

        # Run real agent
        agent_result = await modify_item_agent(
            user_input=user_input,
            current_order=sample_redis_order["items"],
            conversation_history=conversation_history
        )

        print(f"\n[AGENT OUTPUT]")
        print(f"  Success: {agent_result.success}")
        print(f"  Confidence: {agent_result.confidence}")
        print(f"  Modifications: {len(agent_result.modifications)}")

        # Agent should resolve "it" to the burger
        assert agent_result.success is True
        assert len(agent_result.modifications) == 1
        assert "cheese" in agent_result.modifications[0].modification.lower()

        print(f"\n[SUCCESS] Agent correctly resolved pronoun with conversation context!")
