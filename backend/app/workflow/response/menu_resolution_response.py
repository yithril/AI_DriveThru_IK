"""
Pydantic models for Menu Resolution Agent (second agent in the pipeline)
"""

from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator


class NormalizedModifier(BaseModel):
    """
    Normalized modifier with ingredient resolution data
    """
    # Original and final modifier strings
    original_modifier: str = Field(description="Original modifier string from user input")
    final_modifier: str = Field(description="Final normalized modifier string for commands")
    
    # Parsed action and ingredient (for debugging/logging)
    action: str = Field(description="Action type: 'add', 'remove', 'extra', 'no', etc.")
    ingredient_term: str = Field(description="Raw ingredient term from user input")
    
    # Ingredient resolution results
    ingredient_id: Optional[int] = Field(default=None, description="Resolved ingredient ID (None if not found)")
    normalized_ingredient_name: Optional[str] = Field(default=None, description="Normalized ingredient name from database")
    match_confidence: float = Field(default=0.0, description="Confidence in ingredient match (0.0 to 1.0)")
    
    # Resolution status
    is_resolved: bool = Field(default=False, description="Whether ingredient was successfully resolved")
    is_available: bool = Field(default=True, description="Whether ingredient is available in restaurant")
    
    # Additional ingredient data (for future use)
    is_allergen: Optional[bool] = Field(default=None, description="Whether ingredient is an allergen")
    allergen_type: Optional[str] = Field(default=None, description="Type of allergen if applicable")
    unit_cost: Optional[float] = Field(default=None, description="Unit cost of ingredient")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Ensure action is a valid type"""
        valid_actions = ['add', 'remove', 'extra', 'no', 'light', 'heavy', 'well_done', 'rare']
        if v not in valid_actions:
            # Default to 'add' for unknown actions
            return 'add'
        return v


class ResolvedItem(BaseModel):
    """
    Item after menu resolution (with menu_item_id)
    """
    # Original extraction data
    item_name: str = Field(description="Original item name from extraction")
    quantity: int = Field(description="Quantity requested", ge=1)
    size: Optional[str] = Field(default=None, description="Size requested")
    special_instructions: Optional[str] = Field(default=None, description="Special instructions")
    
    # Normalized modifiers (ingredient_id, canonical_action) - for commands
    modifiers: List[Tuple[int, str]] = Field(
        default_factory=list, 
        description="Normalized modifiers as (ingredient_id, canonical_action) tuples"
    )
    
    # Detailed ingredient normalization data (for logging/debugging)
    ingredient_normalization_details: List[NormalizedModifier] = Field(
        default_factory=list, 
        description="Detailed ingredient normalization data for logging and debugging"
    )
    
    # Menu item resolution results
    resolved_menu_item_id: int = Field(description="Resolved menu item ID (0 if ambiguous)")
    resolved_menu_item_name: Optional[str] = Field(default=None, description="Resolved menu item name")
    menu_item_resolution_confidence: float = Field(description="Confidence in menu item resolution (0.0 to 1.0)", ge=0.0, le=1.0)
    
    # Ambiguity and availability handling
    is_ambiguous: bool = Field(default=False, description="Whether this item is ambiguous")
    is_unavailable: bool = Field(default=False, description="Whether this item is unavailable")
    suggested_options: List[str] = Field(default_factory=list, description="Suggested menu items for clarification")
    clarification_question: Optional[str] = Field(default=None, description="Question to ask for clarification")
    
    @field_validator('modifiers')
    @classmethod
    def validate_modifiers(cls, v):
        """Ensure modifiers are valid tuples"""
        if not isinstance(v, list):
            return []
        # Filter out invalid tuples - they should be (int, str) tuples
        return [mod for mod in v if isinstance(mod, tuple) and len(mod) == 2 and isinstance(mod[0], int) and isinstance(mod[1], str)]
    
    @field_validator('special_instructions')
    @classmethod
    def validate_special_instructions(cls, v):
        """Ensure special instructions are not empty strings"""
        if v and not v.strip():
            return None
        return v


class MenuResolutionResponse(BaseModel):
    """
    Response from Menu Resolution Agent (second agent)
    """
    success: bool = Field(description="Whether resolution was successful")
    confidence: float = Field(description="Overall confidence in the resolution (0.0 to 1.0)", ge=0.0, le=1.0)
    resolved_items: List[ResolvedItem] = Field(description="List of items after menu resolution")
    needs_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to ask for clarification")
    resolution_notes: Optional[str] = Field(default=None, description="Notes about the resolution process")
    
    @field_validator('resolved_items')
    @classmethod
    def validate_resolved_items(cls, v):
        """Ensure at least one item is provided for successful resolutions"""
        # Only validate for successful resolutions - allow empty list for error cases
        return v
    
    def has_ambiguous_items(self) -> bool:
        """Check if any items are ambiguous"""
        return any(item.is_ambiguous for item in self.resolved_items)
    
    def get_clear_items(self) -> List[ResolvedItem]:
        """Get items that were successfully resolved (not ambiguous)"""
        return [item for item in self.resolved_items if not item.is_ambiguous and item.resolved_menu_item_id > 0]
    
    def get_ambiguous_items(self) -> List[ResolvedItem]:
        """Get items that are ambiguous and need clarification"""
        return [item for item in self.resolved_items if item.is_ambiguous]

