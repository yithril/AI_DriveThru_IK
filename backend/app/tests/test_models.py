"""
Unit tests for Tortoise ORM models
"""

import pytest
from decimal import Decimal
from tortoise import Tortoise
from app.models import (
    User, Restaurant, Category, MenuItem, Ingredient, 
    Order, OrderItem, OrderStatus
)


@pytest.fixture
async def db():
    """Initialize test database"""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def restaurant(db):
    """Create test restaurant"""
    return await Restaurant.create(
        name="Test Restaurant",
        description="A test restaurant",
        address="123 Test St",
        phone="555-0123"
    )


@pytest.fixture
async def category(db, restaurant):
    """Create test category"""
    return await Category.create(
        name="Burgers",
        description="Delicious burgers",
        restaurant=restaurant,
        display_order=1
    )


@pytest.fixture
async def menu_item(db, restaurant, category):
    """Create test menu item"""
    return await MenuItem.create(
        name="Classic Burger",
        description="A delicious classic burger",
        price=Decimal('12.99'),
        category=category,
        restaurant=restaurant,
        prep_time_minutes=10
    )


class TestRestaurant:
    """Test Restaurant model"""
    
    async def test_create_restaurant(self, db):
        """Test creating a restaurant"""
        restaurant = await Restaurant.create(
            name="Test Restaurant",
            description="A test restaurant",
            primary_color="#FF0000",
            secondary_color="#00FF00"
        )
        
        assert restaurant.id is not None
        assert restaurant.name == "Test Restaurant"
        assert restaurant.primary_color == "#FF0000"
        assert restaurant.secondary_color == "#00FF00"
        assert restaurant.is_active is True
        assert restaurant.created_at is not None
    
    async def test_restaurant_validation(self, db):
        """Test restaurant validation"""
        with pytest.raises(Exception):  # Should fail validation
            await Restaurant.create(
                name="A",  # Too short
                primary_color="invalid",  # Invalid hex color
                secondary_color="also_invalid"
            )
    
    async def test_restaurant_to_dict(self, db):
        """Test restaurant to_dict method"""
        restaurant = await Restaurant.create(
            name="Test Restaurant",
            description="A test restaurant"
        )
        
        data = restaurant.to_dict()
        assert data["name"] == "Test Restaurant"
        assert data["description"] == "A test restaurant"
        assert "created_at" in data
        assert "updated_at" in data
    
    async def test_get_active_restaurants(self, db):
        """Test getting active restaurants"""
        await Restaurant.create(name="Active Restaurant", is_active=True)
        await Restaurant.create(name="Inactive Restaurant", is_active=False)
        
        active_restaurants = await Restaurant.get_active_restaurants()
        assert len(active_restaurants) == 1
        assert active_restaurants[0].name == "Active Restaurant"


class TestCategory:
    """Test Category model"""
    
    async def test_create_category(self, db, restaurant):
        """Test creating a category"""
        category = await Category.create(
            name="Burgers",
            description="Delicious burgers",
            restaurant=restaurant,
            display_order=1
        )
        
        assert category.id is not None
        assert category.name == "Burgers"
        assert category.restaurant_id == restaurant.id
        assert category.is_active is True
    
    async def test_category_validation(self, db, restaurant):
        """Test category validation"""
        with pytest.raises(Exception):  # Should fail validation
            await Category.create(
                name="A",  # Too short
                restaurant=restaurant
            )
    
    async def test_get_by_restaurant(self, db, restaurant):
        """Test getting categories by restaurant"""
        await Category.create(name="Burgers", restaurant=restaurant)
        await Category.create(name="Drinks", restaurant=restaurant)
        
        categories = await Category.get_by_restaurant(restaurant.id)
        assert len(categories) == 2
        assert categories[0].name == "Burgers"  # Ordered by display_order


