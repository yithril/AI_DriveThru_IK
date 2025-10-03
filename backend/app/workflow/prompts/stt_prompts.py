"""
Speech-to-Text Prompts

Prompts for OpenAI Whisper to improve transcription accuracy in drive-thru environments.
Includes menu context and drive-thru specific instructions.
"""

from typing import List, Dict, Any


def build_stt_prompt(menu_items: List[Dict[str, Any]], restaurant_name: str = "restaurant") -> str:
    """
    Build a prompt for OpenAI Whisper to improve transcription accuracy.
    
    Args:
        menu_items: List of menu items with names and ingredients
        restaurant_name: Name of the restaurant for context
        
    Returns:
        Formatted prompt string for Whisper
    """
    
    # Extract menu item names and ingredients
    menu_names = []
    all_ingredients = set()
    
    for item in menu_items:
        name = item.get('name', '')
        if name:
            menu_names.append(name)
        
        # Extract ingredients if available
        ingredients = item.get('ingredients', [])
        if isinstance(ingredients, list):
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    ingredient_name = ingredient.get('name', '')
                else:
                    ingredient_name = str(ingredient)
                if ingredient_name:
                    all_ingredients.add(ingredient_name)
    
    # Build the prompt
    prompt_parts = [
        f"This is a drive-thru AI assistant at {restaurant_name}. ",
        "The customer is ordering food from their car. ",
        "Ignore background noise, car engines, and other drive-thru sounds. ",
        "Focus on the customer's voice and food-related words. ",
        "Common drive-thru phrases include: 'I'd like', 'Can I get', 'I want', 'Add', 'Remove', 'Change', 'Modify'. ",
        "The customer may ask about prices, ingredients, or modifications. ",
        "They might say 'That's all', 'That's it', 'I'm done', or 'Finish my order' when done. ",
    ]
    
    # Add menu context
    if menu_names:
        prompt_parts.append(f"Menu items include: {', '.join(menu_names)}. ")
    
    if all_ingredients:
        ingredient_list = sorted(list(all_ingredients))
        prompt_parts.append(f"Common ingredients: {', '.join(ingredient_list)}. ")
    
    # Add common modifications
    prompt_parts.extend([
        "Common modifications: 'no cheese', 'extra pickles', 'hold the mayo', 'add bacon', 'well done', 'medium rare'. ",
        "Sizes: 'small', 'medium', 'large', 'regular'. ",
        "Quantities: 'one', 'two', 'three', 'a couple', 'a few'. ",
        "The customer might stutter, repeat themselves, or speak quickly. ",
        "They may use slang or abbreviations for menu items. ",
        "Focus on food-related vocabulary and ignore non-food background noise. ",
    ])
    
    return "".join(prompt_parts)


def get_basic_stt_prompt() -> str:
    """
    Get a basic STT prompt without menu context.
    Useful when menu data is not available.
    
    Returns:
        Basic prompt for drive-thru STT
    """
    return (
        "This is a drive-thru AI assistant. "
        "The customer is ordering food from their car. "
        "Ignore background noise, car engines, and other drive-thru sounds. "
        "Focus on the customer's voice and food-related words. "
        "Common phrases: 'I'd like', 'Can I get', 'I want', 'Add', 'Remove', 'Change'. "
        "The customer may ask about prices, ingredients, or modifications. "
        "They might say 'That's all', 'That's it', 'I'm done' when finished. "
        "Focus on food-related vocabulary and ignore non-food background noise."
    )
