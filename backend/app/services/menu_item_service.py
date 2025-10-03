"""
Menu Item Service with CRUD operations using Tortoise ORM and DTOs
"""

from typing import List, Optional
from app.models.menu_item import MenuItem
from app.dto.menu_item_dto import (
    MenuItemCreateDto,
    MenuItemUpdateDto,
    MenuItemResponseDto,
    MenuItemListResponseDto,
    MenuItemDeleteResponseDto
)


class MenuItemService:
    """Service for menu item CRUD operations"""
    
    async def create(self, data: MenuItemCreateDto) -> MenuItemResponseDto:
        """Create a new menu item"""
        menu_item = await MenuItem.create(**data.model_dump(exclude_unset=True))
        return MenuItemResponseDto.model_validate(menu_item)
    
    async def get_by_id(self, menu_item_id: int) -> Optional[MenuItemResponseDto]:
        """Get menu item by ID"""
        menu_item = await MenuItem.get_or_none(id=menu_item_id)
        if menu_item:
            return MenuItemResponseDto.model_validate(menu_item)
        return None
    
    async def get_by_restaurant(self, restaurant_id: int) -> MenuItemListResponseDto:
        """Get all menu items for a restaurant"""
        menu_items = await MenuItem.filter(restaurant_id=restaurant_id).order_by('display_order').all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def get_by_category(self, category_id: int) -> MenuItemListResponseDto:
        """Get all menu items in a category"""
        menu_items = await MenuItem.filter(category_id=category_id).order_by('display_order').all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def get_available_by_restaurant(self, restaurant_id: int) -> MenuItemListResponseDto:
        """Get all available menu items for a restaurant"""
        menu_items = await MenuItem.filter(restaurant_id=restaurant_id, is_available=True).order_by('display_order').all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def get_special_items(self, restaurant_id: int) -> MenuItemListResponseDto:
        """Get special/featured items for a restaurant"""
        menu_items = await MenuItem.filter(restaurant_id=restaurant_id, is_special=True, is_available=True).all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def get_upsell_items(self, restaurant_id: int) -> MenuItemListResponseDto:
        """Get upsell items for a restaurant"""
        menu_items = await MenuItem.filter(restaurant_id=restaurant_id, is_upsell=True, is_available=True).all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def get_all(self) -> MenuItemListResponseDto:
        """Get all menu items"""
        menu_items = await MenuItem.all()
        menu_item_dtos = [MenuItemResponseDto.model_validate(item) for item in menu_items]
        return MenuItemListResponseDto(
            menu_items=menu_item_dtos,
            total=len(menu_item_dtos)
        )
    
    async def update(self, menu_item_id: int, data: MenuItemUpdateDto) -> Optional[MenuItemResponseDto]:
        """Update menu item by ID"""
        menu_item = await MenuItem.get_or_none(id=menu_item_id)
        if menu_item:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(menu_item, key, value)
            await menu_item.save()
            return MenuItemResponseDto.model_validate(menu_item)
        return None
    
    async def delete(self, menu_item_id: int) -> MenuItemDeleteResponseDto:
        """Delete menu item by ID"""
        menu_item = await MenuItem.get_or_none(id=menu_item_id)
        if menu_item:
            await menu_item.delete()
            return MenuItemDeleteResponseDto(
                success=True,
                message=f"Menu item '{menu_item.name}' deleted successfully"
            )
        return MenuItemDeleteResponseDto(
            success=False,
            message=f"Menu item with ID {menu_item_id} not found"
        )
