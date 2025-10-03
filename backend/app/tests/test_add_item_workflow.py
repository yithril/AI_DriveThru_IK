"""
Unit tests for AddItemWorkflow
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.workflow.nodes.add_item_workflow import AddItemWorkflow, AddItemWorkflowResult
from app.workflow.response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.workflow.response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.constants.audio_phrases import AudioPhraseType
from app.constants.order_config import MAX_ITEM_QUANTITY, MAX_TOTAL_ITEMS


class TestAddItemWorkflow:
    """Test cases for AddItemWorkflow"""
    
    @pytest.fixture
    def mock_menu_resolution_service(self):
        """Create mock menu resolution service"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_order_session_service(self):
        """Create mock order session service"""
        return AsyncMock()
    
    @pytest.fixture
    def add_item_workflow(self, mock_menu_resolution_service, mock_order_session_service):
        """Create AddItemWorkflow instance for testing"""
        return AddItemWorkflow(
            restaurant_id=1,
            menu_resolution_service=mock_menu_resolution_service,
            order_session_service=mock_order_session_service
        )
    
    @pytest.fixture
    def sample_extraction_response(self):
        """Sample item extraction response"""
        return ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="burger",
                    quantity=1,
                    size="large",
                    modifiers=["extra cheese"],
                    special_instructions=None,
                    confidence=0.9,
                    context_notes="Clear burger request"
                )
            ]
        )
    
    @pytest.fixture
    def sample_resolution_response(self):
        """Sample menu resolution response"""
        return MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=1,
                    size="large",
                    special_instructions=None,
                    modifiers=[(1, "add")],  # (ingredient_id, action)
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Burger",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_execute_successful_add_item(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service,
        sample_extraction_response,
        sample_resolution_response
    ):
        """Test successful item addition"""
        # Mock services
        mock_order_session_service.get_session_order.return_value = {
            "id": "order_123",
            "items": []
        }
        mock_order_session_service.add_item_to_order.return_value = True
        
        # Mock the agent at the point where it's imported in the workflow
        with patch('app.workflow.nodes.add_item_workflow.item_extraction_agent') as mock_agent:
            mock_agent.return_value = sample_extraction_response
            mock_menu_resolution_service.resolve_items.return_value = sample_resolution_response
            
            result = await add_item_workflow.execute(
                user_input="I'll take a large burger with extra cheese",
                session_id="session_123"
            )
        
        from app.workflow.response.workflow_result import WorkflowResult
        assert isinstance(result, WorkflowResult)
        assert result.success is True
        assert "Added Burger (large) to your order!" in result.message
        assert result.order_updated is True
        assert "added_items" in result.data
        assert len(result.data["added_items"]) == 1
        assert result.audio_phrase_type == AudioPhraseType.ITEM_ADDED_SUCCESS
        assert result.workflow_type.value == "add_item"
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_extraction_failure(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when item extraction fails"""
        # Mock extraction failure
        failed_extraction = ItemExtractionResponse(
            success=False,
            confidence=0.0,
            extracted_items=[
                ExtractedItem(
                    item_name="unknown",
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.0,
                    context_notes="Extraction failed"
                )
            ],
            needs_clarification=True,
            clarification_questions=["I couldn't understand your request"]
        )
        
        with patch('app.workflow.nodes.add_item_workflow.item_extraction_agent', return_value=failed_extraction):
            result = await add_item_workflow.execute(
                user_input="gibberish text",
                session_id="session_123"
            )
        
        assert result.success is False
        assert "I couldn't understand what items you'd like to add" in result.message
        assert result.audio_phrase_type == AudioPhraseType.CLARIFICATION_QUESTION
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_not_called()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_resolution_failure(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when menu resolution fails"""
        # Mock resolution failure
        mock_menu_resolution_service.resolve_items.return_value = MenuResolutionResponse(
            success=False,
            confidence=0.0,
            resolved_items=[]
        )
        
        result = await add_item_workflow.execute(
            user_input="I'll take a unicorn burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert "I couldn't find those items on our menu" in result.message
        assert result.audio_phrase_type == AudioPhraseType.CLARIFICATION_QUESTION
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_needs_clarification(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when clarification is needed"""
        # Mock ambiguous resolution
        ambiguous_resolution = MenuResolutionResponse(
            success=True,
            confidence=0.7,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=1,
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=0,  # Ambiguous
                    resolved_menu_item_name=None,
                    menu_item_resolution_confidence=0.7,
                    is_ambiguous=True,
                    is_unavailable=False,
                    suggested_options=["Cheeseburger", "Hamburger", "Veggie Burger"],
                    clarification_question="Which type of burger would you like?"
                )
            ],
            needs_clarification=True,
            clarification_questions=["Which type of burger would you like?"]
        )
        
        mock_menu_resolution_service.resolve_items.return_value = ambiguous_resolution
        
        result = await add_item_workflow.execute(
            user_input="I'll take a burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert "Which type of burger would you like?" in result.message
        assert result.needs_clarification is True
        assert result.audio_phrase_type == AudioPhraseType.CLARIFICATION_QUESTION
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_quantity_validation_failure(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when quantity exceeds limits"""
        # Mock resolution with excessive quantity
        excessive_quantity_resolution = MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=MAX_ITEM_QUANTITY + 1,  # Exceeds limit
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Burger",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            ]
        )
        
        mock_menu_resolution_service.resolve_items.return_value = excessive_quantity_resolution
        
        result = await add_item_workflow.execute(
            user_input=f"I'll take {MAX_ITEM_QUANTITY + 1} burgers",
            session_id="session_123"
        )
        
        assert result.success is False
        assert f"only order up to {MAX_ITEM_QUANTITY}" in result.message
        assert "Burger" in result.message
        assert result.audio_phrase_type == AudioPhraseType.CLARIFICATION_QUESTION
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_total_items_limit_exceeded(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when total items limit is exceeded"""
        # Mock current order with many items
        current_order = {
            "id": "order_123",
            "items": [{"id": f"item_{i}"} for i in range(MAX_TOTAL_ITEMS - 1)]
        }
        
        # Mock extraction that would lead to exceeding limit
        extraction = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="burger",
                    quantity=2,  # This would exceed MAX_TOTAL_ITEMS
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9,
                    context_notes="Clear request"
                )
            ]
        )
        
        # Mock resolution that would exceed limit
        resolution = MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=2,  # This would exceed MAX_TOTAL_ITEMS
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Burger",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            ]
        )
        
        with patch('app.workflow.nodes.add_item_workflow.item_extraction_agent', return_value=extraction):
            mock_menu_resolution_service.resolve_items.return_value = resolution
            mock_order_session_service.get_session_order.return_value = current_order
            
            result = await add_item_workflow.execute(
                user_input="I'll take 2 more burgers",
                session_id="session_123",
                current_order=current_order
            )
        
        assert result.success is False
        assert f"too many items (maximum {MAX_TOTAL_ITEMS})" in result.message
        assert result.audio_phrase_type == AudioPhraseType.CLARIFICATION_QUESTION
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_partial_success(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test partial success when some items fail to add"""
        # Mock extraction with multiple items
        extraction = ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="burger",
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9,
                    context_notes="Clear request"
                ),
                ExtractedItem(
                    item_name="fries",
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    confidence=0.9,
                    context_notes="Clear request"
                )
            ]
        )
        
        # Mock resolution with multiple items
        resolution = MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=1,
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Burger",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                ),
                ResolvedItem(
                    item_name="fries",
                    quantity=1,
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=2,
                    resolved_menu_item_name="Fries",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            ]
        )
        
        with patch('app.workflow.nodes.add_item_workflow.item_extraction_agent', return_value=extraction):
            mock_menu_resolution_service.resolve_items.return_value = resolution
            mock_order_session_service.get_session_order.return_value = {"id": "order_123", "items": []}
            
            # Mock partial success - first item succeeds, second fails
            async def mock_add_item(order_id, menu_item_id, quantity, modifications):
                return menu_item_id == 1  # Only burger succeeds
            
            mock_order_session_service.add_item_to_order.side_effect = mock_add_item
            
            result = await add_item_workflow.execute(
                user_input="I'll take a burger and fries",
                session_id="session_123"
            )
        
        assert result.success is True
        assert "Added Burger to your order!" in result.message
        assert "I couldn't add Fries" in result.message
        assert len(result.data["added_items"]) == 1
        assert result.audio_phrase_type == AudioPhraseType.ITEM_ADDED_SUCCESS
        
        # Verify service calls
        mock_order_session_service.add_item_to_order.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_all_items_fail(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test when all items fail to add"""
        resolution = MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="burger",
                    quantity=1,
                    size=None,
                    special_instructions=None,
                    modifiers=[],
                    ingredient_normalization_details=[],
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Burger",
                    menu_item_resolution_confidence=0.9,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            ]
        )
        
        mock_menu_resolution_service.resolve_items.return_value = resolution
        mock_order_session_service.get_session_order.return_value = {"id": "order_123", "items": []}
        mock_order_session_service.add_item_to_order.return_value = False  # All items fail
        
        result = await add_item_workflow.execute(
            user_input="I'll take a burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert "I couldn't add those items to your order" in result.message
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_order_session_service.add_item_to_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_service_exception(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service
    ):
        """Test handling of service exceptions"""
        mock_menu_resolution_service.resolve_items.side_effect = Exception("Service error")
        
        result = await add_item_workflow.execute(
            user_input="I'll take a burger",
            session_id="session_123"
        )
        
        assert result.success is False
        assert "Sorry, I couldn't add those items to your order" in result.message
        assert result.error == "Service error"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
        
        # Verify service calls
        mock_menu_resolution_service.resolve_items.assert_called_once()
        mock_order_session_service.add_item_to_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_create_new_order(
        self, 
        add_item_workflow, 
        mock_menu_resolution_service, 
        mock_order_session_service,
        sample_resolution_response
    ):
        """Test creating new order when none exists"""
        mock_menu_resolution_service.resolve_items.return_value = sample_resolution_response
        mock_order_session_service.get_session_order.return_value = None  # No existing order
        mock_order_session_service.create_order.return_value = "new_order_123"
        mock_order_session_service.add_item_to_order.return_value = True
        
        result = await add_item_workflow.execute(
            user_input="I'll take a burger",
            session_id="session_123"
        )
        
        assert result.success is True
        assert "Added Burger (large) to your order!" in result.message
        
        # Verify service calls
        mock_order_session_service.create_order.assert_called_once_with(
            session_id="session_123",
            restaurant_id=1
        )
        mock_order_session_service.add_item_to_order.assert_called_once()
    
    def test_build_modifications_dict(self, add_item_workflow):
        """Test building modifications dictionary"""
        resolved_item = Mock()
        resolved_item.resolved_menu_item_name = "Burger"
        resolved_item.size = "large"
        resolved_item.special_instructions = "well done"
        resolved_item.modifiers = [(1, "add"), (2, "remove")]
        
        modifications = add_item_workflow._build_modifications_dict(resolved_item)
        
        expected = {
            "name": "Burger",
            "size": "large",
            "special_instructions": "well done",
            "ingredient_modifications": "add ingredient_id:1; remove ingredient_id:2"
        }
        assert modifications == expected
    
    def test_build_success_message_single_item(self, add_item_workflow):
        """Test building success message for single item"""
        items = [Mock()]
        items[0].quantity = 2
        items[0].resolved_menu_item_name = "Burger"
        items[0].size = "large"
        
        message = add_item_workflow._build_success_message(items)
        assert message == "Added 2 Burger (large) to your order!"
    
    def test_build_success_message_multiple_items(self, add_item_workflow):
        """Test building success message for multiple items"""
        items = [Mock(), Mock()]
        items[0].quantity = 1
        items[0].resolved_menu_item_name = "Burger"
        items[0].size = "regular"
        
        items[1].quantity = 2
        items[1].resolved_menu_item_name = "Fries"
        items[1].size = "large"
        
        message = add_item_workflow._build_success_message(items)
        assert message == "Added Burger, 2 Fries (large) to your order!"
