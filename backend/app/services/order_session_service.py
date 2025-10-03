"""
Order Session Service - Redis-based order management for drive-thru workflow
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


class OrderSessionService:
    """
    Service for managing orders in Redis during active drive-thru sessions.
    Orders are temporary in Redis and can be archived to PostgreSQL when completed.
    """
    
    def __init__(self, redis_service, order_service=None, menu_item_service=None):
        """
        Initialize with Redis service dependency
        
        Args:
            redis_service: Redis service instance
            order_service: PostgreSQL OrderService for fallback/archiving
            menu_item_service: MenuItemService for getting menu item details
        """
        self.redis = redis_service
        self.order_service = order_service
        self.menu_item_service = menu_item_service
    
    async def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            await self.redis.get("health_check")
            return True
        except Exception as e:
            logger.error(f"Redis not available: {e}")
            return False
    
    async def create_order(
        self, 
        session_id: str,
        restaurant_id: int,
        ttl: int = 1800  # 30 minutes default
    ) -> Optional[str]:
        """
        Create a new order for a session
        
        Args:
            session_id: Session ID to link order to
            restaurant_id: Restaurant ID
            ttl: Time to live in seconds
            
        Returns:
            str: Order ID if successful, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot create order")
            return None
        
        try:
            # Generate unique order ID
            order_id = f"order_{int(datetime.now().timestamp() * 1000)}"
            
            # Create order data
            order_data = {
                "id": order_id,
                "session_id": session_id,
                "restaurant_id": restaurant_id,
                "customer_phone": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active",
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "total_amount": 0.0,
                "items": [],  # List of order items
                "notes": None
            }
            
            # Store in Redis
            success = await self.redis.set_json(f"order:{order_id}", order_data, expire=ttl)
            
            if success:
                # Set as current order for the session
                await self.redis.set(f"session:{session_id}:current_order", order_id, ttl)
                logger.info(f"Created order {order_id} for session {session_id}")
                return order_id
            else:
                logger.error(f"Failed to store order {order_id} in Redis")
                return None
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order data by ID with consolidated items
        
        Args:
            order_id: Order ID to retrieve
            
        Returns:
            dict: Order data with consolidated items if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get order")
            return None
        
        try:
            order_data = await self.redis.get_json(f"order:{order_id}")
            if order_data and "items" in order_data:
                # Consolidate identical items
                order_data["items"] = self._consolidate_order_items(order_data["items"])
            return order_data
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    def _consolidate_order_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate identical order items by menu_item_id and modifications.
        
        Items are considered identical if they have:
        - Same menu_item_id
        - Same modifications (ingredient_modifications, special_instructions, size)
        
        Args:
            items: List of order items to consolidate
            
        Returns:
            List of consolidated order items
        """
        if not items:
            return items
        
        # Group items by consolidation key
        consolidated_groups = {}
        
        for item in items:
            # Create a consolidation key based on menu_item_id and modifications
            consolidation_key = self._create_consolidation_key(item)
            
            if consolidation_key in consolidated_groups:
                # Add to existing group
                consolidated_groups[consolidation_key]["quantity"] += item.get("quantity", 1)
            else:
                # Create new group
                consolidated_groups[consolidation_key] = item.copy()
        
        # Convert back to list
        consolidated_items = list(consolidated_groups.values())
        
        logger.info(f"Consolidated {len(items)} items into {len(consolidated_items)} unique items")
        return consolidated_items
    
    def _create_consolidation_key(self, item: Dict[str, Any]) -> str:
        """
        Create a unique key for item consolidation.
        
        Items with the same key will be consolidated together.
        
        Args:
            item: Order item dictionary
            
        Returns:
            str: Consolidation key
        """
        menu_item_id = item.get("menu_item_id", "unknown")
        
        # Get modifications for comparison
        modifications = item.get("modifications", {})
        ingredient_mods = modifications.get("ingredient_modifications", "")
        special_instructions = item.get("special_instructions", "")
        size = item.get("size", "regular")
        
        # Create key from menu_item_id + modifications
        # Sort ingredient modifications to ensure consistent ordering
        sorted_mods = sorted(ingredient_mods.split("; ")) if ingredient_mods else []
        mods_key = "; ".join(sorted_mods)
        
        consolidation_key = f"{menu_item_id}|{mods_key}|{special_instructions}|{size}"
        return consolidation_key
    
    async def get_session_order(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current order for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Order data if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get session order")
            return None
        
        try:
            current_order_id = await self.redis.get(f"session:{session_id}:current_order")
            if current_order_id:
                return await self.get_order(current_order_id)
            return None
        except Exception as e:
            logger.error(f"Error getting session order for {session_id}: {e}")
            return None
    
    async def update_order(
        self, 
        order_id: str, 
        updates: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """
        Update order data
        
        Args:
            order_id: Order ID to update
            updates: Data to merge into order
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot update order")
            return False
        
        try:
            # Get existing order data
            order_data = await self.get_order(order_id)
            if not order_data:
                logger.error(f"Order {order_id} not found for update")
                return False
            
            # Merge updates
            order_data.update(updates)
            order_data["updated_at"] = datetime.now().isoformat()
            
            # Store updated data
            success = await self.redis.set_json(f"order:{order_id}", order_data, expire=ttl)
            
            if success:
                logger.info(f"Updated order {order_id}")
                return True
            else:
                logger.error(f"Failed to update order {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False
    
    async def add_item_to_order(
        self, 
        order_id: str, 
        menu_item_id: int,
        quantity: int = 1,
        modifications: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an item to an order
        
        Args:
            order_id: Order ID
            menu_item_id: Menu item ID to add
            quantity: Quantity to add
            modifications: Optional modifications (customizations, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            order_data = await self.get_order(order_id)
            if not order_data:
                logger.error(f"Order {order_id} not found")
                return False
            
            # Get menu item details for display
            menu_item_details = await self._get_menu_item_details(menu_item_id)
            
            # Calculate modifier cost breakdown
            modifier_cost_breakdown = await self._get_modifier_cost_breakdown(menu_item_id, modifications or {})
            
            # Create order item
            order_item = {
                "id": f"item_{int(datetime.now().timestamp() * 1000)}",
                "menu_item_id": menu_item_id,
                "quantity": quantity,
                "modifications": modifications or {},
                "modifier_costs": modifier_cost_breakdown,  # Add modifier cost breakdown
                "added_at": datetime.now().isoformat(),
                "menu_item": menu_item_details  # Include menu item details
            }
            
            # Add to order items
            if "items" not in order_data:
                order_data["items"] = []
            
            order_data["items"].append(order_item)
            
            # Recalculate order totals
            order_data = await self._recalculate_order_totals(order_data)
            
            # Update order
            return await self.update_order(order_id, order_data)
            
        except Exception as e:
            logger.error(f"Error adding item to order {order_id}: {e}")
            return False
    
    async def _get_menu_item_details(self, menu_item_id: int) -> Dict[str, Any]:
        """Get menu item details for display"""
        try:
            if self.menu_item_service:
                menu_item = await self.menu_item_service.get_by_id(menu_item_id)
                if menu_item:
                    return {
                        "id": menu_item.id,
                        "name": menu_item.name,
                        "price": float(menu_item.price),
                        "description": menu_item.description,
                        "image_url": menu_item.image_url
                    }
        except Exception as e:
            logger.error(f"Error getting menu item details for {menu_item_id}: {e}")
        
        # Fallback if service not available or item not found
        return {
            "id": menu_item_id,
            "name": "Unknown Item",
            "price": 0.0,
            "description": None,
            "image_url": None
        }
    
    async def _recalculate_order_totals(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate order totals based on items including ingredient modifier costs"""
        try:
            items = order_data.get("items", [])
            subtotal = 0.0
            
            # Calculate subtotal from all items including modifier costs
            for item in items:
                item_price = item.get("menu_item", {}).get("price", 0.0)
                quantity = item.get("quantity", 1)
                modifications = item.get("modifications", {})
                
                # Calculate base item total
                base_item_total = item_price * quantity
                
                # Calculate modifier costs
                modifier_costs = await self._calculate_modifier_costs(
                    item.get("menu_item_id"), 
                    modifications
                )
                
                # Total item cost = base cost + modifier costs
                item_total = base_item_total + modifier_costs
                subtotal += item_total
                
                logger.info(f"Item calculation: base={base_item_total}, modifiers={modifier_costs}, total={item_total}")
            
            # For demo purposes, no tax calculation
            # In production, this would be handled by a tax service based on location/business rules
            tax_amount = 0.0
            total_amount = subtotal
            
            # Update order totals
            order_data["subtotal"] = round(subtotal, 2)
            order_data["tax_amount"] = round(tax_amount, 2)
            order_data["total_amount"] = round(total_amount, 2)
            
            logger.info(f"Recalculated order totals: subtotal={subtotal}, tax={tax_amount}, total={total_amount}")
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error recalculating order totals: {e}")
            return order_data
    
    async def _get_modifier_cost_breakdown(self, menu_item_id: int, modifications: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get detailed breakdown of modifier costs for an order item.
        
        Args:
            menu_item_id: ID of the menu item
            modifications: Modifications dictionary containing modifiers list
            
        Returns:
            List of modifier cost details
        """
        try:
            modifier_costs = []
            modifiers = modifications.get("modifiers", [])
            
            if not modifiers:
                return modifier_costs
            
            # Process each modifier tuple (ingredient_id, action)
            for modifier in modifiers:
                if not isinstance(modifier, (list, tuple)) or len(modifier) != 2:
                    continue
                    
                ingredient_id, action = modifier
                
                # Only charge for "extra" type modifications
                if action not in ["extra", "heavy", "double", "more", "additional"]:
                    continue
                
                # Look up the MenuItemIngredient record to get additional_cost and ingredient name
                from app.models.menu_item_ingredient import MenuItemIngredient
                from app.models.ingredient import Ingredient
                
                menu_item_ingredient = await MenuItemIngredient.filter(
                    menu_item_id=menu_item_id,
                    ingredient_id=ingredient_id
                ).first()
                
                if menu_item_ingredient and menu_item_ingredient.additional_cost:
                    # Get ingredient name
                    ingredient = await Ingredient.get_or_none(id=ingredient_id)
                    ingredient_name = ingredient.name if ingredient else f"ingredient_{ingredient_id}"
                    
                    additional_cost = float(menu_item_ingredient.additional_cost)
                    
                    modifier_costs.append({
                        "ingredient_id": ingredient_id,
                        "ingredient_name": ingredient_name,
                        "action": action,
                        "cost": additional_cost
                    })
                    
                    logger.info(f"Modifier cost breakdown: ingredient_id={ingredient_id}, name={ingredient_name}, action={action}, cost={additional_cost}")
            
            return modifier_costs
            
        except Exception as e:
            logger.error(f"Error getting modifier cost breakdown: {e}")
            return []

    async def _calculate_modifier_costs(self, menu_item_id: int, modifications: Dict[str, Any]) -> float:
        """
        Calculate additional costs for ingredient modifications
        
        Args:
            menu_item_id: ID of the menu item
            modifications: Dictionary containing modification data with modifiers list
            
        Returns:
            Total additional cost for all modifiers
        """
        try:
            if not modifications or not modifications.get("modifiers"):
                return 0.0
            
            modifiers = modifications.get("modifiers", [])
            if not isinstance(modifiers, list):
                return 0.0
            
            total_modifier_cost = 0.0
            
            # Process each modifier tuple (ingredient_id, action)
            for modifier in modifiers:
                if not isinstance(modifier, (list, tuple)) or len(modifier) != 2:
                    continue
                    
                ingredient_id, action = modifier
                
                # Only charge for "extra" type modifications
                if action not in ["extra", "heavy", "double", "more", "additional"]:
                    continue
                
                # Look up the MenuItemIngredient record to get additional_cost
                from app.models.menu_item_ingredient import MenuItemIngredient
                
                menu_item_ingredient = await MenuItemIngredient.filter(
                    menu_item_id=menu_item_id,
                    ingredient_id=ingredient_id
                ).first()
                
                if menu_item_ingredient and menu_item_ingredient.additional_cost:
                    additional_cost = float(menu_item_ingredient.additional_cost)
                    total_modifier_cost += additional_cost
                    
                    logger.info(f"Modifier cost: ingredient_id={ingredient_id}, action={action}, cost={additional_cost}")
            
            logger.info(f"Total modifier costs for menu_item_id={menu_item_id}: {total_modifier_cost}")
            return total_modifier_cost
            
        except Exception as e:
            logger.error(f"Error calculating modifier costs: {e}")
            return 0.0
    
    async def remove_item_from_order(self, order_id: str, item_id: str) -> bool:
        """
        Remove an item from an order
        
        Args:
            order_id: Order ID
            item_id: Order item ID to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            order_data = await self.get_order(order_id)
            if not order_data:
                logger.error(f"Order {order_id} not found")
                return False
            
            # Remove item from order
            if "items" in order_data:
                order_data["items"] = [
                    item for item in order_data["items"] 
                    if item.get("id") != item_id
                ]
            
            # Update order
            return await self.update_order(order_id, order_data)
            
        except Exception as e:
            logger.error(f"Error removing item from order {order_id}: {e}")
            return False
    
    async def clear_order(self, order_id: str) -> bool:
        """
        Clear all items from an order
        
        Args:
            order_id: Order ID to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.update_order(order_id, {"items": []})
    
    async def finalize_order(self, order_id: str) -> bool:
        """
        Finalize an order (set status to completed)
        
        Args:
            order_id: Order ID to finalize
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.update_order(order_id, {"status": "completed"})
    
    async def delete_order(self, order_id: str) -> bool:
        """
        Delete an order
        
        Args:
            order_id: Order ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot delete order")
            return False
        
        try:
            success = await self.redis.delete(f"order:{order_id}")
            
            if success:
                logger.info(f"Deleted order {order_id}")
                return True
            else:
                logger.error(f"Failed to delete order {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {e}")
            return False
    
    async def archive_order_to_postgres(self, order_id: str) -> bool:
        """
        Archive a completed order from Redis to PostgreSQL
        
        Args:
            order_id: Order ID to archive
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.order_service:
                logger.warning("PostgreSQL OrderService not available for archiving")
                return False
            
            # Get order data from Redis
            order_data = await self.get_order(order_id)
            if not order_data:
                logger.error(f"Order {order_id} not found in Redis for archiving")
                return False
            
            # Convert Redis order data to PostgreSQL format
            from app.dto.order_dto import OrderCreateDto
            from app.dto.order_item_dto import OrderItemCreateDto
            
            # Create main order
            order_create_dto = OrderCreateDto(
                customer_name=None,  # Anonymous order
                customer_phone=None,
                restaurant_id=order_data["restaurant_id"],
                subtotal=Decimal(str(order_data.get("subtotal", 0.0))),
                tax_amount=Decimal(str(order_data.get("tax_amount", 0.0))),
                total_amount=Decimal(str(order_data.get("total_amount", 0.0))),
                special_instructions=None,
                status="confirmed"  # Mark as confirmed
            )
            
            # Create order in PostgreSQL
            postgres_order = await self.order_service.create(order_create_dto)
            if not postgres_order:
                logger.error(f"Failed to create order in PostgreSQL for Redis order {order_id}")
                return False
            
            # Create order items using OrderItemService
            from app.services.order_item_service import OrderItemService
            from app.services.menu_item_service import MenuItemService
            
            order_item_service = OrderItemService()
            menu_item_service = MenuItemService()
            
            for item in order_data.get("items", []):
                # Get menu item to get actual price
                menu_item = await menu_item_service.get_by_id(item["menu_item_id"])
                unit_price = Decimal(str(menu_item.price)) if menu_item else Decimal("0.0")
                
                order_item_dto = OrderItemCreateDto(
                    order_id=postgres_order.id,
                    menu_item_id=item["menu_item_id"],
                    quantity=item["quantity"],
                    unit_price=unit_price,
                    special_instructions=item.get("modifications", {}).get("instructions")
                )
                
                await order_item_service.create(order_item_dto)
            
            logger.info(f"Successfully archived order {order_id} to PostgreSQL as order {postgres_order.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving order {order_id} to PostgreSQL: {e}")
            return False
