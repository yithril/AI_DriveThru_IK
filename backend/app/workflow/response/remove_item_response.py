"""
Pydantic models for REMOVE_ITEM agent input and output
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.constants.audio_phrases import AudioPhraseType


class ItemToRemove(BaseModel):
    """
    Individual item to remove from the order
    """
    order_item_id: Optional[int] = Field(default=None, description="Direct ID of the order item to remove")
    target_ref: Optional[str] = Field(default=None, description="Target reference (e.g., 'last_item', 'line_1', 'that burger')")
    removal_reason: Optional[str] = Field(default=None, description="Reason for removal (for logging/analytics)")
    
    # Ambiguity fields (used when both order_item_id and target_ref are None)
    ambiguous_item: Optional[str] = Field(default=None, description="The ambiguous item name (e.g., 'burger')")
    suggested_options: List[str] = Field(default_factory=list, description="List of suggested order items for clarification")
    clarification_question: Optional[str] = Field(default=None, description="Custom clarification question")
    
    @field_validator('target_ref')
    @classmethod
    def validate_target_ref(cls, v):
        """Ensure target_ref is not empty string"""
        if v and not v.strip():
            return None
        return v
    
    @field_validator('removal_reason')
    @classmethod
    def validate_removal_reason(cls, v):
        """Ensure removal_reason is not empty string"""
        if v and not v.strip():
            return None
        return v


class RemoveItemResponse(BaseModel):
    """
    Response from REMOVE_ITEM agent - focused on parsing result
    """
    confidence: float = Field(description="Confidence in the parsing (0.0 to 1.0)", ge=0.0, le=1.0)
    items_to_remove: List[ItemToRemove] = Field(description="List of items to remove from the order")
    relevant_data: Dict[str, Any] = Field(default_factory=dict, description="Additional relevant data")
    
    @field_validator('items_to_remove')
    @classmethod
    def validate_items_to_remove(cls, v):
        """Ensure at least one item is provided for success responses"""
        if not v:
            raise ValueError("At least one item must be provided")
        return v
    
    def to_audio_params(self) -> Dict[str, Any]:
        """Convert to audio generation parameters"""
        return {
            "phrase_type": self.phrase_type,
            "text": self.response_text,
            "confidence": self.confidence
        }


class RemoveItemContext(BaseModel):
    """
    Context for REMOVE_ITEM agent
    """
    restaurant_id: str = Field(description="Restaurant ID")
    user_input: str = Field(description="Original user input")
    normalized_user_input: str = Field(description="Normalized user input")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation history")
    order_state: Dict[str, Any] = Field(default_factory=dict, description="Current order state")
    current_order_items: List[Dict[str, Any]] = Field(default_factory=list, description="Current order items with details")

