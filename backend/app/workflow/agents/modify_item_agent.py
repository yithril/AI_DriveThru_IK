"""
Modify Item Agent

Parses user modification requests and identifies target items with modifications.
Returns structured data for deterministic validation and application.

This agent does NOT modify the database - it only parses and identifies.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from app.workflow.response.modify_item_response import ModifyItemResult
from app.workflow.prompts.modify_item_prompts import get_modify_item_prompt
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


async def modify_item_agent(
    user_input: str,
    current_order: List[Dict[str, Any]],
    conversation_history: Optional[ConversationHistory] = None,
    command_history: Optional[ConversationHistory] = None
) -> ModifyItemResult:
    """
    Parse user modification request and identify target item with modifications.
    
    This agent:
    1. Analyzes user input for modification intent
    2. Identifies target item using order + conversation context
    3. Determines modification type and details
    4. Returns structured data for validation/application
    
    Does NOT:
    - Modify the database
    - Validate against menu constraints
    - Apply modifications
    
    Args:
        user_input: Raw user input text
        current_order: Current order items with IDs, names, quantities, etc.
        conversation_history: Recent conversation turns (defaults to empty list)
        command_history: Recent commands executed (defaults to empty list)
        
    Returns:
        ModifyItemResult with parsed modification details
    """
    try:
        # Use empty ConversationHistory if not provided
        if conversation_history is None:
            conversation_history = ConversationHistory(session_id="")
        if command_history is None:
            command_history = ConversationHistory(session_id="")
        
        # Get formatted prompt
        prompt = get_modify_item_prompt(
            user_input=user_input,
            current_order=current_order,
            conversation_history=conversation_history,
            command_history=command_history
        )
        
        # Set up LangChain with function calling for reliable structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1
        ).with_structured_output(ModifyItemResult, method="function_calling")
        
        # Execute LLM call
        result = await llm.ainvoke(prompt)
        
        logger.info(f"Modify item parsed: {len(result.modifications)} modifications (confidence: {result.confidence})")
        if result.requires_split:
            logger.info(f"Item splitting required: {result.remaining_unchanged} unchanged")
        if result.clarification_needed:
            logger.info(f"Clarification needed: {result.clarification_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Modify item parsing failed: {e}", exc_info=True)
        
        # Fallback to low confidence failure
        return ModifyItemResult(
            success=False,
            confidence=0.1,
            target_item_id=None,
            target_confidence=0.0,
            target_reasoning=f"Parsing failed: {str(e)}",
            modification_type=None,
            clarification_needed=True,
            clarification_message="I didn't understand that modification request. Could you please rephrase?",
            validation_errors=[f"Agent parsing error: {str(e)}"],
            reasoning=f"Modification parsing failed due to error: {str(e)}"
        )
