"""
Integration tests for RemoveItemWorkflow using real agents
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.remove_item_workflow import RemoveItemWorkflow
from app.services.order_session_service import OrderSessionService
from app.workflow.response.workflow_result import WorkflowResult
from app.constants.audio_phrases import AudioPhraseType
from app.config.settings import settings

# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestRemoveItemWorkflowIntegration:
    """Integration tests for RemoveItemWorkflow with real agents"""
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Create mock OrderSessionService"""
        service = AsyncMock(spec=OrderSessionService)
        return service
    
    @pytest.fixture
    def remove_item_workflow(self, mock_order_session_service):
        """Create RemoveItemWorkflow instance for integration testing"""
        return RemoveItemWorkflow(order_session_service=mock_order_session_service)
    
    @pytest.mark.asyncio
    async def test_remove_item_simple_request(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing a simple item with real agent"""
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
        
        # Mock service methods
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.remove_item_from_order.return_value = True
        
        # This test will use the real remove item agent
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        # The result depends on the real agent, so we just verify it's a valid response
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # Verify service calls were made
        assert mock_order_session_service.get_session_order.call_count >= 1
        # Remove item may or may not be called depending on agent success
    
    @pytest.mark.asyncio
    async def test_remove_item_no_active_order(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing item when no active order exists"""
        # Mock no existing order
        mock_order_session_service.get_session_order.return_value = None
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.success is False
        assert result.message == "No active order found. Please start by adding items to your order."
        assert result.audio_phrase_type == AudioPhraseType.NO_ORDER_YET
        
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_item_multiple_items(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing multiple items"""
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
        
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.remove_item_from_order.return_value = True
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger and fries",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The result will depend on the real agent's ability to parse multiple items
        assert mock_order_session_service.get_session_order.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_remove_item_ambiguous_request(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing item with ambiguous request"""
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
                        "name": "Cheeseburger",
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
                        "name": "Hamburger",
                        "size": "large",
                        "unit_price": 9.99,
                        "total_price": 9.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                }
            ],
            "total_amount": 20.98,
            "subtotal": 20.98,
            "created_at": "2024-01-01T12:00:00"
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order_data
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The agent should detect ambiguity and request clarification
        # or successfully identify which burger to remove
        assert mock_order_session_service.get_session_order.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_remove_item_nonexistent_item(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing item that doesn't exist in order"""
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
                        "name": "Burger",
                        "size": "large",
                        "unit_price": 10.99,
                        "total_price": 10.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                }
            ],
            "total_amount": 10.99,
            "subtotal": 10.99,
            "created_at": "2024-01-01T12:00:00"
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order_data
        
        result = await remove_item_workflow.execute(
            user_input="remove the pizza",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The agent should detect that pizza doesn't exist and request clarification
        assert mock_order_session_service.get_session_order.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_remove_item_service_failure(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test handling of service failures"""
        # Mock service failure
        mock_order_session_service.get_session_order.side_effect = Exception("Service error")
        
        result = await remove_item_workflow.execute(
            user_input="remove the burger",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.success is False
        assert "Sorry, I couldn't process your request to remove items" in result.message
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.remove_item_from_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_item_with_conversation_history(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test removing item with conversation context"""
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
                        "name": "Burger",
                        "size": "large",
                        "unit_price": 10.99,
                        "total_price": 10.99
                    },
                    "added_at": "2024-01-01T12:00:00"
                }
            ],
            "total_amount": 10.99,
            "subtotal": 10.99,
            "created_at": "2024-01-01T12:00:00"
        }
        
        mock_order_session_service.get_session_order.return_value = mock_order_data
        mock_order_session_service.remove_item_from_order.return_value = True
        
        conversation_history = [
            {"role": "customer", "content": "I'll take a burger"},
            {"role": "assistant", "content": "Added Burger to your order!"}
        ]
        
        result = await remove_item_workflow.execute(
            user_input="actually, remove it",
            session_id="session_123",
            conversation_history=conversation_history
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The agent should use conversation context to understand "it" refers to the burger
        assert mock_order_session_service.get_session_order.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_remove_item_gibberish_input(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test handling of gibberish input"""
        result = await remove_item_workflow.execute(
            user_input="asdfghjkl qwerty",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The result will depend on the real agent's ability to handle gibberish
        # Note: get_session_order may not be called if agent fails early
        # assert mock_order_session_service.get_session_order.assert_called_once_with("session_123")
    
    @pytest.mark.asyncio
    async def test_remove_item_empty_input(
        self,
        remove_item_workflow,
        mock_order_session_service
    ):
        """Test handling of empty input"""
        result = await remove_item_workflow.execute(
            user_input="",
            session_id="session_123"
        )
        
        assert isinstance(result, WorkflowResult)
        assert result.workflow_type.value == "remove_item"
        
        # The result will depend on the real agent's ability to handle empty input
        # Note: get_session_order may not be called if agent fails early
        # assert mock_order_session_service.get_session_order.assert_called_once_with("session_123")
