"""
Integration tests for ClearOrderWorkflow using real services
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.clear_order_workflow import ClearOrderWorkflow, ClearOrderWorkflowResult
from app.services.order_session_service import OrderSessionService
from app.constants.audio_phrases import AudioPhraseType


class TestClearOrderWorkflowIntegration:
    """Integration tests for ClearOrderWorkflow with real services"""
    
    @pytest.fixture
    def mock_redis_service(self):
        """Create mock Redis service"""
        return AsyncMock()
    
    @pytest.fixture
    def order_session_service(self, mock_redis_service):
        """Create mock OrderSessionService"""
        service = AsyncMock(spec=OrderSessionService)
        return service
    
    @pytest.fixture
    def clear_order_workflow(self, order_session_service):
        """Create ClearOrderWorkflow instance for integration testing"""
        return ClearOrderWorkflow(order_session_service=order_session_service)
    
    @pytest.mark.asyncio
    async def test_clear_order_with_items_success(
        self, 
        clear_order_workflow, 
        order_session_service
    ):
        """Test successful order clearing with items"""
        # Mock order data with items
        mock_order_data = {
            "id": "order_1234567890",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {
                    "id": "item_1",
                    "menu_item_id": 1,
                    "quantity": 1,
                    "modifications": {
                        "size": "regular",
                        "name": "Burger",
                        "unit_price": 8.99,
                        "total_price": 8.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                },
                {
                    "id": "item_2",
                    "menu_item_id": 2,
                    "quantity": 1,
                    "modifications": {
                        "size": "regular",
                        "name": "Fries",
                        "unit_price": 3.99,
                        "total_price": 3.99
                    },
                    "added_at": "2024-01-01T12:01:00"
                }
            ],
            "total_amount": 12.98,
            "subtotal": 12.98,
            "created_at": "2024-01-01T12:00:00"
        }
        
        # Mock service methods
        order_session_service.get_session_order.return_value = mock_order_data
        order_session_service.clear_order.return_value = True
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert isinstance(result, ClearOrderWorkflowResult)
        assert result.success is True
        assert result.workflow_type.value == "clear_order"
        assert result.message == "Your order has been cleared. Would you like to start over?"
        assert result.order_updated is True
        assert result.audio_phrase_type == AudioPhraseType.ORDER_CLEARED_SUCCESS
        
        # Verify service calls
        order_session_service.get_session_order.assert_called_once_with("session_123")
        order_session_service.clear_order.assert_called_once_with("order_1234567890")
    
    @pytest.mark.asyncio
    async def test_clear_order_no_active_order(
        self, 
        clear_order_workflow, 
        order_session_service
    ):
        """Test clearing when no active order exists"""
        # Mock service to return None (no order found)
        order_session_service.get_session_order.return_value = None
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "No active order found to clear."
        assert result.audio_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        # Verify service calls
        order_session_service.get_session_order.assert_called_once_with("session_123")
        order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_order_already_empty(
        self, 
        clear_order_workflow, 
        order_session_service
    ):
        """Test clearing when order is already empty"""
        # Mock empty order data
        mock_order_data = {
            "id": "order_1234567890",
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [],  # Empty items list
            "total_amount": 0.0,
            "subtotal": 0.0,
            "created_at": "2024-01-01T12:00:00"
        }
        
        # Mock service methods
        order_session_service.get_session_order.return_value = mock_order_data
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        # The workflow correctly detects empty order and returns early
        assert result.success is False
        assert result.message == "Your order is already empty."
        assert result.audio_phrase_type == AudioPhraseType.ORDER_ALREADY_EMPTY
        
        # Verify service calls
        order_session_service.get_session_order.assert_called_once_with("session_123")
        order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_order_service_error(
        self, 
        clear_order_workflow, 
        order_session_service
    ):
        """Test handling of service errors"""
        # Mock service to raise an exception
        order_session_service.get_session_order.side_effect = Exception("Service error")
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        # When service fails, the workflow catches the exception
        assert result.success is False
        assert result.message == "Sorry, I couldn't clear your order. Please try again."
        assert result.error == "Service error"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        order_session_service.get_session_order.assert_called_once_with("session_123")
        order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_order_missing_order_id(
        self, 
        clear_order_workflow, 
        order_session_service
    ):
        """Test clearing when order ID is missing"""
        # Mock order data without ID
        mock_order_data = {
            "session_id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "items": [
                {
                    "id": "item_1",
                    "menu_item_id": 1,
                    "quantity": 1,
                    "modifications": {
                        "size": "regular",
                        "name": "Burger",
                        "unit_price": 8.99,
                        "total_price": 8.99
                    }
                }
            ],
            "total_amount": 8.99,
            "subtotal": 8.99,
            "created_at": "2024-01-01T12:00:00"
            # Note: missing "id" field
        }
        
        # Mock service methods
        order_session_service.get_session_order.return_value = mock_order_data
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        # The workflow correctly detects missing order ID and returns early
        assert result.success is False
        assert result.message == "Order ID not found. Please try again."
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        order_session_service.get_session_order.assert_called_once_with("session_123")
        order_session_service.clear_order.assert_not_called()
