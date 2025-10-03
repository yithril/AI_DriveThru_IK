"""
Data Transfer Objects for Modify Item Service
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class ModifyItemRequestDto(BaseModel):
    """DTO for modify item service request"""
    target_item_id: int = Field(..., description="ID of the order item to modify")
    modification_type: str = Field(..., description="Type of modification")
    new_quantity: Optional[int] = Field(None, description="New quantity")
    new_size: Optional[str] = Field(None, description="New size")
    ingredient_modifications: List[str] = Field(default_factory=list, description="Ingredient modifications")
    additional_cost: Decimal = Field(default=Decimal('0.00'), description="Additional cost from modifications")


class ModifyItemResultDto(BaseModel):
    """DTO for modify item service result"""
    success: bool = Field(..., description="Whether the modification was successful")
    message: str = Field(..., description="Human-readable result message")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    additional_cost: Decimal = Field(default=Decimal('0.00'), description="Additional cost applied")
    modified_fields: List[str] = Field(default_factory=list, description="List of fields that were modified")
