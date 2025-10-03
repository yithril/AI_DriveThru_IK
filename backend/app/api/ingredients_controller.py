"""
Ingredients API Controller - CRUD operations for ingredients
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.ingredient_service import IngredientService
from app.dto.ingredient_dto import (
    IngredientCreateDto,
    IngredientUpdateDto,
    IngredientResponseDto,
    IngredientListResponseDto,
    IngredientDeleteResponseDto
)

router = APIRouter(prefix="/api/admin/ingredients", tags=["admin-ingredients"])


@router.post("/", response_model=IngredientResponseDto, status_code=status.HTTP_201_CREATED)
@inject
async def create_ingredient(
    data: IngredientCreateDto,
    ingredient_service: IngredientService = Depends(Provide[Container.ingredient_service])
):
    """
    Create a new ingredient
    
    Args:
        data: Ingredient creation data
        ingredient_service: Injected ingredient service
        
    Returns:
        Created ingredient data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await ingredient_service.create(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create ingredient: {str(e)}"
        )


@router.get("/{ingredient_id}", response_model=IngredientResponseDto)
@inject
async def get_ingredient(
    ingredient_id: int,
    ingredient_service: IngredientService = Depends(Provide[Container.ingredient_service])
):
    """
    Get ingredient by ID
    
    Args:
        ingredient_id: Ingredient ID
        ingredient_service: Injected ingredient service
        
    Returns:
        Ingredient data
        
    Raises:
        HTTPException: If ingredient not found
    """
    try:
        result = await ingredient_service.get_by_id(ingredient_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ingredient: {str(e)}"
        )


@router.get("/", response_model=IngredientListResponseDto)
@inject
async def get_ingredients(
    restaurant_id: int = Query(..., description="Restaurant ID to filter ingredients"),
    ingredient_service: IngredientService = Depends(Provide[Container.ingredient_service])
):
    """
    Get all ingredients for a restaurant
    
    Args:
        restaurant_id: Restaurant ID to filter ingredients
        ingredient_service: Injected ingredient service
        
    Returns:
        List of ingredients for the restaurant
    """
    try:
        ingredients = await ingredient_service.get_by_restaurant(restaurant_id)
        return IngredientListResponseDto(
            ingredients=ingredients,
            total_count=len(ingredients),
            restaurant_id=restaurant_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve ingredients: {str(e)}"
        )


@router.put("/{ingredient_id}", response_model=IngredientResponseDto)
@inject
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdateDto,
    ingredient_service: IngredientService = Depends(Provide[Container.ingredient_service])
):
    """
    Update ingredient by ID
    
    Args:
        ingredient_id: Ingredient ID
        data: Ingredient update data
        ingredient_service: Injected ingredient service
        
    Returns:
        Updated ingredient data
        
    Raises:
        HTTPException: If ingredient not found or update fails
    """
    try:
        result = await ingredient_service.update(ingredient_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update ingredient: {str(e)}"
        )


@router.delete("/{ingredient_id}", response_model=IngredientDeleteResponseDto)
@inject
async def delete_ingredient(
    ingredient_id: int,
    ingredient_service: IngredientService = Depends(Provide[Container.ingredient_service])
):
    """
    Delete ingredient by ID
    
    Args:
        ingredient_id: Ingredient ID
        ingredient_service: Injected ingredient service
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If ingredient not found or deletion fails
    """
    try:
        success = await ingredient_service.delete(ingredient_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with ID {ingredient_id} not found"
            )
        return IngredientDeleteResponseDto(
            success=True,
            message=f"Ingredient with ID {ingredient_id} deleted successfully",
            ingredient_id=ingredient_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete ingredient: {str(e)}"
        )
