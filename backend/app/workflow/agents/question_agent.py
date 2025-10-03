"""
Question Agent - Answers customer questions using LangChain tools

Uses function calling to intelligently search menu/ingredients only when needed.
Perfect for large menus where you don't want to dump everything in the prompt.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.workflow.response.question_response import QuestionResponse
from app.config.settings import settings
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


def create_question_tools(menu_service, ingredient_service):
    """
    Create LangChain tools for the question agent.
    
    Args:
        menu_service: MenuService instance
        ingredient_service: IngredientService instance
        
    Returns:
        List of LangChain tools
    """
    
    @tool
    async def search_menu_items(search_term: str) -> str:
        """
        Search for menu items by name.
        Use this when the customer asks about specific menu items.
        
        Args:
            search_term: The item to search for (e.g., "burger", "fries", "shake")
            
        Returns:
            JSON string with menu items found
        """
        try:
            # Get restaurant_id from the bound service context
            restaurant_id = getattr(menu_service, '_current_restaurant_id', 1)
            
            results = await menu_service.fuzzy_search_menu_items(
                restaurant_id=restaurant_id,
                search_term=search_term,
                limit=5,
                include_ingredients=False
            )
            
            if not results:
                return f"No menu items found matching '{search_term}'"
            
            items = []
            for item in results:
                items.append(f"{item['menu_item_name']} (${item['price']:.2f}) - {item['description']}")
            
            return "\n".join(items)
            
        except Exception as e:
            logger.error(f"Menu search tool error: {e}")
            return f"Error searching menu: {str(e)}"
    
    @tool
    async def search_ingredients(search_term: str) -> str:
        """
        Search for ingredients by name.
        Use this when the customer asks about ingredients or allergens.
        
        Args:
            search_term: The ingredient to search for (e.g., "cheese", "peanuts", "gluten")
            
        Returns:
            JSON string with ingredients found
        """
        try:
            restaurant_id = getattr(ingredient_service, '_current_restaurant_id', 1)
            
            results = await ingredient_service.search_by_name(
                restaurant_id=restaurant_id,
                name=search_term
            )
            
            if not results.ingredients:
                return f"No ingredients found matching '{search_term}'"
            
            items = []
            for ing in results.ingredients:
                allergen_info = f" (ALLERGEN: {ing.allergen_type})" if ing.is_allergen else ""
                items.append(f"{ing.name}{allergen_info} - {ing.description or 'No description'}")
            
            return "\n".join(items)
            
        except Exception as e:
            logger.error(f"Ingredient search tool error: {e}")
            return f"Error searching ingredients: {str(e)}"
    
    @tool
    async def get_menu_item_details(menu_item_name: str) -> str:
        """
        Get detailed information about a specific menu item including its ingredients.
        Use this when the customer asks "what's in X?" or wants details about an item.
        
        Args:
            menu_item_name: Name of the menu item
            
        Returns:
            Detailed information about the menu item
        """
        try:
            restaurant_id = getattr(menu_service, '_current_restaurant_id', 1)
            
            # Search for the item first
            results = await menu_service.fuzzy_search_menu_items(
                restaurant_id=restaurant_id,
                search_term=menu_item_name,
                limit=1,
                include_ingredients=True
            )
            
            if not results:
                return f"Menu item '{menu_item_name}' not found"
            
            item = results[0]
            response = f"{item['menu_item_name']} - ${item['price']:.2f}\n"
            response += f"Description: {item['description']}\n"
            
            if item.get('ingredients'):
                response += "Ingredients: "
                ing_names = [ing['ingredient_name'] for ing in item['ingredients']]
                response += ", ".join(ing_names)
            
            return response
            
        except Exception as e:
            logger.error(f"Menu item details tool error: {e}")
            return f"Error getting menu item details: {str(e)}"
    
    return [search_menu_items, search_ingredients, get_menu_item_details]


async def question_agent(
    user_input: str,
    restaurant_id: int,
    menu_service,
    ingredient_service,
    restaurant_service,
    conversation_history: Optional[ConversationHistory] = None,
    current_order: Optional[Dict[str, Any]] = None
) -> QuestionResponse:
    """
    Question Agent - Answers customer questions using LangChain tools.
    
    Uses function calling to intelligently search menu/ingredients only when needed.
    
    Args:
        user_input: The customer's question
        restaurant_id: Restaurant ID
        menu_service: MenuService instance
        ingredient_service: IngredientService instance
        restaurant_service: RestaurantService instance
        conversation_history: Recent conversation turns (optional)
        current_order: Current order state (optional)
        
    Returns:
        QuestionResponse with structured answer
    """
    try:
        # Get restaurant info (always needed for context)
        restaurant = await restaurant_service.get_by_id(restaurant_id)
        if not restaurant:
            return _error_response("Restaurant not found")
        
        # Store restaurant_id in services for tools to access
        menu_service._current_restaurant_id = restaurant_id
        ingredient_service._current_restaurant_id = restaurant_id
        
        restaurant_info = {
            "name": restaurant.name,
            "description": restaurant.description,
            "phone": restaurant.phone,
            "address": restaurant.address,
            "hours": restaurant.hours
        }
        
        # Build order summary
        order_summary = _format_order_summary(current_order) if current_order else "No items in order"
        
        # Build conversation context
        if conversation_history is None:
            conversation_history = ConversationHistory(session_id="")
        history_text = _format_conversation_history(conversation_history)
        
        # Create tools with service bindings
        tools = create_question_tools(menu_service, ingredient_service)
        
        # Build system prompt
        system_prompt = f"""You are a helpful drive-thru assistant at {restaurant_info['name']}.

