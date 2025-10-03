"""
Unit tests for OrderSessionService - Redis-based order management
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.services.order_session_service import OrderSessionService


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing"""
    redis_service = AsyncMock()
    redis_service.get.return_value = None
    redis_service.set.return_value = True
    redis_service.set_json.return_value = True
    redis_service.get_json.return_value = None
    redis_service.delete.return_value = True
    return redis_service


@pytest.fixture
def mock_order_service():
    """Mock PostgreSQL OrderService for testing"""
    return AsyncMock()


@pytest.fixture
def order_session_service(mock_redis_service, mock_order_service):
    """Fixture for OrderSessionService"""
    return OrderSessionService(mock_redis_service, mock_order_service)


class TestOrderSessionService:
    """Test OrderSessionService operations"""

    async def test_is_redis_available_success(self, order_session_service, mock_redis_service):
        """Test Redis availability check when Redis is available"""
        mock_redis_service.get.return_value = "ok"
        
        result = await order_session_service.is_redis_available()
        
        assert result is True
        mock_redis_service.get.assert_called_once_with("health_check")

    async def test_is_redis_available_failure(self, order_session_service, mock_redis_service):
        """Test Redis availability check when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Connection failed")
        
        result = await order_session_service.is_redis_available()
        
        assert result is False

    async def test_create_order_success(self, order_session_service, mock_redis_service):
        """Test successful order creation"""
        mock_redis_service.set_json.return_value = True
        mock_redis_service.set.return_value = True
        
        order_id = await order_session_service.create_order(
            session_id="session_123",
            restaurant_id=1
        )
        
        assert order_id is not None
        assert order_id.startswith("order_")
        
        # Verify Redis calls
        mock_redis_service.set_json.assert_called_once()
        mock_redis_service.set.assert_called_once()
        
        # Check the order data structure
        call_args = mock_redis_service.set_json.call_args
        order_data = call_args[0][1]  # Second argument is the data
        assert order_data["session_id"] == "session_123"
        assert order_data["restaurant_id"] == 1
        assert order_data["status"] == "active"
        assert order_data["items"] == []
        assert order_data["subtotal"] == 0.0

    async def test_create_order_redis_unavailable(self, order_session_service, mock_redis_service):
        """Test order creation when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Redis unavailable")
        
        order_id = await order_session_service.create_order(
            session_id="session_123",
            restaurant_id=1
        )
        
        assert order_id is None

    async def test_get_order_success(self, order_session_service, mock_redis_service):
        """Test successful order retrieval"""
        expected_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": []
        }
        mock_redis_service.get_json.return_value = expected_data
        
        result = await order_session_service.get_order("order_123")
        
        assert result == expected_data
        mock_redis_service.get_json.assert_called_once_with("order:order_123")

    async def test_get_order_not_found(self, order_session_service, mock_redis_service):
        """Test order retrieval when order doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await order_session_service.get_order("nonexistent")
        
        assert result is None

    async def test_get_session_order_success(self, order_session_service, mock_redis_service):
        """Test successful session order retrieval"""
        expected_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active"
        }
        
        # Mock the get method to return different values for different keys
        def mock_get(key):
            if key == "health_check":
                return "ok"
            elif key == "session:session_123:current_order":
                return "order_123"
            return None
        
        mock_redis_service.get.side_effect = mock_get
        mock_redis_service.get_json.return_value = expected_data
        
        result = await order_session_service.get_session_order("session_123")
        
        assert result == expected_data
        mock_redis_service.get_json.assert_called_once_with("order:order_123")

    async def test_get_session_order_no_current(self, order_session_service, mock_redis_service):
        """Test session order retrieval when no current order exists"""
        mock_redis_service.get.return_value = None
        
        result = await order_session_service.get_session_order("session_123")
        
        assert result is None

    async def test_update_order_success(self, order_session_service, mock_redis_service):
        """Test successful order update"""
        existing_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "subtotal": 0.0
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        updates = {"status": "completed", "subtotal": 15.99}
        result = await order_session_service.update_order("order_123", updates)
        
        assert result is True
        
        # Verify the updated data
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]  # Second argument is the data
        assert updated_data["status"] == "completed"
        assert updated_data["subtotal"] == 15.99
        assert "updated_at" in updated_data

    async def test_update_order_not_found(self, order_session_service, mock_redis_service):
        """Test order update when order doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        updates = {"status": "completed"}
        result = await order_session_service.update_order("nonexistent", updates)
        
        assert result is False

    async def test_add_item_to_order_success(self, order_session_service, mock_redis_service):
        """Test successful item addition to order"""
        existing_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": []
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await order_session_service.add_item_to_order(
            order_id="order_123",
            menu_item_id=1,
            quantity=2,
            modifications={"extra_cheese": True}
        )
        
        assert result is True
        
        # Verify the item was added
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert len(updated_data["items"]) == 1
        item = updated_data["items"][0]
        assert item["menu_item_id"] == 1
        assert item["quantity"] == 2
        assert item["modifications"] == {"extra_cheese": True}
        assert item["id"].startswith("item_")

    async def test_add_item_to_order_not_found(self, order_session_service, mock_redis_service):
        """Test item addition when order doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await order_session_service.add_item_to_order(
            order_id="nonexistent",
            menu_item_id=1
        )
        
        assert result is False

    async def test_remove_item_from_order_success(self, order_session_service, mock_redis_service):
        """Test successful item removal from order"""
        existing_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {"id": "item_1", "menu_item_id": 1, "quantity": 1},
                {"id": "item_2", "menu_item_id": 2, "quantity": 2}
            ]
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await order_session_service.remove_item_from_order("order_123", "item_1")
        
        assert result is True
        
        # Verify the item was removed
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert len(updated_data["items"]) == 1
        assert updated_data["items"][0]["id"] == "item_2"

    async def test_remove_item_from_order_not_found(self, order_session_service, mock_redis_service):
        """Test item removal when order doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await order_session_service.remove_item_from_order("nonexistent", "item_1")
        
        assert result is False

    async def test_clear_order_success(self, order_session_service, mock_redis_service):
        """Test successful order clearing"""
        existing_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {"id": "item_1", "menu_item_id": 1, "quantity": 1}
            ]
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await order_session_service.clear_order("order_123")
        
        assert result is True
        
        # Verify the order was cleared
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert updated_data["items"] == []

    async def test_finalize_order_success(self, order_session_service, mock_redis_service):
        """Test successful order finalization"""
        existing_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active"
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await order_session_service.finalize_order("order_123")
        
        assert result is True
        
        # Verify the order was finalized
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert updated_data["status"] == "completed"

    async def test_delete_order_success(self, order_session_service, mock_redis_service):
        """Test successful order deletion"""
        mock_redis_service.delete.return_value = True
        
        result = await order_session_service.delete_order("order_123")
        
        assert result is True
        mock_redis_service.delete.assert_called_once_with("order:order_123")

    async def test_archive_order_to_postgres_success(self, order_session_service, mock_redis_service, mock_order_service):
        """Test successful order archiving to PostgreSQL"""
        order_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "completed",
            "items": []
        }
        mock_redis_service.get_json.return_value = order_data
        mock_order_service.create.return_value = True
        
        result = await order_session_service.archive_order_to_postgres("order_123")
        
        # For now, this should return True (placeholder implementation)
        assert result is True

    async def test_archive_order_to_postgres_no_order_service(self, order_session_service, mock_redis_service):
        """Test order archiving when PostgreSQL OrderService is not available"""
        order_data = {
            "id": "order_123",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "completed"
        }
        mock_redis_service.get_json.return_value = order_data
        
        # Create service without PostgreSQL OrderService
        service_without_postgres = OrderSessionService(mock_redis_service, None)
        result = await service_without_postgres.archive_order_to_postgres("order_123")
        
        assert result is False

    async def test_redis_error_handling(self, order_session_service, mock_redis_service):
        """Test error handling when Redis operations fail"""
        mock_redis_service.get.side_effect = Exception("Redis error")
        
        # Test various operations that should handle Redis errors gracefully
        assert await order_session_service.is_redis_available() is False
        assert await order_session_service.create_order("session_123", 1) is None
        assert await order_session_service.get_order("test") is None
        assert await order_session_service.get_session_order("test") is None
        assert await order_session_service.update_order("test", {}) is False
        assert await order_session_service.add_item_to_order("test", 1) is False
        assert await order_session_service.remove_item_from_order("test", "item_1") is False
        assert await order_session_service.clear_order("test") is False
        assert await order_session_service.finalize_order("test") is False
        assert await order_session_service.delete_order("test") is False

    async def test_calculate_modifier_costs_with_extra_ingredients(self, order_session_service):
        """Test modifier cost calculation for extra ingredients"""
        # Mock the MenuItemIngredient model
        from unittest.mock import patch, AsyncMock
        
        mock_ingredient = AsyncMock()
        mock_ingredient.additional_cost = 0.50  # $0.50 extra for cheese
        
        with patch('app.services.order_session_service.MenuItemIngredient') as mock_model:
            mock_model.filter.return_value.first.return_value = mock_ingredient
            
            modifications = {
                "modifiers": [
                    [1, "extra"],  # ingredient_id=1, action="extra"
                    [2, "no"]       # ingredient_id=2, action="no" (should not charge)
                ]
            }
            
            result = await order_session_service._calculate_modifier_costs(
                menu_item_id=1,
                modifications=modifications
            )
            
            assert result == 0.50  # Only the "extra" modifier should be charged

    async def test_calculate_modifier_costs_no_modifiers(self, order_session_service):
        """Test modifier cost calculation with no modifiers"""
        modifications = {}
        
        result = await order_session_service._calculate_modifier_costs(
            menu_item_id=1,
            modifications=modifications
        )
        
        assert result == 0.0

    async def test_calculate_modifier_costs_invalid_data(self, order_session_service):
        """Test modifier cost calculation with invalid modifier data"""
        modifications = {
            "modifiers": [
                "invalid_modifier",  # Not a tuple
                [1, "extra", "too_many"],  # Too many elements
                [1, "extra"]  # Valid modifier
            ]
        }
        
        # Mock the MenuItemIngredient model
        from unittest.mock import patch, AsyncMock
        
        mock_ingredient = AsyncMock()
        mock_ingredient.additional_cost = 0.75
        
        with patch('app.services.order_session_service.MenuItemIngredient') as mock_model:
            mock_model.filter.return_value.first.return_value = mock_ingredient
            
            result = await order_session_service._calculate_modifier_costs(
                menu_item_id=1,
                modifications=modifications
            )
            
            assert result == 0.75  # Only the valid modifier should be processed