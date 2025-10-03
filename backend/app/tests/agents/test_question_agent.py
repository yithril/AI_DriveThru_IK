"""
Unit tests for Question Agent
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.workflow.agents.question_agent import question_agent
from app.workflow.response.question_response import QuestionResponse
from app.constants.audio_phrases import AudioPhraseType


class TestQuestionAgent:
    """Tests for question agent"""
    
    @pytest.fixture
    def mock_menu_service(self):
        """Create mock menu service"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_ingredient_service(self):
        """Create mock ingredient service"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_restaurant_service(self):
        """Create mock restaurant service"""
        mock = AsyncMock()
        
        # Mock restaurant data
        mock_restaurant = Mock()
        mock_restaurant.name = "Test Restaurant"
        mock_restaurant.description = "Great food"
        mock_restaurant.phone_number = "555-1234"
        mock_restaurant.address = "123 Main St"
        mock_restaurant.hours_of_operation = "9 AM - 9 PM"
        
        mock.get_by_id = AsyncMock(return_value=mock_restaurant)
        return mock
    
    @pytest.fixture
    def sample_order(self):
        """Sample order data"""
        return {
            "items": [
                {"name": "Burger", "quantity": 2},
                {"name": "Fries", "quantity": 1}
            ]
        }
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history"""
        return [
            {"user": "I want a burger", "ai": "Added to your order"},
            {"user": "What's in it?", "ai": "Let me check"}
        ]
    
    @pytest.mark.asyncio
    async def test_question_agent_restaurant_info_question(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service
    ):
        """Test question about restaurant information"""
        
        # Mock LLM response
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Our phone number is 555-1234.",
            confidence=0.95,
            category="restaurant_info",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What's your phone number?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service
            )
        
        # Verify result
        assert result.response_type == "statement"
        assert result.category == "restaurant_info"
        assert "555-1234" in result.response_text
        assert result.confidence > 0.9
        
        # Verify restaurant service was called
        mock_restaurant_service.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_question_agent_with_order_context(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service, sample_order
    ):
        """Test question about current order"""
        
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Your order: 2x Burger, 1x Fries",
            confidence=0.95,
            category="order",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What's in my order?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service,
                current_order=sample_order
            )
        
        # Verify result
        assert result.response_type == "statement"
        assert result.category == "order"
        assert "Burger" in result.response_text
        assert "Fries" in result.response_text
    
    @pytest.mark.asyncio
    async def test_question_agent_with_conversation_history(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service,
        sample_conversation_history
    ):
        """Test question with conversation history"""
        
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="The burger has lettuce, tomato, cheese, and beef.",
            confidence=0.9,
            category="menu",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What's in the burger?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service,
                conversation_history=sample_conversation_history
            )
        
        # Verify result
        assert result.response_type == "statement"
        assert result.category == "menu"
        assert result.confidence > 0.8
        
        # Verify prompt included conversation history
        call_args = mock_llm_instance.ainvoke.call_args[0][0]
        assert "Customer:" in call_args
        assert "I want a burger" in call_args
    
    @pytest.mark.asyncio
    async def test_question_agent_minimal_context(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service
    ):
        """Test question with minimal context (no order, no history)"""
        
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="We're open 9 AM to 9 PM daily.",
            confidence=0.95,
            category="restaurant_info",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What are your hours?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service
            )
        
        # Verify result
        assert result.response_type == "statement"
        assert result.category == "restaurant_info"
        assert "9 AM" in result.response_text or "9AM" in result.response_text
    
    @pytest.mark.asyncio
    async def test_question_agent_restaurant_not_found(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service
    ):
        """Test error handling when restaurant not found"""
        
        # Mock restaurant not found
        mock_restaurant_service.get_by_id = AsyncMock(return_value=None)
        
        result = await question_agent(
            user_input="What's your address?",
            restaurant_id=999,
            menu_service=mock_menu_service,
            ingredient_service=mock_ingredient_service,
            restaurant_service=mock_restaurant_service
        )
        
        # Verify error response
        assert result.response_type == "statement"
        assert result.phrase_type == AudioPhraseType.LLM_GENERATED
        assert result.confidence == 0.5
        assert result.category == "general"
        assert "error" in result.relevant_data
    
    @pytest.mark.asyncio
    async def test_question_agent_llm_error(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service
    ):
        """Test error handling when LLM fails"""
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What's on the menu?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service
            )
        
        # Verify error response
        assert result.response_type == "statement"
        assert result.phrase_type == AudioPhraseType.LLM_GENERATED
        assert result.confidence == 0.5
        assert "error" in result.relevant_data
    
    @pytest.mark.asyncio
    async def test_question_agent_empty_order(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service
    ):
        """Test question with empty order"""
        
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Your order is empty",
            confidence=0.95,
            category="order",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            result = await question_agent(
                user_input="What's in my order?",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service,
                current_order={"items": []}
            )
        
        # Verify prompt has empty order message
        call_args = mock_llm_instance.ainvoke.call_args[0][0]
        assert "empty" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_question_agent_prompt_includes_all_context(
        self, mock_menu_service, mock_ingredient_service, mock_restaurant_service,
        sample_order, sample_conversation_history
    ):
        """Test that prompt includes all provided context"""
        
        mock_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Test response",
            confidence=0.95,
            category="general",
            relevant_data={}
        )
        
        with patch('app.workflow.agents.question_agent.ChatOpenAI') as mock_llm_class:
            mock_llm_instance = Mock()
            mock_llm_instance.with_structured_output = Mock(return_value=mock_llm_instance)
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_llm_class.return_value = mock_llm_instance
            
            await question_agent(
                user_input="Test question",
                restaurant_id=1,
                menu_service=mock_menu_service,
                ingredient_service=mock_ingredient_service,
                restaurant_service=mock_restaurant_service,
                current_order=sample_order,
                conversation_history=sample_conversation_history
            )
            
            # Verify prompt includes all context
            prompt = mock_llm_instance.ainvoke.call_args[0][0]
            
            # Restaurant info
            assert "Test Restaurant" in prompt
            assert "555-1234" in prompt
            assert "123 Main St" in prompt
            
            # Order
            assert "Burger" in prompt
            assert "Fries" in prompt
            
            # Conversation history
            assert "Customer:" in prompt
            assert "I want a burger" in prompt
            
            # User question
            assert "Test question" in prompt

