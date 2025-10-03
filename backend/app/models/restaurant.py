"""
Restaurant model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator, RegexValidator
from datetime import datetime
from typing import Optional, Dict, Any


class Restaurant(Model):
    """
    Restaurant model with comprehensive validation
    """
    
    id = fields.IntField(primary_key=True)
    name = fields.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        description="Restaurant name - required, max 100 characters"
    )
    logo_url = fields.CharField(
        max_length=255,
        null=True,
        description="URL to restaurant logo image"
    )
    primary_color = fields.CharField(
        max_length=7,
        default="#FF6B35",
        description="Primary brand color in hex format"
    )
    secondary_color = fields.CharField(
        max_length=7,
        default="#F7931E",
        description="Secondary brand color in hex format"
    )
    description = fields.TextField(
        null=True,
        description="Restaurant description"
    )
    address = fields.CharField(
        max_length=255,
        null=True,
        description="Restaurant address"
    )
    phone = fields.CharField(
        max_length=20,
        null=True,
        description="Restaurant phone number"
    )
    hours = fields.CharField(
        max_length=100,
        null=True,
        description="Restaurant operating hours"
    )
    is_active = fields.BooleanField(
        default=True,
        description="Whether the restaurant is active"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the restaurant was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the restaurant was last updated"
    )
    
    # Relationships
    categories = fields.ReverseRelation["Category"]
    menu_items = fields.ReverseRelation["MenuItem"]
    tags = fields.ReverseRelation["Tag"]
    ingredients = fields.ReverseRelation["Ingredient"]
    orders = fields.ReverseRelation["Order"]
    
    class Meta:
        table = "restaurants"
        table_description = "Restaurant information and branding"
    
    def __str__(self):
        return f"Restaurant(id={self.id}, name='{self.name}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "logo_url": self.logo_url,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "description": self.description,
            "address": self.address,
            "phone": self.phone,
            "hours": self.hours,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    async def get_active_restaurants(cls):
        """Get all active restaurants"""
        return await cls.filter(is_active=True).all()
    
    @classmethod
    async def get_by_name(cls, name: str):
        """Get restaurant by name (case-insensitive)"""
        return await cls.filter(name__iexact=name).first()
    
    async def get_menu_items(self):
        """Get all menu items for this restaurant"""
        return await self.menu_items.all()
    
    async def get_categories(self):
        """Get all categories for this restaurant"""
        return await self.categories.all()
