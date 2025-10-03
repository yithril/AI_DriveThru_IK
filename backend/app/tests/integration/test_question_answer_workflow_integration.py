"""
Integration tests for QuestionAnswerWorkflow using real agents and services
"""

import pytest
from unittest.mock import AsyncMock
from app.workflow.nodes.question_answer_workflow import QuestionAnswerWorkflow
from app.workflow.response.workflow_result import QuestionAnswerWorkflowResult
from app.constants.audio_phrases import AudioPhraseType
from app.config.settings import settings


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestQuestionAnswerWorkflowIntegration:
    """Integration tests for QuestionAnswerWorkflow with real agents"""
    
    @pytest.fixture
    async def sample_restaurant(self, test_db):
        """Create a sample restaurant for testing"""
        from app.models.restaurant import Restaurant
        
        restaurant = await Restaurant.create(
            name="Test Restaurant",
            phone="555-0123",
            address="123 Test St",
            hours="9AM-9PM"
        )
        return restaurant
    
    @pytest.fixture
    async def sample_menu_items(self, test_db, sample_restaurant):
        """Create sample menu items for testing"""
        from app.models.menu_item import MenuItem
        from app.models.category import Category
        from decimal import Decimal
        
        # Create category
        category = await Category.create(
            name="Burgers",
            restaurant=sample_restaurant
        )
        
        # Create menu items
        burger = await MenuItem.create(
            name="Burger",
            description="Delicious beef burger",
            price=Decimal('8.99'),
            category=category,
            restaurant=sample_restaurant,
            available_sizes=["regular", "large"],
            modifiable_ingredients=["lettuce", "tomato", "onion"],
            max_quantity=5
        )
        
        fries = await MenuItem.create(
            name="Fries",
            description="Crispy golden fries",
            price=Decimal('3.99'),
            category=category,
            restaurant=sample_restaurant,
            available_sizes=["regular", "large"],
            modifiable_ingredients=[],
            max_quantity=10
        )
        
        return [burger, fries]
    
    @pytest.fixture
    async def sample_ingredients(self, test_db, sample_restaurant):
        """Create sample ingredients for testing"""
        from app.models.ingredient import Ingredient
        
        cheese = await Ingredient.create(
            name="Cheese",
            description="American cheese",
            is_allergen=False,
            allergen_type=None,
            restaurant=sample_restaurant
        )
        
        gluten = await Ingredient.create(
            name="Gluten",
            description="Contains gluten",
            is_allergen=True,
            allergen_type="gluten",
            restaurant=sample_restaurant
        )
        
        return [cheese, gluten]
    
    @pytest.fixture
    async def mock_services(sample_restaurant, sample_menu_items, sample_ingredients):
        """Create mock services with real data"""
        from app.services.menu_service import MenuService
        from app.services.ingredient_service import IngredientService
        from app.services.restaurant_service import RestaurantService
        
        # Create real service instances
        menu_service = MenuService()
        ingredient_service = IngredientService()
        restaurant_service = RestaurantService()
        
        return menu_service, ingredient_service, restaurant_service
    
    @pytest.fixture
    def question_workflow(self, mock_services):
        """Create QuestionAnswerWorkflow instance for integration testing"""
        menu_service, ingredient_service, restaurant_service = mock_services
        return QuestionAnswerWorkflow(
            restaurant_id=1,  # Will be set by sample_restaurant fixture
            menu_service=menu_service,
            ingredient_service=ingredient_service,
            restaurant_service=restaurant_service
        )
    
    @pytest.mark.asyncio
    async def test_menu_item_question_with_real_agent(
        self, 
        question_workflow,
        sample_menu_items,
        sample_restaurant
    ):
        """Test asking about menu items with real agent"""
        # Update restaurant_id in workflow
        question_workflow.restaurant_id = sample_restaurant.id
        
        user_input = "How much is a burger?"
        result = await question_workflow.execute(user_input=user_input)
        
        assert isinstance(result, QuestionAnswerWorkflowResult)
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
        assert "burger" in result.message.lower() or "8.99" in result.message
        assert result.data["question_category"] == "menu"  # Should now correctly classify as menu
        assert result.confidence_score is not None
    
    @pytest.mark.asyncio
    async def test_restaurant_info_question_with_real_agent(
        self,
        question_workflow,
        sample_restaurant
    ):
        """Test asking about restaurant information with real agent"""
        question_workflow.restaurant_id = sample_restaurant.id
        
        user_input = "What are your hours?"
        result = await question_workflow.execute(user_input=user_input)
        
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        assert result.audio_phrase_type == AudioPhraseType.RESTAURANT_INFO
        assert "hours" in result.message.lower() or "9AM" in result.message or "9PM" in result.message
        assert result.data["question_category"] == "restaurant_info"
    
    @pytest.mark.asyncio
    async def test_ingredient_question_with_real_agent(
        self,
        question_workflow,
        sample_ingredients,
        sample_restaurant
    ):
        """Test asking about ingredients with real agent"""
        question_workflow.restaurant_id = sample_restaurant.id
        
        user_input = "Do you have gluten-free options?"
        result = await question_workflow.execute(user_input=user_input)
        
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
        # The agent should mention gluten or allergen information
        assert result.data["question_category"] in ["menu", "general"]
    
    @pytest.mark.asyncio
    async def test_general_question_with_real_agent(
        self,
        question_workflow,
        sample_restaurant
    ):
        """Test asking general/unclear questions with real agent"""
        question_workflow.restaurant_id = sample_restaurant.id
        
        user_input = "What's the weather like?"
        result = await question_workflow.execute(user_input=user_input)
        
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        # Should map to QUESTION_NOT_FOUND or CUSTOM_RESPONSE
        assert result.audio_phrase_type in [
            AudioPhraseType.QUESTION_NOT_FOUND, 
            AudioPhraseType.CUSTOM_RESPONSE
        ]
        assert result.data["question_category"] == "general"
    
    @pytest.mark.asyncio
    async def test_conversation_context_with_real_agent(
        self,
        question_workflow,
        sample_menu_items,
        sample_restaurant
    ):
        """Test question with conversation history using real agent"""
        question_workflow.restaurant_id = sample_restaurant.id
        
        conversation_history = [
            {"role": "customer", "content": "Do you have burgers?"},
            {"role": "assistant", "content": "Yes, we have burgers on our menu."}
        ]
        
        user_input = "What sizes do they come in?"
        result = await question_workflow.execute(
            user_input=user_input,
            conversation_history=conversation_history
        )
        
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
        # Should mention sizes or burger information
        assert result.data["question_category"] in ["menu", "general"]
    
    @pytest.mark.asyncio
    async def test_order_context_question_with_real_agent(
        self,
        question_workflow,
        sample_restaurant
    ):
        """Test question with order context using real agent"""
        question_workflow.restaurant_id = sample_restaurant.id
        
        current_order = {
            "items": [
                {"name": "Burger", "quantity": 1},
                {"name": "Fries", "quantity": 1}
            ],
            "total": 12.98
        }
        
        user_input = "What's in my order?"
        result = await question_workflow.execute(
            user_input=user_input,
            current_order=current_order
        )
        
        assert result.success is True
        assert result.workflow_type.value == "question_answer"
        assert result.audio_phrase_type == AudioPhraseType.QUESTION_ANSWERED
        # Should reference the order items
        assert result.data["question_category"] == "order"
