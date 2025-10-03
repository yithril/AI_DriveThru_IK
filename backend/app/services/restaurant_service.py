"""
Restaurant Service with CRUD operations using Tortoise ORM and DTOs
"""

import logging
from typing import List, Optional
from app.models.restaurant import Restaurant
from app.dto import (
    RestaurantCreateDto,
    RestaurantUpdateDto,
    RestaurantResponseDto,
    RestaurantListResponseDto,
    RestaurantDeleteResponseDto
)

logger = logging.getLogger(__name__)


class RestaurantService:
    """Service for restaurant CRUD operations"""
    
    async def create(self, data: RestaurantCreateDto) -> RestaurantResponseDto:
        """Create a new restaurant"""
        restaurant = await Restaurant.create(**data.model_dump(exclude_unset=True))
        return RestaurantResponseDto.model_validate(restaurant)
    
    async def get_by_id(self, restaurant_id: int) -> Optional[RestaurantResponseDto]:
        """Get restaurant by ID"""
        restaurant = await Restaurant.get_or_none(id=restaurant_id)
        if restaurant:
            return RestaurantResponseDto.model_validate(restaurant)
        return None
    
    async def get_all(self) -> RestaurantListResponseDto:
        """Get all restaurants"""
        try:
            logger.info("Starting get_all restaurants")
            restaurants = await Restaurant.all()
            logger.info(f"Found {len(restaurants)} restaurants in database")
            
            restaurant_dtos = []
            for restaurant in restaurants:
                try:
                    dto = RestaurantResponseDto.model_validate(restaurant)
                    restaurant_dtos.append(dto)
                    logger.debug(f"Successfully converted restaurant {restaurant.id} to DTO")
                except Exception as e:
                    logger.error(f"Failed to convert restaurant {restaurant.id} to DTO: {e}")
                    raise
            
            result = RestaurantListResponseDto(
                restaurants=restaurant_dtos,
                total_count=len(restaurant_dtos)
            )
            logger.info(f"Successfully created RestaurantListResponseDto with {len(restaurant_dtos)} restaurants")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_all restaurants: {e}", exc_info=True)
            raise
    
    async def update(self, restaurant_id: int, data: RestaurantUpdateDto) -> Optional[RestaurantResponseDto]:
        """Update restaurant by ID"""
        restaurant = await Restaurant.get_or_none(id=restaurant_id)
        if restaurant:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(restaurant, key, value)
            await restaurant.save()
            return RestaurantResponseDto.model_validate(restaurant)
        return None
    
    async def delete(self, restaurant_id: int) -> RestaurantDeleteResponseDto:
        """Delete restaurant by ID"""
        restaurant = await Restaurant.get_or_none(id=restaurant_id)
        if restaurant:
            await restaurant.delete()
            return RestaurantDeleteResponseDto(
                success=True,
                message=f"Restaurant '{restaurant.name}' deleted successfully"
            )
        return RestaurantDeleteResponseDto(
            success=False,
            message=f"Restaurant with ID {restaurant_id} not found"
        )
