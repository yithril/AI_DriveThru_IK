"""
MenuItemIngredient model (Many-to-Many with quantity and units)
"""

from tortoise.models import Model
from tortoise import fields
from tortoise.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from typing import Optional, Dict, Any


class MenuItemIngredient(Model):
    """
    Many-to-many relationship between MenuItem and Ingredient with quantity and units
    """
    
    id = fields.IntField(primary_key=True)
    menu_item = fields.ForeignKeyField(
        "models.MenuItem",
        related_name="menu_item_ingredients",
        on_delete=fields.CASCADE,
        description="Reference to menu item"
    )
    ingredient = fields.ForeignKeyField(
        "models.Ingredient",
        related_name="menu_item_ingredients",
        on_delete=fields.CASCADE,
        description="Reference to ingredient"
    )
    quantity = fields.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(1000)],
        description="Quantity of ingredient (e.g., 1.0, 2.5)"
    )
    unit = fields.CharField(
        max_length=20,
        description="Unit of measurement (pieces, oz, cups, lbs, etc.)"
    )
    is_optional = fields.BooleanField(
        default=False,
        description="Whether this ingredient is optional (e.g., 'extra cheese')"
    )
    additional_cost = fields.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(999999.99)],
        description="Additional cost when adding extra of this ingredient"
    )
    created_at = fields.DatetimeField(
        auto_now_add=True,
        description="When the menu item ingredient was created"
    )
    
    class Meta:
        table = "menu_item_ingredients"
        table_description = "Many-to-many relationship between menu items and ingredients"
        unique_together = ("menu_item", "ingredient")
    
    def __str__(self):
        return f"MenuItemIngredient(menu_item_id={self.menu_item_id}, ingredient_id={self.ingredient_id}, quantity={self.quantity} {self.unit})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "ingredient_id": self.ingredient_id,
            "quantity": float(self.quantity) if self.quantity else 0.0,
            "unit": self.unit,
            "is_optional": self.is_optional,
            "additional_cost": float(self.additional_cost) if self.additional_cost else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
