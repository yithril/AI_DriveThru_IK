"""
Simple intent classification prompts
"""

from typing import Dict, Any
from langchain_core.prompts import PromptTemplate


def get_intent_classification_prompt(user_input: str, context: Dict[str, Any]) -> str:
    """
    Build the prompt for LLM intent classification using PromptTemplate

    Args:
        user_input: User's input text
        context: Conversation context

    Returns:
        Formatted prompt string ready for LangChain
    """

    template = """
You are an order taker at a drive-thru restaurant. Classify the user's intent and return ONLY JSON.

CONTEXT:
- Order items (already in cart): {order_items}
- Conversation state: {conversation_state}
- Conversation history (most recent first): {conversation_history}

USER INPUT: "{user_input}"

REQUIRED JSON FORMAT:
{{
  "intent": "INTENT_TYPE",
  "confidence": 0.95,
  "reasoning": "Brief explanation for why this intent was chosen"
}}

INTENT TYPES:
- ADD_ITEM: User wants to add food/drink items
- REMOVE_ITEM: User wants to remove specific items
- CLEAR_ORDER: User wants to remove all items
- MODIFY_ITEM: User wants to change item properties (including quantity) of an EXISTING item
- CONFIRM_ORDER: User is done ordering ("that's it", "done", "that's all")
- QUESTION: User asks questions about menu, prices, etc.
- UNKNOWN: Unclear or ambiguous intent

CRITICAL DISAMBIGUATION (ADD vs MODIFY):
- Prefer MODIFY_ITEM only when BOTH are true:
  1) The language refers to a *specific existing item* (definite reference or anaphora), and
  2) That referenced item (by name or type) already exists in Order items.
- Otherwise, classify as ADD_ITEM.

Signals for MODIFY_ITEM (definite reference / change language):
- Determiners: "the", "my", "that", "this", "the one", "the burger", "the quantum burger"
- Anaphora / callbacks: "the one I added", "the previous one", "that burger", "the last one"
- Change verbs: "make", "change", "have it", "instead", "actually", "on that", "for that", "on the burger"
- Quantity adjustments to an existing item: "make it two", "change it to a large", "swap fries for salad"
If *no matching item exists in Order items*, default to ADD_ITEM even if language is definite.

Signals for ADD_ITEM (indefinite / new):
- Indefinite articles or new introduction: "a", "an", "one", "I'd like a...", "can I get...", "add", "also", "another"
- Item is not yet in Order items
- Includes modifiers as part of the new addition: "with no lettuce", "no pickles", "extra cheese" → still ADD_ITEM if it’s a new item

TIE-BREAKERS (in order):
1) If Order items is empty → cannot MODIFY_ITEM. Use ADD_ITEM (if food intent exists) or other intents.
2) If user names a specific item that exists in Order items AND uses definite/change language → MODIFY_ITEM.
3) If user names a menu item that is NOT in Order items OR uses indefinite/add language → ADD_ITEM.
4) If ambiguous, prefer ADD_ITEM only when language clearly indicates adding; otherwise UNKNOWN.

EDGE CASE GUIDANCE:
- "I'd like a quantum burger with no lettuce" → ADD_ITEM (new item + modifier)
- "I'd like the quantum burger to have no lettuce" → MODIFY_ITEM *only if* a quantum burger is already in Order items; else ADD_ITEM
- "Make it two" after a referenced item → MODIFY_ITEM (quantity change)
- "No pickles" immediately after discussing a specific added burger → MODIFY_ITEM for that burger
- "Cancel my fries" → REMOVE_ITEM (not CLEAR_ORDER)
- "Clear the order" → CLEAR_ORDER
- "Is the shake large?" → QUESTION (not MODIFY_ITEM)

NOISE FILTERING:
Ignore non-food chatter and focus on order-relevant content for intent classification.

CONFIDENCE SCORING:
- 0.9–1.0: Very clear intent
- 0.7–0.8: Clear intent with minor ambiguity
- 0.5–0.6: Somewhat unclear, needs context
- 0.0–0.4: Very unclear → UNKNOWN

EXAMPLES:
- "I'd like a Big Mac and fries"
  → {{"intent": "ADD_ITEM", "confidence": 0.95, "reasoning": "Clear request to add food items"}}

- (Order items contain "quantum burger")
  "I'd like the quantum burger to have no lettuce"
  → {{"intent": "MODIFY_ITEM", "confidence": 0.92, "reasoning": "Definite reference to existing quantum burger with modification request"}}

- (Order items do NOT contain "quantum burger")
  "I'd like the quantum burger to have no lettuce"
  → {{"intent": "ADD_ITEM", "confidence": 0.9, "reasoning": "No existing quantum burger found, treating as new item with modifiers"}}

- "Remove my fries"
  → {{"intent": "REMOVE_ITEM", "confidence": 0.9, "reasoning": "Clear request to remove specific item"}}

- "That's all"
  → {{"intent": "CONFIRM_ORDER", "confidence": 0.95, "reasoning": "Clear signal that ordering is complete"}}

- "How much is a burger?"
  → {{"intent": "QUESTION", "confidence": 0.9, "reasoning": "Question about menu item pricing"}}

Return ONLY the JSON response.
"""

    prompt_template = PromptTemplate(
        template=template,
        input_variables=["user_input", "order_items", "conversation_state", "conversation_history"]
    )

    return prompt_template.format(
        user_input=user_input,
        order_items=context.get("order_items", []),
        conversation_state=context.get("conversation_state", "Ordering"),
        conversation_history=context.get("conversation_history", [])
    )
