"""
User Service with create and delete operations using Tortoise ORM and DTOs
"""

from typing import Optional
from app.models.user import User
from app.dto.user_dto import (
    UserCreateDto,
    UserResponseDto,
    UserDeleteResponseDto
)


class UserService:
    """Service for user operations (create and delete only)"""
    
    async def create(self, data: UserCreateDto) -> UserResponseDto:
        """Create a new user"""
        user = await User.create(**data.model_dump(exclude_unset=True))
        return UserResponseDto.model_validate(user)
    
    async def get_by_id(self, user_id: int) -> Optional[UserResponseDto]:
        """Get user by ID"""
        user = await User.get_or_none(id=user_id)
        if user:
            return UserResponseDto.model_validate(user)
        return None
    
    async def get_by_email(self, email: str) -> Optional[UserResponseDto]:
        """Get user by email"""
        user = await User.get_or_none(email=email.lower())
        if user:
            return UserResponseDto.model_validate(user)
        return None
    
    async def delete(self, user_id: int) -> UserDeleteResponseDto:
        """Delete user by ID"""
        user = await User.get_or_none(id=user_id)
        if user:
            await user.delete()
            return UserDeleteResponseDto(
                success=True,
                message=f"User '{user.email}' deleted successfully"
            )
        return UserDeleteResponseDto(
            success=False,
            message=f"User with ID {user_id} not found"
        )
