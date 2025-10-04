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
    OrderStatusUpdateDto,
    OrderSummaryDto,
    OrderSummaryListResponseDto,
    OrderItemSummaryDto
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
    
    # Order Summary Methods - New functionality for combined order + order items display
    
    async def _resolve_order_items_with_menu_names(self, order_items) -> List[OrderItemSummaryDto]:
        """Helper method to resolve order items with menu item names"""
        from app.models.menu_item import MenuItem
        
        resolved_items = []
        for item in order_items:
            # Get menu item name
            menu_item = await MenuItem.get_or_none(id=item.menu_item_id)
            menu_item_name = menu_item.name if menu_item else f"Unknown Item (ID: {item.menu_item_id})"
            
            # Handle size safely
            size_value = "regular"
            if hasattr(item, 'size') and item.size:
                if hasattr(item.size, 'value'):
                    size_value = item.size.value
                else:
                    size_value = str(item.size)
            
            resolved_item = OrderItemSummaryDto(
                id=item.id,
                menu_item_name=menu_item_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                size=size_value,
                special_instructions=item.special_instructions,
                created_at=item.created_at
            )
            resolved_items.append(resolved_item)
        
        return resolved_items
    
    async def get_order_summary_by_id(self, order_id: int) -> Optional[OrderSummaryDto]:
        """Get order summary by ID with resolved order items"""
        order = await Order.get_or_none(id=order_id)
        if not order:
            return None
        
        # Get order items
        order_items = await order.order_items.all()
        resolved_items = await self._resolve_order_items_with_menu_names(order_items)
        
        return OrderSummaryDto(
            id=order.id,
            restaurant_id=order.restaurant_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            special_instructions=order.special_instructions,
            created_at=order.created_at,
            updated_at=order.updated_at,
            order_items=resolved_items
        )
    
    async def get_order_summaries_by_restaurant(self, restaurant_id: int) -> OrderSummaryListResponseDto:
        """Get order summaries for a restaurant with resolved order items"""
        orders = await Order.filter(restaurant_id=restaurant_id).order_by('-created_at').all()
        
        order_summaries = []
        for order in orders:
            # Get order items for this order
            order_items = await order.order_items.all()
            resolved_items = await self._resolve_order_items_with_menu_names(order_items)
            
            summary = OrderSummaryDto(
                id=order.id,
                restaurant_id=order.restaurant_id,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                total_amount=order.total_amount,
                special_instructions=order.special_instructions,
                created_at=order.created_at,
                updated_at=order.updated_at,
                order_items=resolved_items
            )
            order_summaries.append(summary)
        
        return OrderSummaryListResponseDto(
            orders=order_summaries,
            total=len(order_summaries)
        )
    
    async def get_order_summaries_by_status(self, restaurant_id: int, status: OrderStatus) -> OrderSummaryListResponseDto:
        """Get order summaries by status for a restaurant"""
        orders = await Order.filter(restaurant_id=restaurant_id, status=status).order_by('-created_at').all()
        
        order_summaries = []
        for order in orders:
            order_items = await order.order_items.all()
            resolved_items = await self._resolve_order_items_with_menu_names(order_items)
            
            summary = OrderSummaryDto(
                id=order.id,
                restaurant_id=order.restaurant_id,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                total_amount=order.total_amount,
                special_instructions=order.special_instructions,
                created_at=order.created_at,
                updated_at=order.updated_at,
                order_items=resolved_items
            )
            order_summaries.append(summary)
        
        return OrderSummaryListResponseDto(
            orders=order_summaries,
            total=len(order_summaries)
        )
    
    async def get_today_order_summaries(self, restaurant_id: int) -> OrderSummaryListResponseDto:
        """Get today's order summaries for a restaurant"""
        from datetime import datetime, date
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        orders = await Order.filter(
            restaurant_id=restaurant_id,
            created_at__gte=today_start,
            created_at__lte=today_end
        ).order_by('-created_at').all()
        
        order_summaries = []
        for order in orders:
            order_items = await order.order_items.all()
            resolved_items = await self._resolve_order_items_with_menu_names(order_items)
            
            summary = OrderSummaryDto(
                id=order.id,
                restaurant_id=order.restaurant_id,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                total_amount=order.total_amount,
                special_instructions=order.special_instructions,
                created_at=order.created_at,
                updated_at=order.updated_at,
                order_items=resolved_items
            )
            order_summaries.append(summary)
        
        return OrderSummaryListResponseDto(
            orders=order_summaries,
            total=len(order_summaries)
        )
    
    async def get_all_order_summaries(self) -> OrderSummaryListResponseDto:
        """Get all order summaries"""
        orders = await Order.all().order_by('-created_at')
        
        order_summaries = []
        for order in orders:
            order_items = await order.order_items.all()
            resolved_items = await self._resolve_order_items_with_menu_names(order_items)
            
            summary = OrderSummaryDto(
                id=order.id,
                restaurant_id=order.restaurant_id,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                total_amount=order.total_amount,
                special_instructions=order.special_instructions,
                created_at=order.created_at,
                updated_at=order.updated_at,
                order_items=resolved_items
            )
            order_summaries.append(summary)
        
        return OrderSummaryListResponseDto(
            orders=order_summaries,
            total=len(order_summaries)
        )