class TestMenuItem:
    """Test MenuItem model"""
    
    async def test_create_menu_item(self, db, restaurant, category):
        """Test creating a menu item"""
        menu_item = await MenuItem.create(
            name="Classic Burger",
            description="A delicious classic burger",
            price=Decimal('12.99'),
            category=category,
            restaurant=restaurant,
            prep_time_minutes=10
        )
        
        assert menu_item.id is not None
        assert menu_item.name == "Classic Burger"
        assert menu_item.price == Decimal('12.99')
        assert menu_item.prep_time_minutes == 10
        assert menu_item.is_available is True
    
    async def test_menu_item_validation(self, db, restaurant, category):
        """Test menu item validation"""
        with pytest.raises(Exception):  # Should fail validation
            await MenuItem.create(
                name="A",  # Too short
                price=Decimal('-1.00'),  # Negative price
                category=category,
                restaurant=restaurant,
                prep_time_minutes=0  # Too low
            )
    
    async def test_formatted_price(self, db, restaurant, category):
        """Test formatted price property"""
        menu_item = await MenuItem.create(
            name="Test Item",
            price=Decimal('12.99'),
            category=category,
            restaurant=restaurant
        )
        
        assert menu_item.formatted_price == "$12.99"
    
    async def test_get_by_restaurant(self, db, restaurant, category):
        """Test getting menu items by restaurant"""
        await MenuItem.create(
            name="Item 1",
            price=Decimal('10.00'),
            category=category,
            restaurant=restaurant
        )
        await MenuItem.create(
            name="Item 2",
            price=Decimal('15.00'),
            category=category,
            restaurant=restaurant
        )
        
        items = await MenuItem.get_by_restaurant(restaurant.id)
        assert len(items) == 2


class TestIngredient:
    """Test Ingredient model"""
    
    async def test_create_ingredient(self, db, restaurant):
        """Test creating an ingredient"""
        ingredient = await Ingredient.create(
            name="Beef Patty",
            description="100% beef patty",
            is_allergen=False,
            restaurant=restaurant
        )
        
        assert ingredient.id is not None
        assert ingredient.name == "Beef Patty"
        assert ingredient.is_allergen is False
        assert ingredient.is_optional is False
    
    async def test_create_allergen_ingredient(self, db, restaurant):
        """Test creating an allergen ingredient"""
        ingredient = await Ingredient.create(
            name="Cheese",
            description="Dairy cheese",
            is_allergen=True,
            allergen_type="dairy",
            restaurant=restaurant
        )
        
        assert ingredient.is_allergen is True
        assert ingredient.allergen_type == "dairy"
    
    async def test_get_allergens(self, db, restaurant):
        """Test getting allergen ingredients"""
        await Ingredient.create(
            name="Cheese",
            is_allergen=True,
            allergen_type="dairy",
            restaurant=restaurant
        )
        await Ingredient.create(
            name="Beef",
            is_allergen=False,
            restaurant=restaurant
        )
        
        allergens = await Ingredient.get_allergens(restaurant.id)
        assert len(allergens) == 1
        assert allergens[0].name == "Cheese"


class TestOrder:
    """Test Order model"""
    
    async def test_create_order(self, db, restaurant):
        """Test creating an order"""
        order = await Order.create(
            customer_name="John Doe",
            customer_phone="555-012-3456",
            restaurant=restaurant,
            subtotal=Decimal('25.98'),
            tax_amount=Decimal('2.08'),
            total_amount=Decimal('28.06')
        )
        
        assert order.id is not None
        assert order.customer_name == "John Doe"
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == Decimal('28.06')
    
    async def test_order_validation(self, db, restaurant):
        """Test order validation"""
        with pytest.raises(Exception):  # Should fail validation
            await Order.create(
                customer_name="A",  # Too short
                restaurant=restaurant,
                subtotal=Decimal('-1.00'),  # Negative subtotal
                total_amount=Decimal('10.00')
            )
    
    async def test_formatted_total(self, db, restaurant):
        """Test formatted total property"""
        order = await Order.create(
            restaurant=restaurant,
            subtotal=Decimal('25.98'),
            total_amount=Decimal('28.06')
        )
        
        assert order.formatted_total == "$28.06"
    
    async def test_get_by_status(self, db, restaurant):
        """Test getting orders by status"""
        await Order.create(
            restaurant=restaurant,
            status=OrderStatus.PENDING,
            subtotal=Decimal('10.00'),
            total_amount=Decimal('10.80')
        )
        await Order.create(
            restaurant=restaurant,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal('15.00'),
            total_amount=Decimal('16.20')
        )
        
        pending_orders = await Order.get_by_status(restaurant.id, OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0].status == OrderStatus.PENDING


