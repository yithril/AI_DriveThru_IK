"""
Enhanced Modify Item Service

Handles validation and application of complex item modifications for Redis-based orders.
Supports item splitting, multiple modifications, and natural language modification parsing.
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from app.workflow.response.modify_item_response import ModifyItemResult, ModificationInstruction
from app.dto.modify_item_dto import ModifyItemRequestDto, ModifyItemResultDto
from app.constants.item_sizes import ItemSize
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.constants.order_config import MAX_ITEM_QUANTITY

logger = logging.getLogger(__name__)


class ModifyItemService:
    """Enhanced service for validating and applying complex item modifications to Redis orders"""
    
    def __init__(self, menu_service: MenuService = None, ingredient_service: IngredientService = None):
        """Initialize the service with dependencies"""
        self.menu_service = menu_service or MenuService()
        self.ingredient_service = ingredient_service or IngredientService()
    
    async def apply_modification(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """
        Apply modification from enhanced agent result to Redis order
        
        Args:
            agent_result: Enhanced result from modify item agent
            redis_order: Current Redis order data
            
        Returns:
            ModifyItemResultDto with success/failure details
        """
        try:
            # Check if modification is actionable
            if not agent_result.is_actionable():
                if agent_result.clarification_needed:
                    return ModifyItemResultDto(
                        success=False,
                        message=agent_result.clarification_message or "Modification request could not be processed",
                        validation_errors=agent_result.validation_errors
                    )
                else:
                    return ModifyItemResultDto(
                        success=False,
                        message="No modifications specified",
                        validation_errors=["No modifications provided"]
                    )
            
            # Normalize item IDs to ensure they have the "item_" prefix
            self._normalize_item_ids(agent_result)
            
            # Debug: Log the normalized item IDs
            logger.info(f"DEBUG: After normalization, agent result modifications:")
            for i, mod in enumerate(agent_result.modifications):
                logger.info(f"  Modification {i+1}: item_id='{mod.item_id}', item_name='{mod.item_name}'")
            
            # Validate all modifications before applying
            validation_result = await self._validate_modifications(agent_result, redis_order)
            if validation_result:
                return validation_result
            
            # Handle partial success if some modifications failed
            if hasattr(agent_result, 'failed_modifications') and agent_result.failed_modifications:
                return await self._handle_partial_success(agent_result, redis_order)
            
            # Handle item splitting if required
            if agent_result.requires_split:
                return await self._handle_item_splitting(agent_result, redis_order)
            else:
                # Handle simple modification (no splitting)
                return await self._handle_simple_modification(agent_result, redis_order)
            
        except Exception as e:
            logger.error(f"Failed to apply modification: {e}", exc_info=True)
            return ModifyItemResultDto(
                success=False,
                message="Sorry, I couldn't process your modification request. Please try again.",
                validation_errors=["Service error occurred"]
            )
    
    async def _validate_modifications(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> Optional[ModifyItemResultDto]:
        """Validate all modifications before applying them"""
        validation_errors = []
        successful_modifications = []
        failed_modifications = []
        
        for modification in agent_result.modifications:
            # Check if target item exists in order
            target_item = self._find_redis_item(redis_order, modification.item_id)
            logger.info(f"DEBUG: Looking for item_id='{modification.item_id}', found: {target_item is not None}")
            if not target_item:
                logger.warning(f"DEBUG: Item not found - item_id='{modification.item_id}', available items: {[item['id'] for item in redis_order.get('items', [])]}")
                validation_errors.append(f"Could not find {modification.item_name} in your current order")
                failed_modifications.append(modification)
                continue
            
            # Validate quantity limits
            quantity_error = await self._validate_quantity(modification, redis_order)
            if quantity_error:
                validation_errors.append(quantity_error)
                failed_modifications.append(modification)
                continue
            
            # Validate ingredients
            ingredient_error = await self._validate_ingredients(modification, redis_order)
            if ingredient_error:
                validation_errors.append(ingredient_error)
                failed_modifications.append(modification)
                continue
            
            # If we get here, this modification is valid
            successful_modifications.append(modification)
        
        # If all modifications failed, return error
        if not successful_modifications:
            return ModifyItemResultDto(
                success=False,
                message=f"Validation failed: {'; '.join(validation_errors)}",
                validation_errors=validation_errors
            )
        
        # If some modifications failed, we'll handle partial success in the main method
        if failed_modifications:
            # Store failed modifications for partial success handling
            agent_result.failed_modifications = failed_modifications
            agent_result.successful_modifications = successful_modifications
        
        return None
    
    async def _validate_quantity(self, modification: ModificationInstruction, redis_order: Dict[str, Any]) -> Optional[str]:
        """Validate quantity limits for a modification"""
        # Find the target item to get menu item info
        target_item = self._find_redis_item(redis_order, modification.item_id)
        if not target_item:
            return f"Could not find {modification.item_name} in your order"
        
        # Get menu item details
        menu_item_id = target_item["menu_item_id"]
        restaurant_id = redis_order.get("restaurant_id")
        
        if not restaurant_id:
            return "Restaurant ID not found in order"
        
        try:
            # Get menu item details from database
            from app.models.menu_item import MenuItem
            menu_item = await MenuItem.get_or_none(id=menu_item_id)
            if not menu_item:
                return f"Menu item {menu_item_id} not found"
            
            # Check against max quantity
            if menu_item.max_quantity and modification.quantity > menu_item.max_quantity:
                return f"Cannot order {modification.quantity} {modification.item_name}. Maximum allowed: {menu_item.max_quantity}"
            
            # Check for reasonable limits (business rule)
            if modification.quantity > MAX_ITEM_QUANTITY:
                return f"Cannot order {modification.quantity} {modification.item_name}. Maximum allowed: {MAX_ITEM_QUANTITY}"
            
        except Exception as e:
            logger.warning(f"Could not validate quantity for item {menu_item_id}: {e}")
            # Continue without validation if we can't get menu item details
        
        return None
    
    async def _validate_ingredients(self, modification: ModificationInstruction, redis_order: Dict[str, Any]) -> Optional[str]:
        """Validate that ingredients exist and are available using fuzzy matching"""
        # Parse the modification to extract ingredients
        parsed_mods = self._parse_modification_text(modification.modification)
        
        if not parsed_mods["ingredient_modifications"]:
            return None  # No ingredients to validate
        
        restaurant_id = redis_order.get("restaurant_id")
        if not restaurant_id:
            return "Restaurant ID not found in order"
        
        try:
            # Check each ingredient modification using fuzzy search
            for ingredient_mod in parsed_mods["ingredient_modifications"]:
                # Extract ingredient name from modification (e.g., "extra cheese" -> "cheese")
                ingredient_name = self._extract_ingredient_name(ingredient_mod)
                
                if ingredient_name:
                    # Use fuzzy search like MenuResolutionService does
                    ingredient_matches = await self.ingredient_service.search_by_name(
                        restaurant_id=restaurant_id,
                        name=ingredient_name
                    )
                    
                    if not ingredient_matches.ingredients or len(ingredient_matches.ingredients) == 0:
                        return f"'{ingredient_name}' is not available at this restaurant"
        
        except Exception as e:
            logger.warning(f"Could not validate ingredients: {e}")
            # Continue without validation if we can't get ingredient details
        
        return None
    
    def _extract_ingredient_name(self, ingredient_mod: str) -> Optional[str]:
        """Extract ingredient name from modification string"""
        # Remove action words like "extra", "no", "without"
        action_words = ["extra", "no", "without", "hold", "remove"]
        
        ingredient_name = ingredient_mod.lower()
        for action in action_words:
            ingredient_name = ingredient_name.replace(action, "").strip()
        
        # Clean up extra spaces
        ingredient_name = " ".join(ingredient_name.split())
        
        return ingredient_name if ingredient_name else None
    
    def _normalize_item_ids(self, agent_result: ModifyItemResult) -> None:
        """
        Normalize item IDs to ensure they have the "item_" prefix if missing
        
        This handles cases where the agent generates IDs like "1234567890" 
        instead of "item_1234567890" to match the Redis order format.
        """
        for modification in agent_result.modifications:
            if not modification.item_id.startswith("item_"):
                modification.item_id = f"item_{modification.item_id}"

    def _find_redis_item(self, redis_order: Dict[str, Any], target_item_id: str) -> Optional[Dict[str, Any]]:
        """Find the target item in Redis order by ID"""
        if not redis_order or "items" not in redis_order:
            return None
        
        for item in redis_order["items"]:
            if item["id"] == target_item_id:
                return item
        
        return None
    
    async def _handle_simple_modification(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """Handle simple modification without splitting"""
        if not agent_result.modifications:
            return ModifyItemResultDto(
                success=False,
                message="No modifications specified",
                validation_errors=["No modifications provided"]
            )
        
        # For simple modifications, apply the first (and only) modification
        modification = agent_result.modifications[0]
        target_item = self._find_redis_item(redis_order, modification.item_id)
        
        if not target_item:
            return ModifyItemResultDto(
                success=False,
                message=f"Could not find {modification.item_name} in your current order",
                validation_errors=[f"Could not find {modification.item_name} in your current order"]
            )
        
        # Apply the modification
        return await self._apply_single_modification(modification, target_item, redis_order)
    
    async def _handle_item_splitting(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """Handle complex item splitting with multiple modifications"""
        if not agent_result.modifications:
            return ModifyItemResultDto(
                success=False,
                message="No modifications specified for splitting",
                validation_errors=["No modifications provided for splitting"]
            )
        
        # Find the original item to split
        original_item_id = agent_result.modifications[0].item_id
        original_item = self._find_redis_item(redis_order, original_item_id)
        
        if not original_item:
            return ModifyItemResultDto(
                success=False,
                message=f"Original item {original_item_id} not found for splitting",
                validation_errors=[f"Item {original_item_id} does not exist in order"]
            )
        
        # Validate total quantities
        total_modified = sum(mod.quantity for mod in agent_result.modifications)
        total_unchanged = agent_result.remaining_unchanged
        original_quantity = original_item["quantity"]
        
        if total_modified + total_unchanged != original_quantity:
            return ModifyItemResultDto(
                success=False,
                message=f"Quantity mismatch: {total_modified} modified + {total_unchanged} unchanged ≠ {original_quantity} original",
                validation_errors=[f"Invalid quantity split: {total_modified + total_unchanged} ≠ {original_quantity}"]
            )
        
        # Remove the original item
        redis_order["items"] = [item for item in redis_order["items"] if item["id"] != original_item_id]
        
        # Create new items for each modification
        new_items = []
        modified_fields = []
        total_additional_cost = Decimal('0.00')
        
        for modification in agent_result.modifications:
            new_item = self._create_item_from_original(original_item, modification.quantity)
            parsed_mods = self._parse_modification_text(modification.modification)
            ingredient_cost = await self._apply_parsed_modifications(new_item, parsed_mods)
            total_additional_cost += ingredient_cost * modification.quantity
            new_items.append(new_item)
            modified_fields.append(f"{modification.quantity} {modification.item_name}: {modification.modification}")
        
        # Add unchanged items if any
        if total_unchanged > 0:
            unchanged_item = self._create_item_from_original(original_item, total_unchanged)
            new_items.append(unchanged_item)
            modified_fields.append(f"{total_unchanged} {original_item.get('modifications', {}).get('name', 'items')}: unchanged")
        
        # Add all new items to the order
        redis_order["items"].extend(new_items)
        
        # Build success message - keep it simple and generic
        message = "I've updated your order. Would you like anything else?"
        
        return ModifyItemResultDto(
            success=True,
            message=message,
            additional_cost=total_additional_cost,
            modified_fields=modified_fields
        )
    
    def _create_item_from_original(self, original_item: Dict[str, Any], quantity: int) -> Dict[str, Any]:
        """Create a new item based on the original item with specified quantity"""
        import time
        
        new_item = original_item.copy()
        new_item["id"] = f"item_{int(time.time() * 1000)}"  # Generate new ID
        new_item["quantity"] = quantity
        
        # Get unit price from menu_item.price (production structure)
        unit_price = new_item.get("menu_item", {}).get("price", 0.0)
        new_item["total_price"] = unit_price * quantity
        
        # Reset modifications for the new item
        if "modifications" in new_item:
            new_item["modifications"] = new_item["modifications"].copy()
        
        return new_item
    
    def _parse_modification_text(self, modification_text: str) -> Dict[str, Any]:
        """Parse natural language modification text into structured modifications"""
        parsed = {
            "ingredient_modifications": [],
            "size_change": None,
            "quantity_change": None,
            "special_instructions": []
        }
        
        text = modification_text.lower()
        
        # Parse ingredient modifications
        if "extra" in text:
            # Extract all ingredients after "extra" - handle "extra cheese and extra lettuce"
            # Split by "and" first, then extract each "extra X" pattern
            parts = text.split(" and ")
            for part in parts:
                if "extra" in part:
                    extra_matches = re.findall(r'extra\s+([^,\s]+(?:\s+[^,\s]+)*)', part)
                    for ingredient in extra_matches:
                        parsed["ingredient_modifications"].append(f"extra {ingredient.strip()}")
        
        if "no" in text:
            # Extract ingredients after "no"
            no_match = re.search(r'no\s+([^,\s]+(?:\s+[^,\s]+)*)', text)
            if no_match:
                ingredient = no_match.group(1).strip()
                parsed["ingredient_modifications"].append(f"no {ingredient}")
        
        if "add" in text:
            # Extract ingredients after "add" (normalized from "with X")
            add_match = re.search(r'add\s+([^,\s]+(?:\s+[^,\s]+)*)', text)
            if add_match:
                ingredient = add_match.group(1).strip()
                parsed["ingredient_modifications"].append(f"add {ingredient}")
        
        if "with" in text:
            # Extract ingredients after "with"
            with_match = re.search(r'with\s+([^,\s]+(?:\s+[^,\s]+)*)', text)
            if with_match:
                ingredient = with_match.group(1).strip()
                parsed["ingredient_modifications"].append(f"with {ingredient}")
        
        # Parse size changes
        size_keywords = ["small", "medium", "large", "regular"]
        for size in size_keywords:
            if size in text:
                parsed["size_change"] = size
                break
        
        # Parse quantity changes
        quantity_match = re.search(r'(\d+)\s*(?:of|items?)', text)
        if quantity_match:
            parsed["quantity_change"] = int(quantity_match.group(1))
        
        # Store any remaining text as special instructions
        if "regular" in text and not any(size in text for size in size_keywords):
            parsed["special_instructions"].append("keep regular")
        
        return parsed
    
    async def _apply_parsed_modifications(self, item: Dict[str, Any], parsed_mods: Dict[str, Any]) -> Decimal:
        """Apply parsed modifications to an item and return the additional cost"""
        if "modifications" not in item:
            item["modifications"] = {}
        
        additional_cost = Decimal('0.00')
        
        # Apply ingredient modifications and calculate cost
        if parsed_mods["ingredient_modifications"]:
            item["modifications"]["ingredient_modifications"] = "; ".join(parsed_mods["ingredient_modifications"])
            # Calculate cost for ingredient modifications
            ingredient_cost = await self._calculate_ingredient_cost(parsed_mods["ingredient_modifications"], item)
            additional_cost += ingredient_cost
        
        # Apply size change
        if parsed_mods["size_change"]:
            item["modifications"]["size"] = parsed_mods["size_change"]
        
        # Apply special instructions
        if parsed_mods["special_instructions"]:
            item["modifications"]["special_instructions"] = "; ".join(parsed_mods["special_instructions"])
        
        # Update the item's total price
        if additional_cost > 0:
            base_price = item.get("menu_item", {}).get("price", 0.0)
            quantity = item.get("quantity", 1)
            item["total_price"] = (base_price + float(additional_cost)) * quantity
        
        return additional_cost
    
    async def _calculate_ingredient_cost(self, ingredient_modifications: List[str], item: Dict[str, Any]) -> Decimal:
        """Calculate the additional cost for ingredient modifications"""
        total_cost = Decimal('0.00')
        menu_item_id = item.get("menu_item_id")
        
        if not menu_item_id:
            return total_cost
        
        for modification in ingredient_modifications:
            # Parse the modification (e.g., "extra cheese", "no lettuce")
            if modification.startswith("extra "):
                ingredient_name = modification[6:]  # Remove "extra "
                # Look up the ingredient cost from the database
                try:
                    # Get the menu item ingredient relationship to find the cost
                    menu_item_ingredient = await self.menu_service.get_menu_item_ingredient(menu_item_id, ingredient_name)
                    if menu_item_ingredient and menu_item_ingredient.additional_cost:
                        total_cost += Decimal(str(menu_item_ingredient.additional_cost))
                except Exception as e:
                    logger.warning(f"Could not calculate cost for ingredient '{ingredient_name}': {e}")
        
        return total_cost
    
    async def _apply_single_modification(self, modification: ModificationInstruction, target_item: Dict[str, Any], redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """Apply a single modification to an item"""
        
        # Check if this is a quantity change
        if "change quantity to" in modification.modification.lower():
            # Extract the new quantity from the modification text
            import re
            quantity_match = re.search(r'change quantity to (\d+)', modification.modification.lower())
            if quantity_match:
                new_quantity = int(quantity_match.group(1))
                
                # Update the quantity and recalculate total price
                old_quantity = target_item["quantity"]
                unit_price = target_item.get("menu_item", {}).get("price", 0.0)
                
                target_item["quantity"] = new_quantity
                target_item["total_price"] = new_quantity * unit_price
                
                # Build success message
                item_name = target_item.get("modifications", {}).get("name", f"Item {target_item['menu_item_id']}")
                message = f"Updated {item_name} quantity from {old_quantity} to {new_quantity}"
                
                return ModifyItemResultDto(
                    success=True,
                    message="I've updated your order. Would you like anything else?",
                    additional_cost=Decimal('0.00'),
                    modified_fields=[f"{modification.item_name}: quantity changed to {new_quantity}"]
                )
        
        # Handle other types of modifications (ingredients, size, etc.)
        parsed_mods = self._parse_modification_text(modification.modification)
        await self._apply_parsed_modifications(target_item, parsed_mods)
        
        # Build success message - keep it simple and generic
        message = "I've updated your order. Would you like anything else?"
        
        return ModifyItemResultDto(
            success=True,
            message=message,
            additional_cost=Decimal('0.00'),
            modified_fields=[f"{modification.item_name}: {modification.modification}"]
        )
    
    async def _handle_partial_success(self, agent_result: ModifyItemResult, redis_order: Dict[str, Any]) -> ModifyItemResultDto:
        """Handle partial success when some modifications work and others don't"""
        successful_mods = agent_result.successful_modifications or []
        failed_mods = agent_result.failed_modifications or []
        
        # Apply successful modifications
        applied_modifications = []
        for modification in successful_mods:
            if agent_result.requires_split:
                # Handle splitting for successful modifications
                result = await self._handle_item_splitting(agent_result, redis_order)
                if result.success:
                    applied_modifications.append("Item splitting completed")
            else:
                # Handle simple modification
                target_item = self._find_redis_item(redis_order, modification.item_id)
                if target_item:
                    await self._apply_single_modification(modification, target_item, redis_order)
                    applied_modifications.append(f"{modification.item_name}: {modification.modification}")
        
        # Build success message - keep it simple and generic
        if applied_modifications:
            message = "I've updated your order. Would you like anything else?"
        else:
            message = "I couldn't make those changes. Please try again."
        
        return ModifyItemResultDto(
            success=len(applied_modifications) > 0,
            message=message,
            additional_cost=Decimal('0.00'),
            modified_fields=applied_modifications
        )
    
