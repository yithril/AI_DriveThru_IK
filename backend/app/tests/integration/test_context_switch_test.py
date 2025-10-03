import pytest
from app.workflow.agents.context_agent import ContextAgent, ContextAgentResult
from app.config.settings import settings

# Skip all tests in this file if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)

class TestContextSwitch:
    """Integration tests for ContextAgent with complex context switching scenarios"""

    @pytest.fixture
    def context_agent(self):
        """Create ContextAgent instance for testing"""
        return ContextAgent()

    @pytest.fixture
    def context_switch_conversation_history(self):
        """Complex conversation with context switching"""
        return [
            {
                "role": "customer",
                "content": "So tell me about the veggie wrap."
            },
            {
                "role": "assistant",
                "content": "The veggie wrap is a healthy option with fresh lettuce, tomatoes, cucumbers, red onions, and our house-made hummus spread, all wrapped in a whole wheat tortilla. It's perfect for a light meal and comes with a side of mixed greens."
            },
            {
                "role": "customer",
                "content": "Well what about the quantum salad, what's on that?"
            },
            {
                "role": "assistant",
                "content": "The quantum salad has cosmic lettuce, stellar tomatoes, quantum cucumbers, space onions, and our signature stardust dressing. It's a fresh and healthy option with a cosmic twist!"
            },
            {
                "role": "customer",
                "content": "Okay great I'll take three of those..wait..on second thought, I'll take three of the first one instead."
            }
        ]

    @pytest.fixture
    def context_switch_command_history(self):
        """Command history for context switch scenario"""
        return [
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about veggie wrap ingredients"
            },
            {
                "action": "QUESTION_ANSWERED", 
                "description": "Customer asked about quantum salad ingredients"
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
    async def test_context_switch_resolution(
        self,
        context_agent,
        context_switch_conversation_history,
        context_switch_command_history,
        empty_current_order
    ):
        """Test context resolution for complex context switching scenario"""

        user_input = "Okay great I'll take three of those..wait..on second thought, I'll take three of the first one instead."

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=context_switch_conversation_history,
            command_history=context_switch_command_history,
            current_order=empty_current_order
        )

        # Verify result structure
        assert isinstance(result, ContextAgentResult)
        assert result.status in ["SUCCESS", "CLARIFICATION_NEEDED", "UNRESOLVABLE", "SYSTEM_ERROR"]

        # Print results for analysis
        print(f"\n[CONTEXT SWITCH TEST]")
        print(f"Input: '{user_input}'")
        print(f"\nConversation History:")
        for i, turn in enumerate(context_switch_conversation_history):
            print(f"  {i+1}. {turn['role']}: {turn['content']}")
        print(f"\nCommand History:")
        for i, cmd in enumerate(context_switch_command_history):
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
            # Should resolve to veggie wrap (the "first one" mentioned)
            assert "veggie wrap" in result.resolved_text.lower()
            assert "three" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            assert len(result.clarification_message) > 0
            print(f"❓ CLARIFICATION: {result.clarification_message}")

        elif result.status == "UNRESOLVABLE":
            assert result.clarification_message is not None
            assert len(result.clarification_message) > 0
            print(f"🚫 UNRESOLVABLE: {result.clarification_message}")

        else:  # SYSTEM_ERROR
            print(f"🚨 SYSTEM ERROR: {result.rationale}")
