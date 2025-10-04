"""
Integration tests for Enhanced Modify Item Agent

Tests the new complex modification parsing capabilities with simplified result structure.
"""

import pytest
import json
from unittest.mock import patch
from app.workflow.prompts.modify_item_prompts import get_modify_item_prompt
from app.dto.conversation_dto import ConversationHistory, ConversationRole


class SimplifiedModifyItemResult:
    """Simplified result class for testing"""
    
    def __init__(self, success: bool, confidence: float, modifications: list, 
                 clarification_needed: bool = False, clarification_message: str = None,
                 reasoning: str = None):
        self.success = success
        self.confidence = confidence
        self.modifications = modifications  # List of modification instructions
        self.clarification_needed = clarification_needed
        self.clarification_message = clarification_message
        self.reasoning = reasoning


class TestEnhancedModifyItemAgent:
    """Test the enhanced modify item agent with complex scenarios"""
    
    @pytest.fixture
    def sample_order(self):
        """Sample order with 4 fish sandwiches"""
        return [
            {
                "id": "item_123",
                "name": "Cosmic Fish Sandwich",
                "quantity": 4,
                "size": "regular",
                "modifications": {"name": "Cosmic Fish Sandwich", "size": "regular"},
                "modifier_costs": []
            }
        ]
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history"""
        history = ConversationHistory(session_id="test_session")
        history.add_entry(ConversationRole.USER, "I'd like 4 cosmic fish sandwiches")
        history.add_entry(ConversationRole.ASSISTANT, "I've added 4 Cosmic Fish Sandwich to your order!")
        return history
    
    def test_complex_quantity_modification_real_llm(self, sample_order, sample_conversation_history):
        """Test complex modification with real LLM: 'Make 2 of those fish sandwiches extra cheese and one with no lettuce'"""
        
        # Generate the prompt
        prompt = get_modify_item_prompt(
            user_input="Make 2 of those fish sandwiches extra cheese and one with no lettuce",
            current_order=sample_order,
            conversation_history=sample_conversation_history,
            command_history=sample_conversation_history
        )
        
        print("\n" + "="*80)
        print("PROMPT GENERATED:")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Test with real LLM (this will make an actual API call)
        from langchain_openai import ChatOpenAI
        from app.config.settings import settings
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        try:
            # Make the actual LLM call
            response = llm.invoke(prompt)
            print("\n" + "="*80)
            print("LLM RESPONSE:")
            print("="*80)
            print(response.content)
            print("="*80)
            
            # Try to parse the JSON response
            try:
                parsed_result = json.loads(response.content)
                print("\n" + "="*80)
                print("PARSED RESULT:")
                print("="*80)
                print(json.dumps(parsed_result, indent=2))
                print("="*80)
                
                # Basic validation
                assert "success" in parsed_result
                assert "confidence" in parsed_result
                assert "operations" in parsed_result or "modifications" in parsed_result
                
                print("✅ JSON parsing successful!")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print("Raw response:")
                print(response.content)
                
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            pytest.fail(f"LLM call failed: {e}")
    
    def test_more_complex_scenario_real_llm(self, sample_order, sample_conversation_history):
        """Test more complex scenario: 'Make 3 of those fish sandwiches extra cheese and extra lettuce, leave one regular'"""
        
        # Generate the prompt
        prompt = get_modify_item_prompt(
            user_input="Make 3 of those fish sandwiches extra cheese and extra lettuce, leave one regular",
            current_order=sample_order,
            conversation_history=sample_conversation_history,
            command_history=sample_conversation_history
        )
        
        print("\n" + "="*80)
        print("PROMPT GENERATED (Complex Scenario):")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Test with real LLM
        from langchain_openai import ChatOpenAI
        from app.config.settings import settings
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.openai_api_key
        )
        
        try:
            # Make the actual LLM call
            response = llm.invoke(prompt)
            print("\n" + "="*80)
            print("LLM RESPONSE (Complex Scenario):")
            print("="*80)
            print(response.content)
            print("="*80)
            
            # Try to parse the JSON response
            try:
                parsed_result = json.loads(response.content)
                print("\n" + "="*80)
                print("PARSED RESULT (Complex Scenario):")
                print("="*80)
                print(json.dumps(parsed_result, indent=2))
                print("="*80)
                
                # Validation for this scenario
                assert "success" in parsed_result
                assert "confidence" in parsed_result
                assert "modifications" in parsed_result
                
                # Should have 2 modifications (3 items modified + 1 explicit regular)
                modifications = parsed_result["modifications"]
                assert len(modifications) == 2, f"Expected 2 modifications, got {len(modifications)}"
                
                # Check the first modification (3 items with extra cheese and lettuce)
                mod1 = modifications[0]
                assert mod1["item_id"] == "item_123"
                assert mod1["quantity"] == 3
                assert "extra cheese" in mod1["modification"].lower()
                assert "extra lettuce" in mod1["modification"].lower()
                
                # Check the second modification (1 item regular)
                mod2 = modifications[1]
                assert mod2["item_id"] == "item_123"
                assert mod2["quantity"] == 1
                assert "regular" in mod2["modification"].lower()
                
                # Should require split
                assert parsed_result["requires_split"] is True
                
                print("✅ Complex scenario JSON parsing successful!")
                print("✅ Validated: 3 items modified, 1 remaining unchanged")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                print("Raw response:")
                print(response.content)
                
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            pytest.fail(f"LLM call failed: {e}")
    
    def test_prompt_structure(self, sample_order, sample_conversation_history):
        """Test that the prompt structure is correct"""
        
        prompt = get_modify_item_prompt(
            user_input="Make 2 of those fish sandwiches extra cheese and one with no lettuce",
            current_order=sample_order,
            conversation_history=sample_conversation_history,
            command_history=sample_conversation_history
        )
        
        # Verify prompt contains all necessary sections
        assert "TASK" in prompt
        assert "DEFINITIONS" in prompt
        assert "RESOLUTION RULES" in prompt
        assert "REQUIRED JSON FORMAT" in prompt
        assert "EXAMPLES" in prompt
        
        # Verify JSON structure is defined
        assert '"operations"' in prompt
        assert '"requires_split"' in prompt
        assert '"split_plan"' in prompt
        
        print("✅ Prompt structure validation passed!")