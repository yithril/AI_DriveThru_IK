"""
Category model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator
from typing import Optional, Dict, Any


class Category(Model):
    """
    Menu category model for organizing menu items
    """
    
    id = fields.IntField(primary_key=True)
    name = fields.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        description="Category name - required, max 100 characters"
    )
    description = fields.TextField(
        null=True,
        description="Category description"
    )
    display_order = fields.IntField(
        default=0,
        description="Order for displaying categories"
    )
    is_active = fields.BooleanField(
        default=True,
        description="Whether the category is active"
    )
    restaurant = fields.ForeignKeyField(
        "models.Restaurant",
        related_name="categories",
        on_delete=fields.CASCADE,
        description="Reference to restaurant"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the category was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the category was last updated"
    )
    
    # Relationships
    menu_items = fields.ReverseRelation["MenuItem"]
    
    class Meta:
        table = "categories"
        table_description = "Menu categories for organizing items"
    
    def __str__(self):
        return f"Category(id={self.id}, name='{self.name}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "restaurant_id": self.restaurant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    async def get_by_restaurant(cls, restaurant_id: int):
        """Get all categories for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, is_active=True).order_by('display_order')
    
    async def get_menu_items(self):
        """Get all menu items in this category"""
        return await self.menu_items.filter(is_available=True).order_by('display_order')
