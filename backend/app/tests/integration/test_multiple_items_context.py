"""
Integration test for multiple items context resolution
"""

import pytest
from app.workflow.agents.context_agent import ContextAgent, ContextAgentResult
from app.config.settings import settings


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestMultipleItemsContext:
    """Test context resolution with multiple items discussed"""
    
    @pytest.fixture
    def context_agent(self):
        """Create ContextAgent instance for testing"""
        return ContextAgent()
    
    @pytest.fixture
    def multiple_items_conversation_history(self):
        """Realistic conversation about multiple items"""
        return [
            {
                "role": "customer",
                "content": "Tell me about the cosmic fries"
            },
            {
                "role": "assistant",
                "content": "Our cosmic fries are seasoned with space dust and served crispy. They're the perfect side to any meal."
            },
            {
                "role": "customer",
                "content": "What about the lunar lemonade?"
            },
            {
                "role": "assistant",
                "content": "The lunar lemonade is a refreshing citrus drink with a hint of stardust. It's made with fresh lemons and cosmic ice."
            },
            {
                "role": "customer",
                "content": "I'll take the fries"
            }
        ]
    
    @pytest.fixture
    def multiple_items_command_history(self):
        """Command history for multiple items scenario"""
        return [
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about cosmic fries"
            },
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about lunar lemonade"
            }
        ]
    
    @pytest.fixture
    def empty_current_order(self):
        """Empty current order"""
        return {
            "items": [],
            "total": 0.0
        }
    
    @pytest.mark.asyncio
    async def test_multiple_items_context_resolution(
        self,
        context_agent,
        multiple_items_conversation_history,
        multiple_items_command_history,
        empty_current_order
    ):
        """Test context resolution for 'I'll take the fries' after discussing both fries and lemonade"""
        
        user_input = "I'll take the fries"
        
        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=multiple_items_conversation_history,
            command_history=multiple_items_command_history,
            current_order=empty_current_order
        )
        
        # Print results for analysis
        print(f"\n[MULTIPLE ITEMS CONTEXT TEST]")
        print(f"Input: '{user_input}'")
        print(f"\nConversation History:")
        for i, turn in enumerate(multiple_items_conversation_history):
            print(f"  {i+1}. {turn['role']}: {turn['content']}")
        print(f"\nCommand History:")
        for i, cmd in enumerate(multiple_items_command_history):
            print(f"  {i+1}. {cmd['action']}: {cmd['description']}")
        print(f"\nCurrent Order: {empty_current_order}")
        print(f"\nResult:")
        print(f"  Status: {result.status}")
        print(f"  Resolved Text: {result.resolved_text}")
        print(f"  Clarification Message: {result.clarification_message}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Rationale: {result.rationale}")
        
        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "cosmic fries" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            
        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            assert len(result.clarification_message) > 0
            print(f"❓ CLARIFICATION: {result.clarification_message}")
            
        else:  # SYSTEM_ERROR
            print(f"🚨 SYSTEM ERROR: {result.rationale}")
