"""
Integration tests for Intent Classification Agent with real OpenAI API

These tests use:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- No database needed (pure LLM classification)
- Tests all intent types and edge cases
"""

import pytest
from app.workflow.agents.intent_classification_agent import intent_classification_agent
from app.constants.intent_types import IntentType
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory, ConversationRole


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestIntentClassificationAgentIntegration:
    """Integration tests for intent classification agent with real API calls"""
    
    @pytest.mark.asyncio
    async def test_add_item_intent(self):
        """Test ADD_ITEM intent classification"""
        
        test_cases = [
            "I'd like a burger and fries",
            "Can I get two Big Macs?",
            "I want a large Coke",
            "Add a cheeseburger to my order",
            "I'll have the chicken sandwich"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[]
            )
            
            print(f"\n[ADD_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.ADD_ITEM
            assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_remove_item_intent(self):
        """Test REMOVE_ITEM intent classification"""
        
        test_cases = [
            "Remove my fries",
            "Cancel the burger",
            "Take off the Coke",
            "I don't want the shake anymore",
            "Remove that last item"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[{"name": "fries", "quantity": 1}]
            )
            
            print(f"\n[REMOVE_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.REMOVE_ITEM
            assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_confirm_order_intent(self):
        """Test CONFIRM_ORDER intent classification"""
        
        test_cases = [
            "That's it",
            "That's all",
            "Done",
            "I'm finished",
            "That'll be all",
            "That's everything"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[CONFIRM_ORDER] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.CONFIRM_ORDER
            assert result.confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_question_intent(self):
        """Test QUESTION intent classification"""
        
        test_cases = [
            "How much is a burger?",
            "What sizes do you have?",
            "Do you have chicken?",
            "What's in the combo?",
            "Is the shake dairy-free?",
            "How big is the large?"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[]
            )
            
            print(f"\n[QUESTION] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.QUESTION
            assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_clear_order_intent(self):
        """Test CLEAR_ORDER intent classification"""
        
        test_cases = [
            "Clear my order",
            "Cancel everything",
            "Start over",
            "Clear all items",
            "Remove everything"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[{"name": "burger", "quantity": 1}, {"name": "fries", "quantity": 1}]
            )
            
            print(f"\n[CLEAR_ORDER] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.CLEAR_ORDER
            assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_modify_item_intent(self):
        """Test MODIFY_ITEM intent classification"""
        
        test_cases = [
            "No pickles on the burger",
            "Make it spicy",
            "Add extra cheese",
            "Hold the mayo",
            "Make it medium rare"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[MODIFY_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            # "Add extra cheese" can be ambiguous - could be ADD_ITEM or MODIFY_ITEM
            assert result.intent in [IntentType.MODIFY_ITEM, IntentType.ADD_ITEM]
            assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_set_quantity_intent(self):
        """Test SET_QUANTITY intent classification"""
        
        test_cases = [
            "Make it two",
            "Change to three",
            "I want four of those",
            "Make that five",
            "Double the order"
        ]
        
        for user_input in test_cases:
            # Create conversation history with context
            context_history = ConversationHistory(session_id="test_session")
            context_history.add_entry(ConversationRole.USER, "I want a burger")
            
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=context_history,
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[SET_QUANTITY] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            assert result.intent == IntentType.MODIFY_ITEM
            assert result.confidence >= 0.7
    
    # Note: test_repeat_intent removed - REPEAT intent type does not exist
    
    @pytest.mark.asyncio
    async def test_unknown_intent(self):
        """Test UNKNOWN intent classification for unclear inputs"""
        
        test_cases = [
            "asdfasdf",
            "random gibberish",
            "I don't know",
            "Maybe",
            "Hmm"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[]
            )
            
            print(f"\n[UNKNOWN] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            
            # UNKNOWN should have low confidence
            assert result.intent == IntentType.UNKNOWN
            assert result.confidence <= 0.6
    
    # Note: test_cleansed_input_filtering removed - cleansed input functionality was removed in refactoring
    
    @pytest.mark.asyncio
    async def test_conversation_history_context(self):
        """Test that conversation history influences intent classification"""
        
        # Test ambiguous input that needs context
        result_without_context = await intent_classification_agent(
            user_input="Remove it",
            conversation_history=ConversationHistory(session_id="test_session"),
            order_items=[{"name": "burger", "quantity": 1}]
        )
        
        # Create conversation history with context
        context_history = ConversationHistory(session_id="test_session")
        context_history.add_entry(ConversationRole.USER, "I want a burger")
        context_history.add_entry(ConversationRole.ASSISTANT, "Added burger to your order")
        
        result_with_context = await intent_classification_agent(
            user_input="Remove it",
            conversation_history=context_history,
            order_items=[{"name": "burger", "quantity": 1}]
        )
        
        print(f"\n[CONTEXT] Without context: {result_without_context.intent} (confidence: {result_without_context.confidence})")
        print(f"   With context: {result_with_context.intent} (confidence: {result_with_context.confidence})")
        
        # Context should help with confidence
        assert result_with_context.confidence >= result_without_context.confidence
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling with invalid inputs"""
        
        # Test with empty input
        result = await intent_classification_agent(
            user_input="",
            conversation_history=ConversationHistory(session_id="test_session"),
            order_items=[]
        )
        
        print(f"\n[ERROR HANDLING] Empty input -> {result.intent} (confidence: {result.confidence})")
        
        # Should handle gracefully
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence <= 0.5
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test that confidence scores are reasonable"""
        
        # High confidence cases
        high_confidence_inputs = [
            "I want a burger",
            "That's all",
            "How much is it?"
        ]
        
        for user_input in high_confidence_inputs:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=ConversationHistory(session_id="test_session"),
                order_items=[]
            )
            
            print(f"\n[CONFIDENCE] '{user_input}' -> confidence: {result.confidence}")
            
            # Should be high confidence for clear intents
            assert result.confidence >= 0.7
            assert result.is_actionable() or result.intent == IntentType.QUESTION
    
    @pytest.mark.asyncio
    async def test_response_model_validation(self):
        """Test that response model validation works correctly"""
        
        result = await intent_classification_agent(
            user_input="I want a burger",
            conversation_history=ConversationHistory(session_id="test_session"),
            order_items=[]
        )
        
        # Test model methods
        assert hasattr(result, 'is_high_confidence')
        assert hasattr(result, 'is_actionable')
        
        print(f"\n[MODEL] Intent: {result.intent}")
        print(f"   High confidence: {result.is_high_confidence()}")
        print(f"   Actionable: {result.is_actionable()}")
        
        # Validate model structure
        assert result.intent is not None
        assert 0.0 <= result.confidence <= 1.0
