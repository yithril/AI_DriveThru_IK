"""
Restaurants API Controller - CRUD operations for restaurants
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.restaurant_service import RestaurantService
from app.dto.restaurant_dto import (
    RestaurantCreateDto,
    RestaurantUpdateDto,
    RestaurantResponseDto,
    RestaurantListResponseDto,
    RestaurantDeleteResponseDto
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/restaurants", tags=["admin-restaurants"])


@router.post("/", response_model=RestaurantResponseDto, status_code=status.HTTP_201_CREATED)
@inject
async def create_restaurant(
    data: RestaurantCreateDto,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Create a new restaurant
    
    Args:
        data: Restaurant creation data
        restaurant_service: Injected restaurant service
        
    Returns:
        Created restaurant data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await restaurant_service.create(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create restaurant: {str(e)}"
        )


@router.get("/{restaurant_id}", response_model=RestaurantResponseDto)
@inject
async def get_restaurant(
    restaurant_id: int,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Get restaurant by ID
    
    Args:
        restaurant_id: Restaurant ID
        restaurant_service: Injected restaurant service
        
    Returns:
        Restaurant data
        
    Raises:
        HTTPException: If restaurant not found
    """
    try:
        result = await restaurant_service.get_by_id(restaurant_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve restaurant: {str(e)}"
        )


@router.get("/", response_model=RestaurantListResponseDto)
@inject
async def get_restaurants(
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Get all restaurants
    
    Args:
        restaurant_service: Injected restaurant service
        
    Returns:
        List of all restaurants
    """
    try:
        logger.info("Starting get_restaurants endpoint")
        logger.info(f"Restaurant service instance: {restaurant_service}")
        
        restaurants = await restaurant_service.get_all()
        logger.info(f"Successfully retrieved restaurants from service: {restaurants}")
        
        return restaurants
        
    except Exception as e:
        logger.error(f"Error in get_restaurants endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve restaurants: {str(e)}"
        )


@router.put("/{restaurant_id}", response_model=RestaurantResponseDto)
@inject
async def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdateDto,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Update restaurant by ID
    
    Args:
        restaurant_id: Restaurant ID
        data: Restaurant update data
        restaurant_service: Injected restaurant service
        
    Returns:
        Updated restaurant data
        
    Raises:
        HTTPException: If restaurant not found or update fails
    """
    try:
        result = await restaurant_service.update(restaurant_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update restaurant: {str(e)}"
        )


@router.delete("/{restaurant_id}", response_model=RestaurantDeleteResponseDto)
@inject
async def delete_restaurant(
    restaurant_id: int,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Delete restaurant by ID
    
    Args:
        restaurant_id: Restaurant ID
        restaurant_service: Injected restaurant service
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If restaurant not found or deletion fails
    """
    try:
        success = await restaurant_service.delete(restaurant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        return RestaurantDeleteResponseDto(
            success=True,
            message=f"Restaurant with ID {restaurant_id} deleted successfully",
            restaurant_id=restaurant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete restaurant: {str(e)}"
        )
