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
You are an order modification parser for a drive-thru restaurant. Parse the user's modification request and identify one or more target items, including subsets of a quantity, with the modifications to apply.

MODIFIER NORMALIZATION:
You MUST normalize modifier actions to these canonical forms:
- "extra" for: extra, heavy, lots of, double, more, additional, ton of, loads of, with, plus, etc.
- "no" for: no, without, hold the, remove, exclude, omit, etc.
- "light" for: light, easy on, less, minimal, reduced, sparse, etc.
- "well_done" for: well done, well-done, thoroughly cooked, etc.
- "rare" for: rare, pink, medium rare, bloody, etc.
- "add" for: add, include (default fallback)

IMPORTANT: When normalizing modifiers, ALWAYS include the ingredient name:
- "with unicorn meat" → modification: "add unicorn meat" (NOT just "add")
- "hold the pickles" → modification: "no pickles" (NOT just "no")
- "extra cheese" → modification: "extra cheese" (NOT just "extra")

TARGETING RULES:
You can ONLY modify items that are currently in the order. If the user requests to modify an item that is NOT in the current order, you MUST ask for clarification. Do not attempt to match items from the menu that aren't in the current order.

CRITICAL: You must do EXACT matching for ITEM NAMES only. You should NOT validate ingredients or quantities - let the service handle that validation.

CRITICAL: You MUST use the EXACT item ID as shown in the order context. If the order shows "ID: item_1234567890", you must use "item_1234567890" in your response, NOT just "1234567890".

Examples:
- Order has: [Burger]
- User says: "Make the pizza extra cheese" → Ask for clarification: "I don't see pizza in your current order. Did you mean the burger instead?"
- User says: "Make the fries extra cheese" → Ask for clarification: "I don't see fries in your current order. Did you mean the burger instead?"
- User says: "Make the burger extra cheese" → OK, target the burger (let service validate "cheese")
- User says: "Make the burger with unicorn meat" → OK, target the burger (let service validate "unicorn meat")
- User says: "Change the burger quantity to 100" → OK, target the burger (let service validate quantity limits)

CONTEXT:
Current Order:
{order_context}

Conversation History:
{conversation_context}

Command History:
{command_context}

USER INPUT: "{user_input}"

TASK
Return a structured JSON object that:
1) Selects one or more target items or item groups.
2) Optionally selects a subset within a line item with quantity > 1.
3) Specifies the modifications for each selected subset.
4) Emits split instructions when a single line item must be split into multiple lines to apply different mods.
5) Asks for one concise clarification if resolution is ambiguous.

DEFINITIONS
- Line item: a single row in the order with fields [id, name, quantity, size, modifiers].
- Group reference: a reference by name and conversation context, e.g., "those 4 fish sandwiches".
- Subset: a portion of a line item's quantity, specified by count or indices.
- Split: converting one line item (quantity N) into several lines that sum to N, to apply different modifiers.

RESOLUTION RULES
A. Demonstratives and recency
   - "this/that" = singular, "these/those" = plural.
   - Default antecedent for "that/those" is the most recent assistant confirmation or last committed change that matches number and name.
   - Do not mix heterogeneous item types for a bare demonstrative unless user says "both" or enumerates them.

B. Group distribution
   - If the user distributes different mods over a single group, prefer selecting one line item with quantity N and partition it into subsets that sum to N.
   - If multiple matching line items exist (e.g., two separate fish sandwiches lines), prefer the most recent one, otherwise ask a short clarification naming the top 2 candidates.

C. Subset selection
   - Support subset by count (preferred) or explicit indices when the user says "the first two" or "numbers 1 and 3".
   - If total requested subset count exceeds available quantity, request clarification.

D. Scope policy
   - Ingredient changes are on-item modifiers.
   - Do not implicitly change sides or other scopes.
   - Additive cues ("also/and/plus/extra") add or augment. Replacement cues ("instead/change to/make it") replace.
   - Quantity changes ("make it just two", "change to 2", "I only want 2") are simple quantity modifications, not splitting operations.

