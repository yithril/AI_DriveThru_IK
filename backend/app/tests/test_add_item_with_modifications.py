"""
Unit tests for Add Item Workflow with Modifications

Tests the happy case scenario where a customer orders an item with valid modifications.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.workflow.nodes.add_item_workflow import AddItemWorkflow
from app.workflow.response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.workflow.response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.constants.audio_phrases import AudioPhraseType


class TestAddItemWithModifications:
    """Test cases for AddItemWorkflow with modifications"""
    
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
    def sample_extraction_with_modifications(self):
        """Sample item extraction response with modifications"""
        return ItemExtractionResponse(
            success=True,
            confidence=0.9,
            extracted_items=[
                ExtractedItem(
                    item_name="quantum burger",
                    quantity=1,
                    size=None,
                    modifiers=["no onions"],
                    special_instructions=None,
                    confidence=0.9,
                    context_notes="Clear burger request with modification"
                )
            ],
            needs_clarification=False,
            clarification_questions=[],
            extraction_notes=None
        )
    
    @pytest.fixture
    def sample_resolution_with_modifications(self):
        """Sample menu resolution response with modifications"""
        from app.workflow.response.menu_resolution_response import NormalizedModifier
        
        return MenuResolutionResponse(
            success=True,
            confidence=0.9,
            resolved_items=[
                ResolvedItem(
                    item_name="quantum burger",
                    quantity=1,
                    size=None,
                    resolved_menu_item_id=1,
                    resolved_menu_item_name="Quantum Cheeseburger",
                    menu_item_resolution_confidence=0.95,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None,
                    modifiers=[(5, "remove")],  # (ingredient_id, action) tuple
                    ingredient_normalization_details=[
                        NormalizedModifier(
                            original_modifier="no onions",
                            final_modifier="no onions",
                            action="remove",
                            ingredient_term="onions",
                            ingredient_id=5,
                            normalized_ingredient_name="onions",
                            match_confidence=0.95,
                            is_resolved=True,
                            is_available=True
                        )
                    ]
                )
            ],
            needs_clarification=False,
            clarification_questions=[],
            resolution_notes="Successfully resolved with modifications"
        )
    
    @pytest.mark.asyncio
    async def test_quantum_burger_with_no_onions_happy_case(
        self, 
        add_item_workflow, 
        sample_extraction_with_modifications,
        sample_resolution_with_modifications,
        mock_menu_resolution_service,
        mock_order_session_service
    ):
        """
        Test the happy case: Customer orders "quantum burger with no onions"
        where onions is a valid ingredient for the quantum burger.
        """
        # Setup mocks
        mock_menu_resolution_service.resolve_items.return_value = sample_resolution_with_modifications
        mock_order_session_service.add_item_to_order.return_value = True
        
        # Mock the item extraction agent
        with patch('app.workflow.agents.item_extraction_agent.item_extraction_agent') as mock_agent:
            mock_agent.return_value = sample_extraction_with_modifications
            
            # Execute the workflow
            result = await add_item_workflow.execute(
                user_input="I'd like a quantum burger with no onions",
                session_id="session_123"
            )
        
        # Verify the result
        assert result.success is True
        assert result.message is not None
        assert "Quantum Cheeseburger" in result.message
        assert result.order_updated is True
        assert result.audio_phrase_type == AudioPhraseType.ITEM_ADDED_SUCCESS
        
        # Verify menu resolution was called with modifications
        mock_menu_resolution_service.resolve_items.assert_called_once()
        resolution_call = mock_menu_resolution_service.resolve_items.call_args
        extraction_response = resolution_call[0][0]
        
        # Check that the extraction response contains the modification
        assert len(extraction_response.extracted_items) == 1
        item = extraction_response.extracted_items[0]
        assert item.item_name == "quantum burger"
        assert "no onions" in item.modifiers
        
        # Verify order session service was called with modifications
        mock_order_session_service.add_item_to_order.assert_called_once()
        add_item_call = mock_order_session_service.add_item_to_order.call_args
        
        # Check the parameters passed to add_item_to_order
        order_id = add_item_call[0][0]
        menu_item_id = add_item_call[0][1]
        quantity = add_item_call[0][2]
        modifications = add_item_call[0][3] if len(add_item_call[0]) > 3 else add_item_call[1].get('modifications')
        
        assert order_id == "session_123"
        assert menu_item_id == 1  # Quantum Cheeseburger ID
        assert quantity == 1
        
        # Check that modifications were passed correctly
        print(f"\n=== DEBUG: Modifications passed to add_item_to_order ===")
        print(f"Modifications: {modifications}")
        print(f"Type: {type(modifications)}")
        print("=" * 60)
        
        # The modifications should contain the ingredient modification
        assert modifications is not None
        # Note: The exact structure depends on how the workflow processes the resolved item
        # This test will help us see what actually gets passed to the order service
    
    @pytest.mark.asyncio
    async def test_debug_modification_flow(
        self,
        add_item_workflow,
        sample_extraction_with_modifications,
        sample_resolution_with_modifications,
        mock_menu_resolution_service,
        mock_order_session_service
    ):
        """
        Debug test to see exactly what happens in the modification flow.
        This will help us understand where the issue might be.
        """
        # Setup mocks
        mock_menu_resolution_service.resolve_items.return_value = sample_resolution_with_modifications
        mock_order_session_service.add_item_to_order.return_value = True
        
        # Mock the item extraction agent
        with patch('app.workflow.agents.item_extraction_agent.item_extraction_agent') as mock_agent:
            mock_agent.return_value = sample_extraction_with_modifications
            
            print(f"\n=== DEBUG: Starting modification flow test ===")
            print(f"Extraction response: {sample_extraction_with_modifications}")
            print(f"Resolution response: {sample_resolution_with_modifications}")
            
            # Execute the workflow
            result = await add_item_workflow.execute(
                user_input="I'd like a quantum burger with no onions",
                session_id="session_123"
            )
            
            print(f"Workflow result: {result}")
            print(f"Success: {result.success}")
            print(f"Message: {result.message}")
            print("=" * 60)
        
        # This test is mainly for debugging - we'll see what actually happens
        assert result is not None
