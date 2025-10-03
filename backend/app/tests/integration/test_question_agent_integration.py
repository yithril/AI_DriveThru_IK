"""
Integration tests for Question Agent with real OpenAI API and database

These tests use:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- In-memory SQLite database with test data
- Real service instances (MenuService, RestaurantService, etc.)
"""

import pytest
from app.workflow.agents.question_agent import question_agent
from app.tests.fixtures.database_fixtures import (
    test_db,
    test_restaurant,
    test_categories,
    test_ingredients,
    test_menu_items,
    test_services
)
from app.config.settings import settings


# Skip all tests in this file if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestQuestionAgentIntegration:
    """Integration tests for question agent with real API calls"""
    
    @pytest.mark.asyncio
    async def test_restaurant_info_question_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call for restaurant information question"""
        
        result = await question_agent(
            user_input="What's your phone number?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        # Verify response structure
        assert result.response_type in ["question", "statement"]
        assert result.response_text is not None
        assert len(result.response_text) >= 10
        assert result.confidence >= 0.5
        assert result.category in ["menu", "order", "restaurant_info", "general"]
        
        # Verify it actually has the phone number in response
        assert "555-COSMIC" in result.response_text or "COSMIC" in result.response_text
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Category: {result.category}")
    
    @pytest.mark.asyncio
    async def test_restaurant_hours_question_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call for restaurant hours question"""
        
        result = await question_agent(
            user_input="What are your hours?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        # Verify response
        assert result.response_type == "statement"
        assert result.confidence >= 0.7
        assert result.category == "restaurant_info"
        
        # Should mention hours
        response_lower = result.response_text.lower()
        assert "10" in response_lower or "am" in response_lower or "pm" in response_lower
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
    
    @pytest.mark.asyncio
    async def test_order_question_with_real_order_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call with order context"""
        
        current_order = {
            "items": [
                {"name": "Cosmic Burger", "quantity": 2},
                {"name": "Galaxy Fries", "quantity": 1}
            ]
        }
        
        result = await question_agent(
            user_input="What's in my order?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"],
            current_order=current_order
        )
        
        # Verify response mentions the items
        assert result.response_type == "statement"
        assert result.category == "order"
        
        response_lower = result.response_text.lower()
        assert "burger" in response_lower or "cosmic" in response_lower
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
    
    @pytest.mark.asyncio
    async def test_menu_item_question_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call asking about menu items"""
        
        result = await question_agent(
            user_input="Do you have burgers?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        # Verify response
        assert result.response_type == "statement"
        assert result.confidence >= 0.5
        # Could be menu or general category
        assert result.category in ["menu", "general", "restaurant_info"]
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
        print(f"   Category: {result.category}")
    
    @pytest.mark.asyncio
    async def test_conversation_history_context_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call with conversation history"""
        
        conversation_history = [
            {"user": "I'd like a burger", "ai": "Added Cosmic Burger to your order"},
            {"user": "How much is it?", "ai": "The Cosmic Burger is $12.99"}
        ]
        
        result = await question_agent(
            user_input="Do you have any specials?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"],
            conversation_history=conversation_history
        )
        
        # Verify response
        assert result.response_type == "statement"
        assert result.confidence >= 0.5
        assert len(result.response_text) >= 10
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
    
    @pytest.mark.asyncio
    async def test_allergen_question_real_api(
        self, test_db, test_restaurant, test_menu_items, test_ingredients, test_services
    ):
        """Test real API call asking about allergens"""
        
        result = await question_agent(
            user_input="Do you have anything with peanuts?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        # Verify response structure
        assert result.response_type in ["question", "statement"]
        assert result.confidence >= 0.5
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
        print(f"   Category: {result.category}")
    
    @pytest.mark.asyncio
    async def test_general_question_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test real API call with general question"""
        
        result = await question_agent(
            user_input="Where are you located?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        # Verify response has address
        assert result.response_type == "statement"
        assert result.category == "restaurant_info"
        
        response_lower = result.response_text.lower()
        assert "galaxy" in response_lower or "space city" in response_lower or "123" in response_lower
        
        print(f"\n[SUCCESS] Real API Response: {result.response_text}")
    
    @pytest.mark.asyncio
    async def test_multiple_questions_same_session_real_api(
        self, test_db, test_restaurant, test_menu_items, test_services
    ):
        """Test multiple real API calls in sequence (simulating conversation)"""
        
        # First question
        result1 = await question_agent(
            user_input="What's your name?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"]
        )
        
        assert "Cosmic Burgers" in result1.response_text or "cosmic" in result1.response_text.lower()
        print(f"\n[SUCCESS] Question 1: {result1.response_text}")
        
        # Second question with conversation history
        conversation = [
            {"user": "What's your name?", "ai": result1.response_text}
        ]
        
        result2 = await question_agent(
            user_input="What time do you close?",
            restaurant_id=test_services["restaurant_id"],
            menu_service=test_services["menu_service"],
            ingredient_service=test_services["ingredient_service"],
            restaurant_service=test_services["restaurant_service"],
            conversation_history=conversation
        )
        
        assert result2.confidence >= 0.5
        print(f"[SUCCESS] Question 2: {result2.response_text}")

