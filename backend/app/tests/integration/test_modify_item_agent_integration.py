"""
Integration tests for Modify Item Agent with real OpenAI API

These tests use:
- Real OpenAI API calls (requires OPENAI_API_KEY)
- No database needed (pure LLM parsing)
- Tests target identification and modification parsing
"""

import pytest
from app.workflow.agents.modify_item_agent import modify_item_agent
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory, ConversationRole


# Skip all tests if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)


class TestModifyItemAgentIntegration:
    """Integration tests for modify item agent with real API calls"""
    
    @pytest.fixture
    def sample_order(self):
        """Sample order with multiple items"""
        return [
            {"id": 1, "name": "Burger", "quantity": 1, "size": "regular"},
            {"id": 2, "name": "Fries", "quantity": 1, "size": "medium"},
            {"id": 3, "name": "Coke", "quantity": 1, "size": "large"}
        ]
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history"""
        history = ConversationHistory(session_id="test_session")
        history.add_entry(ConversationRole.USER, "I want a burger")
        history.add_entry(ConversationRole.ASSISTANT, "Added burger to your order")
        history.add_entry(ConversationRole.USER, "And some fries")
        history.add_entry(ConversationRole.ASSISTANT, "Added fries to your order")
        history.add_entry(ConversationRole.USER, "Make it two")
        history.add_entry(ConversationRole.ASSISTANT, "Updated burger quantity to 2")
        return history
    
    @pytest.fixture
    def sample_command_history(self):
        """Sample command history"""
        return [
            {"command_type": "ADD_ITEM", "item_name": "Burger", "quantity": 1, "status": "SUCCESS"},
            {"command_type": "ADD_ITEM", "item_name": "Fries", "quantity": 1, "status": "SUCCESS"},
            {"command_type": "MODIFY_ITEM", "item_name": "Burger", "quantity": 2, "status": "SUCCESS"}
        ]
    
    @pytest.mark.asyncio
    async def test_quantity_modification_with_last_item(self, sample_order, sample_conversation_history, sample_command_history):
        """Test quantity modification using last item context"""
        
        result = await modify_item_agent(
            user_input="Make it three",
            current_order=sample_order,
            conversation_history=sample_conversation_history,
            command_history=sample_command_history
        )
        
        print(f"\n[QUANTITY] 'Make it three' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   New quantity: {result.new_quantity}")
        print(f"   Reasoning: {result.target_reasoning}")
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert result.modification_type == "quantity"
        assert result.new_quantity == 3
        assert result.target_item_id is not None
        assert result.target_confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_quantity_modification_with_explicit_item(self, sample_order):
        """Test quantity modification with explicit item reference"""
        
        result = await modify_item_agent(
            user_input="Make the burger two",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[QUANTITY EXPLICIT] 'Make the burger two' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   New quantity: {result.new_quantity}")
        
        assert result.success is True
        assert result.confidence >= 0.8
        assert result.modification_type == "quantity"
        assert result.new_quantity == 2
        assert result.target_item_id == 1  # Burger ID
        assert result.target_confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_size_modification(self, sample_order):
        """Test size modification"""
        
        result = await modify_item_agent(
            user_input="Make the fries large",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[SIZE] 'Make the fries large' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   New size: {result.new_size}")
        
        assert result.success is True
        assert result.confidence >= 0.8
        assert result.modification_type == "size"
        assert result.new_size == "large"
        assert result.target_item_id == 2  # Fries ID
        assert result.target_confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_ingredient_modification_single(self, sample_order):
        """Test single ingredient modification"""
        
        result = await modify_item_agent(
            user_input="No pickles on the burger",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[INGREDIENT SINGLE] 'No pickles on the burger' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   Modifications: {result.ingredient_modifications}")
        
        assert result.success is True
        assert result.confidence >= 0.8
        assert result.modification_type == "ingredient"
        assert "No pickles" in result.ingredient_modifications
        assert result.target_item_id == 1  # Burger ID
        assert result.target_confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_ingredient_modification_multiple(self, sample_order):
        """Test multiple ingredient modifications"""
        
        result = await modify_item_agent(
            user_input="Extra cheese and no pickles",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[INGREDIENT MULTIPLE] 'Extra cheese and no pickles' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   Modifications: {result.ingredient_modifications}")
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert result.modification_type in ["ingredient", "multiple"]
        assert len(result.ingredient_modifications) >= 2
        assert any("cheese" in mod.lower() for mod in result.ingredient_modifications)
        assert any("pickles" in mod.lower() for mod in result.ingredient_modifications)
    
    @pytest.mark.asyncio
    async def test_ambiguous_modification_needs_clarification(self, sample_order):
        """Test ambiguous modification that needs clarification"""
        
        result = await modify_item_agent(
            user_input="Make it large",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[AMBIGUOUS] 'Make it large' -> clarification needed: {result.clarification_needed}")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   Clarification: {result.clarification_message}")
        
        # Should need clarification due to multiple items
        assert result.clarification_needed is True
        assert result.target_confidence < 0.5
        assert result.clarification_message is not None
        assert "which" in result.clarification_message.lower()
    
    @pytest.mark.asyncio
    async def test_context_resolution_with_conversation(self, sample_order, sample_conversation_history):
        """Test target resolution using conversation context"""
        
        result = await modify_item_agent(
            user_input="Change that to small",
            current_order=sample_order,
            conversation_history=sample_conversation_history,
            command_history=[]
        )
        
        print(f"\n[CONTEXT] 'Change that to small' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   Reasoning: {result.target_reasoning}")
        
        assert result.success is True
        assert result.confidence >= 0.6
        assert result.modification_type == "size"
        assert result.new_size == "small"
        assert result.target_item_id is not None
        assert result.target_confidence >= 0.6
    
    @pytest.mark.asyncio
    async def test_pronoun_resolution(self, sample_order):
        """Test pronoun resolution (it, that, this)"""
        
        result = await modify_item_agent(
            user_input="Make it two",
            current_order=[{"id": 1, "name": "Burger", "quantity": 1, "size": "regular"}],
            conversation_history=[{"user": "I want a burger", "ai": "Added burger to your order"}],
            command_history=[{"command_type": "ADD_ITEM", "item_name": "Burger", "quantity": 1, "status": "SUCCESS"}]
        )
        
        print(f"\n[PRONOUN] 'Make it two' -> {result.modification_type} (confidence: {result.confidence})")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   Reasoning: {result.target_reasoning}")
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert result.modification_type == "quantity"
        assert result.new_quantity == 2
        assert result.target_item_id == 1
        assert result.target_confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_empty_order_handling(self):
        """Test handling of modification request with empty order"""
        
        result = await modify_item_agent(
            user_input="Make it two",
            current_order=[],
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[EMPTY ORDER] 'Make it two' -> clarification needed: {result.clarification_needed}")
        print(f"   Target ID: {result.target_item_id}")
        print(f"   Clarification: {result.clarification_message}")
        
        # Should need clarification since no items exist
        assert result.clarification_needed is True
        assert result.target_item_id is None
        assert result.clarification_message is not None
    
    @pytest.mark.asyncio
    async def test_complex_modification_request(self, sample_order):
        """Test complex modification with multiple aspects"""
        
        result = await modify_item_agent(
            user_input="Make the burger large with extra cheese and no pickles",
            current_order=sample_order,
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        print(f"\n[COMPLEX] 'Make the burger large with extra cheese and no pickles' -> {result.modification_type}")
        print(f"   Target ID: {result.target_item_id} (confidence: {result.target_confidence})")
        print(f"   New size: {result.new_size}")
        print(f"   Modifications: {result.ingredient_modifications}")
        
        assert result.success is True
        assert result.confidence >= 0.7
        assert result.target_item_id == 1  # Burger ID
        assert result.new_size == "large"
        assert len(result.ingredient_modifications) >= 2
        assert any("cheese" in mod.lower() for mod in result.ingredient_modifications)
        assert any("pickles" in mod.lower() for mod in result.ingredient_modifications)
    
    @pytest.mark.asyncio
    async def test_response_model_validation(self, sample_order):
        """Test that response model validation works correctly"""
        
        result = await modify_item_agent(
            user_input="Make it two",
            current_order=[{"id": 1, "name": "Burger", "quantity": 1}],
            conversation_history=ConversationHistory(session_id="test_session"),
            command_history=[]
        )
        
        # Test model methods
        assert hasattr(result, 'is_high_confidence')
        assert hasattr(result, 'has_target')
        assert hasattr(result, 'needs_clarification')
        assert hasattr(result, 'is_actionable')
        
        print(f"\n[MODEL] Success: {result.success}")
        print(f"   High confidence: {result.is_high_confidence()}")
        print(f"   Has target: {result.has_target()}")
        print(f"   Needs clarification: {result.needs_clarification()}")
        print(f"   Actionable: {result.is_actionable()}")
        
        # Validate model structure
        assert isinstance(result.success, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.target_confidence <= 1.0
        assert result.modification_type is None or isinstance(result.modification_type, str)
