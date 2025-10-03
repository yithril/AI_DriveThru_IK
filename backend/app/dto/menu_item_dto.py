"""
Menu Item Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class MenuItemCreateDto(BaseModel):
    """DTO for creating a menu item"""
    name: str = Field(..., min_length=2, max_length=100, description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: Decimal = Field(..., ge=0, le=999999.99, description="Menu item price")
    image_url: Optional[str] = Field(None, max_length=255, description="URL to menu item image")
    category_id: int = Field(..., description="ID of the category this menu item belongs to")
    restaurant_id: int = Field(..., description="ID of the restaurant this menu item belongs to")
    is_available: bool = Field(default=True, description="Whether the menu item is available")
    is_upsell: bool = Field(default=False, description="Whether this item should be suggested for upselling")
    is_special: bool = Field(default=False, description="Whether this item is a special/featured item")
    prep_time_minutes: int = Field(default=5, ge=1, le=120, description="Estimated preparation time in minutes")
    display_order: int = Field(default=0, ge=0, description="Order for displaying menu items within category")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v


class MenuItemUpdateDto(BaseModel):
    """DTO for updating a menu item"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: Optional[Decimal] = Field(None, ge=0, le=999999.99, description="Menu item price")
    image_url: Optional[str] = Field(None, max_length=255, description="URL to menu item image")
    category_id: Optional[int] = Field(None, description="ID of the category this menu item belongs to")
    is_available: Optional[bool] = Field(None, description="Whether the menu item is available")
    is_upsell: Optional[bool] = Field(None, description="Whether this item should be suggested for upselling")
    is_special: Optional[bool] = Field(None, description="Whether this item is a special/featured item")
    prep_time_minutes: Optional[int] = Field(None, ge=1, le=120, description="Estimated preparation time in minutes")
    display_order: Optional[int] = Field(None, ge=0, description="Order for displaying menu items within category")

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v


class MenuItemResponseDto(BaseModel):
    """DTO for menu item response"""
    id: int = Field(..., description="Menu item ID")
    name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: Decimal = Field(..., description="Menu item price")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    category_id: int = Field(..., description="ID of the category this menu item belongs to")
    restaurant_id: int = Field(..., description="ID of the restaurant this menu item belongs to")
    is_available: bool = Field(..., description="Whether the menu item is available")
    is_upsell: bool = Field(..., description="Whether this item should be suggested for upselling")
    is_special: bool = Field(..., description="Whether this item is a special/featured item")
    prep_time_minutes: int = Field(..., description="Estimated preparation time in minutes")
    display_order: int = Field(..., description="Order for displaying menu items within category")
    created_at: datetime = Field(..., description="When the menu item was created")
    updated_at: datetime = Field(..., description="When the menu item was last updated")

    model_config = {"from_attributes": True}


class MenuItemListResponseDto(BaseModel):
    """DTO for menu item list response"""
    menu_items: list[MenuItemResponseDto] = Field(..., description="List of menu items")
    total: int = Field(..., description="Total number of menu items")


class MenuItemDeleteResponseDto(BaseModel):
    """DTO for menu item delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
