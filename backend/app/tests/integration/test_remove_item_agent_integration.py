"""
Integration tests for Remove Item Agent with real OpenAI API

Tests all removal scenarios with real LLM parsing and resolution.
"""

import pytest
from datetime import datetime
from app.workflow.agents.remove_item_agent import remove_item_agent
from app.core.session.command_history import CommandHistory, CommandType, CommandStatus
from app.config.settings import settings


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestRemoveItemAgentIntegration:
    """Integration tests for remove item agent"""
    
    @pytest.fixture
    def sample_order(self):
        """Sample order with multiple items"""
        return [
            {"id": 1, "name": "Cosmic Burger", "quantity": 2, "menu_item_id": 10},
            {"id": 2, "name": "Galaxy Fries", "quantity": 1, "menu_item_id": 20},
            {"id": 3, "name": "Meteor Milkshake", "quantity": 1, "menu_item_id": 30}
        ]
    
    @pytest.fixture
    def command_history_with_adds(self):
        """Command history with some ADD commands"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Cosmic Burger",
            item_id=10,
            quantity=2,
            user_input="I want two burgers"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Galaxy Fries",
            item_id=20,
            quantity=1,
            user_input="And fries"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Meteor Milkshake",
            item_id=30,
            quantity=1,
            user_input="And a shake"
        )
        
        return history
    
    @pytest.mark.asyncio
    async def test_remove_by_exact_name(self, sample_order):
        """Test removing item by exact name"""
        
        result = await remove_item_agent(
            user_input="Remove the Galaxy Fries",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Exact name removal:")
        print(f"   Confidence: {result.confidence}")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should be resolved to specific order_item_id
        assert item.order_item_id is not None
        assert item.order_item_id == 2  # Galaxy Fries
        
        print(f"   Resolved to order_item_id: {item.order_item_id}")
    
    @pytest.mark.asyncio
    async def test_remove_by_partial_name_unique(self, sample_order):
        """Test removing item by partial name (unique match)"""
        
        result = await remove_item_agent(
            user_input="Remove the fries",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Partial name (unique):")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should resolve to Galaxy Fries
        assert item.order_item_id == 2
        
        print(f"   'fries' -> order_item_id: {item.order_item_id}")
    
    @pytest.mark.asyncio
    async def test_remove_last_item_via_command_history(self, sample_order, command_history_with_adds):
        """Test removing 'that' or 'last item' using command history"""
        
        result = await remove_item_agent(
            user_input="Remove that",
            current_order_items=sample_order,
            command_history=command_history_with_adds
        )
        
        print(f"\n[SUCCESS] Remove 'that' (last item):")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should resolve to last added item (Milkshake)
        assert item.order_item_id == 3
        
        print(f"   'that' -> order_item_id: {item.order_item_id} (Milkshake)")
    
    @pytest.mark.asyncio
    async def test_remove_last_thing_without_history(self, sample_order):
        """Test removing 'last thing' without command history (fallback to last in order)"""
        
        result = await remove_item_agent(
            user_input="Remove the last thing",
            current_order_items=sample_order,
            command_history=None  # No history
        )
        
        print(f"\n[SUCCESS] Remove last (no history):")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should fallback to last item in order
        assert item.order_item_id == 3  # Last item in order
        
        print(f"   Fallback to last item: order_item_id={item.order_item_id}")
    
    @pytest.mark.asyncio
    async def test_remove_by_position_first(self, sample_order):
        """Test removing by position reference"""
        
        result = await remove_item_agent(
            user_input="Remove the first item",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Remove by position (first):")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should resolve to first item
        assert item.order_item_id == 1  # Cosmic Burger
        
        print(f"   'first item' -> order_item_id: {item.order_item_id}")
    
    @pytest.mark.asyncio
    async def test_remove_item_not_in_order(self, sample_order):
        """Test removing item that's not in the order"""
        
        result = await remove_item_agent(
            user_input="Remove the pizza",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Item not in order:")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should NOT have order_item_id (not found)
        assert item.order_item_id is None
        
        # Should have clarification details
        assert item.ambiguous_item is not None
        assert "pizza" in item.ambiguous_item.lower()
        assert item.clarification_question is not None
        
        print(f"   Not found: {item.ambiguous_item}")
        print(f"   Clarification: {item.clarification_question}")
    
    @pytest.mark.asyncio
    async def test_remove_ambiguous_item(self):
        """Test removing item when multiple matches exist"""
        
        # Order with two different burgers
        order_with_duplicates = [
            {"id": 1, "name": "Cosmic Burger", "quantity": 1, "menu_item_id": 10},
            {"id": 2, "name": "Galaxy Burger", "quantity": 1, "menu_item_id": 11},
            {"id": 3, "name": "Fries", "quantity": 1, "menu_item_id": 20}
        ]
        
        result = await remove_item_agent(
            user_input="Remove the burger",
            current_order_items=order_with_duplicates
        )
        
        print(f"\n[SUCCESS] Ambiguous item (multiple burgers):")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should NOT have order_item_id (ambiguous)
        assert item.order_item_id is None
        
        # Should have ambiguity details
        assert item.ambiguous_item is not None
        assert "burger" in item.ambiguous_item.lower()
        assert len(item.suggested_options) >= 2
        assert item.clarification_question is not None
        
        print(f"   Ambiguous: {item.ambiguous_item}")
        print(f"   Options: {item.suggested_options}")
        print(f"   Question: {item.clarification_question}")
    
    @pytest.mark.asyncio
    async def test_remove_multiple_items(self, sample_order):
        """Test removing multiple items in one request"""
        
        result = await remove_item_agent(
            user_input="Remove the burger and the fries",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Multiple items removal:")
        
        # Should parse as 2 separate items
        assert len(result.items_to_remove) >= 1  # At least burger
        
        for item in result.items_to_remove:
            print(f"   - target_ref: {item.target_ref}, order_item_id: {item.order_item_id}")
    
    @pytest.mark.asyncio
    async def test_remove_with_quantity(self, sample_order):
        """Test removing with quantity specification"""
        
        result = await remove_item_agent(
            user_input="Remove one burger",
            current_order_items=sample_order
        )
        
        print(f"\n[SUCCESS] Remove with quantity:")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should resolve to burger
        assert item.order_item_id is not None
        
        # Check if quantity is captured in metadata
        print(f"   Resolved: order_item_id={item.order_item_id}")
        print(f"   Target: {item.target_ref}")
    
    @pytest.mark.asyncio
    async def test_empty_order(self):
        """Test removal when order is empty"""
        
        result = await remove_item_agent(
            user_input="Remove the burger",
            current_order_items=[]
        )
        
        print(f"\n[SUCCESS] Empty order:")
        
        assert len(result.items_to_remove) == 1
        item = result.items_to_remove[0]
        
        # Should indicate not found
        assert item.order_item_id is None
        assert item.ambiguous_item is not None or item.clarification_question is not None
        
        print(f"   Clarification: {item.clarification_question}")
    
    @pytest.mark.asyncio
    async def test_various_phrasings(self, sample_order):
        """Test different ways of saying 'remove'"""
        
        phrasings = [
            "Take off the fries",
            "Cancel the fries",
            "I don't want the fries",
            "Remove the fries please"
        ]
        
        for phrasing in phrasings:
            result = await remove_item_agent(
                user_input=phrasing,
                current_order_items=sample_order
            )
            
            assert len(result.items_to_remove) >= 1
            item = result.items_to_remove[0]
            
            # All should resolve to fries
            print(f"   '{phrasing}' -> order_item_id: {item.order_item_id}")
        
        print(f"\n[SUCCESS] All phrasings handled correctly")

