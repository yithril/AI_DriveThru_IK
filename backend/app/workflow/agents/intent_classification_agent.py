"""
Intent Classification Agent

Pure intent detection - extracts what the human wants in a predictable format.
Does NOT validate against menu or state - just classifies intent.

Stateless agent that takes user input and conversation history only.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from app.constants.intent_types import IntentType
from app.workflow.response.intent_classification_response import IntentClassificationResult
from app.workflow.prompts.intent_classification_prompts import get_intent_classification_prompt
from app.config.settings import settings

logger = logging.getLogger(__name__)


async def intent_classification_agent(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    order_items: Optional[List[Dict[str, Any]]] = None
) -> IntentClassificationResult:
    """
    Classify user intent using LLM with structured JSON output.
    
    Stateless function that takes minimal context:
    - user_input: What the user just said
    - conversation_history: Recent conversation (last 3-5 turns)
    - order_items: Current items in order (for context only)
    
    Args:
        user_input: Raw user input text
        conversation_history: Optional previous conversation turns (defaults to empty list)
        order_items: Optional current order items for context (defaults to empty list)
        
    Returns:
        IntentClassificationResult with intent, confidence, and cleansed input
    """
    try:
        # Use empty lists if not provided
        conversation_history = conversation_history or []
        order_items = order_items or []
        
        # Build minimal context for the LLM
        context = {
            "user_input": user_input,
            "conversation_history": conversation_history[-5:],  # Last 5 turns max
            "order_items": order_items,
            "conversation_state": "Ordering"  # Simplified - could be made dynamic if needed
        }
        
        # Get formatted prompt
        prompt = get_intent_classification_prompt(user_input, context)
        
        # Set up LangChain with function calling for reliable structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1
        ).with_structured_output(IntentClassificationResult, method="function_calling")
        
        # Execute LLM call
        result = await llm.ainvoke(prompt)
        
        logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
        
        return result
        
    except Exception as e:
        logger.error(f"Intent classification failed: {e}", exc_info=True)
        # Fallback to low confidence UNKNOWN
        return IntentClassificationResult(
            intent=IntentType.UNKNOWN,
            confidence=0.1,
            reasoning=f"Classification failed: {str(e)}"
        )
