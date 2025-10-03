"""
Integration tests for Modify Item Workflow

These tests use:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- In-memory SQLite database for menu items and validation
- Mock Redis service for order session management
- Tests complete workflow from user input to order update
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.workflow.nodes.modify_item_workflow import ModifyItemWorkflow
from app.services.order_session_service import OrderSessionService
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.ingredient import Ingredient
from app.models.menu_item_ingredient import MenuItemIngredient
from app.constants.item_sizes import ItemSize
from app.config.settings import settings


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
    
    # Create burger
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
    
    # Create fries
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
    
    return [pickles, cheese]


@pytest.fixture
async def sample_menu_item_ingredients(db, sample_menu_items, sample_ingredients):
    """Create menu item ingredients"""
    
    burger, fries = sample_menu_items
    pickles, cheese = sample_ingredients
    
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
    
    return [burger, fries]


@pytest.fixture
async def mock_redis_order_with_postgresql_items(db, sample_menu_items, sample_restaurant):
    """Mock Redis order data with corresponding PostgreSQL OrderItem records"""
    from app.models.order import Order
    from app.models.order_item import OrderItem
    
    # Create a real order in PostgreSQL
    order = await Order.create(
        restaurant=sample_restaurant,
        subtotal=Decimal('15.00'),
        total_amount=Decimal('15.00'),
        status="pending"
    )
    
    # Create real order items in PostgreSQL
    burger_item = await OrderItem.create(
        order=order,
        menu_item=sample_menu_items[0],  # Burger
        quantity=1,
        unit_price=Decimal('10.00'),
        total_price=Decimal('10.00'),
        size=ItemSize.REGULAR
    )
    
    fries_item = await OrderItem.create(
        order=order,
        menu_item=sample_menu_items[1],  # Fries
        quantity=1,
        unit_price=Decimal('5.00'),
        total_price=Decimal('5.00'),
        size=ItemSize.MEDIUM
    )
    
    # Create Redis order data that matches the PostgreSQL items
    return {
        "id": "order_1234567890",
        "session_id": "session_123",
        "restaurant_id": 1,
        "status": "active",
        "items": [
            {
                "id": f"item_{burger_item.id}",
                "menu_item_id": burger_item.menu_item_id,
                "quantity": burger_item.quantity,
                "modifications": {
                    "size": burger_item.size.value,
                    "name": "Burger",
                    "unit_price": float(burger_item.unit_price),
                    "total_price": float(burger_item.total_price)
                },
                "added_at": "2024-01-01T12:00:00"
            },
            {
                "id": f"item_{fries_item.id}",
                "menu_item_id": fries_item.menu_item_id,
                "quantity": fries_item.quantity,
                "modifications": {
                    "size": fries_item.size.value,
                    "name": "Fries",
                    "unit_price": float(fries_item.unit_price),
                    "total_price": float(fries_item.total_price)
                },
                "added_at": "2024-01-01T12:01:00"
            }
        ]
    }, [burger_item, fries_item]


@pytest.fixture
def mock_order_session_service(mock_redis_order_with_postgresql_items):
    """Mock order session service"""
    service = AsyncMock(spec=OrderSessionService)
    redis_order, postgresql_items = mock_redis_order_with_postgresql_items
    service.get_session_order.return_value = redis_order
    service.update_order.return_value = True
    return service


@pytest.fixture
def modify_item_workflow(mock_order_session_service):
    """Create modify item workflow with mocked dependencies"""
    return ModifyItemWorkflow(mock_order_session_service)


class TestModifyItemWorkflowIntegration:
    """Integration tests for modify item workflow with real agent and database"""
    
    @pytest.mark.asyncio
    async def test_quantity_modification_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test quantity modification using real agent"""
        
        user_input = "Make the burger two"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[QUANTITY MODIFICATION] '{user_input}' -> {result}")
        
        # Verify the workflow succeeded
        assert result.success is True
        assert result.workflow_type.value == "modify_item"
        assert result.data["modified_fields"] is not None
        
        # Verify the agent correctly identified the modification
        assert "quantity" in result.message.lower() or "two" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_ingredient_modification_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test ingredient modification using real agent"""
        
        user_input = "No pickles on the burger"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[INGREDIENT MODIFICATION] '{user_input}' -> {result}")
        
        # Verify the workflow succeeded
        assert result.success is True
        assert result.workflow_type.value == "modify_item"
        
        # Verify the agent correctly identified the modification
        assert "pickles" in result.message.lower() or "ingredients" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_size_modification_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test size modification using real agent"""
        
        user_input = "Make the fries large"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[SIZE MODIFICATION] '{user_input}' -> {result}")
        
        # Verify the workflow succeeded
        assert result.success is True
        assert result.workflow_type.value == "modify_item"
        
        # Verify the agent correctly identified the modification
        assert "large" in result.message.lower() or "size" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_ambiguous_modification_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test ambiguous modification using real agent"""
        
        user_input = "Make it large"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[AMBIGUOUS MODIFICATION] '{user_input}' -> {result}")
        
        # This should either succeed (if agent can resolve) or need clarification
        assert result.workflow_type.value == "modify_item"
        
        if not result.success:
            # Should need clarification
            assert result.needs_clarification is True
            assert "which" in result.message.lower() or "clarify" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_pronoun_reference_with_conversation_history(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test pronoun reference using conversation history"""
        
        user_input = "Make it two"
        conversation_history = [
            {"user": "I want a burger", "ai": "Added burger to your order"},
            {"user": "And some fries", "ai": "Added fries to your order"}
        ]
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123",
            conversation_history=conversation_history
        )
        
        print(f"\n[PRONOUN REFERENCE] '{user_input}' -> {result}")
        
        # Verify the workflow succeeded
        assert result.success is True
        assert result.workflow_type.value == "modify_item"
        
        # Should have modified something based on context
        assert result.data["modified_fields"] is not None
    
    @pytest.mark.asyncio
    async def test_multiple_modifications_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test multiple modifications using real agent"""
        
        user_input = "Extra cheese and no pickles on the burger"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[MULTIPLE MODIFICATIONS] '{user_input}' -> {result}")
        
        # Verify the workflow succeeded
        assert result.success is True
        assert result.workflow_type.value == "modify_item"
        
        # Should have modified ingredients
        assert "cheese" in result.message.lower() or "pickles" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_modification_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test invalid modification using real agent"""
        
        user_input = "Make the burger extra large"  # Invalid size
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[INVALID MODIFICATION] '{user_input}' -> {result}")
        
        # Should either fail validation or need clarification
        assert result.workflow_type.value == "modify_item"
        
        # If it succeeds, it means the agent parsed it but service validation should catch it
        # If it fails, it should be due to validation errors
        if not result.success:
            assert len(result.validation_errors) > 0 or "cannot" in result.message.lower() or "clarify" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_no_modification_intent_with_real_agent(
        self, 
        modify_item_workflow,
        sample_menu_item_ingredients,
        mock_redis_order_with_postgresql_items
    ):
        """Test input with no modification intent"""
        
        user_input = "How much is a burger?"
        
        result = await modify_item_workflow.execute(
            user_input=user_input,
            session_id="session_123"
        )
        
        print(f"\n[NO MODIFICATION INTENT] '{user_input}' -> {result}")
        
        # Should either need clarification or fail
        assert result.workflow_type.value == "modify_item"
        
        if not result.success:
            assert "clarify" in result.message.lower() or "understand" in result.message.lower()
