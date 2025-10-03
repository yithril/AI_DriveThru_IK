"""
Ingredient Service with CRUD operations using Tortoise ORM and DTOs
"""

from typing import List, Optional
from app.models.ingredient import Ingredient
from app.dto.ingredient_dto import (
    IngredientCreateDto,
    IngredientUpdateDto,
    IngredientResponseDto,
    IngredientListResponseDto,
    IngredientDeleteResponseDto
)


class IngredientService:
    """Service for ingredient CRUD operations"""
    
    async def create(self, data: IngredientCreateDto) -> IngredientResponseDto:
        """Create a new ingredient"""
        ingredient = await Ingredient.create(**data.model_dump(exclude_unset=True))
        return IngredientResponseDto.model_validate(ingredient)
    
    async def get_by_id(self, ingredient_id: int) -> Optional[IngredientResponseDto]:
        """Get ingredient by ID"""
        ingredient = await Ingredient.get_or_none(id=ingredient_id)
        if ingredient:
            return IngredientResponseDto.model_validate(ingredient)
        return None
    
    async def get_by_restaurant(self, restaurant_id: int) -> IngredientListResponseDto:
        """Get all ingredients for a restaurant"""
        ingredients = await Ingredient.filter(restaurant_id=restaurant_id).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_allergens(self, restaurant_id: int) -> IngredientListResponseDto:
        """Get all allergen ingredients for a restaurant"""
        ingredients = await Ingredient.filter(restaurant_id=restaurant_id, is_allergen=True).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_non_allergens(self, restaurant_id: int) -> IngredientListResponseDto:
        """Get all non-allergen ingredients for a restaurant"""
        ingredients = await Ingredient.filter(restaurant_id=restaurant_id, is_allergen=False).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_optional_ingredients(self, restaurant_id: int) -> IngredientListResponseDto:
        """Get all optional ingredients for a restaurant"""
        ingredients = await Ingredient.filter(restaurant_id=restaurant_id, is_optional=True).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_required_ingredients(self, restaurant_id: int) -> IngredientListResponseDto:
        """Get all required ingredients for a restaurant"""
        ingredients = await Ingredient.filter(restaurant_id=restaurant_id, is_optional=False).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def search_by_name(self, restaurant_id: int, name: str) -> IngredientListResponseDto:
        """Search ingredients by name (case-insensitive)"""
        ingredients = await Ingredient.filter(
            restaurant_id=restaurant_id,
            name__icontains=name
        ).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_by_allergen_type(self, restaurant_id: int, allergen_type: str) -> IngredientListResponseDto:
        """Get ingredients by specific allergen type"""
        ingredients = await Ingredient.filter(
            restaurant_id=restaurant_id,
            is_allergen=True,
            allergen_type__icontains=allergen_type
        ).order_by('name').all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=restaurant_id
        )
    
    async def get_all(self) -> IngredientListResponseDto:
        """Get all ingredients"""
        ingredients = await Ingredient.all()
        ingredient_dtos = [IngredientResponseDto.model_validate(ingredient) for ingredient in ingredients]
        return IngredientListResponseDto(
            ingredients=ingredient_dtos,
            total_count=len(ingredient_dtos),
            restaurant_id=0  # Global method, no specific restaurant
        )
    
    async def update(self, ingredient_id: int, data: IngredientUpdateDto) -> Optional[IngredientResponseDto]:
        """Update ingredient by ID"""
        ingredient = await Ingredient.get_or_none(id=ingredient_id)
        if ingredient:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(ingredient, key, value)
            await ingredient.save()
            return IngredientResponseDto.model_validate(ingredient)
        return None
    
    async def delete(self, ingredient_id: int) -> IngredientDeleteResponseDto:
        """Delete ingredient by ID"""
        ingredient = await Ingredient.get_or_none(id=ingredient_id)
        if ingredient:
            await ingredient.delete()
            return IngredientDeleteResponseDto(
                success=True,
                message=f"Ingredient '{ingredient.name}' deleted successfully"
            )
        return IngredientDeleteResponseDto(
            success=False,
            message=f"Ingredient with ID {ingredient_id} not found"
        )
