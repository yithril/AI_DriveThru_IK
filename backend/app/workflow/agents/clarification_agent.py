"""
Clarification Agent - Uses tools to find similar menu items

Handles error scenarios by intelligently searching for alternatives.
Uses LangChain tools to fuzzy search menu for similar items.
"""

import logging
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.workflow.response.clarification_response import ClarificationResponse, ClarificationContext
from app.workflow.prompts.clarification_prompts import build_clarification_agent_prompt
from app.config.settings import settings
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


def create_clarification_tools(menu_service):
    """Create LangChain tools for the clarification agent."""
    
    @tool
    async def search_menu_for_alternatives(failed_item: str) -> str:
        """
        Search menu for items similar to what the customer wanted.
        Returns the top 3-5 similar items with prices.
        
        Args:
            failed_item: What the customer asked for (e.g., "chocolate shake")
            
        Returns:
            Similar items from the menu
        """
        try:
            restaurant_id = getattr(menu_service, '_current_restaurant_id', 1)
            
            # Use fuzzy search to find similar items
            results = await menu_service.fuzzy_search_menu_items(
                restaurant_id=restaurant_id,
                search_term=failed_item,
                limit=5,
                include_ingredients=False
            )
            
            if not results:
                return f"No menu items found similar to '{failed_item}'. Try broader terms."
            
            items = [f"{item['menu_item_name']} (${item['price']:.2f})" for item in results]
            return "Available: " + ", ".join(items)
            
        except Exception as e:
            logger.error(f"Menu search error: {e}")
            return f"Error: {str(e)}"
    
    return [search_menu_for_alternatives]


async def clarification_agent(
    batch_result: Any,
    context: ClarificationContext,
    menu_service
) -> ClarificationResponse:
    """
    Generate clarification response using tools to find alternatives.
    
    Args:
        batch_result: Command execution results
        context: ClarificationContext with all necessary data
        menu_service: MenuService for searching similar items
        
    Returns:
        ClarificationResponse with structured output
    """
    try:
        # Store restaurant info for tools
        menu_service._current_restaurant_id = getattr(context, 'restaurant_id', 1)
        
        # Create tools
        tools = create_clarification_tools(menu_service)
        
        # Build prompts
        prompts = build_clarification_agent_prompt(context, context.failed_items)
        
        # Create agent prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompts["system_prompt"]),
            ("human", prompts["user_message"]),
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
        result = await agent_executor.ainvoke({"input": prompts["user_message"]})
        response_text = result.get("output", "I'm sorry, could you please try again?")
        
        logger.info(f"Clarification agent response: {response_text[:100]}...")
        
        # Determine if it's a question or statement
        response_type = "question" if "?" in response_text else "statement"
        
        # Return structured response
        return ClarificationResponse(
            response_type=response_type,
            phrase_type=AudioPhraseType.CLARIFICATION_QUESTION if response_type == "question" else AudioPhraseType.LLM_GENERATED,
            response_text=response_text[:200],
            confidence=0.9
        )
        
    except Exception as e:
        logger.error(f"Clarification agent failed: {e}")
        return ClarificationResponse(
            response_type="statement",
            phrase_type=AudioPhraseType.LLM_GENERATED,
            response_text="I'm sorry, I had trouble processing your request. Please try again.",
            confidence=0.5
        )


async def build_clarification_context(
    batch_result: Any,
    order_state: Any,
    conversation_history: list,
    restaurant_id: str,
    available_items: list,
    restaurant_name: str
) -> ClarificationContext:
    """
    Build clarification context from batch result and state.
    
    Args:
        batch_result: Command execution results
        order_state: Current order state
        conversation_history: Recent conversation history
        restaurant_id: Restaurant ID
        available_items: List of available menu items (can be empty - agent will use tools)
        restaurant_name: Restaurant name
        
    Returns:
        ClarificationContext with all necessary data
    """
    # Extract error details from batch result
    if hasattr(batch_result, 'errors_by_code'):
        error_codes = list(batch_result.errors_by_code.keys()) if batch_result.errors_by_code else []
    else:
        error_codes = batch_result.get('error_codes', []) if isinstance(batch_result, dict) else []
    
    if hasattr(batch_result, 'get_failed_results'):
        failed_items = [result.message for result in batch_result.get_failed_results()]
        successful_items = [result.message for result in batch_result.get_successful_results()]
    else:
        failed_items = batch_result.get('failed_items', []) if isinstance(batch_result, dict) else []
        successful_items = batch_result.get('successful_items', []) if isinstance(batch_result, dict) else []
    
    # Extract batch outcome
    if hasattr(batch_result, 'batch_outcome'):
        batch_outcome = batch_result.batch_outcome
    else:
        batch_outcome = batch_result.get('batch_outcome', 'UNKNOWN') if isinstance(batch_result, dict) else 'UNKNOWN'
    
    # Build order summary
    order_summary = _build_order_summary(order_state)
    
    context = ClarificationContext(
        batch_outcome=batch_outcome,
        error_codes=[str(code) for code in error_codes],
        failed_items=failed_items,
        successful_items=successful_items,
        clarification_commands=[],
        current_order_summary=order_summary,
        available_items=available_items,
        restaurant_name=restaurant_name,
        conversation_history=conversation_history,
        similar_items={}
    )
    
    return context


def _build_order_summary(order_state: Any) -> str:
    """Build a summary of the current order state."""
    if not order_state:
        return "Your order is currently empty."
    
    # Handle both object and dict
    if hasattr(order_state, 'line_items'):
        items = order_state.line_items
    elif isinstance(order_state, dict):
        items = order_state.get("items", [])
    else:
        return "Your order is currently empty."
    
    if not items:
        return "Your order is currently empty."
    
    item_summaries = []
    for item in items:
        quantity = item.get("quantity", 1)
        name = item.get("name", "item")
        size = item.get("size")
        
        if size:
            item_summaries.append(f"{quantity} {size} {name}")
        else:
            item_summaries.append(f"{quantity} {name}")
    
    if len(item_summaries) == 1:
        return f"Your current order: {item_summaries[0]}."
    else:
        items_text = ", ".join(item_summaries[:-1]) + f" and {item_summaries[-1]}"
        return f"Your current order: {items_text}."
