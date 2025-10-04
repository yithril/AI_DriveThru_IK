"""
Prompts for REMOVE_ITEM agent
"""

from langchain_core.prompts import PromptTemplate


def get_remove_item_prompt(
    user_input: str,
    current_order_items: list
) -> str:
    """
    Get the prompt for REMOVE_ITEM agent
    
    Args:
        user_input: Normalized user input
        current_order_items: Current order items with details
        
    Returns:
        Formatted prompt string for the REMOVE_ITEM agent
    """
    
    # Format current order items
    order_text = ""
    if current_order_items:
        order_lines = []
        for i, item in enumerate(current_order_items, 1):
            item_name = item.get('name', 'Unknown Item')
            quantity = item.get('quantity', 1)
            size = item.get('size', '')
            modifiers = item.get('modifiers', [])
            size_text = f" ({size})" if size else ""
            modifiers_text = f" with {', '.join(modifiers)}" if modifiers else ""
            order_lines.append(f"  {i}. {item_name}{size_text}{modifiers_text} x{quantity}")
        order_text = "\n".join(order_lines)
    else:
        order_text = "  No items in current order"
    
    template = """Parse this customer request for removing items from their order.

Current Order:
{order_text}

Customer Request: "{user_input}"

Return JSON with this format:
{{
  "confidence": 0.0-1.0,
  "items_to_remove": [
    {{
      "order_item_id": null,
      "target_ref": "item_name_or_last_item",
      "modifier_spec": "optional_modifier_description",
      "removal_reason": "optional_reason"
    }}
  ],
  "relevant_data": {{}}
}}

Examples:
- "Remove the burger" → target_ref: "burger"
- "Remove the last thing" → target_ref: "last_item" 
- "Remove the fries" → target_ref: "fries"
- "Remove the fish sandwich with extra lettuce" → target_ref: "fish sandwich", modifier_spec: "extra lettuce"
- "Remove the burger with extra cheese" → target_ref: "burger", modifier_spec: "extra cheese"

IMPORTANT: If the customer specifies modifiers (like "with extra lettuce", "with no onions"), include the modifier_spec field to help identify the exact item to remove.

Return ONLY the JSON response."""

    # Create PromptTemplate with input variables
    prompt_template = PromptTemplate(
        template=template,
        input_variables=["user_input", "order_text"]
    )
    
    # Format the template with actual values
    return prompt_template.format(
        user_input=user_input,
        order_text=order_text
    )

