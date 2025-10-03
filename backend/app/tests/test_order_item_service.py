"""
Unit tests for Order Item Service
"""

import pytest
from decimal import Decimal
from app.services.order_item_service import OrderItemService
from app.models.order_item import OrderItem
from app.models.order import Order
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.dto import OrderItemCreateDto, OrderItemUpdateDto


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
async def sample_menu_item(db, sample_restaurant, sample_category):
    """Create a sample menu item for testing"""
    return await MenuItem.create(
        name="Test Pizza",
        price=Decimal("12.99"),
        category=sample_category,
        restaurant=sample_restaurant
    )


@pytest.fixture
async def sample_order(db, sample_restaurant):
    """Create a sample order for testing"""
    return await Order.create(
        customer_name="Test Customer",
        restaurant=sample_restaurant,
        subtotal=Decimal('12.99'),
        total_amount=Decimal('14.03')
    )


@pytest.fixture
def order_item_service(db):
    return OrderItemService()


class TestOrderItemService:
    """Test Order Item Service CRUD operations"""
    
    async def test_create_order_item(self, db, order_item_service, sample_order, sample_menu_item):
        """Test creating an order item"""
        data = OrderItemCreateDto(
            order_id=sample_order.id,
            menu_item_id=sample_menu_item.id,
            quantity=2,
            unit_price=Decimal("12.99"),
            special_instructions="Extra cheese please"
        )
        
        order_item = await order_item_service.create(data)
        
        assert order_item.id is not None
        assert order_item.order_id == sample_order.id
        assert order_item.menu_item_id == sample_menu_item.id
        assert order_item.quantity == 2
        assert order_item.unit_price == Decimal("12.99")
        assert order_item.total_price == Decimal("25.98")  # 2 * 12.99
        assert order_item.special_instructions == "Extra cheese please"
    
    async def test_get_by_id(self, db, order_item_service, sample_order, sample_menu_item):
        """Test getting order item by ID"""
        # Create an order item first
        created_item = await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Get by ID
        found_item = await order_item_service.get_by_id(created_item.id)
        
        assert found_item is not None
        assert found_item.order_id == sample_order.id
        assert found_item.menu_item_id == sample_menu_item.id
        assert found_item.quantity == 1
        assert found_item.unit_price == Decimal("12.99")
        assert found_item.total_price == Decimal("12.99")
    
    async def test_get_by_id_not_found(self, db, order_item_service):
        """Test getting non-existent order item"""
        result = await order_item_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_order(self, db, order_item_service, sample_order, sample_menu_item):
        """Test getting order items by order"""
        # Create multiple order items for the order
        await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Create another menu item and order item
        menu_item2 = await MenuItem.create(
            name="Test Burger",
            price=Decimal("8.99"),
            category=sample_menu_item.category,
            restaurant=sample_menu_item.restaurant
        )
        
        await OrderItem.create(
            order=sample_order,
            menu_item=menu_item2,
            quantity=2,
            unit_price=Decimal("8.99"),
            total_price=Decimal("17.98")
        )
        
        # Get order items for order
        result = await order_item_service.get_by_order(sample_order.id)
        
        assert result.total == 2
        assert len(result.order_items) == 2
        assert result.order_items[0].quantity == 1
        assert result.order_items[1].quantity == 2
    
    async def test_get_by_menu_item(self, db, order_item_service, sample_order, sample_menu_item):
        """Test getting order items by menu item"""
        # Create multiple order items for the same menu item
        await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Create another order
        order2 = await Order.create(
            customer_name="Another Customer",
            restaurant=sample_menu_item.restaurant,
            subtotal=Decimal('12.99'),
            total_amount=Decimal('14.03')
        )
        
        await OrderItem.create(
            order=order2,
            menu_item=sample_menu_item,
            quantity=3,
            unit_price=Decimal("12.99"),
            total_price=Decimal("38.97")
        )
        
        # Get order items for menu item
        result = await order_item_service.get_by_menu_item(sample_menu_item.id)
        
        assert result.total == 2
        assert len(result.order_items) == 2
        quantities = [item.quantity for item in result.order_items]
        assert 1 in quantities
        assert 3 in quantities
    
    async def test_get_by_order_and_menu_item(self, db, order_item_service, sample_order, sample_menu_item):
        """Test getting specific order item by order and menu item"""
        # Create an order item
        await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=2,
            unit_price=Decimal("12.99"),
            total_price=Decimal("25.98")
        )
        
        # Get specific order item
        result = await order_item_service.get_by_order_and_menu_item(sample_order.id, sample_menu_item.id)
        
        assert result is not None
        assert result.order_id == sample_order.id
        assert result.menu_item_id == sample_menu_item.id
        assert result.quantity == 2
    
    async def test_get_all(self, db, order_item_service, sample_order, sample_menu_item):
        """Test getting all order items"""
        # Create multiple order items
        await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Create another order and order item
        order2 = await Order.create(
            customer_name="Another Customer",
            restaurant=sample_menu_item.restaurant,
            subtotal=Decimal('8.99'),
            total_amount=Decimal('9.71')
        )
        
        await OrderItem.create(
            order=order2,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("8.99"),
            total_price=Decimal("8.99")
        )
        
        # Get all order items
        result = await order_item_service.get_all()
        
        assert result.total == 2
        assert len(result.order_items) == 2
    
    async def test_update_order_item(self, db, order_item_service, sample_order, sample_menu_item):
        """Test updating an order item"""
        # Create an order item
        created_item = await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Update it
        update_data = OrderItemUpdateDto(
            quantity=3,
            unit_price=Decimal("11.99"),
            special_instructions="No onions"
        )
        
        updated = await order_item_service.update(created_item.id, update_data)
        
        assert updated is not None
        assert updated.id == created_item.id
        assert updated.quantity == 3
        assert updated.unit_price == Decimal("11.99")
        assert updated.total_price == Decimal("35.97")  # 3 * 11.99
        assert updated.special_instructions == "No onions"
    
    async def test_update_order_item_not_found(self, db, order_item_service):
        """Test updating non-existent order item"""
        update_data = OrderItemUpdateDto(quantity=2)
        result = await order_item_service.update(999, update_data)
        assert result is None
    
    async def test_update_quantity(self, db, order_item_service, sample_order, sample_menu_item):
        """Test updating order item quantity"""
        # Create an order item
        created_item = await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Update quantity
        updated = await order_item_service.update_quantity(created_item.id, 4)
        
        assert updated is not None
        assert updated.id == created_item.id
        assert updated.quantity == 4
        assert updated.total_price == Decimal("51.96")  # 4 * 12.99
    
    async def test_delete_order_item(self, db, order_item_service, sample_order, sample_menu_item):
        """Test deleting an order item"""
        # Create an order item
        created_item = await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Delete it
        result = await order_item_service.delete(created_item.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_item = await order_item_service.get_by_id(created_item.id)
        assert deleted_item is None
    
    async def test_delete_order_item_not_found(self, db, order_item_service):
        """Test deleting non-existent order item"""
        result = await order_item_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
    
    async def test_delete_by_order(self, db, order_item_service, sample_order, sample_menu_item):
        """Test deleting all order items for an order"""
        # Create multiple order items for the order
        await OrderItem.create(
            order=sample_order,
            menu_item=sample_menu_item,
            quantity=1,
            unit_price=Decimal("12.99"),
            total_price=Decimal("12.99")
        )
        
        # Create another menu item and order item
        menu_item2 = await MenuItem.create(
            name="Test Burger",
            price=Decimal("8.99"),
            category=sample_menu_item.category,
            restaurant=sample_menu_item.restaurant
        )
        
        await OrderItem.create(
            order=sample_order,
            menu_item=menu_item2,
            quantity=2,
            unit_price=Decimal("8.99"),
            total_price=Decimal("17.98")
        )
        
        # Delete all order items for the order
        result = await order_item_service.delete_by_order(sample_order.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify they're all deleted
        remaining_items = await order_item_service.get_by_order(sample_order.id)
        assert remaining_items.total == 0
