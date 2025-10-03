"""
Remove Item Agent

LLM-based agent for parsing user requests to remove items from their order.
Handles various ways customers might express removal requests.
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config.settings import settings
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class RemoveItemResult(BaseModel):
    """Result from the remove item agent"""
    
    success: bool = Field(..., description="Whether the removal request was successfully parsed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the removal request (0.0 to 1.0)")
    
    # What to remove
    target_item_names: List[str] = Field(default_factory=list, description="Names of items to remove (e.g., ['burger', 'fries'])")
    target_item_ids: List[int] = Field(default_factory=list, description="IDs of specific OrderItems to remove")
    
    # Clarification handling
    clarification_needed: bool = Field(default=False, description="Whether clarification is needed")
    clarification_message: str = Field(default="", description="Message to ask for clarification")
    clarification_options: List[str] = Field(default_factory=list, description="Available options for clarification")
    
    # Context
    context_notes: str = Field(default="", description="Notes about the parsing context")


async def remove_item_agent(
    user_input: str,
    current_order: List[Dict[str, Any]],
    conversation_history: Optional[ConversationHistory] = None,
    command_history: Optional[ConversationHistory] = None
) -> RemoveItemResult:
    """
    Parse a user's request to remove items from their order.
    
    Args:
        user_input: The user's removal request (e.g., "remove the burger")
        current_order: Current order items in PostgreSQL-like format
        conversation_history: Recent conversation turns
        command_history: Recent commands executed
        
    Returns:
        RemoveItemResult with parsed removal information
    """
    try:
        logger.info(f"Remove item agent processing: {user_input}")
        
        # Build context for the agent
        context = _build_agent_context(current_order, conversation_history, command_history)
        
        # Create the LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1  # Low temperature for consistent parsing
        )
        
        # Create structured output parser
        from langchain_core.output_parsers import PydanticOutputParser
        parser = PydanticOutputParser(pydantic_object=RemoveItemResult)
        
        # Build the system prompt
        system_prompt = _build_system_prompt(parser.get_format_instructions())
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User request: {user_input}\n\nContext:\n{context}")
        ]
        
        # Get LLM response
        response = await llm.ainvoke(messages)
        
        # Parse the response
        result = parser.parse(response.content)
        
        logger.info(f"Remove item agent result: success={result.success}, confidence={result.confidence}")
        if result.clarification_needed:
            logger.info(f"Clarification needed: {result.clarification_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Remove item agent failed: {e}", exc_info=True)
        return RemoveItemResult(
            success=False,
            confidence=0.0,
            clarification_needed=True,
            clarification_message="I'm sorry, I didn't understand your request to remove items. Could you please try again?",
            context_notes=f"Agent error: {str(e)}"
        )


def _build_agent_context(
    current_order: List[Dict[str, Any]], 
    conversation_history: Optional[ConversationHistory] = None,
    command_history: Optional[ConversationHistory] = None
) -> str:
    """Build context string for the agent"""
    
    context_parts = []
    
    # Current order context
    if current_order:
        context_parts.append("CURRENT ORDER:")
        for i, item in enumerate(current_order, 1):
            name = item.get("name", "Unknown Item")
            quantity = item.get("quantity", 1)
            size = item.get("size", "regular")
            item_id = item.get("id", "unknown")
            
            item_desc = f"  {i}. {name}"
            if quantity > 1:
                item_desc += f" (qty: {quantity})"
            if size and size != "regular":
                item_desc += f" ({size})"
            item_desc += f" [ID: {item_id}]"
            
            context_parts.append(item_desc)
    else:
        context_parts.append("CURRENT ORDER: No items")
    
    # Conversation history
    if conversation_history and not conversation_history.is_empty():
        context_parts.append("\nRECENT CONVERSATION:")
        for entry in conversation_history.get_recent_entries(3):  # Last 3 turns
            role = entry.role.value
            content = entry.content[:100]  # Truncate long content
            context_parts.append(f"  {role}: {content}")
    
    # Command history
    if command_history and not command_history.is_empty():
        context_parts.append("\nRECENT COMMANDS:")
        for entry in command_history.get_recent_entries(3):  # Last 3 commands
            action = entry.role.value
            context_parts.append(f"  - {action}")
    
    return "\n".join(context_parts)


def _build_system_prompt(format_instructions: str) -> str:
    """Build the system prompt for the remove item agent"""
    
    return f"""You are an AI assistant for a drive-thru restaurant that helps customers remove items from their order.

Your task is to parse the customer's request to remove items and determine:
1. Which specific items they want to remove
2. Whether clarification is needed
3. The confidence level in your understanding

CUSTOMER REMOVAL REQUESTS might include:
- "remove the burger"
- "take off the fries" 
- "I don't want the large drink"
- "cancel the cheeseburger"
- "delete the burger and fries"
- "remove item 2" (referring to order position)
- "I changed my mind about the burger"

IMPORTANT RULES:
1. Look for item names in the current order that match the customer's request
2. Use the item IDs from the current order for precise identification
3. If the request is ambiguous (multiple items match), set clarification_needed=True
4. If no items match the request, set clarification_needed=True
5. Be conservative - ask for clarification when uncertain
6. Consider conversation context and recent commands

OUTPUT FORMAT:
{format_instructions}

EXAMPLES:

Customer: "remove the burger"
Current Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}]
Response: success=True, target_item_names=["burger"], target_item_ids=[1], confidence=0.9

Customer: "remove the burger"  
Current Order: [{{"id": 1, "name": "Cheeseburger", "quantity": 1}}, {{"id": 2, "name": "Hamburger", "quantity": 1}}]
Response: success=True, clarification_needed=True, clarification_message="I see you have both a Cheeseburger and a Hamburger. Which one would you like to remove?", clarification_options=["Cheeseburger", "Hamburger"]

Customer: "remove the pizza"
Current Order: [{{"id": 1, "name": "Burger", "quantity": 1}}]
Response: success=False, clarification_needed=True, clarification_message="I don't see any pizza in your current order. Did you mean to remove something else?"

Remember: Always prioritize customer clarity and provide helpful clarification options when needed."""