RESTAURANT INFO:
- Name: {restaurant_info['name']}
- Phone: {restaurant_info['phone']}
- Address: {restaurant_info['address']}
- Hours: {restaurant_info['hours']}

CURRENT ORDER: {order_summary}

CONVERSATION HISTORY:
{history_text if history_text else 'No previous conversation'}

INSTRUCTIONS:
- Answer the customer's question helpfully and concisely (1-2 sentences max)
- Use the search tools if you need to look up menu items or ingredients
- For general restaurant info, use the RESTAURANT INFO above
- For order questions, use the CURRENT ORDER above
- If you don't know something, say so politely
- IMPORTANT: When describing menu items, use the EXACT menu item names from tool responses, not the customer's search terms

You have access to these tools:
- search_menu_items: Search for menu items by name
- search_ingredients: Search for ingredients/allergens
- get_menu_item_details: Get detailed info including ingredients for a specific item

Use tools wisely - only search when you actually need specific information."""
        
        # Create agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.1
        )
        
        # Create agent with tools
        agent = create_openai_functions_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )
        
        # Execute agent
        result = await agent_executor.ainvoke({"input": user_input})
        response_text = result.get("output", "I'm sorry, I couldn't process your request.")
        
        logger.info(f"Question agent response: {response_text[:100]}...")
        
        # Use LLM to classify the category based on the question and response
        category = await _classify_category_with_llm(user_input, response_text)
        
        # Return structured response
        return QuestionResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text=response_text[:200],  # Enforce max length
            confidence=0.9,  # High confidence for successful tool-based answers
            category=category,
            relevant_data={"tools_used": result.get("intermediate_steps", [])}
        )

    except Exception as e:
        logger.error(f"Question agent failed: {e}")
        return _error_response(str(e))


async def _classify_category_with_llm(user_input: str, response: str) -> str:
    """Use LLM to intelligently classify question category"""
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        classification_prompt = """You are a classification assistant for a drive-thru restaurant.

Classify the customer's question into one of these categories:

1. "menu" - Questions about menu items, prices, ingredients, sizes, availability, what's in items, allergens, etc.
2. "order" - Questions about the customer's current order, total cost, what they've ordered, etc.
3. "restaurant_info" - Questions about restaurant hours, location, phone number, address, etc.
4. "general" - Everything else that doesn't fit the above categories

Customer Question: "{user_input}"
Agent Response: "{response}"

Based on the question and response, classify this as: menu, order, restaurant_info, or general.

Return ONLY the category name, nothing else."""

        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.0  # Deterministic classification
        )
        
        messages = [
            SystemMessage(content=classification_prompt.format(
                user_input=user_input,
                response=response
            ))
        ]
        
        result = await llm.ainvoke(messages)
        category = result.content.strip().lower()
        
        # Validate the category
        valid_categories = ["menu", "order", "restaurant_info", "general"]
        if category in valid_categories:
            return category
        else:
            logger.warning(f"Invalid category from LLM: {category}, defaulting to 'general'")
            return "general"
            
    except Exception as e:
        logger.error(f"Category classification failed: {e}")
        return "general"


def _format_order_summary(order: Dict[str, Any]) -> str:
    """Format order for display"""
    items = order.get("items", []) if isinstance(order, dict) else []
    
    if not items:
        return "Your order is empty"
    
    item_list = []
    for item in items:
        qty = item.get("quantity", 1)
        name = item.get("name", "item")
        item_list.append(f"{qty}x {name}")
    
    return f"Your order: {', '.join(item_list)}"


def _format_conversation_history(history: ConversationHistory) -> str:
    """Format conversation history"""
    if history.is_empty():
        return ""
    
    formatted = []
    for entry in history.get_recent_entries(3):  # Last 3 turns
        if entry.role.value == "user":
            formatted.append(f"Customer: {entry.content}")
        elif entry.role.value == "assistant":
            formatted.append(f"Assistant: {entry.content}")
    
    return "\n".join(formatted)


def _error_response(error_msg: str) -> QuestionResponse:
    """Create error response"""
    return QuestionResponse(
        response_type="statement",
        phrase_type=AudioPhraseType.LLM_GENERATED,
        response_text="I'm sorry, I had trouble processing your question. Please try again.",
        confidence=0.5,
        category="general",
        relevant_data={"error": error_msg}
    )
