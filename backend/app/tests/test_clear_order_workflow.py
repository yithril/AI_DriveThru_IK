"""
Unit tests for ClearOrderWorkflow
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.clear_order_workflow import ClearOrderWorkflow, ClearOrderWorkflowResult
from app.constants.audio_phrases import AudioPhraseType


class TestClearOrderWorkflow:
    """Test cases for ClearOrderWorkflow"""
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Create mock order session service for testing"""
        return AsyncMock()
    
    @pytest.fixture
    def clear_order_workflow(self, mock_order_session_service):
        """Create ClearOrderWorkflow instance for testing"""
        return ClearOrderWorkflow(order_session_service=mock_order_session_service)
    
    @pytest.mark.asyncio
    async def test_execute_successful_clear(self, clear_order_workflow, mock_order_session_service):
        """Test successful order clearing"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "items": [
                {"id": "item_1", "name": "Burger", "quantity": 1},
                {"id": "item_2", "name": "Fries", "quantity": 1}
            ]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.clear_order.return_value = True
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert isinstance(result, ClearOrderWorkflowResult)
        assert result.success is True
        assert result.message == "Your order has been cleared. Would you like to start over?"
        assert result.order_updated is True
        assert result.audio_phrase_type == AudioPhraseType.ORDER_CLEARED_SUCCESS
        assert result.workflow_type.value == "clear_order"
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_called_once_with("order_123")
    
    @pytest.mark.asyncio
    async def test_execute_no_active_order(self, clear_order_workflow, mock_order_session_service):
        """Test clearing when no active order exists"""
        mock_order_session_service.get_session_order.return_value = None
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "No active order found to clear."
        assert result.audio_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_order_already_empty(self, clear_order_workflow, mock_order_session_service):
        """Test clearing when order is already empty"""
        # Mock order with no items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "items": []
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "Your order is already empty."
        assert result.audio_phrase_type == AudioPhraseType.ORDER_ALREADY_EMPTY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_missing_order_id(self, clear_order_workflow, mock_order_session_service):
        """Test clearing when order ID is missing"""
        # Mock order without ID
        mock_order = {
            "session_id": "session_123",
            "items": [{"id": "item_1", "name": "Burger", "quantity": 1}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "Order ID not found. Please try again."
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_clear_service_failure(self, clear_order_workflow, mock_order_session_service):
        """Test when clear order service fails"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "items": [{"id": "item_1", "name": "Burger", "quantity": 1}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.clear_order.return_value = False
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "Sorry, I couldn't clear your order. Please try again."
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_called_once_with("order_123")
    
    @pytest.mark.asyncio
    async def test_execute_service_exception(self, clear_order_workflow, mock_order_session_service):
        """Test handling of service exceptions"""
        mock_order_session_service.get_session_order.side_effect = Exception("Service error")
        
        result = await clear_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert result.message == "Sorry, I couldn't clear your order. Please try again."
        assert result.error == "Service error"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.clear_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_with_conversation_history(self, clear_order_workflow, mock_order_session_service):
        """Test clearing order with conversation history (should be ignored)"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "items": [{"id": "item_1", "name": "Burger", "quantity": 1}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.clear_order.return_value = True
        
        conversation_history = [
            {"role": "customer", "content": "I want to clear my order"},
            {"role": "assistant", "content": "I'll help you clear your order."}
        ]
        
        result = await clear_order_workflow.execute(
            session_id="session_123",
            conversation_history=conversation_history
        )
        
        assert result.success is True
        assert result.message == "Your order has been cleared. Would you like to start over?"
        assert result.order_updated is True
