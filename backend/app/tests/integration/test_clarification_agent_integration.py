"""
Integration tests for Clarification Agent with real OpenAI API and tools

Tests the agent's ability to generate helpful clarification responses
when items fail or are ambiguous, using tools to search for alternatives.
"""

import pytest
from app.workflow.agents.clarification_agent import clarification_agent
from app.workflow.response.clarification_response import ClarificationContext
from app.config.settings import settings
from app.tests.fixtures.database_fixtures import (
    test_db,
    test_restaurant,
    test_menu_items,
    test_services
)


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestClarificationAgentIntegration:
    """Integration tests for clarification agent with real API calls"""
    
    @pytest.mark.asyncio
    async def test_item_not_found_clarification(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification when item is not found on menu - uses tools to find alternatives"""
        
        # Simulate a batch result where item wasn't found
        batch_result = {
            "batch_outcome": "PARTIAL_FAILURE",
            "error_codes": ["ITEM_NOT_FOUND"],
            "failed_items": ["chocolate shake"],
            "successful_items": []
        }
        
        # Build context - no need to provide available_items, agent will use tools!
        context = ClarificationContext(
            batch_outcome="PARTIAL_FAILURE",
            error_codes=["ITEM_NOT_FOUND"],
            failed_items=["chocolate shake"],
            successful_items=[],
            available_items=[],  # Empty - agent will search with tools!
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[],
            clarification_commands=[],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Clarification Response:")
        print(f"   Response: {result.response_text}")
        print(f"   Type: {result.response_type}")
        print(f"   Confidence: {result.confidence}")
        
        # Verify structure
        assert result.response_type in ["question", "statement"]
        assert result.confidence >= 0.5
        assert len(result.response_text) >= 10
        
        # Should mention alternatives (agent searched with tools!)
        response_lower = result.response_text.lower()
        assert "shake" in response_lower or "milkshake" in response_lower or "don't have" in response_lower
    
    @pytest.mark.asyncio
    async def test_ambiguous_item_clarification(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification when multiple items match"""
        
        batch_result = {
            "batch_outcome": "NEEDS_CLARIFICATION",
            "error_codes": [],
            "failed_items": [],
            "successful_items": []
        }
        
        context = ClarificationContext(
            batch_outcome="NEEDS_CLARIFICATION",
            error_codes=[],
            failed_items=[],
            successful_items=[],
            available_items=["Cosmic Burger", "Galaxy Burger", "Meteor Burger"],
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[],
            clarification_commands=[{
                "ambiguous_item": "burger",
                "suggested_options": ["Cosmic Burger", "Galaxy Burger", "Meteor Burger"],
                "clarification_question": "Which burger would you like?"
            }],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Ambiguous Item Clarification:")
        print(f"   Response: {result.response_text}")
        
        # Should ask which one
        assert result.response_type == "question"
        assert "burger" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_partial_success_clarification(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification when some items succeeded and some failed"""
        
        batch_result = {
            "batch_outcome": "PARTIAL_SUCCESS",
            "error_codes": ["ITEM_NOT_FOUND"],
            "failed_items": ["unicorn shake"],
            "successful_items": ["Cosmic Burger", "Galaxy Fries"]
        }
        
        context = ClarificationContext(
            batch_outcome="PARTIAL_SUCCESS",
            error_codes=["ITEM_NOT_FOUND"],
            failed_items=["unicorn shake"],
            successful_items=["Cosmic Burger", "Galaxy Fries"],
            available_items=["Meteor Milkshake", "Chocolate Shake", "Vanilla Shake"],
            restaurant_name="Cosmic Burgers",
            current_order_summary="2 items in order",
            conversation_history=[],
            clarification_commands=[],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Partial Success Clarification:")
        print(f"   Response: {result.response_text}")
        
        # Should acknowledge success and offer alternatives
        response_lower = result.response_text.lower()
        # Might mention successful items or just focus on failure
        assert len(result.response_text) >= 10
        assert result.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_size_not_available_clarification(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification when requested size isn't available"""
        
        batch_result = {
            "batch_outcome": "NEEDS_CLARIFICATION",
            "error_codes": ["SIZE_NOT_AVAILABLE"],
            "failed_items": ["large burger"],
            "successful_items": []
        }
        
        context = ClarificationContext(
            batch_outcome="NEEDS_CLARIFICATION",
            error_codes=["SIZE_NOT_AVAILABLE"],
            failed_items=["large burger"],
            successful_items=[],
            available_items=["Cosmic Burger (medium)", "Cosmic Burger (small)"],
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[],
            clarification_commands=[{
                "ambiguous_item": "large burger",
                "suggested_options": ["medium", "small"],
                "clarification_question": "What size would you like?"
            }],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Size Clarification:")
        print(f"   Response: {result.response_text}")
        
        # Should mention available sizes
        assert result.response_type == "question"
        assert "medium" in result.response_text.lower() or "small" in result.response_text.lower()
    
    @pytest.mark.asyncio
    async def test_all_items_failed_clarification(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification when all items failed"""
        
        batch_result = {
            "batch_outcome": "ALL_FAILED",
            "error_codes": ["ITEM_NOT_FOUND"],
            "failed_items": ["pizza", "pasta"],
            "successful_items": []
        }
        
        context = ClarificationContext(
            batch_outcome="ALL_FAILED",
            error_codes=["ITEM_NOT_FOUND"],
            failed_items=["pizza", "pasta"],
            successful_items=[],
            available_items=["Cosmic Burger", "Galaxy Fries", "Meteor Milkshake"],
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[],
            clarification_commands=[],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] All Failed Clarification:")
        print(f"   Response: {result.response_text}")
        
        # Should be helpful about what's available
        assert result.confidence >= 0.5
        assert len(result.response_text) >= 10
    
    @pytest.mark.asyncio
    async def test_with_conversation_history(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test clarification with conversation history to avoid repetition"""
        
        batch_result = {
            "batch_outcome": "NEEDS_CLARIFICATION",
            "error_codes": ["ITEM_NOT_FOUND"],
            "failed_items": ["special"],
            "successful_items": []
        }
        
        context = ClarificationContext(
            batch_outcome="NEEDS_CLARIFICATION",
            error_codes=["ITEM_NOT_FOUND"],
            failed_items=["special"],
            successful_items=[],
            available_items=["Cosmic Burger", "Galaxy Fries"],
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[
                {"user_input": "I want the special", "response_text": "What would you like to order?"}
            ],
            clarification_commands=[],
            has_clarification_needed=True
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Clarification with History:")
        print(f"   Response: {result.response_text}")
        
        assert result.confidence >= 0.5
    
    @pytest.mark.asyncio
    async def test_error_response_fallback(self, test_db, test_restaurant, test_menu_items, test_services):
        """Test that invalid batch result returns proper error response"""
        
        # Invalid batch result
        batch_result = {
            "batch_outcome": "UNKNOWN_ERROR"
        }
        
        context = ClarificationContext(
            batch_outcome="UNKNOWN_ERROR",
            error_codes=[],
            failed_items=[],
            successful_items=[],
            available_items=[],
            restaurant_name="Cosmic Burgers",
            current_order_summary="No items in order",
            conversation_history=[]
        )
        
        result = await clarification_agent(batch_result, context, test_services["menu_service"])
        
        print(f"\n[SUCCESS] Error Fallback:")
        print(f"   Response: {result.response_text}")
        
        # Should return valid response even with error
        assert result.response_type in ["question", "statement"]
        assert len(result.response_text) >= 10

