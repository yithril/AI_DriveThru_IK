"""
Integration tests for ConfirmOrderWorkflow using real services
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.confirm_order_workflow import ConfirmOrderWorkflow, ConfirmOrderWorkflowResult
from app.services.order_session_service import OrderSessionService
from app.constants.audio_phrases import AudioPhraseType


class TestConfirmOrderWorkflowIntegration:
    """Integration tests for ConfirmOrderWorkflow with real services"""
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Create mock OrderSessionService"""
        service = AsyncMock(spec=OrderSessionService)
        return service
    
    @pytest.fixture
    def confirm_order_workflow(self, mock_order_session_service):
        """Create ConfirmOrderWorkflow instance for integration testing"""
        return ConfirmOrderWorkflow(order_session_service=mock_order_session_service)
    
    @pytest.mark.asyncio
    async def test_confirm_order_with_items_success(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test successful order confirmation with items"""
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
                        "size": "large",
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
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.archive_order_to_postgres.return_value = True
        mock_order_session_service.finalize_order.return_value = True
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert isinstance(result, ConfirmOrderWorkflowResult)
        assert result.success is True
        assert result.workflow_type.value == "confirm_order"
        assert "Perfect! If everything looks correct on your screen" in result.message
        assert "$12.98" in result.message
        assert "Pull around to the next window" in result.message
        assert result.order_updated is True
        assert result.total_cost == 12.98
        assert result.audio_phrase_type == AudioPhraseType.ORDER_CONFIRMED
        assert result.order_summary == "1x Burger; 1x Fries (large)"
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_1234567890")
        mock_order_session_service.finalize_order.assert_called_once_with("order_1234567890")
        
        # Verify result data
        assert result.data["order_id"] == "order_1234567890"
        assert result.data["total_amount"] == 12.98
        assert result.data["item_count"] == 2
        assert result.data["archived_to_postgres"] is True
        assert result.data["session_finalized"] is True
    
    @pytest.mark.asyncio
    async def test_confirm_order_no_active_order(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test confirmation when no active order exists"""
        # Mock service to return None (no order found)
        mock_order_session_service.get_session_order.return_value = None
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "No active order found to confirm" in result.message
        assert result.audio_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_order_empty_order(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test confirmation when order is empty"""
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
        mock_order_session_service.get_session_order.return_value = mock_order_data
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "Your order is empty" in result.message
        assert result.audio_phrase_type == AudioPhraseType.ORDER_ALREADY_EMPTY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_order_archive_failure_continues(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test that archive failure doesn't prevent confirmation"""
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
                    }
                }
            ],
            "total_amount": 8.99,
            "subtotal": 8.99,
            "created_at": "2024-01-01T12:00:00"
        }
        
        # Mock service methods - archive fails
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.archive_order_to_postgres.return_value = False
        mock_order_session_service.finalize_order.return_value = True
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        # Should still succeed even if archive fails
        assert result.success is True
        assert "Perfect! If everything looks correct" in result.message
        assert "$8.99" in result.message
        assert result.data["archived_to_postgres"] is False
        assert result.data["session_finalized"] is True
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_1234567890")
        mock_order_session_service.finalize_order.assert_called_once_with("order_1234567890")
    
    @pytest.mark.asyncio
    async def test_confirm_order_finalize_failure_continues(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test that finalize failure doesn't prevent confirmation"""
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
                    }
                }
            ],
            "total_amount": 8.99,
            "subtotal": 8.99,
            "created_at": "2024-01-01T12:00:00"
        }
        
        # Mock service methods - finalize fails
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.archive_order_to_postgres.return_value = True
        mock_order_session_service.finalize_order.return_value = False
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        # Should still succeed even if finalize fails
        assert result.success is True
        assert "Perfect! If everything looks correct" in result.message
        assert "$8.99" in result.message
        assert result.data["archived_to_postgres"] is True
        assert result.data["session_finalized"] is False
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_1234567890")
        mock_order_session_service.finalize_order.assert_called_once_with("order_1234567890")
    
    @pytest.mark.asyncio
    async def test_confirm_order_service_error(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test handling of service errors"""
        # Mock service to raise an exception
        mock_order_session_service.get_session_order.side_effect = Exception("Service error")
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        # When service fails, the workflow catches the exception
        assert result.success is False
        assert "Sorry, I couldn't confirm your order" in result.message
        assert result.error == "Service error"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_confirm_order_missing_order_id(
        self, 
        confirm_order_workflow, 
        mock_order_session_service
    ):
        """Test confirmation when order ID is missing"""
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
        mock_order_session_service.get_session_order.return_value = mock_order_data
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "Order ID not found" in result.message
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
