"""
Category Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryCreateDto(BaseModel):
    """DTO for creating a category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=255, description="Category description")
    restaurant_id: int = Field(..., description="ID of the restaurant this category belongs to")


class CategoryUpdateDto(BaseModel):
    """DTO for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=255, description="Category description")


class CategoryResponseDto(BaseModel):
    """DTO for category response"""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    restaurant_id: int = Field(..., description="ID of the restaurant this category belongs to")
    created_at: datetime = Field(..., description="When the category was created")
    updated_at: datetime = Field(..., description="When the category was last updated")

    model_config = {"from_attributes": True}


class CategoryListResponseDto(BaseModel):
    """DTO for category list response"""
    categories: list[CategoryResponseDto] = Field(..., description="List of categories")
    total: int = Field(..., description="Total number of categories")


class CategoryDeleteResponseDto(BaseModel):
    """DTO for category delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
