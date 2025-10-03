"""
Add Item Workflow - Handles adding items to orders.

This workflow orchestrates:
1. Item Extraction Agent (LLM) - extracts items from user input
2. Menu Resolution Service (deterministic) - resolves items against menu database
3. Order Session Service - adds resolved items to the current order
4. Validation - ensures quantities are within limits
"""

import logging
from typing import Dict, Any, Optional, List
from app.workflow.agents.item_extraction_agent import item_extraction_agent
from app.services.menu_resolution_service import MenuResolutionService
from app.services.order_session_service import OrderSessionService
from app.services.ingredient_service import IngredientService
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.workflow.response.item_extraction_response import ItemExtractionResponse
from app.workflow.response.menu_resolution_response import MenuResolutionResponse
from app.constants.audio_phrases import AudioPhraseType
from app.constants.order_config import MAX_ITEM_QUANTITY, MAX_TOTAL_ITEMS, DEFAULT_ITEM_QUANTITY

logger = logging.getLogger(__name__)


class AddItemWorkflowResult(WorkflowResult):
    """Result specifically for add item workflows"""
    
    def __init__(self, success: bool, message: str, **kwargs):
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.ADD_ITEM,
            **kwargs
        )


class AddItemWorkflow:
    """
    Workflow for adding items to orders.
    
    This workflow:
    1. Extracts items from user input using LLM
    2. Resolves items against the menu database
    3. Validates quantities and availability
    4. Adds items to the current order
    5. Provides confirmation or clarification messages
    """
    
    def __init__(
        self, 
        restaurant_id: int,
        menu_resolution_service: MenuResolutionService,
        order_session_service: OrderSessionService,
        ingredient_service: IngredientService
    ):
        self.restaurant_id = restaurant_id
        self.menu_resolution_service = menu_resolution_service
        self.order_session_service = order_session_service
        self.ingredient_service = ingredient_service
    
    async def execute(
        self, 
        user_input: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        current_order: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute the add item workflow.
        
        Args:
            user_input: The user's request to add items
            session_id: The customer's session ID
            conversation_history: Recent conversation turns (optional)
            current_order: Current order state (optional)
            
        Returns:
            WorkflowResult with the operation result
        """
        try:
            logger.info(f"Adding items to order for session: {session_id}")
            logger.debug(f"User input: {user_input}")
            
            # Step 1: Extract items from user input using LLM
            extraction_context = self._build_extraction_context(
                conversation_history or [], 
                current_order or {}
            )
            
            extraction_result: ItemExtractionResponse = await item_extraction_agent(
                user_input=user_input,
                context=extraction_context
            )
            
            if not extraction_result.success:
                return WorkflowResult(
                    success=False,
                    message="I couldn't understand what items you'd like to add. Could you please try again?",
                    audio_phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"extraction_failed": True}
                )
            
            # Step 2: Resolve items against menu database
            logger.info(f"DEBUG: About to resolve items. Extraction result: {extraction_result}")
            resolution_result: MenuResolutionResponse = await self.menu_resolution_service.resolve_items(
                extraction_response=extraction_result,
                restaurant_id=self.restaurant_id
            )
            logger.info(f"DEBUG: Resolution result: success={resolution_result.success}, needs_clarification={resolution_result.needs_clarification}")
            logger.info(f"DEBUG: Resolved items count: {len(resolution_result.resolved_items)}")
            for i, item in enumerate(resolution_result.resolved_items):
                logger.info(f"DEBUG: Resolved item {i+1}: name='{item.resolved_menu_item_name}', id={item.resolved_menu_item_id}, qty={item.quantity}")
            
            if not resolution_result.success:
                return WorkflowResult(
                    success=False,
                    message="I couldn't find those items on our menu. Could you please try again?",
                    audio_phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"resolution_failed": True}
                )
            
            # Step 3: Check if clarification is needed
            if resolution_result.needs_clarification:
                clarification_message = self._build_clarification_message(resolution_result)
                return WorkflowResult(
                    success=False,
                    message=clarification_message,
                    audio_phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                    needs_clarification=True,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"clarification_questions": resolution_result.clarification_questions}
                )
            
            # Step 4: Validate quantities and order limits
            validation_result = await self._validate_order_limits(
                resolution_result.resolved_items, 
                current_order or {}
            )
            
            if not validation_result["valid"]:
                return WorkflowResult(
                    success=False,
                    message=validation_result["message"],
                    audio_phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"validation_failed": True}
                )
            
            # Step 5: Add items to order
            added_items = []
            failed_items = []
            
            logger.debug(f"DEBUG: resolution_result.get_clear_items(): {resolution_result.get_clear_items()}")
            for resolved_item in resolution_result.get_clear_items():
                success = await self._add_single_item_to_order(
                    session_id=session_id,
                    resolved_item=resolved_item
                )
                
                if success:
                    added_items.append(resolved_item)
                else:
                    failed_items.append(resolved_item)
            
            # Step 6: Build response
            logger.debug(f"DEBUG: added_items count: {len(added_items)}, failed_items count: {len(failed_items)}")
            logger.debug(f"DEBUG: added_items: {added_items}")
            logger.debug(f"DEBUG: failed_items: {failed_items}")
            if added_items and not failed_items:
                # All items added successfully
                success_message = self._build_success_message(added_items)
                added_items_data = [
                    {
                        "name": item.resolved_menu_item_name,
                        "quantity": item.quantity,
                        "size": item.size
                    } for item in added_items
                ]
                logger.debug(f"DEBUG: Creating result with added_items_data={added_items_data}")
                result = WorkflowResult(
                    success=True,
                    message=success_message,
                    order_updated=True,
                    audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"added_items": added_items_data, "total_cost": 0.0}
                )
                logger.debug(f"DEBUG: Created result, result.data={result.data}")
                return result
            elif added_items and failed_items:
                # Partial success
                partial_message = self._build_partial_success_message(added_items, failed_items)
                added_items_data = [
                    {
                        "name": item.resolved_menu_item_name,
                        "quantity": item.quantity,
                        "size": item.size
                    } for item in added_items
                ]
                return WorkflowResult(
                    success=True,
                    message=partial_message,
                    order_updated=True,
                    audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"added_items": added_items_data, "total_cost": 0.0}
                )
            else:
                # All items failed
                return WorkflowResult(
                    success=False,
                    message="I couldn't add those items to your order. Please try again.",
                    audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
                    workflow_type=WorkflowType.ADD_ITEM,
                    data={"all_items_failed": True}
                )
                
        except Exception as e:
            logger.error(f"Add item workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                message="Sorry, I couldn't add those items to your order. Please try again.",
                error=str(e),
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
                workflow_type=WorkflowType.ADD_ITEM
            )
    
    def _build_extraction_context(self, conversation_history: List[Dict[str, Any]], current_order: Dict[str, Any]) -> Dict[str, Any]:
        """Build context for item extraction agent"""
        return {
            "conversation_history": conversation_history,
            "order_state": current_order,
            "restaurant_id": str(self.restaurant_id)
        }
    
    async def _validate_order_limits(self, resolved_items: List, current_order: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that adding these items won't exceed order limits"""
        current_item_count = len(current_order.get("items", []))
        new_item_count = sum(item.quantity for item in resolved_items)
        total_item_count = current_item_count + new_item_count
        
        # Check total items limit
        if total_item_count > MAX_TOTAL_ITEMS:
            return {
                "valid": False,
                "message": f"Your order would have too many items (maximum {MAX_TOTAL_ITEMS}). Please reduce the quantity."
            }
        
        # Check individual item quantity limits
        for item in resolved_items:
            if item.quantity > MAX_ITEM_QUANTITY:
                return {
                    "valid": False,
                    "message": f"You can only order up to {MAX_ITEM_QUANTITY} of any single item. Please reduce the quantity for {item.resolved_menu_item_name}."
                }
        
        return {"valid": True, "message": ""}
    
    async def _add_single_item_to_order(self, session_id: str, resolved_item) -> bool:
        """Add a single resolved item to the order"""
        try:
            # Get current order
            current_order = await self.order_session_service.get_session_order(session_id)
            if not current_order:
                # Create new order if none exists
                order_id = await self.order_session_service.create_order(
                    session_id=session_id,
                    restaurant_id=self.restaurant_id
                )
                if not order_id:
                    logger.error(f"Failed to create order for session {session_id}")
                    return False
            else:
                order_id = current_order["id"]
            
            # Build modifications dictionary
            modifications = await self._build_modifications_dict(resolved_item)
            
            # Add item to order
            success = await self.order_session_service.add_item_to_order(
                order_id=order_id,
                menu_item_id=resolved_item.resolved_menu_item_id,
                quantity=resolved_item.quantity,
                modifications=modifications
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add item {resolved_item.resolved_menu_item_name} to order: {e}")
            return False
    
    async def _build_modifications_dict(self, resolved_item) -> Dict[str, Any]:
        """Build modifications dictionary for order item"""
        modifications = {
            "name": resolved_item.resolved_menu_item_name,
            "size": resolved_item.size or "regular"
        }
        
        # Add special instructions if present
        if resolved_item.special_instructions:
            modifications["special_instructions"] = resolved_item.special_instructions
        
        # Add ingredient modifications with ingredient names
        if resolved_item.modifiers:
            ingredient_mods = []
            for ingredient_id, action in resolved_item.modifiers:
                # Look up ingredient name
                logger.info(f"DEBUG: Looking up ingredient_id {ingredient_id} for action '{action}'")
                try:
                    ingredient = await self.ingredient_service.get_by_id(ingredient_id)
                    logger.info(f"DEBUG: Ingredient lookup result for ID {ingredient_id}: {ingredient}")
                    if ingredient:
                        ingredient_name = ingredient.name.lower()
                        logger.info(f"DEBUG: Using ingredient name '{ingredient_name}' for ID {ingredient_id}")
                        ingredient_mods.append(f"{action} {ingredient_name}")
                    else:
                        logger.warning(f"DEBUG: No ingredient found for ID {ingredient_id}")
                        ingredient_mods.append(f"{action} ingredient_id:{ingredient_id}")
                except Exception as e:
                    logger.error(f"DEBUG: Exception looking up ingredient {ingredient_id}: {e}")
                    ingredient_mods.append(f"{action} ingredient_id:{ingredient_id}")
            
            if ingredient_mods:
                modifications["ingredient_modifications"] = "; ".join(ingredient_mods)
        
        return modifications
    
    def _build_clarification_message(self, resolution_result: MenuResolutionResponse) -> str:
        """Build clarification message for ambiguous items"""
        if resolution_result.clarification_questions:
            return resolution_result.clarification_questions[0]
        
        ambiguous_items = resolution_result.get_ambiguous_items()
        if ambiguous_items:
            item_names = [item.item_name for item in ambiguous_items]
            return f"I'm not sure which {', '.join(item_names)} you meant. Could you be more specific?"
        
        return "I need more information to help you. Could you please clarify?"
    
    def _build_success_message(self, added_items: List) -> str:
        """Build success message for added items"""
        if len(added_items) == 1:
            item = added_items[0]
            quantity_text = f"{item.quantity} " if item.quantity > 1 else ""
            size_text = f" ({item.size})" if item.size and item.size != "regular" else ""
            return f"Added {quantity_text}{item.resolved_menu_item_name}{size_text} to your order! Would you like anything else?"
        else:
            item_names = []
            for item in added_items:
                quantity_text = f"{item.quantity} " if item.quantity > 1 else ""
                size_text = f" ({item.size})" if item.size and item.size != "regular" else ""
                item_names.append(f"{quantity_text}{item.resolved_menu_item_name}{size_text}")
            
            return f"Added {', '.join(item_names)} to your order! Would you like anything else?"
    
    def _build_partial_success_message(self, added_items: List, failed_items: List) -> str:
        """Build message for partial success"""
        success_msg = self._build_success_message(added_items)
        failed_names = [item.resolved_menu_item_name for item in failed_items]
        return f"{success_msg} However, I couldn't add {', '.join(failed_names)}. Please try again. Would you like anything else?"
