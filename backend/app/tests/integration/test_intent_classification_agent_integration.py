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
                conversation_history=[],
                order_items=[]
            )
            
            print(f"\n[ADD_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.ADD_ITEM
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[{"name": "fries", "quantity": 1}]
            )
            
            print(f"\n[REMOVE_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.REMOVE_ITEM
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[CONFIRM_ORDER] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.CONFIRM_ORDER
            assert result.confidence >= 0.8
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[]
            )
            
            print(f"\n[QUESTION] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.QUESTION
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[{"name": "burger", "quantity": 1}, {"name": "fries", "quantity": 1}]
            )
            
            print(f"\n[CLEAR_ORDER] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.CLEAR_ORDER
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[MODIFY_ITEM] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.MODIFY_ITEM
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=[{"role": "user", "content": "I want a burger"}],
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[SET_QUANTITY] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.SET_QUANTITY
            assert result.confidence >= 0.7
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_repeat_intent(self):
        """Test REPEAT intent classification"""
        
        test_cases = [
            "I'll have what she's having",
            "Same as before",
            "Repeat that order",
            "I want the same thing",
            "Make it the same as last time"
        ]
        
        for user_input in test_cases:
            result = await intent_classification_agent(
                user_input=user_input,
                conversation_history=[],
                order_items=[{"name": "burger", "quantity": 1}]
            )
            
            print(f"\n[REPEAT] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            assert result.intent == IntentType.REPEAT
            assert result.confidence >= 0.6  # Repeat can be more ambiguous
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
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
                conversation_history=[],
                order_items=[]
            )
            
            print(f"\n[UNKNOWN] '{user_input}' -> {result.intent} (confidence: {result.confidence})")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            # UNKNOWN should have low confidence
            assert result.intent == IntentType.UNKNOWN
            assert result.confidence <= 0.6
            assert result.cleansed_input is not None
            assert len(result.cleansed_input.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_cleansed_input_filtering(self):
        """Test that cleansed input properly filters noise"""
        
        test_cases = [
            {
                "input": "I'd like two burgers... Shawn stop hitting your sister... with no pickles",
                "expected_contains": ["burgers", "no pickles"],
                "expected_excludes": ["Shawn", "sister"]
            },
            {
                "input": "Can I get fries? Thanks!",
                "expected_contains": ["fries"],
                "expected_excludes": []
            },
            {
                "input": "I'd like a burger... um... with no pickles",
                "expected_contains": ["burger", "no pickles"],
                "expected_excludes": ["um"]
            }
        ]
        
        for test_case in test_cases:
            result = await intent_classification_agent(
                user_input=test_case["input"],
                conversation_history=[],
                order_items=[]
            )
            
            print(f"\n[CLEANSED] '{test_case['input']}'")
            print(f"   Cleansed: '{result.cleansed_input}'")
            
            # Check expected content is present
            for expected in test_case["expected_contains"]:
                assert expected.lower() in result.cleansed_input.lower(), f"Expected '{expected}' in cleansed input"
            
            # Check noise is filtered out
            for excluded in test_case["expected_excludes"]:
                assert excluded.lower() not in result.cleansed_input.lower(), f"Didn't expect '{excluded}' in cleansed input"
    
    @pytest.mark.asyncio
    async def test_conversation_history_context(self):
        """Test that conversation history influences intent classification"""
        
        # Test ambiguous input that needs context
        result_without_context = await intent_classification_agent(
            user_input="Remove it",
            conversation_history=[],
            order_items=[{"name": "burger", "quantity": 1}]
        )
        
        result_with_context = await intent_classification_agent(
            user_input="Remove it",
            conversation_history=[
                {"role": "user", "content": "I want a burger"},
                {"role": "assistant", "content": "Added burger to your order"}
            ],
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
            conversation_history=[],
            order_items=[]
        )
        
        print(f"\n[ERROR HANDLING] Empty input -> {result.intent} (confidence: {result.confidence})")
        
        # Should handle gracefully
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence <= 0.5
        assert result.cleansed_input is not None
    
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
                conversation_history=[],
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
            conversation_history=[],
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
        assert isinstance(result.cleansed_input, str)
        assert len(result.cleansed_input.strip()) > 0
