"""
Pydantic models for Item Extraction Agent (first agent in the pipeline)
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ExtractedItem(BaseModel):
    """
    Individual item extracted from user input (before menu resolution)
    """
    # Raw extraction fields
    item_name: str = Field(description="The name/description of the item as mentioned by the user")
    quantity: int = Field(description="Quantity requested", ge=1, le=100)
    size: Optional[str] = Field(default=None, description="Size mentioned (e.g., 'large', 'medium', 'small')")
    modifiers: List[str] = Field(default_factory=list, description="List of modifiers mentioned (e.g., 'extra cheese', 'no pickles')")
    special_instructions: Optional[str] = Field(default=None, description="Special cooking instructions mentioned")
    
    # Confidence and context
    confidence: float = Field(description="Confidence in extraction (0.0 to 1.0)", ge=0.0, le=1.0)
    context_notes: Optional[str] = Field(default=None, description="Additional context or notes about this item")
    
    @field_validator('modifiers')
    @classmethod
    def validate_modifiers(cls, v):
        """Ensure modifiers are not empty strings"""
        return [mod for mod in v if mod and mod.strip()]
    
    @field_validator('special_instructions')
    @classmethod
    def validate_special_instructions(cls, v):
        """Ensure special instructions are not empty strings"""
        if v and not v.strip():
            return None
        return v


class ItemExtractionResponse(BaseModel):
    """
    Response from Item Extraction Agent (first agent)
    """
    success: bool = Field(description="Whether extraction was successful")
    confidence: float = Field(description="Overall confidence in the extraction (0.0 to 1.0)", ge=0.0, le=1.0)
    extracted_items: List[ExtractedItem] = Field(description="List of items extracted from user input")
    needs_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to ask for clarification")
    extraction_notes: Optional[str] = Field(default=None, description="Notes about the extraction process")
    
    @field_validator('extracted_items')
    @classmethod
    def validate_extracted_items(cls, v):
        """Ensure at least one item is provided for successful extractions"""
        if not v:
            raise ValueError("At least one item must be provided for successful extraction")
        return v
    
    def has_ambiguous_items(self) -> bool:
        """Check if any items need clarification"""
        return any(item.confidence < 0.8 for item in self.extracted_items)
    
    def get_high_confidence_items(self) -> List[ExtractedItem]:
        """Get items with high confidence (>= 0.8)"""
        return [item for item in self.extracted_items if item.confidence >= 0.8]
    
    def get_low_confidence_items(self) -> List[ExtractedItem]:
        """Get items with low confidence (< 0.8)"""
        return [item for item in self.extracted_items if item.confidence < 0.8]

