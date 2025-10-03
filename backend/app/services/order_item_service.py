"""
Order Item Service with CRUD operations using Tortoise ORM and DTOs
"""

from typing import List, Optional
from decimal import Decimal
from app.models.order_item import OrderItem
from app.dto.order_item_dto import (
    OrderItemCreateDto,
    OrderItemUpdateDto,
    OrderItemResponseDto,
    OrderItemListResponseDto,
    OrderItemDeleteResponseDto
)


class OrderItemService:
    """Service for order item CRUD operations"""
    
    async def create(self, data: OrderItemCreateDto) -> OrderItemResponseDto:
        """Create a new order item"""
        # Calculate total price
        total_price = data.quantity * data.unit_price
        
        order_item = await OrderItem.create(
            order_id=data.order_id,
            menu_item_id=data.menu_item_id,
            quantity=data.quantity,
            unit_price=data.unit_price,
            total_price=total_price,
            special_instructions=data.special_instructions
        )
        
        return OrderItemResponseDto.model_validate(order_item)
    
    async def get_by_id(self, order_item_id: int) -> Optional[OrderItemResponseDto]:
        """Get order item by ID"""
        order_item = await OrderItem.get_or_none(id=order_item_id)
        if order_item:
            return OrderItemResponseDto.model_validate(order_item)
        return None
    
    async def get_by_order(self, order_id: int) -> OrderItemListResponseDto:
        """Get all order items for an order"""
        order_items = await OrderItem.filter(order_id=order_id).order_by('created_at').all()
        order_item_dtos = [OrderItemResponseDto.model_validate(item) for item in order_items]
        return OrderItemListResponseDto(
            order_items=order_item_dtos,
            total=len(order_item_dtos)
        )
    
    async def get_by_menu_item(self, menu_item_id: int) -> OrderItemListResponseDto:
        """Get all order items for a specific menu item"""
        order_items = await OrderItem.filter(menu_item_id=menu_item_id).order_by('-created_at').all()
        order_item_dtos = [OrderItemResponseDto.model_validate(item) for item in order_items]
        return OrderItemListResponseDto(
            order_items=order_item_dtos,
            total=len(order_item_dtos)
        )
    
    async def get_by_order_and_menu_item(self, order_id: int, menu_item_id: int) -> Optional[OrderItemResponseDto]:
        """Get specific order item by order and menu item"""
        order_item = await OrderItem.get_or_none(order_id=order_id, menu_item_id=menu_item_id)
        if order_item:
            return OrderItemResponseDto.model_validate(order_item)
        return None
    
    async def get_all(self) -> OrderItemListResponseDto:
        """Get all order items"""
        order_items = await OrderItem.all()
        order_item_dtos = [OrderItemResponseDto.model_validate(item) for item in order_items]
        return OrderItemListResponseDto(
            order_items=order_item_dtos,
            total=len(order_item_dtos)
        )
    
    async def update(self, order_item_id: int, data: OrderItemUpdateDto) -> Optional[OrderItemResponseDto]:
        """Update order item by ID"""
        order_item = await OrderItem.get_or_none(id=order_item_id)
        if order_item:
            update_data = data.model_dump(exclude_unset=True)
            
            # Update fields
            for key, value in update_data.items():
                setattr(order_item, key, value)
            
            # Recalculate total price if quantity or unit_price changed
            if 'quantity' in update_data or 'unit_price' in update_data:
                order_item.total_price = order_item.quantity * order_item.unit_price
            
            await order_item.save()
            return OrderItemResponseDto.model_validate(order_item)
        return None
    
    async def update_quantity(self, order_item_id: int, quantity: int) -> Optional[OrderItemResponseDto]:
        """Update order item quantity and recalculate total"""
        order_item = await OrderItem.get_or_none(id=order_item_id)
        if order_item:
            order_item.quantity = quantity
            order_item.total_price = order_item.quantity * order_item.unit_price
            await order_item.save()
            return OrderItemResponseDto.model_validate(order_item)
        return None
    
    async def delete(self, order_item_id: int) -> OrderItemDeleteResponseDto:
        """Delete order item by ID"""
        order_item = await OrderItem.get_or_none(id=order_item_id)
        if order_item:
            await order_item.delete()
            return OrderItemDeleteResponseDto(
                success=True,
                message=f"Order item deleted successfully"
            )
        return OrderItemDeleteResponseDto(
            success=False,
            message=f"Order item with ID {order_item_id} not found"
        )
    
    async def delete_by_order(self, order_id: int) -> OrderItemDeleteResponseDto:
        """Delete all order items for an order"""
        order_items = await OrderItem.filter(order_id=order_id).all()
        if order_items:
            for order_item in order_items:
                await order_item.delete()
            return OrderItemDeleteResponseDto(
                success=True,
                message=f"All order items for order #{order_id} deleted successfully"
            )
        return OrderItemDeleteResponseDto(
            success=False,
            message=f"No order items found for order {order_id}"
        )
