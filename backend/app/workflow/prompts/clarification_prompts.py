"""
Clarification Agent Prompts

Prompts for the clarification agent with tool support.
"""

from typing import Any


def build_clarification_agent_prompt(context: Any, failed_items: list) -> dict:
    """
    Build the prompt for clarification agent with tools.
    
    Args:
        context: ClarificationContext with all data
        failed_items: List of failed item names
        
    Returns:
        Dict with system_prompt and user_message
    """
    
    # Build user message with clear task
    failed_items_text = ', '.join(failed_items) if failed_items else 'unknown items'
    
    user_message = f"""The customer wanted: {failed_items_text}

These items are not available.

TASK: Generate a 1-2 sentence clarification response that:
1. Acknowledges what they wanted isn't available
2. Suggests 2-3 similar alternatives (use search_menu_for_alternatives tool)
3. Asks if they'd like one of the alternatives

Be friendly and sales-oriented. End with a question mark."""
    
    # Build system prompt
    system_prompt = f"""You are a helpful drive-thru assistant at {context.restaurant_name}.

Current Order: {context.current_order_summary}

You have ONE tool: search_menu_for_alternatives(failed_item)
Use it ONCE per failed item, then IMMEDIATELY give your final answer.
Do NOT call the tool multiple times."""
    
    return {
        "system_prompt": system_prompt,
        "user_message": user_message
    }
