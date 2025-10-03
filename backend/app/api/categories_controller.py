"""
Categories API Controller - CRUD operations for categories
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.category_service import CategoryService
from app.dto.category_dto import (
    CategoryCreateDto,
    CategoryUpdateDto,
    CategoryResponseDto,
    CategoryListResponseDto,
    CategoryDeleteResponseDto
)

router = APIRouter(prefix="/api/admin/categories", tags=["admin-categories"])


@router.post("/", response_model=CategoryResponseDto, status_code=status.HTTP_201_CREATED)
@inject
async def create_category(
    data: CategoryCreateDto,
    category_service: CategoryService = Depends(Provide[Container.category_service])
):
    """
    Create a new category
    
    Args:
        data: Category creation data
        category_service: Injected category service
        
    Returns:
        Created category data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await category_service.create(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get("/{category_id}", response_model=CategoryResponseDto)
@inject
async def get_category(
    category_id: int,
    category_service: CategoryService = Depends(Provide[Container.category_service])
):
    """
    Get category by ID
    
    Args:
        category_id: Category ID
        category_service: Injected category service
        
    Returns:
        Category data
        
    Raises:
        HTTPException: If category not found
    """
    try:
        result = await category_service.get_by_id(category_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve category: {str(e)}"
        )


@router.get("/", response_model=CategoryListResponseDto)
@inject
async def get_categories(
    restaurant_id: int = Query(..., description="Restaurant ID to filter categories"),
    category_service: CategoryService = Depends(Provide[Container.category_service])
):
    """
    Get all categories for a restaurant
    
    Args:
        restaurant_id: Restaurant ID to filter categories
        category_service: Injected category service
        
    Returns:
        List of categories for the restaurant
    """
    try:
        categories = await category_service.get_by_restaurant(restaurant_id)
        return CategoryListResponseDto(
            categories=categories,
            total_count=len(categories),
            restaurant_id=restaurant_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.put("/{category_id}", response_model=CategoryResponseDto)
@inject
async def update_category(
    category_id: int,
    data: CategoryUpdateDto,
    category_service: CategoryService = Depends(Provide[Container.category_service])
):
    """
    Update category by ID
    
    Args:
        category_id: Category ID
        data: Category update data
        category_service: Injected category service
        
    Returns:
        Updated category data
        
    Raises:
        HTTPException: If category not found or update fails
    """
    try:
        result = await category_service.update(category_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update category: {str(e)}"
        )


@router.delete("/{category_id}", response_model=CategoryDeleteResponseDto)
@inject
async def delete_category(
    category_id: int,
    category_service: CategoryService = Depends(Provide[Container.category_service])
):
    """
    Delete category by ID
    
    Args:
        category_id: Category ID
        category_service: Injected category service
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If category not found or deletion fails
    """
    try:
        success = await category_service.delete(category_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with ID {category_id} not found"
            )
        return CategoryDeleteResponseDto(
            success=True,
            message=f"Category with ID {category_id} deleted successfully",
            category_id=category_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete category: {str(e)}"
        )
