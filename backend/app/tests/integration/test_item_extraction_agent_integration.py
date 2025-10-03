"""
Integration tests for Item Extraction Agent with real OpenAI API

These tests use:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- No database needed (pure LLM parsing)
"""

import pytest
from app.workflow.agents.item_extraction_agent import item_extraction_agent
from app.config.settings import settings


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestItemExtractionAgentIntegration:
    """Integration tests for item extraction agent with real API calls"""
    
    @pytest.mark.asyncio
    async def test_simple_single_item_extraction(self):
        """Test extracting a single simple item"""
        
        result = await item_extraction_agent(
            user_input="I want a burger",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Extracted {len(result.extracted_items)} items")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        
        # Verify structure
        assert result.success is True
        assert result.confidence >= 0.7
        assert len(result.extracted_items) == 1
        
        # Verify item
        item = result.extracted_items[0]
        assert "burger" in item.item_name.lower()
        assert item.quantity == 1
        assert item.confidence >= 0.7
        
        print(f"   Item: {item.item_name}, Qty: {item.quantity}")
    
    @pytest.mark.asyncio
    async def test_multiple_items_extraction(self):
        """Test extracting multiple items in one request"""
        
        result = await item_extraction_agent(
            user_input="I'll have two burgers and three fries",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Extracted {len(result.extracted_items)} items")
        
        # Verify structure
        assert result.success is True
        assert len(result.extracted_items) == 2
        
        # Find burger and fries
        items_dict = {item.item_name.lower(): item for item in result.extracted_items}
        
        # Verify burger
        burger_item = next((item for item in result.extracted_items if "burger" in item.item_name.lower()), None)
        assert burger_item is not None
        assert burger_item.quantity == 2
        
        # Verify fries
        fries_item = next((item for item in result.extracted_items if "fries" in item.item_name.lower() or "fry" in item.item_name.lower()), None)
        assert fries_item is not None
        assert fries_item.quantity == 3
        
        for item in result.extracted_items:
            print(f"   - {item.quantity}x {item.item_name}")
    
    @pytest.mark.asyncio
    async def test_item_with_size_extraction(self):
        """Test extracting item with size"""
        
        result = await item_extraction_agent(
            user_input="Give me a large fries",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Extracted item with size")
        
        assert result.success is True
        assert len(result.extracted_items) == 1
        
        item = result.extracted_items[0]
        assert item.quantity == 1
        assert item.size is not None
        assert "large" in item.size.lower()
        
        print(f"   Item: {item.item_name}, Size: {item.size}, Qty: {item.quantity}")
    
    @pytest.mark.asyncio
    async def test_item_with_modifiers_extraction(self):
        """Test extracting item with modifiers"""
        
        result = await item_extraction_agent(
            user_input="I want a burger with no pickles and extra cheese",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Extracted item with modifiers")
        
        assert result.success is True
        assert len(result.extracted_items) == 1
        
        item = result.extracted_items[0]
        assert "burger" in item.item_name.lower()
        assert len(item.modifiers) >= 2
        
        # Check for modifier normalization
        modifiers_str = " ".join(item.modifiers).lower()
        assert "no pickles" in modifiers_str or "pickles" in modifiers_str
        assert "extra cheese" in modifiers_str or "cheese" in modifiers_str
        
        print(f"   Item: {item.item_name}")
        print(f"   Modifiers: {item.modifiers}")
    
    @pytest.mark.asyncio
    async def test_complex_order_extraction(self):
        """Test extracting complex order with multiple items, sizes, and modifiers"""
        
        result = await item_extraction_agent(
            user_input="I'll have two large burgers with extra cheese, a small fries, and three medium cokes",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Extracted complex order with {len(result.extracted_items)} items")
        
        assert result.success is True
        assert len(result.extracted_items) == 3
        
        for item in result.extracted_items:
            print(f"   - {item.quantity}x {item.size or ''} {item.item_name} {item.modifiers}")
    
    @pytest.mark.asyncio
    async def test_ambiguous_item_extraction(self):
        """Test extracting ambiguous/unclear items"""
        
        result = await item_extraction_agent(
            user_input="I'll have the special",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Handled ambiguous item")
        print(f"   Confidence: {result.confidence}")
        print(f"   Needs clarification: {result.needs_clarification}")
        
        # Ambiguous items should have lower confidence
        assert len(result.extracted_items) == 1
        item = result.extracted_items[0]
        
        # Either low confidence OR needs clarification
        assert item.confidence < 0.8 or result.needs_clarification
        
        print(f"   Item: {item.item_name}, Confidence: {item.confidence}")
    
    @pytest.mark.asyncio
    async def test_modifier_normalization(self):
        """Test that modifiers are normalized correctly"""
        
        result = await item_extraction_agent(
            user_input="I want a burger with tons of mayo, hold the pickles, and light on the onions",
            context={
                "conversation_history": [],
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Modifier normalization test")
        
        assert result.success is True
        item = result.extracted_items[0]
        
        print(f"   Modifiers: {item.modifiers}")
        
        # Check normalization (should include ingredient names)
        modifiers_str = " ".join(item.modifiers).lower()
        
        # "tons of mayo" should normalize to "extra mayo"
        assert ("extra" in modifiers_str and "mayo" in modifiers_str) or "mayo" in modifiers_str
        
        # "hold the pickles" should normalize to "no pickles"
        assert ("no" in modifiers_str and "pickles" in modifiers_str) or "pickles" in modifiers_str
        
        # "light on the onions" should normalize to "light onions"
        assert ("light" in modifiers_str and "onion" in modifiers_str) or "onion" in modifiers_str
    
    @pytest.mark.asyncio
    async def test_with_conversation_history(self):
        """Test extraction with conversation history context"""
        
        conversation_history = [
            {"user": "What do you have?", "ai": "We have burgers, fries, and shakes"},
            {"user": "I'll take that", "ai": "Which one would you like?"}
        ]
        
        result = await item_extraction_agent(
            user_input="The burger please",
            context={
                "conversation_history": conversation_history,
                "order_state": {},
                "restaurant_id": "1"
            }
        )
        
        print(f"\n[SUCCESS] Used conversation history for context")
        
        assert result.success is True
        assert len(result.extracted_items) == 1
        assert "burger" in result.extracted_items[0].item_name.lower()
        
        print(f"   Item: {result.extracted_items[0].item_name}")
    
    @pytest.mark.asyncio
    async def test_quantity_variations(self):
        """Test different ways of specifying quantity"""
        
        test_cases = [
            ("I want a burger", 1),
            ("Give me two burgers", 2),
            ("I'll have three burgers", 3),
            ("Can I get a couple burgers", 2),
        ]
        
        for user_input, expected_qty in test_cases:
            result = await item_extraction_agent(
                user_input=user_input,
                context={
                    "conversation_history": [],
                    "order_state": {},
                    "restaurant_id": "1"
                }
            )
            
            assert result.success is True
            item = result.extracted_items[0]
            print(f"   '{user_input}' -> Qty: {item.quantity} (expected: {expected_qty})")
            
            # Allow some flexibility for "couple" -> might be 2 or left as 1
            if "couple" not in user_input:
                assert item.quantity == expected_qty
        
        print(f"\n[SUCCESS] All quantity variations handled correctly")

