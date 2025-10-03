"""
Order model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, MinValueValidator
from decimal import Decimal
from typing import Optional, Dict, Any
import enum


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Model):
    """
    Order model with comprehensive validation
    """
    
    id = fields.IntField(primary_key=True)
    customer_name = fields.CharField(
        max_length=100,
        null=True,
        validators=[MinLengthValidator(2)],
        description="Customer name - optional for anonymous orders"
    )
    customer_phone = fields.CharField(
        max_length=20,
        null=True,
        validators=[MinLengthValidator(10)],
        description="Customer phone number - optional"
    )
    user = fields.ForeignKeyField(
        "models.User",
        related_name="orders",
        on_delete=fields.SET_NULL,
        null=True,
        description="Reference to registered user - optional"
    )
    restaurant = fields.ForeignKeyField(
        "models.Restaurant",
        related_name="orders",
        on_delete=fields.CASCADE,
        description="Reference to restaurant"
    )
    status = fields.CharEnumField(
        OrderStatus,
        default=OrderStatus.PENDING,
        description="Current order status"
    )
    subtotal = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        description="Subtotal before tax"
    )
    tax_amount = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)],
        description="Tax amount"
    )
    total_amount = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        description="Total amount including tax"
    )
    special_instructions = fields.TextField(
        null=True,
        description="Special instructions for the order"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the order was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the order was last updated"
    )
    
    # Relationships
    order_items = fields.ReverseRelation["OrderItem"]
    
    class Meta:
        table = "orders"
        table_description = "Customer orders with status and pricing"
    
    def __str__(self):
        return f"Order(id={self.id}, status='{self.status}', total={self.total_amount})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "user_id": self.user_id,
            "restaurant_id": self.restaurant_id,
            "status": self.status.value if self.status else None,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def formatted_total(self) -> str:
        """Return formatted total amount string"""
        return f"${self.total_amount:.2f}" if self.total_amount else "$0.00"
    
    @property
    async def item_count(self) -> int:
        """Return total number of items in the order"""
        order_items = await self.order_items.all()
        return sum(item.quantity for item in order_items)
    
    @classmethod
    async def get_by_restaurant(cls, restaurant_id: int):
        """Get all orders for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id).order_by('-created_at')
    
    @classmethod
    async def get_by_status(cls, restaurant_id: int, status: OrderStatus):
        """Get orders by status for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, status=status).order_by('-created_at')
    
    @classmethod
    async def get_pending_orders(cls, restaurant_id: int):
        """Get pending orders for a restaurant"""
        return await cls.filter(
            restaurant_id=restaurant_id,
            status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED]
        ).order_by('created_at')
    
    async def calculate_totals(self):
        """Calculate and update order totals"""
        order_items = await self.order_items.all()
        subtotal = sum(item.quantity * item.unit_price for item in order_items)
        tax_amount = subtotal * Decimal('0.08')  # 8% tax rate
        total_amount = subtotal + tax_amount
        
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        await self.save()
