"""
Order Data Converter

Converts between Redis order format (used by OrderSessionService) 
and PostgreSQL order format (used by ModifyItemService and agents)
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal


class OrderDataConverter:
    """Static converter for order data between Redis and PostgreSQL formats"""
    
    @staticmethod
    def redis_to_postgresql_format(redis_order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert Redis order items to format expected by modify_item_service and agents
        
        Redis format:
        {
            "id": "order_1234567890",
            "session_id": "session_123",
            "restaurant_id": 1,
            "items": [
                {
                    "id": "item_1234567890",
                    "menu_item_id": 1,
                    "quantity": 1,
                    "modifications": {"size": "large", "special_instructions": "No pickles"},
                    "added_at": "2024-01-01T12:00:00"
                }
            ]
        }
        
        PostgreSQL format (expected by agents/services):
        [
            {
                "id": 1,
                "name": "Burger",
                "quantity": 1,
                "size": "large",
                "special_instructions": "No pickles",
                "unit_price": 10.00,
                "total_price": 10.00
            }
        ]
        
        Args:
            redis_order_data: Order data from Redis
            
        Returns:
            List of order items in PostgreSQL format
        """
        if not redis_order_data or "items" not in redis_order_data:
            return []
        
        postgresql_items = []
        
        for redis_item in redis_order_data["items"]:
            # Extract modifications
            modifications = redis_item.get("modifications", {})
            
            # Convert Redis item to PostgreSQL format
            postgresql_item = {
                "id": int(redis_item["id"].split("_")[1]) if "_" in redis_item["id"] else redis_item["id"],
                "menu_item_id": redis_item["menu_item_id"],
                "quantity": redis_item["quantity"],
                "size": modifications.get("size", "regular"),
                "special_instructions": modifications.get("special_instructions"),
                "unit_price": modifications.get("unit_price", 0.0),
                "total_price": modifications.get("total_price", 0.0)
            }
            
            # Try to get menu item name (if available in modifications)
            if "name" in modifications:
                postgresql_item["name"] = modifications["name"]
            else:
                # Fallback - we'll need to fetch this from menu service
                postgresql_item["name"] = f"Item {redis_item['menu_item_id']}"
            
            postgresql_items.append(postgresql_item)
        
        return postgresql_items
    
    @staticmethod
    def postgresql_to_redis_format(
        modified_items: List[Dict[str, Any]], 
        original_redis_order: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert modified PostgreSQL items back to Redis format for updating
        
        Args:
            modified_items: Modified items from modify_item_service
            original_redis_order: Original Redis order data
            
        Returns:
            Redis order data with updated items
        """
        if not original_redis_order:
            return {}
        
        # Create a mapping of item IDs to modified data
        modified_map = {}
        for item in modified_items:
            modified_map[item["id"]] = item
        
        # Update the Redis order items
        updated_items = []
        
        for redis_item in original_redis_order.get("items", []):
            item_id = int(redis_item["id"].split("_")[1]) if "_" in redis_item["id"] else redis_item["id"]
            
            if item_id in modified_map:
                # Update this item with modified data
                modified_item = modified_map[item_id]
                
                # Update the Redis item
                redis_item["quantity"] = modified_item["quantity"]
                
                # Update modifications
                if "modifications" not in redis_item:
                    redis_item["modifications"] = {}
                
                redis_item["modifications"]["size"] = modified_item["size"]
                if modified_item.get("special_instructions"):
                    redis_item["modifications"]["special_instructions"] = modified_item["special_instructions"]
                
                # Update pricing if available
                if "unit_price" in modified_item:
                    redis_item["modifications"]["unit_price"] = float(modified_item["unit_price"])
                if "total_price" in modified_item:
                    redis_item["modifications"]["total_price"] = float(modified_item["total_price"])
            
            updated_items.append(redis_item)
        
        # Create updated Redis order data
        updated_order = original_redis_order.copy()
        updated_order["items"] = updated_items
        
        return updated_order
    
    @staticmethod
    def create_redis_order_item(
        menu_item_id: int,
        quantity: int,
        size: str = "regular",
        special_instructions: Optional[str] = None,
        unit_price: float = 0.0,
        total_price: float = 0.0,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Redis order item from individual parameters
        
        Args:
            menu_item_id: ID of the menu item
            quantity: Quantity to order
            size: Size of the item
            special_instructions: Special instructions
            unit_price: Unit price
            total_price: Total price
            name: Name of the menu item
            
        Returns:
            Redis order item format
        """
        import time
        
        modifications = {
            "size": size,
            "unit_price": unit_price,
            "total_price": total_price
        }
        
        if special_instructions:
            modifications["special_instructions"] = special_instructions
        
        if name:
            modifications["name"] = name
        
        return {
            "id": f"item_{int(time.time() * 1000)}",
            "menu_item_id": menu_item_id,
            "quantity": quantity,
            "modifications": modifications,
            "added_at": "2024-01-01T12:00:00"  # This would be set by the service
        }
    
    @staticmethod
    def extract_order_summary(redis_order_data: Dict[str, Any]) -> str:
        """
        Extract a human-readable summary of the order
        
        Args:
            redis_order_data: Order data from Redis
            
        Returns:
            Human-readable order summary
        """
        if not redis_order_data or "items" not in redis_order_data:
            return "No items in order"
        
        items = []
        for item in redis_order_data["items"]:
            modifications = item.get("modifications", {})
            name = modifications.get("name", f"Item {item['menu_item_id']}")
            quantity = item["quantity"]
            size = modifications.get("size", "regular")
            
            item_summary = f"{quantity}x {name}"
            if size != "regular":
                item_summary += f" ({size})"
            
            if modifications.get("special_instructions"):
                item_summary += f" - {modifications['special_instructions']}"
            
            items.append(item_summary)
        
        return "; ".join(items)
