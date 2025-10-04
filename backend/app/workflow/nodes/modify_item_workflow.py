"""
Modify Item Workflow

Handles the complete flow for modifying items in a drive-thru order:
1. Parse user modification request
2. Validate and apply modifications
3. Update Redis order
4. Return response to user
"""

import logging
from typing import Dict, Any, Optional, List
from app.workflow.agents.modify_item_agent import modify_item_agent
from app.services.modify_item_service import ModifyItemService
from app.services.order_session_service import OrderSessionService
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.workflow.converters.order_data_converter import OrderDataConverter
from app.dto.modify_item_dto import ModifyItemResultDto
from app.workflow.response.workflow_result import ModifyItemWorkflowResult
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class ModifyItemWorkflow:
    """Workflow for handling item modifications in drive-thru orders"""
    
    def __init__(
        self, 
        order_session_service: OrderSessionService,
        menu_service: MenuService = None,
        ingredient_service: IngredientService = None
    ):
        """
        Initialize the workflow
        
        Args:
            order_session_service: Service for managing Redis-based orders
            menu_service: Service for menu operations
            ingredient_service: Service for ingredient operations
        """
        self.order_session_service = order_session_service
        self.modify_item_service = ModifyItemService(
            menu_service=menu_service,
            ingredient_service=ingredient_service
        )
    
    async def execute(
        self, 
        user_input: str, 
        session_id: str,
        conversation_history: Optional[ConversationHistory] = None,
        command_history: Optional[ConversationHistory] = None
    ) -> ModifyItemWorkflowResult:
        """
        Execute the modify item workflow
        
        Args:
            user_input: User's modification request
            session_id: Current session ID
            conversation_history: Recent conversation turns
            command_history: Recent commands executed
            
        Returns:
            Workflow result with success/failure and response message
        """
        try:
            # Step 1: Get current order from Redis
            redis_order = await self.order_session_service.get_session_order(session_id)
            if not redis_order:
                return ModifyItemWorkflowResult(
                    success=False,
                    message="No active order found. Please start by adding items to your order.",
                    audio_phrase_type=AudioPhraseType.NO_ORDER_YET
                )
            
            # Step 2: Convert Redis order to PostgreSQL format
            postgresql_order = OrderDataConverter.redis_to_postgresql_format(redis_order)
            
            # Step 3: Parse modification request using agent
            agent_result = await modify_item_agent(
                user_input=user_input,
                current_order=postgresql_order,
                conversation_history=conversation_history or ConversationHistory(session_id=session_id),
                command_history=command_history or ConversationHistory(session_id=session_id)
            )
            
            # Step 4: Check if agent needs clarification
            if agent_result.clarification_needed:
                return ModifyItemWorkflowResult(
                    success=False,
                    message=agent_result.clarification_message,
                    needs_clarification=True,
                    audio_phrase_type=AudioPhraseType.MODIFICATION_CLARIFICATION
                )
            
            # Step 5: Apply modification using service (pass Redis order)
            service_result = await self.modify_item_service.apply_modification(agent_result, redis_order)
            
            # Step 6: Check if service validation failed
            if not service_result.success:
                return ModifyItemWorkflowResult(
                    success=False,
                    message=service_result.message,
                    validation_errors=service_result.validation_errors,
                    audio_phrase_type=AudioPhraseType.MODIFICATION_ERROR
                )
            
            # Step 7: Save the updated Redis order back to Redis
            await self.order_session_service.update_order(redis_order["id"], redis_order)
            
            # Step 9: Return success response
            return ModifyItemWorkflowResult(
                success=True,
                message=service_result.message,
                modified_fields=service_result.modified_fields,
                additional_cost=float(service_result.additional_cost),
                order_updated=True,
                order_summary=OrderDataConverter.extract_order_summary(redis_order),
                confidence_score=agent_result.confidence,
                audio_phrase_type=AudioPhraseType.ITEM_MODIFIED_SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Modify item workflow failed: {e}", exc_info=True)
            return ModifyItemWorkflowResult(
                success=False,
                message="Sorry, I couldn't process your modification request. Please try again.",
                error=str(e),
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
    
    
    async def get_current_order_summary(self, session_id: str) -> str:
        """
        Get a summary of the current order
        
        Args:
            session_id: Current session ID
            
        Returns:
            Human-readable order summary
        """
        try:
            redis_order = await self.order_session_service.get_session_order(session_id)
            if not redis_order:
                return "No active order"
            
            return OrderDataConverter.extract_order_summary(redis_order)
            
        except Exception as e:
            logger.error(f"Failed to get order summary: {e}", exc_info=True)
            return "Unable to retrieve order summary"
