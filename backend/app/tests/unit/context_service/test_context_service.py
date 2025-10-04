"""
Unit tests for ContextService

Tests the context resolution service with fast-path logic for explicit inputs
and LLM fallback for ambiguous inputs.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.context_service import ContextService, ContextResolutionResult
from app.dto.conversation_dto import ConversationHistory, ConversationEntry, ConversationRole
from datetime import datetime


class TestContextService:
    """Unit tests for ContextService with fast-path logic"""
    
    @pytest.fixture
    def context_service(self):
        """Create ContextService instance for testing"""
        return ContextService()
    
    @pytest.fixture
    def conversation_history(self):
        """Create ConversationHistory for testing"""
        history = ConversationHistory(session_id="test_session")
        history.add_entry(
            role=ConversationRole.USER,
            content="Tell me about the veggie wrap"
        )
        history.add_entry(
            role=ConversationRole.ASSISTANT,
            content="The veggie wrap is a healthy option with fresh vegetables"
        )
        history.add_entry(
            role=ConversationRole.USER,
            content="I'll take two"
        )
        return history
    
    @pytest.fixture
    def command_history(self):
        """Create command history for testing"""
        history = ConversationHistory(session_id="test_session")
        history.add_entry(
            role=ConversationRole.ASSISTANT,
            content="Added Quantum Burger to your order"
        )
        history.add_entry(
            role=ConversationRole.ASSISTANT,
            content="Added Cosmic Fries to your order"
        )
        return history
    
    @pytest.fixture
    def current_order(self):
        """Mock current order"""
        return {
            "items": [
                {"name": "Quantum Burger", "quantity": 1},
                {"name": "Cosmic Fries", "quantity": 1}
            ]
        }

    # ========== ELIGIBILITY CHECK TESTS ==========
    
    def test_eligibility_check_pronouns_should_trigger(self, context_service):
        """Test that pronouns trigger eligibility check"""
        test_cases = [
            ("I'll take it", "ADD_ITEM"),
            ("That sounds good", "ADD_ITEM"),
            ("I want this", "ADD_ITEM"),
            ("Give me them", "ADD_ITEM"),
            ("I'll take one", "ADD_ITEM"),  # Standalone "one"
        ]
        
        for user_input, intent in test_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for input: '{user_input}'"
    
    def test_eligibility_check_repair_markers_should_trigger(self, context_service):
        """Test that repair markers trigger eligibility check"""
        test_cases = [
            ("Actually, I'll take that", "ADD_ITEM"),
            ("Scratch that, give me this", "ADD_ITEM"),
            ("Undo that last order", "REMOVE_ITEM"),
            ("Cancel that", "REMOVE_ITEM"),
            ("Remove that from my order", "REMOVE_ITEM"),
            ("Not that one", "REMOVE_ITEM"),
            ("Take that off", "REMOVE_ITEM"),
        ]
        
        for user_input, intent in test_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for input: '{user_input}'"
    
    def test_eligibility_check_ellipsis_markers_should_trigger(self, context_service):
        """Test that ellipsis markers trigger eligibility check"""
        test_cases = [
            ("Another one please", "ADD_ITEM"),
            ("One more of those", "ADD_ITEM"),
            ("Same again", "ADD_ITEM"),
            ("The usual", "ADD_ITEM"),
            ("Make it large", "MODIFY_ITEM"),
            ("Make them extra crispy", "MODIFY_ITEM"),
            ("Keep it as is", "MODIFY_ITEM"),
            ("Leave it alone", "MODIFY_ITEM"),
        ]
        
        for user_input, intent in test_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for input: '{user_input}'"
    
    def test_eligibility_check_explicit_inputs_should_trigger(self, context_service):
        """Test that explicit inputs DO trigger eligibility check (let LLM handle nuances)"""
        test_cases = [
            # Clear item requests - these will go to LLM but LLM will quickly resolve them
            ("I'd like one burger", "ADD_ITEM"),
            ("I'll take 3 wraps", "ADD_ITEM"),
            ("Can I get two fries", "ADD_ITEM"),
            ("Add a shake to my order", "ADD_ITEM"),
            ("I want a sandwich", "ADD_ITEM"),
            ("Give me some cookies", "ADD_ITEM"),
            ("I'll have a taco", "ADD_ITEM"),
            ("One combo meal please", "ADD_ITEM"),
            ("Two drinks", "ADD_ITEM"),
            ("A packet of sauce", "ADD_ITEM"),

            # Clear modification requests
            ("Make the burger large", "MODIFY_ITEM"),
            ("Change the fries to extra crispy", "MODIFY_ITEM"),
            ("Remove the onions from my burger", "MODIFY_ITEM"),

            # Clear questions
            ("What's your phone number?", "QUESTION"),
            ("What are your hours?", "QUESTION"),
            ("How much does a burger cost?", "QUESTION"),
        ]

        for user_input, intent in test_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for input (let LLM decide): '{user_input}'"
    
    def test_eligibility_check_ambiguous_vs_explicit_quantities(self, context_service):
        """Test the difference between ambiguous and explicit quantity usage"""
        # Ambiguous - should trigger (obvious patterns)
        ambiguous_cases = [
            ("I'll take two", "ADD_ITEM"),  # No item specified
            ("Give me three", "ADD_ITEM"),  # No item specified
            ("I want a couple", "ADD_ITEM"),  # No item specified
            ("Some of those", "ADD_ITEM"),  # Demonstrative
        ]
        
        for user_input, intent in ambiguous_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for ambiguous: '{user_input}'"
        
        # Explicit - should also trigger (let LLM handle nuanced cases)
        # The LLM will quickly resolve these as explicit
        explicit_cases = [
            ("I'll take two burgers", "ADD_ITEM"),  # Item specified
            ("Give me three wraps", "ADD_ITEM"),  # Item specified
            ("I want a couple of fries", "ADD_ITEM"),  # Item specified
            ("Some cookies please", "ADD_ITEM"),  # Item specified
        ]
        
        for user_input, intent in explicit_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is True, f"Should trigger for explicit (let LLM decide): '{user_input}'"
    
    def test_eligibility_check_non_eligible_intents(self, context_service):
        """Test that non-eligible intents never trigger resolution"""
        test_cases = [
            ("I'll take two", "GREETING"),
            ("That sounds good", "SMALLTALK"),
            ("I want this", "UNKNOWN"),
        ]
        
        for user_input, intent in test_cases:
            result = context_service.check_eligibility(user_input, intent)
            assert result is False, f"Should NOT trigger for intent: '{intent}'"

    # ========== FAST PATH TESTS ==========
    
    @pytest.mark.asyncio
    async def test_fast_path_explicit_inputs_pass_through(self, context_service, conversation_history, command_history, current_order):
        """Test that explicit inputs use fast path and pass through unchanged"""
        test_cases = [
            "I'd like one burger",
            "I'll take 3 wraps", 
            "Can I get two fries",
            "Add a shake to my order",
            "I want a sandwich",
            "Give me some cookies",
        ]
        
        for user_input in test_cases:
            result = await context_service.resolve_context(
                user_input=user_input,
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            # Should use fast path
            assert result.needs_resolution is False, f"Should not need resolution for: '{user_input}'"
            assert result.resolved_text == user_input, f"Should pass through unchanged: '{user_input}'"
            assert result.confidence == 0.98, f"Should have high confidence for: '{user_input}'"
            assert "Explicit request" in result.rationale, f"Should have explicit rationale for: '{user_input}'"
    
    @pytest.mark.asyncio
    async def test_fast_path_ambiguous_inputs_trigger_llm(self, context_service, conversation_history, command_history, current_order):
        """Test that ambiguous inputs trigger LLM resolution"""
        # Mock the LLM call
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "SUCCESS",
                "I'll take two veggie wraps",
                None,
                0.95,
                "Resolved from context"
            )
            
            result = await context_service.resolve_context(
                user_input="I'll take two",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            # Should call LLM
            mock_llm.assert_called_once()
            assert result.needs_resolution is True
            assert result.resolved_text == "I'll take two veggie wraps"
            assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_fast_path_repair_markers_trigger_llm(self, context_service, conversation_history, command_history, current_order):
        """Test that repair markers trigger LLM resolution"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "SUCCESS",
                "Remove the veggie wrap from my order",
                None,
                0.9,
                "Resolved repair marker"
            )
            
            result = await context_service.resolve_context(
                user_input="Actually, take that off",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            mock_llm.assert_called_once()
            assert result.needs_resolution is True
            assert result.resolved_text == "Remove the veggie wrap from my order"
    
    @pytest.mark.asyncio
    async def test_fast_path_ellipsis_markers_trigger_llm(self, context_service, conversation_history, command_history, current_order):
        """Test that ellipsis markers trigger LLM resolution"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "SUCCESS",
                "Add another veggie wrap to my order",
                None,
                0.9,
                "Resolved ellipsis"
            )
            
            result = await context_service.resolve_context(
                user_input="Another one please",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            mock_llm.assert_called_once()
            assert result.needs_resolution is True
            assert result.resolved_text == "Add another veggie wrap to my order"

    # ========== LLM INTEGRATION TESTS ==========
    
    @pytest.mark.asyncio
    async def test_llm_success_response(self, context_service, conversation_history, command_history, current_order):
        """Test handling of successful LLM response"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "SUCCESS",
                "I'll take two veggie wraps",
                None,
                0.95,
                "Successfully resolved from context"
            )
            
            result = await context_service.resolve_context(
                user_input="I'll take two",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            assert result.needs_resolution is True
            assert result.resolved_text == "I'll take two veggie wraps"
            assert result.confidence == 0.95
            assert result.rationale == "Successfully resolved from context"
    
    @pytest.mark.asyncio
    async def test_llm_clarification_needed_response(self, context_service, conversation_history, command_history, current_order):
        """Test handling of clarification needed response"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "CLARIFICATION_NEEDED",
                None,
                "Which item would you like to remove?",
                0.5,
                "Multiple candidates found"
            )
            
            result = await context_service.resolve_context(
                user_input="Take those off",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            assert result.needs_resolution is True
            assert result.resolved_text == "Which item would you like to remove?"
            assert result.confidence == 0.5
            assert result.rationale == "Multiple candidates found"
    
    @pytest.mark.asyncio
    async def test_llm_unresolvable_response(self, context_service, conversation_history, command_history, current_order):
        """Test handling of unresolvable response"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "UNRESOLVABLE",
                None,
                "Could you please be more specific?",
                0.2,
                "Insufficient context"
            )
            
            result = await context_service.resolve_context(
                user_input="I want that thing",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            assert result.needs_resolution is True
            assert result.resolved_text == "I want that thing"  # Falls back to original
            assert result.confidence == 0.2
            assert result.rationale == "Insufficient context"
    
    @pytest.mark.asyncio
    async def test_llm_error_handling(self, context_service, conversation_history, command_history, current_order):
        """Test LLM error handling"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")
            
            result = await context_service.resolve_context(
                user_input="I'll take two",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            assert result.needs_resolution is True
            assert result.resolved_text == "I'll take two"  # Falls back to original
            assert result.confidence == 0.0
            assert "LLM API error" in result.rationale

    # ========== EDGE CASE TESTS ==========
    
    def test_eligibility_check_edge_cases(self, context_service):
        """Test edge cases for eligibility checking"""
        # Test case sensitivity
        assert context_service.check_eligibility("I'll take IT", "ADD_ITEM") is True
        assert context_service.check_eligibility("THAT sounds good", "ADD_ITEM") is True
        
        # Test with extra whitespace
        assert context_service.check_eligibility("  I'll take it  ", "ADD_ITEM") is True
        assert context_service.check_eligibility("  I want a burger  ", "ADD_ITEM") is True  # Let LLM decide
        
        # Test with punctuation
        assert context_service.check_eligibility("I'll take it!", "ADD_ITEM") is True
        assert context_service.check_eligibility("I want a burger.", "ADD_ITEM") is True  # Let LLM decide
    
    @pytest.mark.asyncio
    async def test_resolve_context_empty_conversation_history(self, context_service, command_history, current_order):
        """Test context resolution with empty conversation history"""
        empty_history = ConversationHistory()
        
        # Explicit input should still work
        result = await context_service.resolve_context(
            user_input="I want a burger",
            conversation_history=empty_history,
            command_history=command_history,
            current_order=current_order
        )
        
        assert result.needs_resolution is False
        assert result.resolved_text == "I want a burger"
        assert result.confidence == 0.98
    
    @pytest.mark.asyncio
    async def test_resolve_context_no_current_order(self, context_service, conversation_history, command_history):
        """Test context resolution without current order"""
        result = await context_service.resolve_context(
            user_input="I want a burger",
            conversation_history=conversation_history,
            command_history=command_history,
            current_order=None
        )
        
        assert result.needs_resolution is False
        assert result.resolved_text == "I want a burger"
        assert result.confidence == 0.98

    # ========== CONFIDENCE THRESHOLD TESTS ==========
    
    def test_should_use_resolution_high_confidence(self, context_service):
        """Test resolution decision with high confidence"""
        result = ContextResolutionResult(
            needs_resolution=True,
            resolved_text="I'll take two veggie wraps",
            confidence=0.9,
            rationale="High confidence resolution",
            original_text="I'll take two"
        )
        
        should_use = context_service.should_use_resolution(result, threshold=0.8)
        assert should_use is True
    
    def test_should_use_resolution_low_confidence(self, context_service):
        """Test resolution decision with low confidence"""
        result = ContextResolutionResult(
            needs_resolution=True,
            resolved_text="I'll take two veggie wraps",
            confidence=0.5,
            rationale="Low confidence resolution",
            original_text="I'll take two"
        )
        
        should_use = context_service.should_use_resolution(result, threshold=0.8)
        assert should_use is False
    
    def test_should_use_resolution_custom_threshold(self, context_service):
        """Test resolution decision with custom threshold"""
        result = ContextResolutionResult(
            needs_resolution=True,
            resolved_text="I'll take two veggie wraps",
            confidence=0.7,
            rationale="Medium confidence resolution",
            original_text="I'll take two"
        )
        
        # Test with lower threshold
        should_use_low = context_service.should_use_resolution(result, threshold=0.6)
        assert should_use_low is True
        
        # Test with higher threshold
        should_use_high = context_service.should_use_resolution(result, threshold=0.8)
        assert should_use_high is False

    # ========== INTEGRATION TESTS ==========
    
    @pytest.mark.asyncio
    async def test_full_flow_explicit_input(self, context_service, conversation_history, command_history, current_order):
        """Test full flow for explicit input - should bypass LLM entirely"""
        # This should not call the LLM at all
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            result = await context_service.resolve_context(
                user_input="I'll take 3 wraps",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            # LLM should not be called
            mock_llm.assert_not_called()
            
            # Should use fast path
            assert result.needs_resolution is False
            assert result.resolved_text == "I'll take 3 wraps"
            assert result.confidence == 0.98
    
    @pytest.mark.asyncio
    async def test_full_flow_ambiguous_input(self, context_service, conversation_history, command_history, current_order):
        """Test full flow for ambiguous input - should call LLM"""
        with patch.object(context_service, '_llm_call_and_parse', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = (
                "SUCCESS",
                "I'll take two veggie wraps",
                None,
                0.9,
                "Resolved from conversation context"
            )
            
            result = await context_service.resolve_context(
                user_input="I'll take two",
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            # LLM should be called
            mock_llm.assert_called_once()
            
            # Should use LLM result
            assert result.needs_resolution is True
            assert result.resolved_text == "I'll take two veggie wraps"
            assert result.confidence == 0.9