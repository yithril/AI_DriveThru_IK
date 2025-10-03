"""
Integration tests for Context Agent with realistic conversation scenarios
"""

import pytest
from app.workflow.agents.context_agent import ContextAgent, ContextAgentResult
from app.config.settings import settings


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestContextAgentIntegration:
    """Integration tests for context agent with realistic scenarios"""
    
    @pytest.fixture
    def context_agent(self):
        """Create ContextAgent instance for testing"""
        return ContextAgent()
    
    @pytest.fixture
    def veggie_wrap_conversation_history(self):
        """Realistic conversation about veggie wrap"""
        return [
            {
                "role": "customer",
                "content": "Tell me about the veggie wrap"
            },
            {
                "role": "assistant", 
                "content": "The veggie wrap is a healthy option with fresh lettuce, tomatoes, cucumbers, red onions, and our house-made hummus spread, all wrapped in a whole wheat tortilla. It's perfect for a light meal and comes with a side of mixed greens."
            },
            {
                "role": "customer",
                "content": "Okay I'll take two of those"
            }
        ]
    
    @pytest.fixture
    def quantum_burger_conversation_history(self):
        """Realistic conversation about quantum burger with modifiers"""
        return [
            {
                "role": "customer",
                "content": "What's on the quantum burger?"
            },
            {
                "role": "assistant",
                "content": "The quantum burger comes with a beef patty, cosmic cheese, space sauce, quantum lettuce, and stellar onions on a stellar bun. It's our signature burger with a cosmic twist!"
            },
            {
                "role": "customer",
                "content": "Cool I'll take that but no cheese and extra lettuce."
            }
        ]
    
    @pytest.fixture
    def veggie_wrap_command_history(self):
        """Command history for veggie wrap scenario"""
        return [
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about veggie wrap ingredients"
            }
        ]
    
    @pytest.fixture
    def quantum_burger_command_history(self):
        """Command history for quantum burger scenario"""
        return [
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about quantum burger ingredients"
            }
        ]
    
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
    async def test_veggie_wrap_context_resolution(
        self,
        context_agent,
        veggie_wrap_conversation_history,
        veggie_wrap_command_history,
        empty_current_order
    ):
        """Test context resolution for 'I'll take two of those' after veggie wrap discussion"""
        
        user_input = "I'll take two of those"
        
        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=veggie_wrap_conversation_history,
            command_history=veggie_wrap_command_history,
            current_order=empty_current_order
        )
        
        # Verify result structure
        assert isinstance(result, ContextAgentResult)
        assert result.status in ["SUCCESS", "CLARIFICATION_NEEDED", "SYSTEM_ERROR"]
        
        # Print results for analysis
        print(f"\n[CONTEXT AGENT TEST]")
        print(f"Input: '{user_input}'")
        print(f"\nConversation History:")
        for i, turn in enumerate(veggie_wrap_conversation_history):
            print(f"  {i+1}. {turn['role']}: {turn['content']}")
        print(f"\nCommand History:")
        for i, cmd in enumerate(veggie_wrap_command_history):
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
            assert "veggie wrap" in result.resolved_text.lower()
            assert "two" in result.resolved_text.lower()
            assert result.confidence >= 0.8
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            
        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            assert len(result.clarification_message) > 0
            print(f"❓ CLARIFICATION: {result.clarification_message}")
            
        else:  # SYSTEM_ERROR
            print(f"🚨 SYSTEM ERROR: {result.rationale}")
    
    @pytest.mark.asyncio
    async def test_quantum_burger_with_modifiers(
        self,
        context_agent,
        quantum_burger_conversation_history,
        quantum_burger_command_history,
        empty_current_order
    ):
        """Test context resolution for 'I'll take that but no cheese and extra lettuce' after quantum burger discussion"""
        
        user_input = "Cool I'll take that but no cheese and extra lettuce."
        
        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=quantum_burger_conversation_history,
            command_history=quantum_burger_command_history,
            current_order=empty_current_order
        )
        
        # Print results for analysis
        print(f"\n[QUANTUM BURGER WITH MODIFIERS TEST]")
        print(f"Input: '{user_input}'")
        print(f"\nConversation History:")
        for i, turn in enumerate(quantum_burger_conversation_history):
            print(f"  {i+1}. {turn['role']}: {turn['content']}")
        print(f"\nCommand History:")
        for i, cmd in enumerate(quantum_burger_command_history):
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
            assert "quantum burger" in result.resolved_text.lower()
            assert "no cheese" in result.resolved_text.lower()
            assert "extra lettuce" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            
        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            assert len(result.clarification_message) > 0
            print(f"❓ CLARIFICATION: {result.clarification_message}")
            
        else:  # SYSTEM_ERROR
            print(f"🚨 SYSTEM ERROR: {result.rationale}")
    
