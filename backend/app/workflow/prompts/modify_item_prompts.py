"""
Prompts for Modify Item Agent

Handles parsing user modification requests and identifying target items.
"""

from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from app.dto.conversation_dto import ConversationHistory


def get_modify_item_prompt(
    user_input: str,
    current_order: List[Dict[str, Any]],
    conversation_history: ConversationHistory,
    command_history: ConversationHistory
) -> str:
    """
    Build the prompt for LLM item modification parsing
    
    Args:
        user_input: User's modification request
        current_order: Current order items with details
        conversation_history: Recent conversation turns
        command_history: Recent commands executed
        
    Returns:
        Formatted prompt string ready for LangChain
    """
    
    # Format order items for context
    order_context = _format_order_context(current_order)
    
    # Format conversation history
    conversation_context = _format_conversation_context(conversation_history)
    
    # Format command history
    command_context = _format_command_context(command_history)
    
    template = """
You are an order modification parser for a drive-thru restaurant. Parse the user's modification request and identify the target item.

CONTEXT:
Current Order: {order_context}
Conversation History: {conversation_context}
Command History: {command_context}

USER INPUT: "{user_input}"

TASK: Parse this modification request and return structured JSON.

REQUIRED JSON FORMAT:
{{
  "success": true,
  "confidence": 0.95,
  "target_item_id": 123,
  "target_confidence": 0.9,
  "target_reasoning": "Last added item was burger",
  "modification_type": "quantity",
  "new_quantity": 2,
  "new_size": null,
  "ingredient_modifications": [],
  "clarification_needed": false,
  "clarification_message": null,
  "additional_cost": 0.00,
  "validation_errors": [],
  "reasoning": "User wants to change quantity to 2"
}}

MODIFICATION TYPES:
- "quantity": Change item quantity (e.g., "make it two", "change to 3")
- "size": Change item size (e.g., "make it large", "change to small")
- "ingredient": Modify ingredients (e.g., "no pickles", "extra cheese")
- "multiple": Multiple modifications in one request

TARGET IDENTIFICATION RULES:
1. **Explicit references**: "the burger", "my fries", "that drink" → match by name/type
2. **Last item**: "make it two", "change that" → use most recent ADD_ITEM command
3. **Positional**: "the first one", "last item" → use order position
4. **Conversation context**: Use recent conversation to resolve "it", "that"

EXAMPLES:

Input: "Make it two"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}]
Last Command: ADD_ITEM(Burger)
→ {{"target_item_id": 1, "target_confidence": 0.95, "modification_type": "quantity", "new_quantity": 2}}

Input: "No pickles on the burger"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}]
→ {{"target_item_id": 1, "target_confidence": 0.9, "modification_type": "ingredient", "ingredient_modifications": ["No pickles"]}}

Input: "Make the fries large"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}]
→ {{"target_item_id": 2, "target_confidence": 0.95, "modification_type": "size", "new_size": "large"}}

Input: "Change that to medium"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}]
Last Command: ADD_ITEM(Fries)
→ {{"target_item_id": 2, "target_confidence": 0.9, "modification_type": "size", "new_size": "medium"}}

Input: "Extra cheese and no pickles"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}]
→ {{"target_item_id": 1, "target_confidence": 0.95, "modification_type": "multiple", "ingredient_modifications": ["Extra cheese", "No pickles"]}}

AMBIGUOUS CASES - REQUEST CLARIFICATION:

Input: "Make it large"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}, {{"id": 3, "name": "Drink", "quantity": 1}}]
→ {{"target_item_id": null, "target_confidence": 0.2, "clarification_needed": true, "clarification_message": "Which item would you like to make large?"}}

Input: "Change that"
Order: [{{"id": 1, "name": "Burger", "quantity": 1}}, {{"id": 2, "name": "Fries", "quantity": 1}}]
→ {{"target_item_id": null, "target_confidence": 0.1, "clarification_needed": true, "clarification_message": "Which item would you like to change?"}}

INGREDIENT MODIFICATION EXAMPLES:
- "No pickles" → ["No pickles"]
- "Hold the mayo" → ["No mayo"]
- "Extra cheese" → ["Extra cheese"]
- "Add bacon" → ["Extra bacon"]
- "No pickles, extra cheese" → ["No pickles", "Extra cheese"]
- "Make it spicy" → ["Spicy"]
- "Well done" → ["Well done"]

SIZE EXAMPLES:
- "Make it large" → "large"
- "Change to small" → "small"
- "Medium size" → "medium"
- "Extra large" → "extra_large"

QUANTITY EXAMPLES:
- "Make it two" → 2
- "Change to three" → 3
- "I want four" → 4
- "Double it" → multiply current quantity by 2

CONFIDENCE SCORING:
- 0.9-1.0: Very clear request with obvious target
- 0.7-0.8: Clear request with some ambiguity
- 0.5-0.6: Somewhat unclear, needs context
- 0.0-0.4: Very unclear, should request clarification

Return ONLY the JSON response. Do not include any other text.
"""
    
    # Create PromptTemplate with input variables
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["user_input", "order_context", "conversation_context", "command_context"]
    )
    
    # Format the template with actual values
    return prompt_template.format(
        user_input=user_input,
        order_context=order_context,
        conversation_context=conversation_context,
        command_context=command_context
    )


def _format_order_context(current_order: List[Dict[str, Any]]) -> str:
    """Format current order for context"""
    if not current_order:
        return "No items in order"
    
    items = []
    for item in current_order:
        item_str = f"ID: {item.get('id', 'unknown')}, Name: {item.get('name', 'unknown')}"
        if 'quantity' in item:
            item_str += f", Quantity: {item['quantity']}"
        if 'size' in item:
            item_str += f", Size: {item['size']}"
        if 'special_instructions' in item and item['special_instructions']:
            item_str += f", Instructions: {item['special_instructions']}"
        items.append(item_str)
    
    return "\n".join(items)


def _format_conversation_context(conversation_history: ConversationHistory) -> str:
    """Format conversation history for context"""
    if conversation_history.is_empty():
        return "No conversation history"
    
    # Get last 3 conversation turns
    recent_history = conversation_history.get_recent_entries(3)
    
    turns = []
    for entry in recent_history:
        turn_str = f"{entry.role.value}: {entry.content}"
        turns.append(turn_str)
    
    return "\n\n".join(turns)


def _format_command_context(command_history: ConversationHistory) -> str:
    """Format command history for context"""
    if command_history.is_empty():
        return "No command history"
    
    # Get last 5 commands
    recent_commands = command_history.get_recent_entries(5)
    
    commands = []
    for entry in recent_commands:
        # For now, just show the content since command history is the same as conversation history
        cmd_text = f"{entry.role.value}: {entry.content}"
        commands.append(cmd_text)
    
    return "\n".join(commands)
