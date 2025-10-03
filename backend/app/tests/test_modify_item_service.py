"""
Unit tests for Modify Item Service
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from app.services.modify_item_service import ModifyItemService
from app.workflow.response.modify_item_response import ModifyItemResult
from app.dto.modify_item_dto import ModifyItemRequestDto
from app.models.order_item import OrderItem
from app.models.menu_item import MenuItem
from app.models.menu_item_ingredient import MenuItemIngredient
from app.models.ingredient import Ingredient
from app.constants.item_sizes import ItemSize


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
async def sample_menu_item(db):
    """Create a sample menu item with modification options"""
    from app.models.restaurant import Restaurant
    from app.models.category import Category
    
    restaurant = await Restaurant.create(
        name="Test Restaurant",
        description="A test restaurant",
        address="123 Test St",
        phone="555-012-3456"
    )
    
    category = await Category.create(
        name="Burgers",
        description="Burger category",
        restaurant=restaurant
    )
    
    menu_item = await MenuItem.create(
        name="Test Burger",
        description="A test burger",
        price=Decimal('10.00'),
        category=category,
        restaurant=restaurant,
        size=ItemSize.REGULAR,
        available_sizes=["small", "medium", "large"],
        modifiable_ingredients=["pickles", "cheese", "mayo"],
        max_quantity=5
    )
    
    return menu_item


@pytest.fixture
async def sample_order_item(db, sample_menu_item):
    """Create a sample order item"""
    from app.models.order import Order
    
    order = await Order.create(
        restaurant=sample_menu_item.restaurant,
        subtotal=Decimal('10.00'),
        total_amount=Decimal('10.00'),
        status="pending"
    )
    
    order_item = await OrderItem.create(
        order=order,
        menu_item=sample_menu_item,
        quantity=1,
        unit_price=Decimal('10.00'),
        total_price=Decimal('10.00'),
        size=ItemSize.REGULAR
    )
    
    return order_item


@pytest.fixture
async def sample_ingredients(db, sample_menu_item):
    """Create sample ingredients and menu item ingredients"""
    # Create ingredients
    pickles = await Ingredient.create(
        name="Pickles",
        restaurant=sample_menu_item.restaurant,
        is_optional=True
    )
    
    cheese = await Ingredient.create(
        name="Cheese",
        restaurant=sample_menu_item.restaurant,
        is_optional=True
    )
    
    # Create menu item ingredients
    await MenuItemIngredient.create(
        menu_item=sample_menu_item,
        ingredient=pickles,
        quantity=Decimal('2.0'),
        unit="pieces",
        is_optional=True,
        additional_cost=Decimal('0.00')
    )
    
    await MenuItemIngredient.create(
        menu_item=sample_menu_item,
        ingredient=cheese,
        quantity=Decimal('1.0'),
        unit="slice",
        is_optional=True,
        additional_cost=Decimal('0.50')
    )
    
    return [pickles, cheese]


@pytest.fixture
def modify_item_service():
    """Create modify item service instance"""
    return ModifyItemService()


class TestModifyItemService:
    """Test cases for modify item service"""
    
    @pytest.mark.asyncio
    async def test_apply_quantity_modification_success(
        self, modify_item_service, sample_order_item, sample_menu_item
    ):
        """Test successful quantity modification"""
        
        # Create agent result
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to change quantity",
            modification_type="quantity",
            new_quantity=3
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify success
        assert result.success is True
        assert "quantity from 1 to 3" in result.message
        assert "quantity from 1 to 3" in result.modified_fields
        
        # Verify database was updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.quantity == 3
        assert updated_item.total_price == Decimal('30.00')  # 3 * 10.00
    
    @pytest.mark.asyncio
    async def test_apply_quantity_modification_invalid_quantity(
        self, modify_item_service, sample_order_item, sample_menu_item
    ):
        """Test quantity modification with invalid quantity"""
        
        # Create agent result with invalid quantity
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to change quantity",
            modification_type="quantity",
            new_quantity=10  # Exceeds max_quantity of 5
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify failure
        assert result.success is False
        assert "Cannot set quantity to 10" in result.message
        assert "Valid range: 1-5" in result.message
        assert len(result.validation_errors) > 0
        
        # Verify database was not updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.quantity == 1  # Original quantity
    
    @pytest.mark.asyncio
    async def test_apply_size_modification_success(
        self, modify_item_service, sample_order_item, sample_menu_item
    ):
        """Test successful size modification"""
        
        # Create agent result
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to change size",
            modification_type="size",
            new_size="large"
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify success
        assert result.success is True
        assert "size from regular to large" in result.message
        assert "size from regular to large" in result.modified_fields
        
        # Verify database was updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.size == ItemSize.LARGE
    
    @pytest.mark.asyncio
    async def test_apply_size_modification_invalid_size(
        self, modify_item_service, sample_order_item, sample_menu_item
    ):
        """Test size modification with invalid size"""
        
        # Create agent result with invalid size
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to change size",
            modification_type="size",
            new_size="extra_small"  # Not in available_sizes
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify failure
        assert result.success is False
        assert "Cannot change size to extra_small" in result.message
        assert "Available sizes: ['small', 'medium', 'large']" in result.message
        
        # Verify database was not updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.size == ItemSize.REGULAR  # Original size
    
    @pytest.mark.asyncio
    async def test_apply_ingredient_modification_success(
        self, modify_item_service, sample_order_item, sample_menu_item, sample_ingredients
    ):
        """Test successful ingredient modification"""
        
        # Create agent result
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to modify ingredients",
            modification_type="ingredient",
            ingredient_modifications=["No pickles", "Extra cheese"]
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify success
        assert result.success is True
        assert "ingredients" in result.message
        assert "No pickles" in result.message
        assert "Extra cheese" in result.message
        assert result.additional_cost == Decimal('0.50')  # Extra cheese cost
        assert len(result.modified_fields) > 0
        
        # Verify database was updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert "No pickles" in updated_item.special_instructions
        assert "Extra cheese" in updated_item.special_instructions
    
    @pytest.mark.asyncio
    async def test_apply_ingredient_modification_invalid_ingredient(
        self, modify_item_service, sample_order_item, sample_menu_item
    ):
        """Test ingredient modification with invalid ingredient"""
        
        # Create agent result with invalid ingredient
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to modify ingredients",
            modification_type="ingredient",
            ingredient_modifications=["No ketchup"]  # Not in modifiable_ingredients
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify failure
        assert result.success is False
        assert "Some ingredient modifications are not valid" in result.message
        
        # Verify database was not updated
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.special_instructions is None  # No changes
    
    @pytest.mark.asyncio
    async def test_apply_modification_nonexistent_order_item(self, modify_item_service, db):
        """Test modification of non-existent order item"""
        
        # Create agent result with non-existent ID
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=99999,
            target_confidence=0.9,
            target_reasoning="User wants to modify item",
            modification_type="quantity",
            new_quantity=2
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify failure
        assert result.success is False
        assert "Order item with ID 99999 not found" in result.message
        assert "does not exist" in result.validation_errors[0]
    
    @pytest.mark.asyncio
    async def test_apply_modification_not_actionable(self, modify_item_service):
        """Test modification that is not actionable (needs clarification)"""
        
        # Create agent result that needs clarification
        agent_result = ModifyItemResult(
            success=False,
            confidence=0.3,
            target_item_id=None,
            target_confidence=0.2,
            target_reasoning="Ambiguous request",
            modification_type=None,
            clarification_needed=True,
            clarification_message="Which item would you like to modify?"
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify failure
        assert result.success is False
        assert "Which item would you like to modify?" in result.message
    
    @pytest.mark.asyncio
    async def test_merge_special_instructions(
        self, modify_item_service, sample_order_item, sample_menu_item, sample_ingredients
    ):
        """Test merging of special instructions"""
        
        # Set existing special instructions
        sample_order_item.special_instructions = "No mayo, Extra lettuce"
        await sample_order_item.save()
        
        # Create agent result
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants to modify ingredients",
            modification_type="ingredient",
            ingredient_modifications=["No pickles", "Extra cheese"]
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify success
        assert result.success is True
        
        # Verify merged instructions
        updated_item = await OrderItem.get(id=sample_order_item.id)
        instructions = updated_item.special_instructions
        
        assert "No mayo" in instructions
        assert "Extra lettuce" in instructions
        assert "No pickles" in instructions
        assert "Extra cheese" in instructions
        
        # Verify no duplicates
        assert instructions.count("No mayo") == 1
        assert instructions.count("No pickles") == 1
    
    @pytest.mark.asyncio
    async def test_parse_ingredient_modification(self, modify_item_service):
        """Test parsing of ingredient modifications"""
        
        # Test "no" pattern
        ingredient, action = modify_item_service._parse_ingredient_modification("No pickles")
        assert ingredient == "pickles"
        assert action == "remove"
        
        # Test "hold" pattern
        ingredient, action = modify_item_service._parse_ingredient_modification("Hold the mayo")
        assert ingredient == "mayo"
        assert action == "remove"
        
        # Test "extra" pattern
        ingredient, action = modify_item_service._parse_ingredient_modification("Extra cheese")
        assert ingredient == "cheese"
        assert action == "extra"
        
        # Test other pattern
        ingredient, action = modify_item_service._parse_ingredient_modification("Spicy")
        assert ingredient == "spicy"
        assert action == "modify"
    
    @pytest.mark.asyncio
    async def test_multiple_modifications_success(
        self, modify_item_service, sample_order_item, sample_menu_item, sample_ingredients
    ):
        """Test multiple modifications in one request"""
        
        # Create agent result with multiple modifications
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            target_item_id=sample_order_item.id,
            target_confidence=0.9,
            target_reasoning="User wants multiple modifications",
            modification_type="multiple",
            new_quantity=2,
            new_size="large",
            ingredient_modifications=["No pickles", "Extra cheese"]
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result)
        
        # Verify success
        assert result.success is True
        assert "quantity from 1 to 2" in result.message
        assert "size from regular to large" in result.message
        assert "ingredients" in result.message
        assert len(result.modified_fields) >= 3  # Should have quantity, size, and ingredients
        
        # Verify all changes were applied
        updated_item = await OrderItem.get(id=sample_order_item.id)
        assert updated_item.quantity == 2
        assert updated_item.size == ItemSize.LARGE
        assert updated_item.total_price == Decimal('20.00')  # 2 * 10.00
        assert "No pickles" in updated_item.special_instructions
        assert "Extra cheese" in updated_item.special_instructions
