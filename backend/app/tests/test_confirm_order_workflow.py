"""
Unit tests for ConfirmOrderWorkflow
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.confirm_order_workflow import ConfirmOrderWorkflow, ConfirmOrderWorkflowResult
from app.constants.audio_phrases import AudioPhraseType


class TestConfirmOrderWorkflow:
    """Test cases for ConfirmOrderWorkflow"""
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Create mock order session service for testing"""
        return AsyncMock()
    
    @pytest.fixture
    def confirm_order_workflow(self, mock_order_session_service):
        """Create ConfirmOrderWorkflow instance for testing"""
        return ConfirmOrderWorkflow(order_session_service=mock_order_session_service)
    
    @pytest.mark.asyncio
    async def test_execute_successful_confirmation(self, confirm_order_workflow, mock_order_session_service):
        """Test successful order confirmation"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "total_amount": 12.98,
            "items": [
                {"quantity": 1, "modifications": {"name": "Burger", "size": "regular"}},
                {"quantity": 1, "modifications": {"name": "Fries", "size": "large"}}
            ]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.archive_order_to_postgres.return_value = True
        mock_order_session_service.finalize_order.return_value = True
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert isinstance(result, ConfirmOrderWorkflowResult)
        assert result.success is True
        assert "Perfect! If everything looks correct on your screen" in result.message
        assert "$12.98" in result.message
        assert "Pull around to the next window" in result.message
        assert result.order_updated is True
        assert result.total_cost == 12.98
        assert result.audio_phrase_type == AudioPhraseType.ORDER_CONFIRMED
        assert result.workflow_type.value == "confirm_order"
        assert result.data["order_id"] == "order_123"
        assert result.data["total_amount"] == 12.98
        assert result.data["item_count"] == 2
        assert result.data["archived_to_postgres"] is True
        assert result.data["session_finalized"] is True
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_123")
        mock_order_session_service.finalize_order.assert_called_once_with("order_123")
    
    @pytest.mark.asyncio
    async def test_execute_no_active_order(self, confirm_order_workflow, mock_order_session_service):
        """Test confirmation when no active order exists"""
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
    async def test_execute_empty_order(self, confirm_order_workflow, mock_order_session_service):
        """Test confirmation when order is empty"""
        # Mock empty order
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "total_amount": 0.0,
            "items": []
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "Your order is empty" in result.message
        assert result.audio_phrase_type == AudioPhraseType.ORDER_ALREADY_EMPTY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_missing_order_id(self, confirm_order_workflow, mock_order_session_service):
        """Test confirmation when order ID is missing"""
        # Mock order without ID
        mock_order = {
            "session_id": "session_123",
            "total_amount": 12.98,
            "items": [{"quantity": 1, "modifications": {"name": "Burger"}}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "Order ID not found" in result.message
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_archive_failure_continues(self, confirm_order_workflow, mock_order_session_service):
        """Test that archive failure doesn't stop confirmation"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "total_amount": 12.98,
            "items": [{"quantity": 1, "modifications": {"name": "Burger"}}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.archive_order_to_postgres.return_value = False  # Archive fails
        mock_order_session_service.finalize_order.return_value = True
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        # Should still succeed even if archive fails
        assert result.success is True
        assert result.data["archived_to_postgres"] is False
        assert result.data["session_finalized"] is True
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_123")
        mock_order_session_service.finalize_order.assert_called_once_with("order_123")
    
    @pytest.mark.asyncio
    async def test_execute_finalize_failure_continues(self, confirm_order_workflow, mock_order_session_service):
        """Test that finalize failure doesn't stop confirmation"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "total_amount": 12.98,
            "items": [{"quantity": 1, "modifications": {"name": "Burger"}}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.archive_order_to_postgres.return_value = True
        mock_order_session_service.finalize_order.return_value = False  # Finalize fails
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        # Should still succeed even if finalize fails
        assert result.success is True
        assert result.data["archived_to_postgres"] is True
        assert result.data["session_finalized"] is False
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_called_once_with("order_123")
        mock_order_session_service.finalize_order.assert_called_once_with("order_123")
    
    @pytest.mark.asyncio
    async def test_execute_service_exception(self, confirm_order_workflow, mock_order_session_service):
        """Test handling of service exceptions"""
        mock_order_session_service.get_session_order.side_effect = Exception("Service error")
        
        result = await confirm_order_workflow.execute(session_id="session_123")
        
        assert result.success is False
        assert "Sorry, I couldn't confirm your order" in result.message
        assert result.error == "Service error"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.archive_order_to_postgres.assert_not_called()
        mock_order_session_service.finalize_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_with_conversation_history(self, confirm_order_workflow, mock_order_session_service):
        """Test confirmation with conversation history (should be ignored)"""
        # Mock order with items
        mock_order = {
            "id": "order_123",
            "session_id": "session_123",
            "total_amount": 12.98,
            "items": [{"quantity": 1, "modifications": {"name": "Burger"}}]
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order
        mock_order_session_service.archive_order_to_postgres.return_value = True
        mock_order_session_service.finalize_order.return_value = True
        
        conversation_history = [
            {"role": "customer", "content": "That's everything"},
            {"role": "assistant", "content": "Great! Ready to confirm your order?"}
        ]
        
        result = await confirm_order_workflow.execute(
            session_id="session_123",
            conversation_history=conversation_history
        )
        
        assert result.success is True
        assert "Perfect! If everything looks correct" in result.message
    
    def test_create_order_summary(self, confirm_order_workflow):
        """Test order summary creation"""
        # Test with multiple items
        items = [
            {"quantity": 1, "modifications": {"name": "Burger", "size": "regular"}},
            {"quantity": 2, "modifications": {"name": "Fries", "size": "large"}},
            {"quantity": 1, "modifications": {"name": "Drink", "size": "medium"}}
        ]
        
        summary = confirm_order_workflow._create_order_summary(items)
        expected = "1x Burger; 2x Fries (large); 1x Drink (medium)"
        assert summary == expected
        
        # Test with empty items
        empty_summary = confirm_order_workflow._create_order_summary([])
        assert empty_summary == "No items in order"
        
        # Test with missing name
        items_missing_name = [
            {"quantity": 1, "modifications": {"size": "regular"}}
        ]
        summary_missing = confirm_order_workflow._create_order_summary(items_missing_name)
        assert summary_missing == "1x Unknown Item"
