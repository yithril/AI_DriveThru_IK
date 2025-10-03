import pytest
from app.workflow.agents.context_agent import ContextAgent, ContextAgentResult
from app.config.settings import settings

# Skip all tests in this file if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)

class TestQuestionContext:
    """Integration tests for ContextAgent with question scenarios"""

    @pytest.fixture
    def context_agent(self):
        """Create ContextAgent instance for testing"""
        return ContextAgent()

    @pytest.fixture
    def question_context_conversation_history(self):
        """Conversation about multiple burgers with questions"""
        return [
            {
                "role": "customer",
                "content": "So what's on the quantum burger?"
            },
            {
                "role": "assistant",
                "content": "The quantum burger comes with a beef patty, cosmic cheese, space sauce, quantum lettuce, and stellar onions on a stellar bun. It's our signature burger with a cosmic twist!"
            },
            {
                "role": "customer",
                "content": "Okay well what's on the neon burger then?"
            },
            {
                "role": "assistant",
                "content": "The neon burger features a beef patty, neon cheese, electric sauce, glow-in-the-dark lettuce, and cyber onions on a cyber bun. It's our futuristic burger with a glowing neon effect!"
            },
            {
                "role": "customer",
                "content": "What's the difference between the two?"
            }
        ]

    @pytest.fixture
    def question_context_command_history(self):
        """Command history for question scenario"""
        return [
            {
                "action": "QUESTION_ANSWERED",
                "description": "Customer asked about quantum burger ingredients"
            },
            {
                "action": "QUESTION_ANSWERED", 
                "description": "Customer asked about neon burger ingredients"
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
    async def test_question_context_resolution(
        self,
        context_agent,
        question_context_conversation_history,
        question_context_command_history,
        empty_current_order
    ):
        """Test context resolution for question scenario with ambiguous references"""

        user_input = "What's the difference between the two?"

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=question_context_conversation_history,
            command_history=question_context_command_history,
            current_order=empty_current_order
        )

        # Verify result structure
        assert isinstance(result, ContextAgentResult)
        assert result.status in ["SUCCESS", "CLARIFICATION_NEEDED", "UNRESOLVABLE", "SYSTEM_ERROR"]

        # Print results for analysis
        print(f"\n[QUESTION CONTEXT TEST]")
        print(f"Input: '{user_input}'")
        print(f"\nConversation History:")
        for i, turn in enumerate(question_context_conversation_history):
            print(f"  {i+1}. {turn['role']}: {turn['content']}")
        print(f"\nCommand History:")
        for i, cmd in enumerate(question_context_command_history):
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
            # Should resolve to explicit question about both burgers
            assert "quantum burger" in result.resolved_text.lower()
            assert "neon burger" in result.resolved_text.lower()
            assert "difference" in result.resolved_text.lower()
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
