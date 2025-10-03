"""
Prompts for the question agent
"""

from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate


def get_question_prompt(
    user_input: str,
    conversation_history: List[Dict[str, Any]],
    order_state: Any,
    menu_items: List[str],
    restaurant_info: Dict[str, Any]
) -> str:
    """
    Generate the prompt for the question agent
    
    Args:
        user_input: The customer's question
        conversation_history: Recent conversation turns
        order_state: Current order state (can be dict or object)
        menu_items: Available menu items
        restaurant_info: Restaurant information
        
    Returns:
        Formatted prompt string
    """
    template = """You are a helpful drive-thru assistant specializing in answering customer questions about the restaurant, menu, and their order.

FACTS:
RESTAURANT INFORMATION:
- Restaurant Name: {restaurant_name}
- Opening Hours: {opening_hours}
- Address: {address}
- Phone: {phone}
- Menu Items: {menu_items}
- Current Order: {current_order_summary}
- Conversation History: {conversation_history}
- User Input: {user_input}

INSTRUCTIONS:
- Answer the user's question concisely and accurately based on the provided FACTS.
- If the question is about menu items, refer to the "Menu Items" in FACTS.
- If the question is about the current order, refer to the "Current Order" in FACTS.
- If the question is about restaurant information (hours, address, etc.), refer to "RESTAURANT INFORMATION" in FACTS.
- If you cannot find the answer in the provided FACTS, state that you don't have that information.
- Keep responses to 1-2 sentences.
- Maintain a friendly and helpful tone.

CONSTRAINTS:
- Do not invent information not present in FACTS.
- Do not ask follow-up questions unless absolutely necessary for clarification.
- Do not reference technical terms.

TASK:
Generate a helpful response to the customer's question.

OUTPUT FORMAT:
Respond with a JSON object matching this exact structure:
{{
  "response_type": "question" or "statement",
  "phrase_type": "CLARIFICATION_QUESTION", "CUSTOM_RESPONSE", or "LLM_GENERATED",
  "response_text": "Your helpful response here (10-200 characters)",
  "confidence": 0.95,
  "category": "menu", "order", "restaurant_info", or "general",
  "relevant_data": {{}}
}}

RESPONSE TYPE RULES:
- Use "question" when you need more information from the customer
- Use "statement" when you're providing information or confirming something

PHRASE TYPE RULES:
- Use "CLARIFICATION_QUESTION" for questions that need customer input
- Use "CUSTOM_RESPONSE" for statements that provide information
- Use "LLM_GENERATED" for complex responses that need custom text

CONFIDENCE RULES:
- Use 0.9+ for clear, confident responses
- 0.7-0.8 for responses with some uncertainty
- Never use below 0.5
Return ONLY the JSON response. Do not include any other text."""

    # Placeholder for restaurant info (will be fetched by agent)
    restaurant_name = restaurant_info.get("name", "Our Restaurant")
    opening_hours = restaurant_info.get("hours", "7 AM to 10 PM daily")
    address = restaurant_info.get("address", "123 Main St, Anytown, USA")
    phone = restaurant_info.get("phone", "555-123-4567")

    # Format conversation history
    formatted_history = "\n".join([f"{entry['role']}: {entry['content']}" for entry in conversation_history])

    # Format current order summary - handle both dict and object
    current_order_summary = "No items in order."
    if order_state:
        line_items = order_state.line_items if hasattr(order_state, 'line_items') else order_state.get('line_items', [])
        if line_items:
            current_order_summary = ", ".join([f"{item.get('quantity', 1)}x {item.get('name', 'Unknown Item')}" for item in line_items])

    prompt_template = PromptTemplate(
        template=template,
        input_variables=[
            "restaurant_name", "opening_hours", "address", "phone", "menu_items",
            "current_order_summary", "conversation_history", "user_input"
        ]
    )
    return prompt_template.format(
        restaurant_name=restaurant_name,
        opening_hours=opening_hours,
        address=address,
        phone=phone,
        menu_items=", ".join(menu_items) if menu_items else "No menu items available.",
        current_order_summary=current_order_summary,
        conversation_history=formatted_history,
        user_input=user_input
    )

