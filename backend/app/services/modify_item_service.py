"""
Modify Item Service

Handles validation and application of item modifications for Redis-based orders.
Takes the output from the modify item agent and applies changes to Redis order data.
"""

import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from app.workflow.response.modify_item_response import ModifyItemResult
from app.dto.modify_item_dto import ModifyItemRequestDto, ModifyItemResultDto
from app.constants.item_sizes import ItemSize

logger = logging.getLogger(__name__)


class ModifyItemService:
    """Service for validating and applying item modifications to Redis orders"""
    
    async def apply_modification(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """
        Apply modification from agent result to Redis order
        
        Args:
            agent_result: Result from modify item agent
            redis_order: Current Redis order data
            
        Returns:
            ModifyItemResultDto with success/failure details
        """
        try:
            # Check if modification is actionable
            if not agent_result.is_actionable():
                return ModifyItemResultDto(
                    success=False,
                    message=agent_result.clarification_message or "Modification request could not be processed",
                    validation_errors=agent_result.validation_errors
                )
            
            # Find the target item in Redis order
            target_item = self._find_redis_item(redis_order, agent_result.target_item_id)
            if not target_item:
                return ModifyItemResultDto(
                    success=False,
                    message=f"Item with ID {agent_result.target_item_id} not found in current order",
                    validation_errors=[f"Item {agent_result.target_item_id} does not exist in order"]
                )
            
            # Apply the modification to Redis item
            return await self._apply_redis_modification(agent_result, target_item, redis_order)
            
        except Exception as e:
            logger.error(f"Failed to apply modification: {e}", exc_info=True)
            return ModifyItemResultDto(
                success=False,
                message=f"Failed to apply modification: {str(e)}",
                validation_errors=[f"Service error: {str(e)}"]
            )
    
    def _find_redis_item(self, redis_order: Dict[str, Any], target_item_id: int) -> Optional[Dict[str, Any]]:
        """Find the target item in Redis order by ID"""
        if not redis_order or "items" not in redis_order:
            return None
        
        for item in redis_order["items"]:
            # Extract numeric part from Redis item ID (e.g., "item_1759408689854" -> 1759408689854)
            item_id = int(item["id"].split("_")[1]) if "_" in item["id"] else int(item["id"])
            if item_id == target_item_id:
                return item
        
        return None
    
    async def _apply_redis_modification(
        self, 
        agent_result: ModifyItemResult, 
        target_item: Dict[str, Any], 
        redis_order: Dict[str, Any]
    ) -> ModifyItemResultDto:
        """Apply modification to Redis item"""
        
        modified_fields = []
        validation_errors = []
        additional_cost = Decimal('0.00')
        
        # Apply quantity modification
        if agent_result.new_quantity is not None:
            old_quantity = target_item["quantity"]
            if agent_result.new_quantity >= 1 and agent_result.new_quantity <= 20:  # Basic validation
                target_item["quantity"] = agent_result.new_quantity
                modified_fields.append(f"quantity from {old_quantity} to {agent_result.new_quantity}")
                logger.info(f"Updated quantity for Redis item {target_item['id']}: {old_quantity} -> {agent_result.new_quantity}")
            else:
                validation_errors.append(f"Cannot set quantity to {agent_result.new_quantity}. Valid range: 1-20")
        
        # Apply size modification
        if agent_result.new_size is not None:
            # Ensure modifications dict exists
            if "modifications" not in target_item:
                target_item["modifications"] = {}
            
            old_size = target_item["modifications"].get("size", "regular")
            target_item["modifications"]["size"] = agent_result.new_size.lower()
            modified_fields.append(f"size from {old_size} to {agent_result.new_size}")
            logger.info(f"Updated size for Redis item {target_item['id']}: {old_size} -> {agent_result.new_size}")
        
        # Apply ingredient modifications
        if agent_result.ingredient_modifications:
            if "modifications" not in target_item:
                target_item["modifications"] = {}
            
            # Store ingredient modifications as special instructions
            ingredient_mods_str = "; ".join(agent_result.ingredient_modifications)
            target_item["modifications"]["ingredient_modifications"] = ingredient_mods_str
            modified_fields.append(f"ingredients: {', '.join(agent_result.ingredient_modifications)}")
            logger.info(f"Updated ingredients for Redis item {target_item['id']}: {ingredient_mods_str}")
        
        # Check if any validation errors occurred
        if validation_errors:
            return ModifyItemResultDto(
                success=False,
                message=f"Cannot apply modifications: {'; '.join(validation_errors)}",
                validation_errors=validation_errors
            )
        
        # Build success message
        item_name = target_item.get("modifications", {}).get("name", f"Item {target_item['menu_item_id']}")
        if modified_fields:
            message = f"Updated {item_name}: {', '.join(modified_fields)}"
            if additional_cost > 0:
                message += f" (additional cost: ${additional_cost:.2f})"
        else:
            message = "No changes were applied"
        
        return ModifyItemResultDto(
            success=True,
            message=message,
            additional_cost=additional_cost,
            modified_fields=modified_fields
        )
    
