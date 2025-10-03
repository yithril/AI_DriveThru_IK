"""
Unit tests for RemoveItemWorkflow
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.workflow.nodes.remove_item_workflow import RemoveItemWorkflow
from app.workflow.agents.remove_item_agent import RemoveItemResult
from app.services.order_session_service import OrderSessionService
from app.workflow.response.workflow_result import WorkflowResult
from app.constants.audio_phrases import AudioPhraseType


class TestRemoveItemWorkflow:
    """Unit tests for RemoveItemWorkflow"""
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Mock OrderSessionService for unit tests"""
        return AsyncMock(spec=OrderSessionService)
    
    @pytest.fixture
    def remove_item_workflow(self, mock_order_session_service):
        """Create RemoveItemWorkflow instance for testing"""
        return RemoveItemWorkflow(order_session_service=mock_order_session_service)
    
    @pytest.fixture
    def sample_redis_order(self):
        """Sample Redis order data"""
        return {
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
                        "name": "Burger",
                        "size": "large",
                        "unit_price": 10.99,
                        "total_price": 10.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                },
                {
                    "id": "item_2", 
                    "menu_item_id": 2,
                    "quantity": 1,
                    "modifications": {
                        "name": "Fries",
                        "size": "regular",
                        "unit_price": 3.99,
                        "total_price": 3.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                }
            ],
            "total_amount": 14.98,
            "subtotal": 14.98,
            "created_at": "2024-01-01T12:00:00"
        }
    
    @pytest.mark.asyncio
    async def test_execute_successful_removal(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test successful item removal"""
        # Mock agent result
        agent_result = RemoveItemResult(
            success=True,
            confidence=0.9,
            target_item_names=["burger"],
            target_item_ids=[1],
            clarification_needed=False
        )
        
        # Mock service calls
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        mock_order_session_service.remove_item_from_order.return_value = True
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="remove the burger",
                session_id="session_123"
            )
        
        assert isinstance(result, WorkflowResult)
        assert result.success is True
        assert "Removed Burger from your order" in result.message
        assert result.order_updated is True
        assert "removed_items" in result.data
        assert len(result.data["removed_items"]) == 1
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVED_SUCCESS
        assert result.workflow_type.value == "remove_item"
        
        # Verify service calls
        assert mock_order_session_service.get_session_order.call_count == 2  # Called twice: once in main workflow, once in _remove_single_item_from_order
        mock_order_session_service.remove_item_from_order.assert_called_once_with("session_123", "item_1")
    
    @pytest.mark.asyncio
    async def test_execute_no_active_order(self, remove_item_workflow, mock_order_session_service):
        """Test removal when no active order exists"""
        mock_order_session_service.get_session_order.return_value = None
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert result.message == "No active order found. Please start by adding items to your order."
        assert result.audio_phrase_type == AudioPhraseType.NO_ORDER_YET
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_agent_failure(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test when agent fails to parse the request"""
        # Mock agent failure
        agent_result = RemoveItemResult(
            success=False,
            confidence=0.0,
            clarification_needed=True,
            clarification_message="I couldn't understand your request.",
            context_notes="Agent error"
        )
        
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="asdfghjkl",
                session_id="session_123"
            )
        
        assert result.success is False
        assert "I couldn't understand your request" in result.message
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVE_ERROR
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_clarification_needed(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test when clarification is needed"""
        # Mock agent result requiring clarification
        agent_result = RemoveItemResult(
            success=True,
            confidence=0.6,
            clarification_needed=True,
            clarification_message="Which burger would you like to remove?",
            clarification_options=["Cheeseburger", "Hamburger"],
            context_notes="Ambiguous request"
        )
        
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="remove the burger",
                session_id="session_123"
            )
        
        assert result.success is False
        assert result.needs_clarification is True
        assert result.message == "Which burger would you like to remove?"
        assert result.clarification_options == ["Cheeseburger", "Hamburger"]
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVE_CLARIFICATION
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_multiple_items_removal(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test removing multiple items"""
        # Mock agent result for multiple items
        agent_result = RemoveItemResult(
            success=True,
            confidence=0.9,
            target_item_names=["burger", "fries"],
            target_item_ids=[1, 2],
            clarification_needed=False
        )
        
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        mock_order_session_service.remove_item_from_order.return_value = True
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="remove the burger and fries",
                session_id="session_123"
            )
        
        assert result.success is True
        assert "Removed Burger, Fries from your order" in result.message
        assert len(result.data["removed_items"]) == 2
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVED_SUCCESS
        
        # Verify both items were removed
        assert mock_order_session_service.remove_item_from_order.call_count == 2
        mock_order_session_service.remove_item_from_order.assert_any_call("session_123", "item_1")
        mock_order_session_service.remove_item_from_order.assert_any_call("session_123", "item_2")
    
    @pytest.mark.asyncio
    async def test_execute_partial_removal_failure(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test when some items are removed successfully and others fail"""
        # Mock agent result for multiple items
        agent_result = RemoveItemResult(
            success=True,
            confidence=0.9,
            target_item_names=["burger", "fries"],
            target_item_ids=[1, 2],
            clarification_needed=False
        )
        
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        # Mock first removal success, second failure
        def mock_remove_item(session_id, item_id):
            if item_id == "item_1":
                return True
            elif item_id == "item_2":
                return False
            return False
        
        mock_order_session_service.remove_item_from_order.side_effect = mock_remove_item
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="remove the burger and fries",
                session_id="session_123"
            )
        
        assert result.success is True  # Partial success is still success
        assert "Removed Burger from your order" in result.message
        assert "I couldn't remove Fries" in result.message
        assert len(result.data["removed_items"]) == 1
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVED_SUCCESS
    
    @pytest.mark.asyncio
    async def test_execute_all_removals_fail(self, remove_item_workflow, mock_order_session_service, sample_redis_order):
        """Test when all item removals fail"""
        # Mock agent result
        agent_result = RemoveItemResult(
            success=True,
            confidence=0.9,
            target_item_names=["burger"],
            target_item_ids=[1],
            clarification_needed=False
        )
        
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        mock_order_session_service.remove_item_from_order.return_value = False
        
        with patch('app.workflow.nodes.remove_item_workflow.remove_item_agent', return_value=agent_result):
            result = await remove_item_workflow.execute(
                user_input="remove the burger",
                session_id="session_123"
            )
        
        assert result.success is False
        assert "I couldn't remove those items from your order" in result.message
        assert result.audio_phrase_type == AudioPhraseType.ITEM_REMOVE_ERROR
        assert "failed_items" in result.data
        assert "Burger" in result.data["failed_items"]
    
    @pytest.mark.asyncio
    async def test_execute_service_exception(self, remove_item_workflow, mock_order_session_service):
        """Test handling of exceptions from the order session service"""
        mock_order_session_service.get_session_order.side_effect = Exception("Redis connection error")
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert "Sorry, I couldn't process your request to remove items" in result.message
        assert "Redis connection error" in result.error
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_build_success_message_single_item(self, remove_item_workflow):
        """Test building success message for single item"""
        removed_items = [{"name": "Burger", "quantity": 1}]
        message = remove_item_workflow._build_success_message(removed_items)
        assert message == "Removed Burger from your order."
    
    @pytest.mark.asyncio
    async def test_build_success_message_multiple_items(self, remove_item_workflow):
        """Test building success message for multiple items"""
        removed_items = [
            {"name": "Burger", "quantity": 1},
            {"name": "Fries", "quantity": 1}
        ]
        message = remove_item_workflow._build_success_message(removed_items)
        assert message == "Removed Burger, Fries from your order."
    
    @pytest.mark.asyncio
    async def test_build_success_message_quantity(self, remove_item_workflow):
        """Test building success message with quantity"""
        removed_items = [{"name": "Burger", "quantity": 2}]
        message = remove_item_workflow._build_success_message(removed_items)
        assert message == "Removed 2 Burgers from your order."
    
    @pytest.mark.asyncio
    async def test_build_partial_success_message(self, remove_item_workflow):
        """Test building partial success message"""
        removed_items = [{"name": "Burger", "quantity": 1}]
        failed_removals = [{"name": "Fries", "quantity": 1}]
        message = remove_item_workflow._build_partial_success_message(removed_items, failed_removals)
        assert "Removed Burger from your order" in message
        assert "I couldn't remove Fries" in message
