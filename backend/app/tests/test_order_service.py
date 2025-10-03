"""
Unit tests for Order Service
"""

import pytest
from decimal import Decimal
from app.services.order_service import OrderService
from app.models.order import Order, OrderStatus
from app.models.restaurant import Restaurant
from app.models.user import User
from app.dto import OrderCreateDto, OrderUpdateDto, OrderStatusUpdateDto


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
async def sample_user(db):
    """Create a sample user for testing"""
    return await User.create(
        email="test@example.com",
        name="Test User"
    )


@pytest.fixture
def order_service(db):
    return OrderService()


class TestOrderService:
    """Test Order Service CRUD operations"""
    
    async def test_create_order(self, db, order_service, sample_restaurant):
        """Test creating an order"""
        data = OrderCreateDto(
            customer_name="John Doe",
            customer_phone="555-012-3456",
            restaurant_id=sample_restaurant.id,
            special_instructions="Extra sauce please",
            status=OrderStatus.PENDING
        )
        
        order = await order_service.create(data)
        
        assert order.id is not None
        assert order.customer_name == "John Doe"
        assert order.customer_phone == "555-012-3456"
        assert order.restaurant_id == sample_restaurant.id
        assert order.special_instructions == "Extra sauce please"
        assert order.status == OrderStatus.PENDING
        assert order.subtotal == Decimal('0.00')
        assert order.tax_amount == Decimal('0.00')
        assert order.total_amount == Decimal('0.00')
    
    async def test_create_order_with_user(self, db, order_service, sample_restaurant, sample_user):
        """Test creating an order with a registered user"""
        data = OrderCreateDto(
            customer_name="Jane Smith",
            customer_phone="555-987-6543",
            user_id=sample_user.id,
            restaurant_id=sample_restaurant.id,
            status=OrderStatus.PENDING
        )
        
        order = await order_service.create(data)
        
        assert order.id is not None
        assert order.customer_name == "Jane Smith"
        assert order.user_id == sample_user.id
        assert order.restaurant_id == sample_restaurant.id
        assert order.status == OrderStatus.PENDING
    
    async def test_get_by_id(self, db, order_service, sample_restaurant):
        """Test getting order by ID"""
        # Create an order first
        created_order = await Order.create(
            customer_name="Get Test",
            restaurant=sample_restaurant,
            subtotal=Decimal('10.00'),
            tax_amount=Decimal('0.80'),
            total_amount=Decimal('10.80')
        )
        
        # Get by ID
        found_order = await order_service.get_by_id(created_order.id)
        
        assert found_order is not None
        assert found_order.customer_name == "Get Test"
        assert found_order.restaurant_id == sample_restaurant.id
        assert found_order.subtotal == Decimal('10.00')
        assert found_order.total_amount == Decimal('10.80')
    
    async def test_get_by_id_not_found(self, db, order_service):
        """Test getting non-existent order"""
        result = await order_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_restaurant(self, db, order_service, sample_restaurant):
        """Test getting orders by restaurant"""
        # Create multiple orders for the restaurant
        await Order.create(
            customer_name="Order 1",
            restaurant=sample_restaurant,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="Order 2",
            restaurant=sample_restaurant,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        # Get orders for restaurant
        result = await order_service.get_by_restaurant(sample_restaurant.id)
        
        assert result.total == 2
        assert len(result.orders) == 2
        # Should be ordered by created_at descending
        assert result.orders[0].customer_name == "Order 2"
        assert result.orders[1].customer_name == "Order 1"
    
    async def test_get_by_status(self, db, order_service, sample_restaurant):
        """Test getting orders by status"""
        # Create orders with different statuses
        await Order.create(
            customer_name="Pending Order",
            restaurant=sample_restaurant,
            status=OrderStatus.PENDING,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="Completed Order",
            restaurant=sample_restaurant,
            status=OrderStatus.COMPLETED,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        # Get pending orders
        result = await order_service.get_by_status(sample_restaurant.id, OrderStatus.PENDING)
        
        assert result.total == 1
        assert len(result.orders) == 1
        assert result.orders[0].customer_name == "Pending Order"
        assert result.orders[0].status == OrderStatus.PENDING
    
    async def test_get_pending_orders(self, db, order_service, sample_restaurant):
        """Test getting pending orders (PENDING and CONFIRMED)"""
        # Create orders with different statuses
        await Order.create(
            customer_name="Pending Order",
            restaurant=sample_restaurant,
            status=OrderStatus.PENDING,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="Confirmed Order",
            restaurant=sample_restaurant,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        await Order.create(
            customer_name="Completed Order",
            restaurant=sample_restaurant,
            status=OrderStatus.COMPLETED,
            subtotal=Decimal('20.00'),
            total_amount=Decimal('21.60')
        )
        
        # Get pending orders
        result = await order_service.get_pending_orders(sample_restaurant.id)
        
        assert result.total == 2
        assert len(result.orders) == 2
        statuses = [order.status for order in result.orders]
        assert OrderStatus.PENDING in statuses
        assert OrderStatus.CONFIRMED in statuses
        assert OrderStatus.COMPLETED not in statuses
    
    async def test_get_by_user(self, db, order_service, sample_restaurant, sample_user):
        """Test getting orders by user"""
        # Create orders for the user
        await Order.create(
            customer_name="User Order 1",
            restaurant=sample_restaurant,
            user=sample_user,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="User Order 2",
            restaurant=sample_restaurant,
            user=sample_user,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        # Get orders for user
        result = await order_service.get_by_user(sample_user.id)
        
        assert result.total == 2
        assert len(result.orders) == 2
        assert result.orders[0].user_id == sample_user.id
        assert result.orders[1].user_id == sample_user.id
    
    async def test_get_by_customer_phone(self, db, order_service, sample_restaurant):
        """Test getting orders by customer phone"""
        phone = "555-012-3456"
        
        # Create orders with the same phone
        await Order.create(
            customer_name="Phone Order 1",
            customer_phone=phone,
            restaurant=sample_restaurant,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="Phone Order 2",
            customer_phone=phone,
            restaurant=sample_restaurant,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        # Get orders by phone
        result = await order_service.get_by_customer_phone(phone)
        
        assert result.total == 2
        assert len(result.orders) == 2
        assert result.orders[0].customer_phone == phone
        assert result.orders[1].customer_phone == phone
    
    async def test_get_all(self, db, order_service, sample_restaurant):
        """Test getting all orders"""
        # Create multiple orders
        await Order.create(
            customer_name="All Order 1",
            restaurant=sample_restaurant,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            customer_name="All Order 2",
            restaurant=sample_restaurant,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        # Get all orders
        result = await order_service.get_all()
        
        assert result.total == 2
        assert len(result.orders) == 2
    
    async def test_update_order(self, db, order_service, sample_restaurant):
        """Test updating an order"""
        # Create an order
        created_order = await Order.create(
            customer_name="Original Name",
            customer_phone="555-000-0000",
            restaurant=sample_restaurant,
            status=OrderStatus.PENDING,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        
        # Update it
        update_data = OrderUpdateDto(
            customer_name="Updated Name",
            customer_phone="555-999-9999",
            status=OrderStatus.CONFIRMED,
            special_instructions="Updated instructions"
        )
        
        updated = await order_service.update(created_order.id, update_data)
        
        assert updated is not None
        assert updated.id == created_order.id
        assert updated.customer_name == "Updated Name"
        assert updated.customer_phone == "555-999-9999"
        assert updated.status == OrderStatus.CONFIRMED
        assert updated.special_instructions == "Updated instructions"
    
    async def test_update_order_not_found(self, db, order_service):
        """Test updating non-existent order"""
        update_data = OrderUpdateDto(customer_name="New Name")
        result = await order_service.update(999, update_data)
        assert result is None
    
    async def test_update_status(self, db, order_service, sample_restaurant):
        """Test updating order status"""
        # Create an order
        created_order = await Order.create(
            customer_name="Status Test",
            restaurant=sample_restaurant,
            status=OrderStatus.PENDING,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        
        # Update status
        status_data = OrderStatusUpdateDto(status=OrderStatus.PREPARING)
        updated = await order_service.update_status(created_order.id, status_data)
        
        assert updated is not None
        assert updated.id == created_order.id
        assert updated.status == OrderStatus.PREPARING
    
    async def test_delete_order(self, db, order_service, sample_restaurant):
        """Test deleting an order"""
        # Create an order
        created_order = await Order.create(
            customer_name="Delete Order",
            restaurant=sample_restaurant,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        
        # Delete it
        result = await order_service.delete(created_order.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_order = await order_service.get_by_id(created_order.id)
        assert deleted_order is None
    
    async def test_delete_order_not_found(self, db, order_service):
        """Test deleting non-existent order"""
        result = await order_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
