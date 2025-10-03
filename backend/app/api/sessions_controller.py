"""
Sessions API Controller - Drive-thru session management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel

from app.core.container import Container
from app.services.session_service import SessionService
from app.services.order_session_service import OrderSessionService
from app.constants.audio_phrases import AudioPhraseType


class CreateSessionRequest(BaseModel):
    restaurant_id: int

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("/current")
@inject
async def get_current_session(
    session_service: SessionService = Depends(Provide[Container.session_service])
):
    """
    Get current active session
    
    Returns:
        Current session data or null if no active session
    """
    try:
        session = await session_service.get_current_session()
        if session:
            return {
                "success": True,
                "data": {
                    "session": session
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "session": None
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current session: {str(e)}"
        )


@router.post("/new-car")
@inject
async def create_new_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(Provide[Container.session_service]),
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
):
    """
    Create a new drive-thru session (simulate car arriving)
    
    Args:
        request: Request containing restaurant_id
        
    Returns:
        New session data with conversation history, command history, and linked order
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        restaurant_id = request.restaurant_id
        logger.info(f"Creating new session for restaurant {restaurant_id}")
        
        # Create session using the proper service method
        session_id = await session_service.create_session(restaurant_id)
        
        if not session_id:
            logger.error("Failed to create session")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        # Create order for the session
        order_id = await order_session_service.create_order(session_id, restaurant_id)
        
        if not order_id:
            # Clean up session if order creation failed
            await session_service.delete_session(session_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order for session"
            )
        
        # Link order to session
        await session_service.link_order_to_session(session_id, order_id)
        
        # Generate greeting audio with restaurant name
        from app.services.voice.voice_service import VoiceService
        from app.core.container import Container
        from app.services.restaurant_service import RestaurantService
        
        # Get restaurant name for greeting
        restaurant_service = Container().restaurant_service()
        restaurant = await restaurant_service.get_by_id(restaurant_id)
        restaurant_name = restaurant.name if restaurant else "our restaurant"
        
        # Generate greeting audio
        voice_service = Container().voice_service()
        greeting_audio_url = await voice_service.generate_from_phrase_type(
            phrase_type=AudioPhraseType.GREETING,
            restaurant_id=restaurant_id,
            restaurant_name=restaurant_name
        )
        
        logger.info(f"Generated greeting audio URL: {greeting_audio_url}")
        
        # Get the complete session data
        session_data = await session_service.get_session(session_id)
        order_data = await order_session_service.get_order(order_id)
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "session": session_data,
                "order": order_data,
                "greeting_audio_url": greeting_audio_url
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in create_new_session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new session: {str(e)}"
        )


@router.post("/next-car")
@inject
async def clear_current_session(
    session_service: SessionService = Depends(Provide[Container.session_service])
):
    """
    Clear current session (simulate car leaving)
    
    Returns:
        Success message
    """
    try:
        await session_service.clear_current_session()
        
        return {
            "success": True,
            "message": "Session cleared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )


@router.get("/current-order")
@inject
async def get_current_order(
    session_service: SessionService = Depends(Provide[Container.session_service]),
    order_session_service: OrderSessionService = Depends(Provide[Container.order_session_service])
):
    """
    Get current order for active session
    
    Returns:
        Current order data
    """
    try:
        session = await session_service.get_current_session()
        if session and session.get("order_id"):
            order = await order_session_service.get_order(session["order_id"])
            return {
                "success": True,
                "data": {
                    "order": order
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "order": None
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current order: {str(e)}"
        )

@router.get("/performance-logs")
@inject
async def get_performance_logs(
    session_service: SessionService = Depends(Provide[Container.session_service])
):
    """
    Get performance logs for current session
    
    Returns:
        Performance timing data for debugging
    """
    try:
        session = await session_service.get_current_session()
        if not session:
            return {
                "success": True,
                "data": {
                    "performance_logs": [],
                    "message": "No active session"
                }
            }
        
        session_id = session.get("session_id")
        if not session_id:
            return {
                "success": True,
                "data": {
                    "performance_logs": [],
                    "message": "No session ID found"
                }
            }
        
        performance_logs = await session_service.get_performance_logs(session_id)
        
        # Calculate summary statistics
        if performance_logs:
            total_time = sum(log["duration_ms"] for log in performance_logs)
            step_summary = {}
            for log in performance_logs:
                step_name = log["step_name"]
                if step_name not in step_summary:
                    step_summary[step_name] = {"count": 0, "total_ms": 0, "avg_ms": 0}
                step_summary[step_name]["count"] += 1
                step_summary[step_name]["total_ms"] += log["duration_ms"]
                step_summary[step_name]["avg_ms"] = step_summary[step_name]["total_ms"] / step_summary[step_name]["count"]
        else:
            total_time = 0
            step_summary = {}
        
        return {
            "success": True,
            "data": {
                "performance_logs": performance_logs,
                "summary": {
                    "total_processing_time_ms": total_time,
                    "step_summary": step_summary
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance logs: {str(e)}"
        )
