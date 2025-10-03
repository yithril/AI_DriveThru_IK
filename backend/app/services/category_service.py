"""
Category Service with CRUD operations using Tortoise ORM and DTOs
"""

from typing import List, Optional
from app.models.category import Category
from app.dto.category_dto import (
    CategoryCreateDto,
    CategoryUpdateDto,
    CategoryResponseDto,
    CategoryListResponseDto,
    CategoryDeleteResponseDto
)


class CategoryService:
    """Service for category CRUD operations"""
    
    async def create(self, data: CategoryCreateDto) -> CategoryResponseDto:
        """Create a new category"""
        category = await Category.create(**data.model_dump(exclude_unset=True))
        return CategoryResponseDto.model_validate(category)
    
    async def get_by_id(self, category_id: int) -> Optional[CategoryResponseDto]:
        """Get category by ID"""
        category = await Category.get_or_none(id=category_id)
        if category:
            return CategoryResponseDto.model_validate(category)
        return None
    
    async def get_by_restaurant(self, restaurant_id: int) -> CategoryListResponseDto:
        """Get all categories for a restaurant"""
        categories = await Category.filter(restaurant_id=restaurant_id).all()
        category_dtos = [CategoryResponseDto.model_validate(category) for category in categories]
        return CategoryListResponseDto(
            categories=category_dtos,
            total=len(category_dtos)
        )
    
    async def get_all(self) -> CategoryListResponseDto:
        """Get all categories"""
        categories = await Category.all()
        category_dtos = [CategoryResponseDto.model_validate(category) for category in categories]
        return CategoryListResponseDto(
            categories=category_dtos,
            total=len(category_dtos)
        )
    
    async def update(self, category_id: int, data: CategoryUpdateDto) -> Optional[CategoryResponseDto]:
        """Update category by ID"""
        category = await Category.get_or_none(id=category_id)
        if category:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(category, key, value)
            await category.save()
            return CategoryResponseDto.model_validate(category)
        return None
    
    async def delete(self, category_id: int) -> CategoryDeleteResponseDto:
        """Delete category by ID"""
        category = await Category.get_or_none(id=category_id)
        if category:
            await category.delete()
            return CategoryDeleteResponseDto(
                success=True,
                message=f"Category '{category.name}' deleted successfully"
            )
        return CategoryDeleteResponseDto(
            success=False,
            message=f"Category with ID {category_id} not found"
        )
