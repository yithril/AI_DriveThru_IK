"""
Menu Items API Controller - CRUD operations for menu items
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.menu_item_service import MenuItemService
from app.dto.menu_item_dto import (
    MenuItemCreateDto,
    MenuItemUpdateDto,
    MenuItemResponseDto,
    MenuItemListResponseDto,
    MenuItemDeleteResponseDto
)

router = APIRouter(prefix="/api/admin/menu-items", tags=["admin-menu-items"])


@router.post("/", response_model=MenuItemResponseDto, status_code=status.HTTP_201_CREATED)
@inject
async def create_menu_item(
    data: MenuItemCreateDto,
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Create a new menu item
    
    Args:
        data: Menu item creation data
        menu_item_service: Injected menu item service
        
    Returns:
        Created menu item data
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        result = await menu_item_service.create(data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create menu item: {str(e)}"
        )


@router.get("/{menu_item_id}", response_model=MenuItemResponseDto)
@inject
async def get_menu_item(
    menu_item_id: int,
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Get menu item by ID
    
    Args:
        menu_item_id: Menu item ID
        menu_item_service: Injected menu item service
        
    Returns:
        Menu item data
        
    Raises:
        HTTPException: If menu item not found
    """
    try:
        result = await menu_item_service.get_by_id(menu_item_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item with ID {menu_item_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menu item: {str(e)}"
        )


@router.get("/", response_model=MenuItemListResponseDto)
@inject
async def get_menu_items(
    restaurant_id: int = Query(..., description="Restaurant ID to filter menu items"),
    category_id: Optional[int] = Query(None, description="Optional category ID to filter menu items"),
    available_only: Optional[bool] = Query(None, description="Filter only available items"),
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Get menu items for a restaurant
    
    Args:
        restaurant_id: Restaurant ID to filter menu items
        category_id: Optional category ID to filter menu items
        menu_item_service: Injected menu item service
        
    Returns:
        List of menu items for the restaurant
    """
    try:
        if category_id:
            menu_items = await menu_item_service.get_by_category(category_id)
        else:
            menu_items = await menu_item_service.get_by_restaurant(restaurant_id)
            
        return MenuItemListResponseDto(
            menu_items=menu_items,
            total_count=len(menu_items),
            restaurant_id=restaurant_id,
            category_id=category_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menu items: {str(e)}"
        )


@router.get("/restaurant/{restaurant_id}/category/{category_id}", response_model=MenuItemListResponseDto)
@inject
async def get_menu_items_by_category(
    restaurant_id: int,
    category_id: int,
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Get menu items for a specific restaurant and category
    
    Args:
        restaurant_id: Restaurant ID
        category_id: Category ID
        menu_item_service: Injected menu item service
        
    Returns:
        List of menu items for the restaurant and category
    """
    try:
        menu_items = await menu_item_service.get_by_category(category_id)
        
        # Filter by restaurant as well (additional safety check)
        restaurant_menu_items = [
            item for item in menu_items 
            if item.restaurant_id == restaurant_id
        ]
        
        return MenuItemListResponseDto(
            menu_items=restaurant_menu_items,
            total_count=len(restaurant_menu_items),
            restaurant_id=restaurant_id,
            category_id=category_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve menu items: {str(e)}"
        )


@router.put("/{menu_item_id}", response_model=MenuItemResponseDto)
@inject
async def update_menu_item(
    menu_item_id: int,
    data: MenuItemUpdateDto,
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Update menu item by ID
    
    Args:
        menu_item_id: Menu item ID
        data: Menu item update data
        menu_item_service: Injected menu item service
        
    Returns:
        Updated menu item data
        
    Raises:
        HTTPException: If menu item not found or update fails
    """
    try:
        result = await menu_item_service.update(menu_item_id, data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item with ID {menu_item_id} not found"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update menu item: {str(e)}"
        )


@router.delete("/{menu_item_id}", response_model=MenuItemDeleteResponseDto)
@inject
async def delete_menu_item(
    menu_item_id: int,
    menu_item_service: MenuItemService = Depends(Provide[Container.menu_item_service])
):
    """
    Delete menu item by ID
    
    Args:
        menu_item_id: Menu item ID
        menu_item_service: Injected menu item service
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If menu item not found or deletion fails
    """
    try:
        success = await menu_item_service.delete(menu_item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu item with ID {menu_item_id} not found"
            )
        return MenuItemDeleteResponseDto(
            success=True,
            message=f"Menu item with ID {menu_item_id} deleted successfully",
            menu_item_id=menu_item_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete menu item: {str(e)}"
        )
