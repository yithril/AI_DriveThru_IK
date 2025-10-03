"""
Prompts for the context resolution agent
"""

from typing import List, Dict, Any, Optional


def get_context_resolution_prompt(
    user_input: str,
    conversation_history: List[Dict[str, Any]],
    command_history: List[Dict[str, Any]],
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

TASK:
Transform the ambiguous user input into explicit text that the downstream system can understand.

RULES:
1. Always return ONLY the JSON object, no extra text.
2. Use conversation, commands, and current order to resolve references.
3. Expand pronouns (e.g. "it", "that", "same thing") into explicit item names.
4. Expand vague quantities into explicit numbers where possible.
5. If input cannot be resolved with high confidence, return CLARIFICATION_NEEDED and provide a concrete, context-aware question.
6. Confidence guidelines:
   - 0.8–1.0 → SUCCESS
   - 0.3–0.7 → CLARIFICATION_NEEDED
   - <0.3 → UNRESOLVABLE (with clarification_message asking user to restate request)

EXAMPLES:
- "I'll take two" → "I'll take two veggie wraps" (if veggie wrap was recently discussed)
- "Same thing" → "I'll take the same veggie wrap" (if veggie wrap was recently ordered)
- "Make it large" → "Make the veggie wrap large" (if veggie wrap is in current order)
- "That sounds good" → "I'll take the veggie wrap" (if veggie wrap was recently discussed)

OUTPUT FORMAT:
Respond ONLY with a JSON object matching this exact structure:
{{
  "status": "SUCCESS" or "CLARIFICATION_NEEDED" or "UNRESOLVABLE",
  "resolved_text": "Explicit text if SUCCESS, null otherwise",
  "clarification_message": "Clarification request if CLARIFICATION_NEEDED or UNRESOLVABLE, null if SUCCESS",
  "confidence": 0.95,
  "rationale": "Brief explanation of your decision"
}}

STATUS RULES:
- Use "SUCCESS" when you can confidently resolve the context (confidence 0.8+)
- Use "CLARIFICATION_NEEDED" when context is ambiguous but resolvable with more info (confidence 0.3-0.7)
- Use "UNRESOLVABLE" when the input is too vague or context is insufficient (confidence <0.3)
- For UNRESOLVABLE, ask the user to restate their request more clearly

Return ONLY the JSON response. Do not include any other text."""

    return prompt


def _build_context_summary(
    conversation_history: List[Dict[str, Any]],
    command_history: List[Dict[str, Any]],
    current_order: Optional[Dict[str, Any]]
) -> str:
    """Build a summary of context for the prompt"""
    summary_parts = []
    
    # Recent conversation (last 3 turns)
    if conversation_history:
        recent_conv = conversation_history[-3:]
        conv_text = "\n".join([
            f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" 
            for turn in recent_conv
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
    if command_history:
        recent_commands = command_history[-3:]
        cmd_text = "\n".join([
            f"Command: {cmd.get('action', 'unknown')} - {cmd.get('description', '')}" 
            for cmd in recent_commands
        ])
        summary_parts.append(f"Recent commands:\n{cmd_text}")
    
    return "\n\n".join(summary_parts)
