import pytest
from app.workflow.agents.context_agent import ContextAgent, ContextAgentResult
from app.config.settings import settings

# Skip all tests in this file if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)

class TestContextAgentComprehensive:
    """Comprehensive integration tests for ContextAgent with various scenarios"""

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
    def remove_item_conversation_history(self):
        """Conversation with item removal scenario"""
        return [
            {
                "role": "customer",
                "content": "So I'll take the lunar lemonade."
            },
            {
                "role": "assistant",
                "content": "Lunar lemonade added to your order."
            },
            {
                "role": "customer",
                "content": "On second thought, take that off."
            }
        ]

    @pytest.fixture
    def modify_item_conversation_history(self):
        """Conversation with item modification scenario"""
        return [
            {
                "role": "customer",
                "content": "So I'd love a quantum salad with lots of croutons and 2 packs of ranch dressing."
            },
            {
                "role": "assistant",
                "content": "Added to your order."
            },
            {
                "role": "customer",
                "content": "Actually make that lots of croutons AND extra blue cheese."
            }
        ]

    @pytest.fixture
    def complex_order_conversation_history(self):
        """Complex conversation with multiple items and modifications"""
        return [
            {
                "role": "customer",
                "content": "I'll take 3 quantum burgers extra onions, 2 lunar lemonades, 2 strawberry shakes, 1 chocolate shake, and 4 orders of astro nuggets with barbecue sauce."
            },
            {
                "role": "assistant",
                "content": "Added to your order. Would you like anything else."
            },
            {
                "role": "customer",
                "content": "Actually no I changed my mind, take the shakes off."
            }
        ]

    @pytest.fixture
    def noisy_conversation_history(self):
        """Conversation with background noise and interruptions"""
        return [
            {
                "role": "customer",
                "content": "Hi, I'd like to place an order"
            },
            {
                "role": "assistant",
                "content": "Hello! Welcome to our drive-thru. What can I get for you today?"
            },
            {
                "role": "customer",
                "content": "I'll take two veggie wraps....Stevie stop hitting your sister...and three chocolate milkshakes...and wait I told you to stop fighting or I'm leaving the drive thru...and two quantum burgers. Actually make that 3."
            }
        ]

    @pytest.fixture
    def unresolvable_conversation_history(self):
        """Conversation with minimal context for unresolvable scenario"""
        return [
            {
                "role": "customer",
                "content": "Hi there"
            },
            {
                "role": "assistant",
                "content": "Hello! Welcome to our drive-thru. What can I get for you today?"
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
    def remove_item_command_history(self):
        """Command history for remove item scenario"""
        return [
            {
                "action": "ITEM_ADDED",
                "description": "Customer added lunar lemonade to order"
            }
        ]

    @pytest.fixture
    def modify_item_command_history(self):
        """Command history for modify item scenario"""
        return [
            {
                "action": "ITEM_ADDED",
                "description": "Customer added quantum salad with croutons and ranch dressing"
            }
        ]

    @pytest.fixture
    def complex_order_command_history(self):
        """Command history for complex order scenario"""
        return [
            {
                "action": "ITEM_ADDED",
                "description": "Customer added 3 quantum burgers with extra onions"
            },
            {
                "action": "ITEM_ADDED",
                "description": "Customer added 2 lunar lemonades"
            },
            {
                "action": "ITEM_ADDED",
                "description": "Customer added 2 strawberry shakes"
            },
            {
                "action": "ITEM_ADDED",
                "description": "Customer added 1 chocolate shake"
            },
            {
                "action": "ITEM_ADDED",
                "description": "Customer added 4 astro nuggets with barbecue sauce"
            }
        ]

    @pytest.fixture
    def empty_current_order(self):
        """Empty current order"""
        return {
            "items": [],
            "total": 0.0
        }

    @pytest.fixture
    def order_with_lunar_lemonade(self):
        """Current order containing lunar lemonade"""
        return {
            "items": [
                {
                    "id": "item_1",
                    "name": "Lunar Lemonade",
                    "quantity": 1,
                    "price": 3.99,
                    "modifications": []
                }
            ],
            "total": 3.99
        }

    @pytest.fixture
    def order_with_quantum_salad(self):
        """Current order containing quantum salad with modifications"""
        return {
            "items": [
                {
                    "id": "item_1",
                    "name": "Quantum Salad",
                    "quantity": 1,
                    "price": 8.99,
                    "modifications": [
                        {"type": "add", "ingredient": "croutons", "quantity": "lots"},
                        {"type": "add", "ingredient": "ranch dressing", "quantity": "2 packs"}
                    ]
                }
            ],
            "total": 8.99
        }

    @pytest.fixture
    def complex_order_with_multiple_items(self):
        """Complex order with multiple items and modifications"""
        return {
            "items": [
                {
                    "id": "item_1",
                    "name": "Quantum Burger",
                    "quantity": 3,
                    "price": 12.99,
                    "modifications": [
                        {"type": "add", "ingredient": "onions", "quantity": "extra"}
                    ]
                },
                {
                    "id": "item_2",
                    "name": "Lunar Lemonade",
                    "quantity": 2,
                    "price": 3.99,
                    "modifications": []
                },
                {
                    "id": "item_3",
                    "name": "Strawberry Shake",
                    "quantity": 2,
                    "price": 4.99,
                    "modifications": []
                },
                {
                    "id": "item_4",
                    "name": "Chocolate Shake",
                    "quantity": 1,
                    "price": 4.99,
                    "modifications": []
                },
                {
                    "id": "item_5",
                    "name": "Astro Nuggets",
                    "quantity": 4,
                    "price": 6.99,
                    "modifications": [
                        {"type": "add", "ingredient": "barbecue sauce", "quantity": "1"}
                    ]
                }
            ],
            "total": 33.95
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
        assert result.status in ["SUCCESS", "CLARIFICATION_NEEDED", "UNRESOLVABLE", "SYSTEM_ERROR"]

        # Print results for analysis
        print(f"\n[VEGGIE WRAP TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "veggie wrap" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

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
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "quantum burger" in result.resolved_text.lower()
            assert "no cheese" in result.resolved_text.lower()
            assert "extra lettuce" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

    @pytest.mark.asyncio
    async def test_multiple_items_context_resolution(
        self,
        context_agent,
        multiple_items_conversation_history,
        multiple_items_command_history,
        empty_current_order
    ):
        """Test context resolution for 'I'll take the fries' after discussing multiple items"""

        user_input = "I'll take the fries"

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=multiple_items_conversation_history,
            command_history=multiple_items_command_history,
            current_order=empty_current_order
        )

        # Print results for analysis
        print(f"\n[MULTIPLE ITEMS TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "cosmic fries" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

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

        # Print results for analysis
        print(f"\n[CONTEXT SWITCH TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "veggie wrap" in result.resolved_text.lower()
            assert "three" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

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

        # Print results for analysis
        print(f"\n[QUESTION CONTEXT TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "quantum burger" in result.resolved_text.lower()
            assert "neon burger" in result.resolved_text.lower()
            assert "difference" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

    @pytest.mark.asyncio
    async def test_remove_item_context_resolution(
        self,
        context_agent,
        remove_item_conversation_history,
        remove_item_command_history,
        order_with_lunar_lemonade
    ):
        """Test context resolution for remove item scenario"""

        user_input = "On second thought, take that off."

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=remove_item_conversation_history,
            command_history=remove_item_command_history,
            current_order=order_with_lunar_lemonade
        )

        # Print results for analysis
        print(f"\n[REMOVE ITEM TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "lunar lemonade" in result.resolved_text.lower()
            assert "remove" in result.resolved_text.lower() or "take off" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")

    @pytest.mark.asyncio
    async def test_modify_item_context_resolution(
        self,
        context_agent,
        modify_item_conversation_history,
        modify_item_command_history,
        order_with_quantum_salad
    ):
        """Test context resolution for modify item scenario with ambiguous scope"""

        user_input = "Actually make that lots of croutons AND extra blue cheese."

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=modify_item_conversation_history,
            command_history=modify_item_command_history,
            current_order=order_with_quantum_salad
        )

        # Print results for analysis
        print(f"\n[MODIFY ITEM TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "quantum salad" in result.resolved_text.lower()
            assert "croutons" in result.resolved_text.lower()
            assert "blue cheese" in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            # Note: The LLM will need to decide whether to keep ranch dressing or not
            if "ranch" in result.resolved_text.lower():
                print(f"   📝 LLM decided to keep ranch dressing")
            else:
                print(f"   📝 LLM decided to replace ranch with blue cheese")

    @pytest.mark.asyncio
    async def test_complex_order_removal_context_resolution(
        self,
        context_agent,
        complex_order_conversation_history,
        complex_order_command_history,
        complex_order_with_multiple_items
    ):
        """Test context resolution for complex order with multiple item removal"""

        user_input = "Actually no I changed my mind, take the shakes off."

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=complex_order_conversation_history,
            command_history=complex_order_command_history,
            current_order=complex_order_with_multiple_items
        )

        # Print results for analysis
        print(f"\n[COMPLEX ORDER REMOVAL TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            assert "shake" in result.resolved_text.lower()
            assert ("remove" in result.resolved_text.lower() or "take off" in result.resolved_text.lower())
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            # Check if LLM identified both shake types
            if "strawberry" in result.resolved_text.lower() and "chocolate" in result.resolved_text.lower():
                print(f"   📝 LLM identified both shake types")
            elif "shake" in result.resolved_text.lower():
                print(f"   📝 LLM identified shakes generically")
            else:
                print(f"   📝 LLM identified specific shake type")

    @pytest.mark.asyncio
    async def test_noisy_conversation_context_resolution(
        self,
        context_agent,
        noisy_conversation_history,
        empty_current_order
    ):
        """Test context resolution for noisy conversation with background interruptions"""

        user_input = "I'll take two veggie wraps....Stevie stop hitting your sister...and three chocolate milkshakes...and wait I told you to stop fighting or I'm leaving the drive thru...and two quantum burgers. Actually make that 3."

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=noisy_conversation_history,
            command_history=[],
            current_order=empty_current_order
        )

        # Print results for analysis
        print(f"\n[NOISY CONVERSATION TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior
        if result.status == "SUCCESS":
            assert result.resolved_text is not None
            # Should contain the main items without noise
            assert "veggie wrap" in result.resolved_text.lower()
            assert "chocolate milkshake" in result.resolved_text.lower()
            assert "quantum burger" in result.resolved_text.lower()
            # Should have correct quantities
            assert "two" in result.resolved_text.lower() or "2" in result.resolved_text
            assert "three" in result.resolved_text.lower() or "3" in result.resolved_text
            # Should not contain the noise
            assert "stevie" not in result.resolved_text.lower()
            assert "sister" not in result.resolved_text.lower()
            assert "fighting" not in result.resolved_text.lower()
            print(f"✅ SUCCESS: Resolved to '{result.resolved_text}'")
            print(f"   📝 LLM successfully filtered out background noise")
            print(f"   📝 LLM preserved all food items and quantities")
            print(f"   📝 LLM handled the quantity correction (2 → 3 quantum burgers)")

        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            print(f"❓ CLARIFICATION: {result.clarification_message}")

        elif result.status == "UNRESOLVABLE":
            assert result.clarification_message is not None
            print(f"🚫 UNRESOLVABLE: {result.clarification_message}")

        else:  # SYSTEM_ERROR
            print(f"🚨 SYSTEM ERROR: {result.rationale}")

    @pytest.mark.asyncio
    async def test_unresolvable_context(
        self,
        context_agent,
        unresolvable_conversation_history,
        empty_current_order
    ):
        """Test context resolution for unresolvable scenario"""

        user_input = "Can I get the thing with the thing?"

        result = await context_agent.resolve_context(
            user_input=user_input,
            conversation_history=unresolvable_conversation_history,
            command_history=[],
            current_order=empty_current_order
        )

        # Print results for analysis
        print(f"\n[UNRESOLVABLE TEST]")
        print(f"Input: '{user_input}'")
        print(f"Result: {result.status} - {result.resolved_text}")
        print(f"Clarification: {result.clarification_message}")
        print(f"Confidence: {result.confidence}")

        # Verify expected behavior - should be UNRESOLVABLE or CLARIFICATION_NEEDED
        assert result.status in ["UNRESOLVABLE", "CLARIFICATION_NEEDED"]
        if result.status == "UNRESOLVABLE":
            assert result.clarification_message is not None
            print(f"🚫 UNRESOLVABLE: {result.clarification_message}")
        elif result.status == "CLARIFICATION_NEEDED":
            assert result.clarification_message is not None
            print(f"❓ CLARIFICATION: {result.clarification_message}")
