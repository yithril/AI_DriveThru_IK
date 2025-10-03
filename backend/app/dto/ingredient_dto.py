"""
Ingredient Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class IngredientCreateDto(BaseModel):
    """DTO for creating an ingredient"""
    name: str = Field(..., min_length=2, max_length=100, description="Ingredient name")
    description: Optional[str] = Field(None, description="Ingredient description")
    is_allergen: bool = Field(default=False, description="Whether this ingredient is an allergen")
    allergen_type: Optional[str] = Field(None, max_length=50, description="Type of allergen (e.g., 'dairy', 'nuts', 'gluten')")
    is_optional: bool = Field(default=False, description="Whether this ingredient is optional in menu items")
    restaurant_id: int = Field(..., description="ID of the restaurant this ingredient belongs to")

    @field_validator('allergen_type')
    @classmethod
    def validate_allergen_type(cls, v):
        if v is not None:
            common_allergens = [
                'dairy', 'nuts', 'peanuts', 'tree nuts', 'gluten', 'wheat', 'soy', 
                'eggs', 'fish', 'shellfish', 'sesame', 'sulfites'
            ]
            if v.lower() not in common_allergens:
                # Allow custom allergen types but warn
                pass
        return v


class IngredientUpdateDto(BaseModel):
    """DTO for updating an ingredient"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Ingredient name")
    description: Optional[str] = Field(None, description="Ingredient description")
    is_allergen: Optional[bool] = Field(None, description="Whether this ingredient is an allergen")
    allergen_type: Optional[str] = Field(None, max_length=50, description="Type of allergen")
    is_optional: Optional[bool] = Field(None, description="Whether this ingredient is optional in menu items")

    @field_validator('allergen_type')
    @classmethod
    def validate_allergen_type(cls, v):
        if v is not None:
            common_allergens = [
                'dairy', 'nuts', 'peanuts', 'tree nuts', 'gluten', 'wheat', 'soy', 
                'eggs', 'fish', 'shellfish', 'sesame', 'sulfites'
            ]
            if v.lower() not in common_allergens:
                # Allow custom allergen types but warn
                pass
        return v


class IngredientResponseDto(BaseModel):
    """DTO for ingredient response"""
    id: int = Field(..., description="Ingredient ID")
    name: str = Field(..., description="Ingredient name")
    description: Optional[str] = Field(None, description="Ingredient description")
    is_allergen: bool = Field(..., description="Whether this ingredient is an allergen")
    allergen_type: Optional[str] = Field(None, description="Type of allergen")
    is_optional: bool = Field(..., description="Whether this ingredient is optional in menu items")
    restaurant_id: int = Field(..., description="ID of the restaurant this ingredient belongs to")
    created_at: datetime = Field(..., description="When the ingredient was created")
    updated_at: datetime = Field(..., description="When the ingredient was last updated")

    model_config = {"from_attributes": True}


class IngredientListResponseDto(BaseModel):
    """DTO for ingredient list response"""
    ingredients: list[IngredientResponseDto] = Field(..., description="List of ingredients")
    total_count: int = Field(..., description="Total number of ingredients")
    restaurant_id: int = Field(..., description="Restaurant ID")


class IngredientDeleteResponseDto(BaseModel):
    """DTO for ingredient delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
    ingredient_id: int = Field(..., description="ID of the deleted ingredient")
