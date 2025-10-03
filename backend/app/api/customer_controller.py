"""
Customer API Controller - Customer-facing endpoints for drive-thru interface
"""

from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.restaurant_service import RestaurantService
from app.services.menu_service import MenuService
from app.dto.restaurant_dto import RestaurantResponseDto
from app.dto.menu_item_dto import MenuItemListResponseDto
from app.dto.category_dto import CategoryListResponseDto

router = APIRouter(prefix="/api/restaurants", tags=["customer-restaurants"])


@router.get("/{restaurant_id}", response_model=RestaurantResponseDto)
@inject
async def get_restaurant(
    restaurant_id: int,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Get restaurant by ID for customer interface
    
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


@router.get("/{restaurant_id}/menu", response_model=dict)
@inject
async def get_restaurant_menu(
    restaurant_id: int,
    restaurant_service: RestaurantService = Depends(Provide[Container.restaurant_service])
):
    """
    Get complete menu for a restaurant (restaurant info + placeholder for menu)
    
    Args:
        restaurant_id: Restaurant ID
        restaurant_service: Injected restaurant service
        
    Returns:
        Restaurant data with menu placeholder
        
    Raises:
        HTTPException: If restaurant not found or menu retrieval fails
    """
    try:
        restaurant = await restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        
        # Get menu categories and items for the restaurant
        from app.models.category import Category
        from app.models.menu_item import MenuItem
        
        # Get categories
        categories = await Category.filter(restaurant_id=restaurant_id, is_active=True).order_by('display_order')
        
        # Get menu items
        menu_items = await MenuItem.filter(restaurant_id=restaurant_id, is_available=True).order_by('display_order')
        
        # Group menu items by category
        menu_categories = []
        for category in categories:
            category_items = [item for item in menu_items if item.category_id == category.id]
            if category_items:  # Only include categories that have items
                menu_categories.append({
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "items": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "description": item.description,
                            "price": item.price,
                            "image_url": item.image_url,
                            "is_upsell": item.is_upsell,
                            "is_special": item.is_special,
                            "prep_time_minutes": item.prep_time_minutes
                        }
                        for item in category_items
                    ]
                })
        
        return {
            "restaurant": restaurant,
            "menu": menu_categories
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve restaurant menu: {str(e)}"
        )
