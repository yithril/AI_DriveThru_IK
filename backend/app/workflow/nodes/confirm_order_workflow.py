"""
Confirm Order Workflow - Handles order confirmation and completion.

When customer confirms their order, this workflow:
1. Validates the order exists and has items
2. Calculates the final total
3. Archives the order to PostgreSQL
4. Marks the session as complete
5. Tells customer to proceed to next window
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from app.services.order_session_service import OrderSessionService
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


class ConfirmOrderWorkflowResult(WorkflowResult):
    """Result specifically for confirm order workflows"""
    
    def __init__(self, success: bool, message: str, **kwargs):
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.CONFIRM_ORDER,
            **kwargs
        )


class ConfirmOrderWorkflow:
    """
    Workflow for confirming and completing orders.
    
    This workflow:
    1. Gets the current order from the session
    2. Validates the order has items
    3. Archives the order to PostgreSQL
    4. Marks the session as complete
    5. Provides confirmation message with total
    """
    
    def __init__(self, order_session_service: OrderSessionService):
        self.order_session_service = order_session_service
    
    async def execute(
        self, 
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> ConfirmOrderWorkflowResult:
        """
        Execute the confirm order workflow.
        
        Args:
            session_id: The customer's session ID
            conversation_history: Recent conversation turns (optional)
            
        Returns:
            ConfirmOrderWorkflowResult with the operation result
        """
        try:
            logger.info(f"Confirming order for session: {session_id}")
            
            # Get the current order from the session
            current_order = await self.order_session_service.get_session_order(session_id)
            if not current_order:
                return ConfirmOrderWorkflowResult(
                    success=False,
                    message="No active order found to confirm. Please add items to your order first.",
                    audio_phrase_type=AudioPhraseType.NO_ORDER_YET
                )
            
            # Check if order has items
            items = current_order.get("items", [])
            if not items:
                return ConfirmOrderWorkflowResult(
                    success=False,
                    message="Your order is empty. Please add items before confirming.",
                    audio_phrase_type=AudioPhraseType.ORDER_ALREADY_EMPTY
                )
            
            # Get order total
            total_amount = current_order.get("total_amount", 0.0)
            order_id = current_order.get("id")
            
            if not order_id:
                return ConfirmOrderWorkflowResult(
                    success=False,
                    message="Order ID not found. Please try again.",
                    audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
                )
            
            # Archive order to PostgreSQL
            archive_success = await self.order_session_service.archive_order_to_postgres(order_id)
            
            if not archive_success:
                logger.warning(f"Failed to archive order {order_id} to PostgreSQL, but continuing with confirmation")
                # Continue anyway - the order is still valid in Redis
            
            # Mark session as complete
            session_success = await self.order_session_service.finalize_order(order_id)
            
            if not session_success:
                logger.warning(f"Failed to finalize order {order_id}, but continuing with confirmation")
                # Continue anyway - the order is still valid
            
            # Format total for display
            total_display = f"${total_amount:.2f}" if isinstance(total_amount, (int, float)) else f"${float(total_amount):.2f}"
            
            # Create confirmation message
            confirmation_message = f"Perfect! If everything looks correct on your screen, that'll be {total_display}. Pull around to the next window!"
            
            return ConfirmOrderWorkflowResult(
                success=True,
                message=confirmation_message,
                order_updated=True,
                total_cost=float(total_amount),
                order_summary=self._create_order_summary(items),
                audio_phrase_type=AudioPhraseType.ORDER_CONFIRMED,
                data={
                    "order_id": order_id,
                    "total_amount": float(total_amount),
                    "item_count": len(items),
                    "archived_to_postgres": archive_success,
                    "session_finalized": session_success
                }
            )
                
        except Exception as e:
            logger.error(f"Confirm order workflow failed: {e}", exc_info=True)
            return ConfirmOrderWorkflowResult(
                success=False,
                message="Sorry, I couldn't confirm your order. Please try again.",
                error=str(e),
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
    
    def _create_order_summary(self, items: List[Dict[str, Any]]) -> str:
        """
        Create a human-readable summary of the order items.
        
        Args:
            items: List of order items
            
        Returns:
            String summary of the order
        """
        if not items:
            return "No items in order"
        
        summary_parts = []
        for item in items:
            quantity = item.get("quantity", 1)
            name = item.get("modifications", {}).get("name", "Unknown Item")
            size = item.get("modifications", {}).get("size", "regular")
            
            item_summary = f"{quantity}x {name}"
            if size and size != "regular":
                item_summary += f" ({size})"
            
            summary_parts.append(item_summary)
        
        return "; ".join(summary_parts)