class TestOrderItem:
    """Test OrderItem model"""
    
    async def test_create_order_item(self, db, restaurant, category, menu_item):
        """Test creating an order item"""
        order = await Order.create(
            restaurant=restaurant,
            subtotal=Decimal('12.99'),
            total_amount=Decimal('14.03')
        )
        
        order_item = await OrderItem.create_order_item(
            order=order,
            menu_item=menu_item,
            quantity=2,
            unit_price=Decimal('12.99'),
            special_instructions="No pickles"
        )
        
        assert order_item.id is not None
        assert order_item.quantity == 2
        assert order_item.unit_price == Decimal('12.99')
        assert order_item.total_price == Decimal('25.98')
        assert order_item.special_instructions == "No pickles"
    
    async def test_order_item_validation(self, db, restaurant, category, menu_item):
        """Test order item validation"""
        order = await Order.create(
            restaurant=restaurant,
            subtotal=Decimal('12.99'),
            total_amount=Decimal('14.03')
        )
        
        with pytest.raises(Exception):  # Should fail validation
            await OrderItem.create(
                order=order,
                menu_item=menu_item,
                quantity=0,  # Too low
                unit_price=Decimal('12.99'),
                total_price=Decimal('0.00')
            )
    
    async def test_calculate_total(self, db, restaurant, category, menu_item):
        """Test calculating total price"""
        order = await Order.create(
            restaurant=restaurant,
            subtotal=Decimal('12.99'),
            total_amount=Decimal('14.03')
        )
        
        order_item = await OrderItem.create(
            order=order,
            menu_item=menu_item,
            quantity=2,
            unit_price=Decimal('12.99'),
            total_price=Decimal('0.00')  # Will be calculated
        )
        
        await order_item.calculate_total()
        assert order_item.total_price == Decimal('25.98')


class TestModelRelationships:
    """Test model relationships"""
    
    async def test_restaurant_categories_relationship(self, db, restaurant):
        """Test restaurant-categories relationship"""
        category = await Category.create(
            name="Burgers",
            restaurant=restaurant
        )
        
        categories = await restaurant.categories.all()
        assert len(categories) == 1
        assert categories[0].name == "Burgers"
    
    async def test_category_menu_items_relationship(self, db, restaurant, category):
        """Test category-menu_items relationship"""
        menu_item = await MenuItem.create(
            name="Classic Burger",
            price=Decimal('12.99'),
            category=category,
            restaurant=restaurant
        )
        
        menu_items = await category.menu_items.all()
        assert len(menu_items) == 1
        assert menu_items[0].name == "Classic Burger"
    
    async def test_order_order_items_relationship(self, db, restaurant, category, menu_item):
        """Test order-order_items relationship"""
        order = await Order.create(
            restaurant=restaurant,
            subtotal=Decimal('12.99'),
            total_amount=Decimal('14.03')
        )
        
        order_item = await OrderItem.create(
            order=order,
            menu_item=menu_item,
            quantity=1,
            unit_price=Decimal('12.99'),
            total_price=Decimal('12.99')
        )
        
        order_items = await order.order_items.all()
        assert len(order_items) == 1
        assert order_items[0].quantity == 1
