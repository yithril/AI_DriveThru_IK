"""
Canonical modifier actions for ingredient normalization

Maps various user expressions to standardized action terms.
This ensures consistent processing across the system.
"""

from typing import Dict, List

# Canonical action mappings
CANONICAL_ACTIONS: Dict[str, List[str]] = {
    "extra": ["extra", "heavy", "lots of", "double", "more", "additional", "ton of", "loads of"],
    "no": ["no", "without", "hold the", "hold", "remove", "exclude", "omit"],
    "light": ["light", "easy on", "less", "minimal", "reduced", "sparse"],
    "well_done": ["well done", "well-done", "thoroughly cooked", "cooked through"],
    "rare": ["rare", "pink", "medium rare", "bloody"],
    "add": ["add", "include", "with", "plus"]  # Default fallback
}


def canonicalize_action(action: str) -> str:
    """
    Convert user action to canonical form.
    
    Args:
        action: Raw action string from user input
        
    Returns:
        Canonical action string
    """
    action_lower = action.lower().strip()
    
    # Find matching canonical action
    for canonical, synonyms in CANONICAL_ACTIONS.items():
        if action_lower in synonyms:
            return canonical
    
    # Default fallback
    return "add"


def get_action_synonyms(canonical_action: str) -> List[str]:
    """
    Get all synonyms for a canonical action.
    
    Args:
        canonical_action: Canonical action string
        
    Returns:
        List of synonym strings
    """
    return CANONICAL_ACTIONS.get(canonical_action, [canonical_action])


def parse_modifier_string(modifier: str) -> tuple[str, str]:
    """
    Parse modifier string to extract action and ingredient term.
    Deterministic pattern matching for reliability.
    
    Args:
        modifier: Modifier string (e.g., "extra cheese", "no pickles")
        
    Returns:
        Tuple of (canonical_action, ingredient_term)
    """
    modifier_lower = modifier.lower().strip()
    
    # Action patterns with their canonical forms
    action_patterns = [
        ("no ", "no"),
        ("without ", "no"), 
        ("hold the ", "no"),
        ("hold ", "no"),
        ("remove ", "no"),
        ("exclude ", "no"),
        ("omit ", "no"),
        ("extra ", "extra"),
        ("heavy ", "extra"),
        ("lots of ", "extra"),
        ("ton of ", "extra"),
        ("loads of ", "extra"),
        ("double ", "extra"),
        ("more ", "extra"),
        ("additional ", "extra"),
        ("light ", "light"),
        ("easy on ", "light"),
        ("easy on the ", "light"),
        ("less ", "light"),
        ("minimal ", "light"),
        ("reduced ", "light"),
        ("sparse ", "light"),
        ("well done", "well_done"),
        ("well-done", "well_done"),
        ("rare", "rare"),
        ("medium rare", "rare"),
        ("pink", "rare"),
        ("add ", "add"),
        ("with ", "add"),
        ("include ", "add"),
        ("plus ", "add")
    ]
    
    # Find matching action pattern
    for pattern, action in action_patterns:
        if modifier_lower.startswith(pattern):
            ingredient_term = modifier_lower[len(pattern):].strip()
            # Clean up "the" prefix from ingredient
            if ingredient_term.startswith("the "):
                ingredient_term = ingredient_term[4:].strip()
            return action, ingredient_term
    
    # Default: treat as "add" action
    return "add", modifier_lower

