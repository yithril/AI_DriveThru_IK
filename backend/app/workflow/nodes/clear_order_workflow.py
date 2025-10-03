"""
Clear Order Workflow - Handles clearing all items from the current order.

Simple workflow that clears the order items and provides feedback to the customer.
"""

import logging
from typing import Dict, Any, Optional, List
from app.services.order_session_service import OrderSessionService
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class ClearOrderWorkflowResult(WorkflowResult):
    """Result specifically for clear order workflows"""
    
    def __init__(self, success: bool, message: str, **kwargs):
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.CLEAR_ORDER,
            **kwargs
        )


class ClearOrderWorkflow:
    """
    Workflow for clearing all items from the current order.
    
    This is a simple workflow that:
    1. Gets the current order from the session
    2. Clears all items from the order
    3. Returns success confirmation
    """
    
    def __init__(self, order_session_service: OrderSessionService):
        self.order_session_service = order_session_service
    
    async def execute(
        self, 
        session_id: str,
        conversation_history: Optional[ConversationHistory] = None
    ) -> ClearOrderWorkflowResult:
        """
        Execute the clear order workflow.
        
        Args:
            session_id: The customer's session ID
            conversation_history: Recent conversation turns (optional)
            
        Returns:
            ClearOrderWorkflowResult with the operation result
        """
        try:
            logger.info(f"Clearing order for session: {session_id}")
            
            # Get the current order from the session
            current_order = await self.order_session_service.get_session_order(session_id)
            if not current_order:
                return ClearOrderWorkflowResult(
                    success=False,
                    message="No active order found to clear.",
                    audio_phrase_type=AudioPhraseType.NO_ORDER_YET
                )
            
            # Check if order already has items
            items = current_order.get("items", [])
            if not items:
                return ClearOrderWorkflowResult(
                    success=False,
                    message="Your order is already empty.",
                    audio_phrase_type=AudioPhraseType.ORDER_ALREADY_EMPTY
                )
            
            # Clear the order items
            order_id = current_order.get("id")
            if not order_id:
                return ClearOrderWorkflowResult(
                    success=False,
                    message="Order ID not found. Please try again.",
                    audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
                )
            
            success = await self.order_session_service.clear_order(order_id)
            
            if success:
                return ClearOrderWorkflowResult(
                    success=True,
                    message="Your order has been cleared. Would you like to start over?",
                    order_updated=True,
                    audio_phrase_type=AudioPhraseType.ORDER_CLEARED_SUCCESS
                )
            else:
                return ClearOrderWorkflowResult(
                    success=False,
                    message="Sorry, I couldn't clear your order. Please try again.",
                    audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
                )
                
        except Exception as e:
            logger.error(f"Clear order workflow failed: {e}", exc_info=True)
            return ClearOrderWorkflowResult(
                success=False,
                message="Sorry, I couldn't clear your order. Please try again.",
                error=str(e),
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
