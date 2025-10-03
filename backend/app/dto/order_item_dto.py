"""
Order Item Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class OrderItemCreateDto(BaseModel):
    """DTO for creating an order item"""
    order_id: int = Field(..., description="ID of the order")
    menu_item_id: int = Field(..., description="ID of the menu item")
    quantity: int = Field(..., ge=1, le=10, description="Quantity of the item (max 10)")
    unit_price: Decimal = Field(..., ge=0, description="Unit price at time of order")
    special_instructions: Optional[str] = Field(None, description="Special instructions for this item")

    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Unit price must be non-negative')
        return v


class OrderItemUpdateDto(BaseModel):
    """DTO for updating an order item"""
    quantity: Optional[int] = Field(None, ge=1, le=10, description="Quantity of the item")
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Unit price at time of order")
    special_instructions: Optional[str] = Field(None, description="Special instructions for this item")

    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Unit price must be non-negative')
        return v


class OrderItemResponseDto(BaseModel):
    """DTO for order item response"""
    id: int = Field(..., description="Order item ID")
    order_id: int = Field(..., description="ID of the order")
    menu_item_id: int = Field(..., description="ID of the menu item")
    quantity: int = Field(..., description="Quantity of the item")
    unit_price: Decimal = Field(..., description="Unit price at time of order")
    total_price: Decimal = Field(..., description="Total price for this line item")
    special_instructions: Optional[str] = Field(None, description="Special instructions for this item")
    created_at: datetime = Field(..., description="When the order item was created")
    updated_at: datetime = Field(..., description="When the order item was last updated")

    model_config = {"from_attributes": True}


class OrderItemListResponseDto(BaseModel):
    """DTO for order item list response"""
    order_items: list[OrderItemResponseDto] = Field(..., description="List of order items")
    total: int = Field(..., description="Total number of order items")


class OrderItemDeleteResponseDto(BaseModel):
    """DTO for order item delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
