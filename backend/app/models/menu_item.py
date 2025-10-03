"""
MenuItem model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import Optional, Dict, Any
from app.constants.item_sizes import ItemSize


class MenuItem(Model):
    """
    Menu item model with comprehensive validation
    """
    
    id = fields.IntField(primary_key=True)
    name = fields.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        description="Menu item name - required, max 100 characters"
    )
    description = fields.TextField(
        null=True,
        description="Menu item description"
    )
    price = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(999999.99)],
        description="Menu item price - required, max 999999.99"
    )
    image_url = fields.CharField(
        max_length=255,
        null=True,
        description="URL to menu item image"
    )
    category = fields.ForeignKeyField(
        "models.Category",
        related_name="menu_items",
        on_delete=fields.CASCADE,
        description="Reference to category"
    )
    restaurant = fields.ForeignKeyField(
        "models.Restaurant",
        related_name="menu_items",
        on_delete=fields.CASCADE,
        description="Reference to restaurant"
    )
    is_available = fields.BooleanField(
        default=True,
        description="Whether the menu item is available for ordering"
    )
    is_upsell = fields.BooleanField(
        default=False,
        description="Whether this item should be suggested for upselling"
    )
    is_special = fields.BooleanField(
        default=False,
        description="Whether this item is a special/featured item"
    )
    prep_time_minutes = fields.IntField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        description="Estimated preparation time in minutes"
    )
    display_order = fields.IntField(
        default=0,
        validators=[MinValueValidator(0)],
        description="Order for displaying menu items within category"
    )
    size = fields.CharEnumField(
        ItemSize,
        default=ItemSize.REGULAR,
        description="Size of the menu item (small, medium, large, etc.)"
    )
    
    # Modification options
    available_sizes = fields.JSONField(
        default=list,
        description="List of available sizes for this item (e.g., ['small', 'medium', 'large'])"
    )
    modifiable_ingredients = fields.JSONField(
        default=list,
        description="List of ingredient names that can be modified (added/removed/extra)"
    )
    max_quantity = fields.IntField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        description="Maximum quantity allowed for this item"
    )
    
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the menu item was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the menu item was last updated"
    )
    
    # Relationships
    tags = fields.ReverseRelation["MenuItemTag"]
    menu_item_ingredients = fields.ReverseRelation["MenuItemIngredient"]
    order_items = fields.ReverseRelation["OrderItem"]
    
    class Meta:
        table = "menu_items"
        table_description = "Menu items with pricing and availability"
    
    def __str__(self):
        return f"MenuItem(id={self.id}, name='{self.name}', price={self.price})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0.0,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "restaurant_id": self.restaurant_id,
            "is_available": self.is_available,
            "is_upsell": self.is_upsell,
            "is_special": self.is_special,
            "prep_time_minutes": self.prep_time_minutes,
            "display_order": self.display_order,
            "size": self.size.value if self.size else ItemSize.REGULAR.value,
            "available_sizes": self.available_sizes or [],
            "modifiable_ingredients": self.modifiable_ingredients or [],
            "max_quantity": self.max_quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def formatted_price(self) -> str:
        """Return formatted price string"""
        return f"${self.price:.2f}" if self.price else "$0.00"
    
    @classmethod
    async def get_by_restaurant(cls, restaurant_id: int):
        """Get all menu items for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, is_available=True).order_by('display_order')
    
    @classmethod
    async def get_by_category(cls, category_id: int):
        """Get all menu items in a category"""
        return await cls.filter(category_id=category_id, is_available=True).order_by('display_order')
    
    @classmethod
    async def get_special_items(cls, restaurant_id: int):
        """Get special/featured items for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, is_special=True, is_available=True)
    
    @classmethod
    async def get_upsell_items(cls, restaurant_id: int):
        """Get upsell items for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, is_upsell=True, is_available=True)
    
    def can_modify_size(self, new_size: str) -> bool:
        """Check if a size modification is allowed"""
        if not self.available_sizes:
            return False
        return new_size.lower() in [s.lower() for s in self.available_sizes]
    
    def can_modify_ingredient(self, ingredient_name: str) -> bool:
        """Check if an ingredient modification is allowed"""
        if not self.modifiable_ingredients:
            return False
        return ingredient_name.lower() in [i.lower() for i in self.modifiable_ingredients]
    
    def can_modify_quantity(self, new_quantity: int) -> bool:
        """Check if a quantity modification is allowed"""
        return 1 <= new_quantity <= self.max_quantity
