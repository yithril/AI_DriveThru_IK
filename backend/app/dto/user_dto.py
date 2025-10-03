"""
User Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserCreateDto(BaseModel):
    """DTO for creating a user"""
    email: str = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Email must contain @ symbol')
        return v.lower()



class UserResponseDto(BaseModel):
    """DTO for user response"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: datetime = Field(..., description="When the user was last updated")

    model_config = {"from_attributes": True}


class UserDeleteResponseDto(BaseModel):
    """DTO for user delete response"""
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")
