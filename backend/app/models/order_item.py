"""
OrderItem model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import Optional, Dict, Any
from app.constants.item_sizes import ItemSize


class OrderItem(Model):
    """
    Order item model representing individual items in an order
    """
    
    id = fields.IntField(primary_key=True)
    order = fields.ForeignKeyField(
        "models.Order",
        related_name="order_items",
        on_delete=fields.CASCADE,
        description="Reference to order"
    )
    menu_item = fields.ForeignKeyField(
        "models.MenuItem",
        related_name="order_items",
        on_delete=fields.CASCADE,
        description="Reference to menu item"
    )
    quantity = fields.IntField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        description="Quantity of the item - max 10 per item"
    )
    unit_price = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        description="Unit price at time of order"
    )
    total_price = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        description="Total price for this line item"
    )
    special_instructions = fields.TextField(
        null=True,
        description="Special instructions for this item"
    )
    size = fields.CharEnumField(
        ItemSize,
        default=ItemSize.REGULAR,
        description="Size of the ordered item (can be different from menu item default)"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the order item was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the order item was last updated"
    )
    
    # Relationships
    
    class Meta:
        table = "order_items"
        table_description = "Individual items within orders"
    
    def __str__(self):
        return f"OrderItem(id={self.id}, quantity={self.quantity}, total={self.total_price})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "special_instructions": self.special_instructions,
            "size": self.size.value if self.size else ItemSize.REGULAR.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def formatted_total(self) -> str:
        """Return formatted total price string"""
        return f"${self.total_price:.2f}" if self.total_price else "$0.00"
    
    @classmethod
    async def get_by_order(cls, order_id: int):
        """Get all order items for an order"""
        return await cls.filter(order_id=order_id).order_by('created_at')
    
    @classmethod
    async def get_by_menu_item(cls, menu_item_id: int):
        """Get all order items for a specific menu item"""
        return await cls.filter(menu_item_id=menu_item_id).order_by('-created_at')
    
    async def calculate_total(self):
        """Calculate and update total price for this order item"""
        self.total_price = self.quantity * self.unit_price
        await self.save()
    
    @classmethod
    async def create_order_item(
        cls,
        order,
        menu_item,
        quantity: int,
        unit_price: Decimal,
        special_instructions: Optional[str] = None,
        size: Optional[ItemSize] = None
    ):
        """Create a new order item with calculated total"""
        total_price = quantity * unit_price
        
        order_item = await cls.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            special_instructions=special_instructions,
            size=size or menu_item.size
        )
        
        return order_item
