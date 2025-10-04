"""
Order Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.order import OrderStatus


class OrderCreateDto(BaseModel):
    """DTO for creating an order"""
    customer_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Customer name")
    customer_phone: Optional[str] = Field(None, min_length=10, max_length=20, description="Customer phone number")
    user_id: Optional[int] = Field(None, description="ID of registered user (optional)")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    special_instructions: Optional[str] = Field(None, description="Special instructions for the order")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    subtotal: Decimal = Field(default=Decimal('0.00'), ge=0, description="Subtotal before tax")
    tax_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Tax amount")
    total_amount: Decimal = Field(default=Decimal('0.00'), ge=0, description="Total amount including tax")

    @field_validator('customer_phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) < 10:
            raise ValueError('Phone number must be at least 10 characters')
        return v


class OrderUpdateDto(BaseModel):
    """DTO for updating an order"""
    customer_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Customer name")
    customer_phone: Optional[str] = Field(None, min_length=10, max_length=20, description="Customer phone number")
    status: Optional[OrderStatus] = Field(None, description="Order status")
    special_instructions: Optional[str] = Field(None, description="Special instructions for the order")

    @field_validator('customer_phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) < 10:
            raise ValueError('Phone number must be at least 10 characters')
        return v


class OrderResponseDto(BaseModel):
    """DTO for order response"""
    id: int = Field(..., description="Order ID")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    user_id: Optional[int] = Field(None, description="ID of registered user")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    status: OrderStatus = Field(..., description="Order status")
    subtotal: Decimal = Field(..., description="Subtotal before tax")
    tax_amount: Decimal = Field(..., description="Tax amount")
    total_amount: Decimal = Field(..., description="Total amount including tax")
    special_instructions: Optional[str] = Field(None, description="Special instructions for the order")
    created_at: datetime = Field(..., description="When the order was created")
    updated_at: datetime = Field(..., description="When the order was last updated")

    model_config = {"from_attributes": True}


class OrderListResponseDto(BaseModel):
    """DTO for order list response"""
    orders: list[OrderResponseDto] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")


class OrderDeleteResponseDto(BaseModel):
    """DTO for order delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")


class OrderStatusUpdateDto(BaseModel):
    """DTO for updating order status"""
    status: OrderStatus = Field(..., description="New order status")


# Order Summary DTOs for combined order + order items display
class OrderItemSummaryDto(BaseModel):
    """DTO for order item in summary view with resolved menu item name"""
    id: int = Field(..., description="Order item ID")
    menu_item_name: str = Field(..., description="Resolved menu item name")
    quantity: int = Field(..., description="Quantity of the item")
    unit_price: Decimal = Field(..., description="Unit price at time of order")
    total_price: Decimal = Field(..., description="Total price for this line item")
    size: str = Field(..., description="Size of the item")
    special_instructions: Optional[str] = Field(None, description="Special instructions for this item")
    created_at: datetime = Field(..., description="When the order item was created")

    model_config = {"from_attributes": True}


class OrderSummaryDto(BaseModel):
    """DTO for order summary with embedded order items"""
    id: int = Field(..., description="Order ID")
    restaurant_id: int = Field(..., description="ID of the restaurant")
    status: OrderStatus = Field(..., description="Order status")
    subtotal: Decimal = Field(..., description="Subtotal before tax")
    tax_amount: Decimal = Field(..., description="Tax amount")
    total_amount: Decimal = Field(..., description="Total amount including tax")
    special_instructions: Optional[str] = Field(None, description="Special instructions for the order")
    created_at: datetime = Field(..., description="When the order was created")
    updated_at: datetime = Field(..., description="When the order was last updated")
    order_items: List[OrderItemSummaryDto] = Field(default=[], description="List of order items with resolved names")

    model_config = {"from_attributes": True}


class OrderSummaryListResponseDto(BaseModel):
    """DTO for order summary list response"""
    orders: List[OrderSummaryDto] = Field(..., description="List of order summaries")
    total: int = Field(..., description="Total number of orders")