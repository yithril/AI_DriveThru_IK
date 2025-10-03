"""
Restaurant Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class RestaurantCreateDto(BaseModel):
    """DTO for creating a restaurant"""
    name: str = Field(..., min_length=2, max_length=100, description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, max_length=255, description="Restaurant address")
    phone: Optional[str] = Field(None, max_length=20, description="Restaurant phone number")
    hours: Optional[str] = Field(None, max_length=100, description="Restaurant operating hours")
    primary_color: str = Field(default="#FF6B35", pattern=r"^#[0-9A-Fa-f]{6}$", description="Primary brand color")
    secondary_color: str = Field(default="#F7931E", pattern=r"^#[0-9A-Fa-f]{6}$", description="Secondary brand color")
    logo_url: Optional[str] = Field(None, max_length=255, description="URL to restaurant logo")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) < 7:
            raise ValueError('Phone number must be at least 7 characters')
        return v


class RestaurantUpdateDto(BaseModel):
    """DTO for updating a restaurant"""
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, max_length=255, description="Restaurant address")
    phone: Optional[str] = Field(None, max_length=20, description="Restaurant phone number")
    hours: Optional[str] = Field(None, max_length=100, description="Restaurant operating hours")
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Primary brand color")
    secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Secondary brand color")
    logo_url: Optional[str] = Field(None, max_length=255, description="URL to restaurant logo")
    is_active: Optional[bool] = Field(None, description="Whether the restaurant is active")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None and len(v) < 7:
            raise ValueError('Phone number must be at least 7 characters')
        return v


class RestaurantResponseDto(BaseModel):
    """DTO for restaurant response"""
    id: int = Field(..., description="Restaurant ID")
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, description="Restaurant address")
    phone: Optional[str] = Field(None, description="Restaurant phone number")
    hours: Optional[str] = Field(None, description="Restaurant operating hours")
    primary_color: str = Field(..., description="Primary brand color")
    secondary_color: str = Field(..., description="Secondary brand color")
    logo_url: Optional[str] = Field(None, description="URL to restaurant logo")
    is_active: bool = Field(..., description="Whether the restaurant is active")
    created_at: datetime = Field(..., description="When the restaurant was created")
    updated_at: datetime = Field(..., description="When the restaurant was last updated")

    model_config = {"from_attributes": True}


class RestaurantListResponseDto(BaseModel):
    """DTO for restaurant list response"""
    restaurants: list[RestaurantResponseDto] = Field(..., description="List of restaurants")
    total_count: int = Field(..., description="Total number of restaurants")


class RestaurantDeleteResponseDto(BaseModel):
    """DTO for restaurant delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
    restaurant_id: int = Field(..., description="ID of the deleted restaurant")
