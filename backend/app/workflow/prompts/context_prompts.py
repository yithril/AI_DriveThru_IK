"""
Prompts for the context resolution agent
"""

from typing import List, Dict, Any, Optional
from app.dto.conversation_dto import ConversationHistory


def get_context_resolution_prompt(
    user_input: str,
    conversation_history: ConversationHistory,
    command_history: ConversationHistory,
    current_order: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the prompt for context resolution.
    
    Args:
        user_input: The ambiguous user input
        conversation_history: Recent conversation turns
        command_history: Recent command history
        current_order: Current order state (optional)
        
    Returns:
        Formatted prompt string
    """
    
    # Build context summary
    context_summary = _build_context_summary(
        conversation_history, command_history, current_order
    )
    
    prompt = f"""You are a context resolution agent for a drive-thru restaurant AI system.

Your job is to transform ambiguous user input into explicit, actionable text by using conversation and command history.

CONTEXT:
{context_summary}

USER INPUT: "{user_input}"

PURPOSE:
You are ONLY called when the user’s message *might* contain deixis (it/that/these), ellipsis (“one more,” “same again”), or repair markers (“actually,” “scratch that”).  
If the input is already explicit (names an item/category and optionally a quantity, with no pronouns/demonstratives), you MUST return it unchanged.

ACTIVATION CRITERIA:
- Pronouns/demonstratives: it, that, this, these, those, same, the same, that one, this one.
- Repair markers: actually, scratch that, undo that, cancel that, remove that.
- Ellipsis markers: another, one more, the usual, the same again.
- If NONE of these are present, pass the user’s text through unchanged.

TASK:
Transform ambiguous user input into explicit text *only* when deixis, ellipsis, or repairs require clarification using conversation/command history and the current order.  
If input is already clear and explicit, return it unchanged.

PRINCIPLES:
- Minimal edits, deterministic changes.
- Do not expand clear category orders like “Give me 3 wraps” or “Add 2 fries.” Leave them untouched.
- Only resolve pronouns/demonstratives/repairs when context provides a confident antecedent.
- When multiple candidates remain, ask one short clarification question.
- Never invent or over-specify items beyond what the user said.

RULES:
1. Return ONLY the JSON object below.
2. If explicit and clear, return SUCCESS with the original text unchanged (confidence ≥ 0.95).
3. Expand deixis/repairs/ellipsis using last assistant confirmation, command history, or current order.
4. If confidence < 0.8 because multiple candidates remain → CLARIFICATION_NEEDED.
5. If input is too vague (<0.3 confidence) → UNRESOLVABLE, ask user to restate.

OUTPUT FORMAT:
{{
  "status": "SUCCESS" | "CLARIFICATION_NEEDED" | "UNRESOLVABLE",
  "resolved_text": "Explicit text if SUCCESS, null otherwise",
  "clarification_message": "Clarification request if needed, null if SUCCESS",
  "confidence": 0.95,
  "rationale": "Brief explanation of decision"
}}

EXAMPLES:
- User: "Give me 3 wraps."
  → SUCCESS; resolved_text: "Give me 3 wraps." (unchanged; explicit)
- Context: Last assistant added “Veggie Nebula Wrap.”
  User: "Make it two."
  → SUCCESS; resolved_text: "Change quantity of Veggie Nebula Wrap to 2."
- Context: Last assistant added “2 Asteroid Cookies.”
  User: "Actually, take those off."
  → SUCCESS; resolved_text: "Remove the 2 Asteroid Cookies from my order."
- Context: Last assistant added “2 Cookies” and “2 Tacos.”
  User: "Take those off."
  → CLARIFICATION_NEEDED; clarification_message: "Remove the 2 Cookies or the 2 Tacos?
  """

    return prompt


def _build_context_summary(
    conversation_history: ConversationHistory,
    command_history: ConversationHistory,
    current_order: Optional[Dict[str, Any]]
) -> str:
    """Build a summary of context for the prompt"""
    summary_parts = []
    
    # Recent conversation (last 3 turns)
    if not conversation_history.is_empty():
        recent_conv = conversation_history.get_recent_entries(3)
        conv_text = "\n".join([
            f"{entry.role.value}: {entry.content}" 
            for entry in recent_conv
        ])
        summary_parts.append(f"Recent conversation:\n{conv_text}")
    
    # Current order summary
    if current_order and current_order.get('items'):
        order_items = current_order['items']
        order_text = ", ".join([
            f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}" 
            for item in order_items
        ])
        summary_parts.append(f"Current order: {order_text}")
    
    # Recent commands (last 3 commands)
    if not command_history.is_empty():
        recent_commands = command_history.get_recent_entries(3)
        cmd_text = "\n".join([
            f"{entry.role.value}: {entry.content}" 
            for entry in recent_commands
        ])
        summary_parts.append(f"Recent commands:\n{cmd_text}")
    
    return "\n\n".join(summary_parts)