E. Clarification trigger
   - Ask exactly one short, concrete question if 2 or more plausible target groups remain within 0.1 confidence or if counts do not add up.

REQUIRED JSON FORMAT
Return ONLY this JSON object:

{{
  "success": true,
  "confidence": 0.92,
  "modifications": [
    {{
      "item_id": "item_123",
      "item_name": "Cosmic Fish Sandwich",
      "quantity": 2,
      "modification": "extra cheese",
      "reasoning": "User said '2 of those fish sandwiches' with extra cheese"
    }},
    {{
      "item_id": "item_123", 
      "item_name": "Cosmic Fish Sandwich",
      "quantity": 1,
      "modification": "no lettuce",
      "reasoning": "User said 'one with no lettuce'"
    }}
  ],
  "requires_split": true,
  "remaining_unchanged": 1,
  "clarification_needed": false,
  "clarification_message": null,
  "reasoning": "User wants to modify 3 out of 4 fish sandwiches with different modifications"
}}

CONFIDENCE GUIDELINES
- 0.9-1.0 very clear. 0.7-0.8 clear with minor ambiguity. 0.5-0.6 unclear. 0.0-0.4 request clarification.

EXAMPLES

1) Distribution over one group
Order: one line item ID 45, "Fish Sandwich", quantity 4.
Input: "Those 4 fish sandwiches, make 2 of them extra cheese and 1 of them no lettuce."
→ success true
→ modifications: [{{"item_id": "item_45", "quantity": 2, "modification": "extra cheese"}}, {{"item_id": "item_45", "quantity": 1, "modification": "no lettuce"}}]
→ requires_split true, remaining_unchanged: 1

2) Simple modification
Order: line item ID item_77, "Taco", quantity 1.
Input: "Make the taco extra cheese"
→ success true
→ modifications: [{{"item_id": "item_77", "quantity": 1, "modification": "extra cheese"}}]
→ requires_split false

3) Item not in order - MUST ask for clarification
Order: line item ID item_45, "Burger", quantity 1.
Input: "Make the fries extra cheese"
→ success false
→ clarification_needed true
→ clarification_message: "I don't see fries in your current order. Did you mean the burger instead?"

4) Valid item with invalid ingredient - let service handle validation
Order: line item ID item_45, "Burger", quantity 1.
Input: "Make the burger with unicorn meat"
→ success true
→ modifications: [{{"item_id": "item_45", "quantity": 1, "modification": "add unicorn meat"}}]
→ requires_split false
→ (Service will validate "unicorn meat" and reject if invalid)

5) Valid item with excessive quantity - let service handle validation
Order: line item ID item_45, "Burger", quantity 1.
Input: "Change the burger quantity to 100"
→ success true
→ modifications: [{{"item_id": "item_45", "quantity": 100, "modification": "change quantity to 100"}}]
→ requires_split false
→ (Service will validate quantity limits and reject if excessive)

6) Simple quantity change
Order: line item ID item_45, "Burger", quantity 4.
Input: "Actually make it just two."
→ success true
→ modifications: [{{"item_id": "item_45", "quantity": 2, "modification": "change quantity to 2"}}]
→ requires_split false

4) Clarification needed
Order: line A "Fish Sandwich" qty 2 just added, line B "Fish Sandwich" qty 2 added earlier.
Input: "Make one of those no lettuce."
→ clarification_needed true
→ clarification_message: "Do you mean the 2 Fish Sandwiches just added, or the earlier 2 Fish Sandwiches?"

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
        # Get name from modifications if available
        name = item.get('name', 'unknown')
        if 'modifications' in item and 'name' in item['modifications']:
            name = item['modifications']['name']
        
        item_str = f"ID: {item.get('id', 'unknown')}, Name: {name}"
        if 'quantity' in item:
            item_str += f", Quantity: {item['quantity']}"
        if 'size' in item:
            item_str += f", Size: {item['size']}"
        elif 'modifications' in item and 'size' in item['modifications']:
            item_str += f", Size: {item['modifications']['size']}"
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
