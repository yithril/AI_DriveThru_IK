"""
Unit tests for Modify Item Workflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from app.workflow.nodes.modify_item_workflow import ModifyItemWorkflow
from app.services.order_session_service import OrderSessionService
from app.workflow.response.modify_item_response import ModifyItemResult
from app.dto.modify_item_dto import ModifyItemResultDto


@pytest.fixture
def mock_order_session_service():
    """Mock order session service"""
    return AsyncMock(spec=OrderSessionService)


@pytest.fixture
def modify_item_workflow(mock_order_session_service):
    """Create modify item workflow with mocked dependencies"""
    return ModifyItemWorkflow(mock_order_session_service)


@pytest.fixture
def sample_redis_order():
    """Sample Redis order data"""
    return {
        "id": "order_1234567890",
        "session_id": "session_123",
        "restaurant_id": 1,
        "status": "active",
        "items": [
            {
                "id": "item_1234567890",
                "menu_item_id": 1,
                "quantity": 1,
                "modifications": {
                    "size": "regular",
                    "name": "Burger",
                    "unit_price": 10.0,
                    "total_price": 10.0
                },
                "added_at": "2024-01-01T12:00:00"
            },
            {
                "id": "item_1234567891",
                "menu_item_id": 2,
                "quantity": 1,
                "modifications": {
                    "size": "medium",
                    "name": "Fries",
                    "unit_price": 5.0,
                    "total_price": 5.0
                },
                "added_at": "2024-01-01T12:01:00"
            }
        ]
    }


@pytest.fixture
def sample_agent_result():
    """Sample agent result for successful modification"""
    return ModifyItemResult(
        success=True,
        confidence=0.95,
        target_item_id=1234567890,  # Matches the Redis item ID
        target_confidence=0.9,
        target_reasoning="User wants to change quantity",
        modification_type="quantity",
        new_quantity=2
    )


@pytest.fixture
def sample_service_result():
    """Sample service result for successful modification"""
    return ModifyItemResultDto(
        success=True,
        message="Updated Burger: quantity from 1 to 2",
        modified_fields=["quantity from 1 to 2"],
        additional_cost=Decimal('0.00')
    )


class TestModifyItemWorkflow:
    """Test cases for modify item workflow"""
    
    @pytest.mark.asyncio
    async def test_execute_successful_quantity_modification(
        self, 
        modify_item_workflow, 
        mock_order_session_service,
        sample_redis_order,
        sample_agent_result,
        sample_service_result
    ):
        """Test successful quantity modification workflow"""
        
        # Setup mocks
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        mock_order_session_service.update_order.return_value = True
        
        # Mock the agent and service
        with patch('app.workflow.nodes.modify_item_workflow.modify_item_agent') as mock_agent, \
             patch.object(modify_item_workflow.modify_item_service, 'apply_modification') as mock_service:
            
            mock_agent.return_value = sample_agent_result
            mock_service.return_value = sample_service_result
            
            # Execute workflow
            result = await modify_item_workflow.execute(
                user_input="Make it two",
                session_id="session_123"
            )
            
            # Verify result
            assert result["success"] is True
            assert "Updated Burger: quantity from 1 to 2" in result["message"]
            assert result["workflow_type"] == "modify_item"
            assert "quantity from 1 to 2" in result["modified_fields"]
            
            # Verify service calls
            mock_order_session_service.get_session_order.assert_called_once_with("session_123")
            mock_order_session_service.update_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_no_active_order(
        self, 
        modify_item_workflow, 
        mock_order_session_service
    ):
        """Test workflow when no active order exists"""
        
        # Setup mock to return no order
        mock_order_session_service.get_session_order.return_value = None
        
        # Execute workflow
        result = await modify_item_workflow.execute(
            user_input="Make it two",
            session_id="session_123"
        )
        
        # Verify result
        assert result["success"] is False
        assert "No active order found" in result["message"]
        assert result["workflow_type"] == "modify_item"
        
        # Verify service calls
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
        mock_order_session_service.update_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_agent_clarification_needed(
        self, 
        modify_item_workflow, 
        mock_order_session_service,
        sample_redis_order
    ):
        """Test workflow when agent needs clarification"""
        
        # Setup mocks
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        # Create agent result that needs clarification
        clarification_result = ModifyItemResult(
            success=False,
            confidence=0.3,
            target_item_id=None,
            target_confidence=0.2,
            target_reasoning="Ambiguous request",
            modification_type=None,
            clarification_needed=True,
            clarification_message="Which item would you like to modify?"
        )
        
        # Mock the agent
        with patch('app.workflow.nodes.modify_item_workflow.modify_item_agent') as mock_agent:
            mock_agent.return_value = clarification_result
            
            # Execute workflow
            result = await modify_item_workflow.execute(
                user_input="Make it large",
                session_id="session_123"
            )
            
            # Verify result
            assert result["success"] is False
            assert "Which item would you like to modify?" in result["message"]
            assert result["workflow_type"] == "modify_item"
            assert result["needs_clarification"] is True
            
            # Verify service calls
            mock_order_session_service.get_session_order.assert_called_once_with("session_123")
            mock_order_session_service.update_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_service_validation_failed(
        self, 
        modify_item_workflow, 
        mock_order_session_service,
        sample_redis_order,
        sample_agent_result
    ):
        """Test workflow when service validation fails"""
        
        # Setup mocks
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        # Create service result that fails validation
        validation_failed_result = ModifyItemResultDto(
            success=False,
            message="Cannot set quantity to 10. Valid range: 1-5",
            validation_errors=["Quantity exceeds maximum allowed"]
        )
        
        # Mock the agent and service
        with patch('app.workflow.nodes.modify_item_workflow.modify_item_agent') as mock_agent, \
             patch.object(modify_item_workflow.modify_item_service, 'apply_modification') as mock_service:
            
            mock_agent.return_value = sample_agent_result
            mock_service.return_value = validation_failed_result
            
            # Execute workflow
            result = await modify_item_workflow.execute(
                user_input="Make it ten",
                session_id="session_123"
            )
            
            # Verify result
            assert result["success"] is False
            assert "Cannot set quantity to 10" in result["message"]
            assert result["workflow_type"] == "modify_item"
            assert "validation_errors" in result
            
            # Verify service calls
            mock_order_session_service.get_session_order.assert_called_once_with("session_123")
            mock_order_session_service.update_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_redis_update_failed(
        self, 
        modify_item_workflow, 
        mock_order_session_service,
        sample_redis_order,
        sample_agent_result,
        sample_service_result
    ):
        """Test workflow when Redis update fails"""
        
        # Setup mocks
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        mock_order_session_service.update_order.return_value = False  # Redis update fails
        
        # Mock the agent and service
        with patch('app.workflow.nodes.modify_item_workflow.modify_item_agent') as mock_agent, \
             patch.object(modify_item_workflow.modify_item_service, 'apply_modification') as mock_service:
            
            mock_agent.return_value = sample_agent_result
            mock_service.return_value = sample_service_result
            
            # Execute workflow
            result = await modify_item_workflow.execute(
                user_input="Make it two",
                session_id="session_123"
            )
            
            # Verify result - should still succeed since service validation passed
            # The Redis update failure would be logged but not cause workflow failure
            assert result["success"] is True
            assert result["workflow_type"] == "modify_item"
            
            # Verify service calls
            mock_order_session_service.get_session_order.assert_called_once_with("session_123")
            mock_order_session_service.update_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_exception_handling(
        self, 
        modify_item_workflow, 
        mock_order_session_service
    ):
        """Test workflow exception handling"""
        
        # Setup mock to raise exception
        mock_order_session_service.get_session_order.side_effect = Exception("Redis connection failed")
        
        # Execute workflow
        result = await modify_item_workflow.execute(
            user_input="Make it two",
            session_id="session_123"
        )
        
        # Verify result
        assert result["success"] is False
        assert "Sorry, I couldn't process your modification request" in result["message"]
        assert result["workflow_type"] == "modify_item"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_current_order_summary_success(
        self, 
        modify_item_workflow, 
        mock_order_session_service,
        sample_redis_order
    ):
        """Test getting current order summary"""
        
        # Setup mock
        mock_order_session_service.get_session_order.return_value = sample_redis_order
        
        # Execute
        summary = await modify_item_workflow.get_current_order_summary("session_123")
        
        # Verify
        assert "1x Burger" in summary
        assert "1x Fries (medium)" in summary
        
        # Verify service call
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
    
    @pytest.mark.asyncio
    async def test_get_current_order_summary_no_order(
        self, 
        modify_item_workflow, 
        mock_order_session_service
    ):
        """Test getting order summary when no order exists"""
        
        # Setup mock
        mock_order_session_service.get_session_order.return_value = None
        
        # Execute
        summary = await modify_item_workflow.get_current_order_summary("session_123")
        
        # Verify
        assert summary == "No active order"
        
        # Verify service call
        mock_order_session_service.get_session_order.assert_called_once_with("session_123")
    
    @pytest.mark.asyncio
    async def test_get_current_order_summary_exception(
        self, 
        modify_item_workflow, 
        mock_order_session_service
    ):
        """Test getting order summary when exception occurs"""
        
        # Setup mock to raise exception
        mock_order_session_service.get_session_order.side_effect = Exception("Redis error")
        
        # Execute
        summary = await modify_item_workflow.get_current_order_summary("session_123")
        
        # Verify
        assert summary == "Unable to retrieve order summary"
