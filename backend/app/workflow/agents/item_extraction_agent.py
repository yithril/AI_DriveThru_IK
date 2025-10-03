"""
Item Extraction Agent

First agent in the pipeline that extracts items, quantities, modifiers, and special instructions
from user input without doing any menu resolution. Pure LLM processing with structured output.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.config.settings import settings
from app.workflow.response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.workflow.prompts.item_extraction_prompts import build_item_extraction_prompt

logger = logging.getLogger(__name__)


async def item_extraction_agent(user_input: str, context: Dict[str, Any]) -> ItemExtractionResponse:
    """
    Extract items, quantities, modifiers, and special instructions from user input.
    
    This is the first agent in the pipeline - it only does LLM processing, no tools.
    It extracts structured data that will be passed to the menu resolution agent.
    
    Args:
        user_input: The cleaned user input text
        context: Context containing conversation history, order state, etc.
        
    Returns:
        ItemExtractionResponse with extracted items and metadata
    """
    try:
        # Set up LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1
        ).with_structured_output(ItemExtractionResponse, method="function_calling")
        
        # Get context data
        conversation_history = context.get("conversation_history", [])
        order_state = context.get("order_state", {})
        restaurant_id = context.get("restaurant_id", "1")
        
        # Build the prompt
        prompt = build_item_extraction_prompt(user_input, conversation_history, order_state, restaurant_id)
        
        # Execute the extraction
        result = await llm.ainvoke(prompt)
        
        # DEBUG: Log the result
        print(f"\n[DEBUG] ITEM EXTRACTION AGENT:")
        print(f"   Success: {result.success}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Items extracted: {len(result.extracted_items)}")
        for i, item in enumerate(result.extracted_items):
            print(f"     Item {i+1}: '{item.item_name}' (qty: {item.quantity}, confidence: {item.confidence})")
        
        return result
        
    except Exception as e:
        logger.error(f"Item extraction agent failed: {e}")
        print(f"[DEBUG] Extraction agent exception: {e}")
        
        # Return error response
        return ItemExtractionResponse(
            success=False,
            confidence=0.0,
            extracted_items=[
                ExtractedItem(
                    item_name="unknown",
                    quantity=1,
                    confidence=0.0,
                    context_notes=f"Extraction failed: {str(e)}"
                )
            ],
            needs_clarification=True,
            clarification_questions=["I'm sorry, I had trouble understanding your request. Could you please try again?"]
        )

