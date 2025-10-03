"""
Ingredient model with Tortoise ORM and validation
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinLengthValidator
from typing import Optional, Dict, Any


class Ingredient(Model):
    """
    Ingredient model for menu item components
    """
    
    id = fields.IntField(primary_key=True)
    name = fields.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        description="Ingredient name - required, max 100 characters"
    )
    description = fields.TextField(
        null=True,
        description="Ingredient description"
    )
    is_allergen = fields.BooleanField(
        default=False,
        description="Whether this ingredient is an allergen"
    )
    allergen_type = fields.CharField(
        max_length=50,
        null=True,
        description="Type of allergen (e.g., 'dairy', 'nuts', 'gluten')"
    )
    is_optional = fields.BooleanField(
        default=False,
        description="Whether this ingredient is optional in menu items"
    )
    restaurant = fields.ForeignKeyField(
        "models.Restaurant",
        related_name="ingredients",
        on_delete=fields.CASCADE,
        description="Reference to restaurant"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the ingredient was created"
    )
    updated_at = fields.DatetimeField(
        auto_now=True,
        description="When the ingredient was last updated"
    )
    
    # Relationships
    menu_item_ingredients = fields.ReverseRelation["MenuItemIngredient"]
    
    class Meta:
        table = "ingredients"
        table_description = "Ingredients for menu items"
    
    def __str__(self):
        return f"Ingredient(id={self.id}, name='{self.name}')"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_allergen": self.is_allergen,
            "allergen_type": self.allergen_type,
            "is_optional": self.is_optional,
            "restaurant_id": self.restaurant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    async def get_by_restaurant(cls, restaurant_id: int):
        """Get all ingredients for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id).order_by('name')
    
    @classmethod
    async def get_allergens(cls, restaurant_id: int):
        """Get all allergen ingredients for a restaurant"""
        return await cls.filter(restaurant_id=restaurant_id, is_allergen=True).order_by('name')
    
    @classmethod
    async def search_by_name(cls, restaurant_id: int, name: str):
        """Search ingredients by name (case-insensitive)"""
        return await cls.filter(
            restaurant_id=restaurant_id,
            name__icontains=name
        ).order_by('name')
