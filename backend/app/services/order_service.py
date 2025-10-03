"""
Order Service with CRUD operations using Tortoise ORM and DTOs
"""

from typing import List, Optional
from decimal import Decimal
from app.models.order import Order, OrderStatus
from app.dto.order_dto import (
    OrderCreateDto,
    OrderUpdateDto,
    OrderResponseDto,
    OrderListResponseDto,
    OrderDeleteResponseDto,
    OrderStatusUpdateDto
)


class OrderService:
    """Service for order CRUD operations"""
    
    async def create(self, data: OrderCreateDto) -> OrderResponseDto:
        """Create a new order"""
        order = await Order.create(**data.model_dump())
        return OrderResponseDto.model_validate(order)
    
    async def get_by_id(self, order_id: int) -> Optional[OrderResponseDto]:
        """Get order by ID"""
        order = await Order.get_or_none(id=order_id)
        if order:
            return OrderResponseDto.model_validate(order)
        return None
    
    async def get_by_restaurant(self, restaurant_id: int) -> OrderListResponseDto:
        """Get all orders for a restaurant"""
        orders = await Order.filter(restaurant_id=restaurant_id).order_by('-created_at').all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_by_status(self, restaurant_id: int, status: OrderStatus) -> OrderListResponseDto:
        """Get orders by status for a restaurant"""
        orders = await Order.filter(restaurant_id=restaurant_id, status=status).order_by('-created_at').all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_pending_orders(self, restaurant_id: int) -> OrderListResponseDto:
        """Get pending orders for a restaurant (PENDING and CONFIRMED status)"""
        orders = await Order.filter(
            restaurant_id=restaurant_id,
            status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED]
        ).order_by('created_at').all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_by_user(self, user_id: int) -> OrderListResponseDto:
        """Get all orders for a user"""
        orders = await Order.filter(user_id=user_id).order_by('-created_at').all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_by_customer_phone(self, phone: str) -> OrderListResponseDto:
        """Get orders by customer phone number"""
        orders = await Order.filter(customer_phone=phone).order_by('-created_at').all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_today_orders(self, restaurant_id: int) -> OrderListResponseDto:
        """Get today's orders for a restaurant"""
        from datetime import datetime, date
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        orders = await Order.filter(
            restaurant_id=restaurant_id,
            created_at__gte=today_start,
            created_at__lte=today_end
        ).order_by('-created_at').all()
        
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def get_all(self) -> OrderListResponseDto:
        """Get all orders"""
        orders = await Order.all()
        order_dtos = [OrderResponseDto.model_validate(order) for order in orders]
        return OrderListResponseDto(
            orders=order_dtos,
            total=len(order_dtos)
        )
    
    async def update(self, order_id: int, data: OrderUpdateDto) -> Optional[OrderResponseDto]:
        """Update order by ID"""
        order = await Order.get_or_none(id=order_id)
        if order:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(order, key, value)
            await order.save()
            return OrderResponseDto.model_validate(order)
        return None
    
    async def update_status(self, order_id: int, data: OrderStatusUpdateDto) -> Optional[OrderResponseDto]:
        """Update order status"""
        order = await Order.get_or_none(id=order_id)
        if order:
            order.status = data.status
            await order.save()
            return OrderResponseDto.model_validate(order)
        return None
    
    async def calculate_totals(self, order_id: int) -> Optional[OrderResponseDto]:
        """Calculate and update order totals"""
        order = await Order.get_or_none(id=order_id)
        if order:
            await order.calculate_totals()
            return OrderResponseDto.model_validate(order)
        return None
    
    async def delete(self, order_id: int) -> OrderDeleteResponseDto:
        """Delete order by ID"""
        order = await Order.get_or_none(id=order_id)
        if order:
            await order.delete()
            return OrderDeleteResponseDto(
                success=True,
                message=f"Order #{order.id} deleted successfully"
            )
        return OrderDeleteResponseDto(
            success=False,
            message=f"Order with ID {order_id} not found"
        )
