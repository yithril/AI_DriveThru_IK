"""
Unit tests for QuestionAnswerWorkflow
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.workflow.nodes.question_answer_workflow import QuestionAnswerWorkflow
from app.workflow.response.question_response import QuestionResponse
from app.workflow.response.workflow_result import QuestionAnswerWorkflowResult
from app.constants.audio_phrases import AudioPhraseType


class TestQuestionAnswerWorkflow:
    """Test cases for QuestionAnswerWorkflow"""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing"""
        menu_service = AsyncMock()
        ingredient_service = AsyncMock()
        restaurant_service = AsyncMock()
        
        # Mock restaurant data
        restaurant_service.get_by_id.return_value = {
            "id": 1,
            "name": "Test Restaurant",
            "phone": "555-0123",
            "address": "123 Test St",
            "hours": "9AM-9PM"
        }
        
        return menu_service, ingredient_service, restaurant_service
    
    @pytest.fixture
    def question_workflow(self, mock_services):
        """Create QuestionAnswerWorkflow instance for testing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        return QuestionAnswerWorkflow(
            restaurant_id=1,
            menu_service=menu_service,
            ingredient_service=ingredient_service,
            restaurant_service=restaurant_service
        )
    
    @pytest.mark.asyncio
    async def test_execute_menu_question_success(self, question_workflow, mock_services):
        """Test successful menu question processing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        # Mock agent response for menu question
        mock_agent_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Our burger is $8.99 and comes with fries.",
            confidence=0.9,
            category="menu",
            relevant_data={"item": "burger", "price": 8.99}
        )
        
        # Mock the question_agent function
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                return mock_agent_response
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute("How much is a burger?")
        
        assert isinstance(result, QuestionAnswerWorkflowResult)
        assert result.success is True
        assert result.message == "Our burger is $8.99 and comes with fries."
        assert result.data["question_category"] == "menu"
        assert result.confidence_score == 0.9
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
        assert result.data["relevant_data"]["item"] == "burger"
    
    @pytest.mark.asyncio
    async def test_execute_restaurant_info_question(self, question_workflow, mock_services):
        """Test restaurant info question processing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        # Mock agent response for restaurant info
        mock_agent_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="We're open 9AM to 9PM daily.",
            confidence=0.95,
            category="restaurant_info",
            relevant_data={"hours": "9AM-9PM"}
        )
        
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                return mock_agent_response
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute("What are your hours?")
        
        assert result.success is True
        assert result.message == "We're open 9AM to 9PM daily."
        assert result.data["question_category"] == "restaurant_info"
        assert result.audio_phrase_type == AudioPhraseType.RESTAURANT_INFO
    
    @pytest.mark.asyncio
    async def test_execute_order_question(self, question_workflow, mock_services):
        """Test order-related question processing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        # Mock agent response for order question
        mock_agent_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="You currently have a burger and fries in your order.",
            confidence=0.85,
            category="order",
            relevant_data={"order_items": ["burger", "fries"]}
        )
        
        current_order = {"items": [{"name": "burger"}, {"name": "fries"}]}
        
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                return mock_agent_response
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute(
                "What's in my order?", 
                current_order=current_order
            )
        
        assert result.success is True
        assert result.message == "You currently have a burger and fries in your order."
        assert result.data["question_category"] == "order"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
    
    @pytest.mark.asyncio
    async def test_execute_general_question(self, question_workflow, mock_services):
        """Test general/unclear question processing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        # Mock agent response for general question
        mock_agent_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="I'm not sure about that. Can you ask me about our menu or hours?",
            confidence=0.6,
            category="general",
            relevant_data={}
        )
        
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                return mock_agent_response
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute("What's the meaning of life?")
        
        assert result.success is True
        assert "I'm not sure about that" in result.message
        assert result.data["question_category"] == "general"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_execute_agent_exception(self, question_workflow, mock_services):
        """Test handling of agent exceptions"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                raise Exception("Agent failed")
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute("Test question")
        
        assert result.success is False
        assert "I'm sorry, I couldn't process your question" in result.message
        assert result.error == "Agent failed"
        assert result.audio_phrase_type == AudioPhraseType.SYSTEM_ERROR_RETRY
    
    @pytest.mark.asyncio
    async def test_execute_with_conversation_history(self, question_workflow, mock_services):
        """Test question processing with conversation history"""
        menu_service, ingredient_service, restaurant_service = mock_services
        
        mock_agent_response = QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="Yes, our burger has cheese.",
            confidence=0.9,
            category="menu",
            relevant_data={}
        )
        
        conversation_history = [
            {"role": "customer", "content": "Do you have burgers?"},
            {"role": "assistant", "content": "Yes, we have burgers."}
        ]
        
        with pytest.MonkeyPatch().context() as m:
            async def mock_question_agent(*args, **kwargs):
                return mock_agent_response
            m.setattr("app.workflow.nodes.question_answer_workflow.question_agent", mock_question_agent)
            
            result = await question_workflow.execute(
                "Does it have cheese?",
                conversation_history=conversation_history
            )
        
        assert result.success is True
        assert "burger has cheese" in result.message
    
    def test_map_category_to_audio_phrase(self, question_workflow):
        """Test category to audio phrase mapping"""
        # Test restaurant_info category
        phrase_type = question_workflow._map_category_to_audio_phrase("restaurant_info")
        assert phrase_type == AudioPhraseType.RESTAURANT_INFO
        
        # Test menu category
        phrase_type = question_workflow._map_category_to_audio_phrase("menu")
        assert phrase_type == AudioPhraseType.QUESTION_ANSWERED
        
        # Test order category
        phrase_type = question_workflow._map_category_to_audio_phrase("order")
        assert phrase_type == AudioPhraseType.QUESTION_ANSWERED
        
        # Test general category
        phrase_type = question_workflow._map_category_to_audio_phrase("general")
        assert phrase_type == AudioPhraseType.QUESTION_NOT_FOUND
        
        # Test unknown category
        phrase_type = question_workflow._map_category_to_audio_phrase("unknown")
        assert phrase_type == AudioPhraseType.CUSTOM_RESPONSE
