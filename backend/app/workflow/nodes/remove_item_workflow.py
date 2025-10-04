"""
Remove Item Workflow

Orchestrates the removal of items from customer orders.
Uses RemoveItemAgent for parsing and OrderSessionService for removal.
"""

import logging
from typing import Dict, Any, Optional, List
from app.workflow.agents.remove_item_agent import remove_item_agent
from app.services.order_session_service import OrderSessionService
from app.workflow.response.workflow_result import RemoveItemWorkflowResult, WorkflowType, WorkflowResult
from app.workflow.converters.order_data_converter import OrderDataConverter
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class RemoveItemWorkflow:
    """Workflow for removing items from customer orders"""
    
    def __init__(self, order_session_service: OrderSessionService):
        self.order_session_service = order_session_service
    
    async def execute(
        self,
        user_input: str,
        session_id: str,
        conversation_history: Optional[ConversationHistory] = None,
        command_history: Optional[ConversationHistory] = None
    ) -> WorkflowResult:
        """
        Execute the remove item workflow.
        
        Args:
            user_input: The user's request to remove items
            session_id: The customer's session ID
            conversation_history: Recent conversation turns (optional)
            command_history: Recent commands executed (optional)
            
        Returns:
            WorkflowResult with the operation result
        """
        try:
            logger.info(f"Executing RemoveItemWorkflow for session {session_id} with input: {user_input}")
            
            # Step 1: Get current order from Redis
            redis_order = await self.order_session_service.get_session_order(session_id)
            if not redis_order:
                return WorkflowResult(
                    success=False,
                    message="No active order found. Please start by adding items to your order.",
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    audio_phrase_type=AudioPhraseType.NO_ORDER_YET
                )
            
            # Step 2: Convert Redis order to PostgreSQL-like format for agent
            postgresql_order = OrderDataConverter.redis_to_postgresql_format(redis_order)
            
            # Step 3: Parse removal request using LLM agent
            agent_result = await remove_item_agent(
                user_input=user_input,
                current_order=postgresql_order,
                conversation_history=conversation_history or ConversationHistory(session_id=session_id),
                command_history=command_history or ConversationHistory(session_id=session_id)
            )
            
            if not agent_result.success:
                logger.warning(f"Remove item agent failed for session {session_id}: {agent_result.context_notes}")
                return WorkflowResult(
                    success=False,
                    message=agent_result.clarification_message or "I couldn't understand your request to remove items. Please try again.",
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVE_ERROR
                )
            
            # Step 4: Check if clarification is needed
            if agent_result.clarification_needed:
                return WorkflowResult(
                    success=False,
                    message=agent_result.clarification_message,
                    needs_clarification=True,
                    clarification_options=agent_result.clarification_options,
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVE_CLARIFICATION
                )
            
            # Step 5: Find items to remove based on agent result
            logger.info(f"DEBUG: Agent result - target_item_names: {agent_result.target_item_names}, modifier_specs: {agent_result.modifier_specs}")
            items_to_remove = self._find_items_to_remove(postgresql_order, agent_result)
            logger.info(f"DEBUG: Found {len(items_to_remove)} items to remove")
            
            if not items_to_remove:
                return WorkflowResult(
                    success=False,
                    message="I couldn't find the items you want to remove. Could you please be more specific?",
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVE_ERROR
                )
            
            # Step 6: Remove items from order
            removed_items = []
            failed_removals = []
            
            for item in items_to_remove:
                success = await self._remove_single_item_from_order(session_id, item["id"])
                if success:
                    removed_items.append(item)
                else:
                    failed_removals.append(item)
            
            # Step 7: Build response
            if removed_items and not failed_removals:
                # All items removed successfully
                success_message = self._build_success_message(removed_items)
                removed_items_data = [
                    {
                        "name": item.get("name", "Unknown Item"),
                        "quantity": item.get("quantity", 1),
                        "size": item.get("size", "regular")
                    } for item in removed_items
                ]
                
                return WorkflowResult(
                    success=True,
                    message=success_message,
                    order_updated=True,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVED_SUCCESS,
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    order_summary=OrderDataConverter.extract_order_summary(redis_order),
                    data={"removed_items": removed_items_data}
                )
            elif removed_items and failed_removals:
                # Partial success
                partial_message = self._build_partial_success_message(removed_items, failed_removals)
                removed_items_data = [
                    {
                        "name": item.get("name", "Unknown Item"),
                        "quantity": item.get("quantity", 1),
                        "size": item.get("size", "regular")
                    } for item in removed_items
                ]
                
                return WorkflowResult(
                    success=True,
                    message=partial_message,
                    order_updated=True,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVED_SUCCESS,
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    data={"removed_items": removed_items_data}
                )
            else:
                # All removals failed
                logger.warning(f"All item removals failed for session {session_id}. Failed items: {failed_removals}")
                return WorkflowResult(
                    success=False,
                    message="I couldn't remove those items from your order. Please try again.",
                    workflow_type=WorkflowType.REMOVE_ITEM,
                    audio_phrase_type=AudioPhraseType.ITEM_REMOVE_ERROR,
                    data={"failed_items": [item.get("name", "Unknown Item") for item in failed_removals]}
                )
                
        except Exception as e:
            logger.error(f"RemoveItemWorkflow failed for session {session_id}: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                message="Sorry, I couldn't process your request to remove items. Please try again.",
                error=str(e),
                workflow_type=WorkflowType.REMOVE_ITEM,
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
    
    async def _remove_single_item_from_order(self, session_id: str, item_id: int) -> bool:
        """Remove a single item from the order session"""
        try:
            # Get current order to find the Redis item ID
            redis_order = await self.order_session_service.get_session_order(session_id)
            if not redis_order:
                logger.error(f"No order found for session {session_id}")
                return False
            
            # Find the Redis item ID that corresponds to the PostgreSQL item ID
            redis_item_id = None
            for item in redis_order.get("items", []):
                # Extract numeric ID from Redis item ID (e.g., "item_123" -> 123)
                redis_numeric_id = int(item["id"].split('_')[-1]) if isinstance(item["id"], str) and item["id"].startswith("item_") else item["id"]
                if redis_numeric_id == item_id:
                    redis_item_id = item["id"]
                    break
            
            if not redis_item_id:
                logger.error(f"Could not find Redis item ID for PostgreSQL item ID {item_id}")
                return False
            
            # Get the order ID for this session
            order_data = await self.order_session_service.get_session_order(session_id)
            if not order_data:
                logger.error(f"No order found for session {session_id}")
                return False
            
            order_id = order_data.get("id")
            if not order_id:
                logger.error(f"No order ID found in order data for session {session_id}")
                return False
            
            # Remove the item from the order
            success = await self.order_session_service.remove_item_from_order(order_id, redis_item_id)
            
            if success:
                logger.info(f"Successfully removed item {redis_item_id} from session {session_id}")
            else:
                logger.error(f"Failed to remove item {redis_item_id} from session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing item {item_id} from session {session_id}: {e}", exc_info=True)
            return False
    
    def _find_items_to_remove(self, current_order: List[Dict[str, Any]], agent_result) -> List[Dict[str, Any]]:
        """
        Find items to remove based on agent result, including modifier specifications.
        
        Args:
            current_order: Current order items
            agent_result: Result from RemoveItemAgent
            
        Returns:
            List of items to remove
        """
        items_to_remove = []
        
        # If agent provided specific item IDs, use those
        if agent_result.target_item_ids:
            for item_id in agent_result.target_item_ids:
                item = next((item for item in current_order if item.get("id") == item_id), None)
                if item:
                    items_to_remove.append(item)
            return items_to_remove
        
        # Otherwise, match by item names and modifier specifications
        for i, target_name in enumerate(agent_result.target_item_names):
            modifier_spec = agent_result.modifier_specs[i] if i < len(agent_result.modifier_specs) else None
            logger.info(f"DEBUG: Processing target_name='{target_name}', modifier_spec='{modifier_spec}'")
            
            # Find items matching the target name
            matching_items = []
            for item in current_order:
                item_name = item.get("name", "").lower()
                if target_name.lower() in item_name or item_name in target_name.lower():
                    matching_items.append(item)
            
            logger.info(f"DEBUG: Found {len(matching_items)} matching items for '{target_name}'")
            
            if not matching_items:
                continue
            
            # If no modifier specified, take the first match
            if not modifier_spec:
                logger.info(f"DEBUG: No modifier specified, taking first match: {matching_items[0].get('id')}")
                items_to_remove.append(matching_items[0])
                continue
            
            # Find item with matching modifier specification
            modifier_spec_lower = modifier_spec.lower()
            logger.info(f"DEBUG: Looking for modifier '{modifier_spec_lower}'")
            for item in matching_items:
                modifications = item.get("modifications", {})
                ingredient_mods = modifications.get("ingredient_modifications", "")
                logger.info(f"DEBUG: Item {item.get('id')} has ingredient_modifications='{ingredient_mods}'")
                
                # Check if the modifier specification matches
                # Use exact matching to avoid false positives
                ingredient_mods_lower = ingredient_mods.lower()
                if modifier_spec_lower == ingredient_mods_lower:
                    logger.info(f"DEBUG: Found exact match! Item {item.get('id')} matches modifier '{modifier_spec_lower}'")
                    items_to_remove.append(item)
                    break
                elif modifier_spec_lower in ingredient_mods_lower:
                    # Check if it's a word boundary match, not just substring
                    import re
                    pattern = r'\b' + re.escape(modifier_spec_lower) + r'\b'
                    if re.search(pattern, ingredient_mods_lower):
                        logger.info(f"DEBUG: Found word boundary match! Item {item.get('id')} matches modifier '{modifier_spec_lower}'")
                        items_to_remove.append(item)
                        break
            else:
                # If no exact modifier match, take the first item (fallback)
                logger.info(f"DEBUG: No exact modifier match, taking first item as fallback: {matching_items[0].get('id')}")
                items_to_remove.append(matching_items[0])
        
        return items_to_remove

    def _build_success_message(self, removed_items: List[Dict[str, Any]]) -> str:
        """Build success message for removed items"""
        if len(removed_items) == 1:
            item = removed_items[0]
            name = item.get("name", "item")
            quantity = item.get("quantity", 1)
            if quantity > 1:
                return f"Removed {quantity} {name}s from your order."
            else:
                return f"Removed {name} from your order."
        else:
            item_names = [item.get("name", "item") for item in removed_items]
            return f"Removed {', '.join(item_names)} from your order."
    
    def _build_partial_success_message(self, removed_items: List[Dict[str, Any]], failed_removals: List[Dict[str, Any]]) -> str:
        """Build partial success message"""
        success_names = [item.get("name", "item") for item in removed_items]
        failed_names = [item.get("name", "item") for item in failed_removals]
        
        return f"Removed {', '.join(success_names)} from your order. I couldn't remove {', '.join(failed_names)}. Please try again."
