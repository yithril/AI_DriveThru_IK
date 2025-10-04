"""
Orders API Controller - Order summary endpoints with embedded order items
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.order_service import OrderService
from app.dto.order_dto import (
    OrderSummaryDto,
    OrderSummaryListResponseDto
)
from app.models.order import OrderStatus

router = APIRouter(prefix="/api/admin/orders", tags=["admin-orders"])


@router.get("/", response_model=OrderSummaryListResponseDto)
@inject
async def get_all_order_summaries(
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Get all order summaries with embedded order items
    
    Returns:
        List of all orders with resolved menu item names and order items
    """
    try:
        return await order_service.get_all_order_summaries()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order summaries: {str(e)}"
        )


@router.get("/{order_id}", response_model=OrderSummaryDto)
@inject
async def get_order_summary(
    order_id: int,
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Get order summary by ID with embedded order items
    
    Args:
        order_id: Order ID
        
    Returns:
        Order summary with resolved menu item names and order items
        
    Raises:
        HTTPException: If order not found
    """
    try:
        order_summary = await order_service.get_order_summary_by_id(order_id)
        if not order_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found"
            )
        return order_summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order summary: {str(e)}"
        )


@router.get("/restaurant/{restaurant_id}", response_model=OrderSummaryListResponseDto)
@inject
async def get_order_summaries_by_restaurant(
    restaurant_id: int,
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Get order summaries for a specific restaurant
    
    Args:
        restaurant_id: Restaurant ID
        
    Returns:
        List of order summaries for the restaurant
    """
    try:
        return await order_service.get_order_summaries_by_restaurant(restaurant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order summaries for restaurant: {str(e)}"
        )


@router.get("/status/{status}", response_model=OrderSummaryListResponseDto)
@inject
async def get_order_summaries_by_status(
    status: OrderStatus,
    restaurant_id: int = Query(..., description="Restaurant ID to filter orders"),
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Get order summaries by status for a restaurant
    
    Args:
        status: Order status (pending, confirmed, preparing, ready, completed, cancelled)
        restaurant_id: Restaurant ID to filter orders
        
    Returns:
        List of order summaries with the specified status
    """
    try:
        return await order_service.get_order_summaries_by_status(restaurant_id, status)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order summaries by status: {str(e)}"
        )


@router.get("/today", response_model=OrderSummaryListResponseDto)
@inject
async def get_today_order_summaries(
    restaurant_id: int = Query(..., description="Restaurant ID to filter orders"),
    order_service: OrderService = Depends(Provide[Container.order_service])
):
    """
    Get today's order summaries for a restaurant
    
    Args:
        restaurant_id: Restaurant ID to filter orders
        
    Returns:
        List of today's order summaries
    """
    try:
        return await order_service.get_today_order_summaries(restaurant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve today's order summaries: {str(e)}"
        )
