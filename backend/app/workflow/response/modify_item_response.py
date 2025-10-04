"""
Pydantic models for Modify Item Agent responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from app.constants.item_sizes import ItemSize


class ModificationInstruction(BaseModel):
    """Individual modification instruction for a specific quantity of items"""
    
    item_id: str = Field(..., description="ID of the order item to modify")
    item_name: str = Field(..., description="Name of the item being modified")
    quantity: int = Field(..., description="Number of items to apply this modification to")
    modification: str = Field(..., description="Human-readable modification instruction (e.g., 'extra cheese', 'no lettuce')")
    reasoning: Optional[str] = Field(None, description="Explanation of why this modification was identified")


class ModifyItemResult(BaseModel):
    """
    Enhanced response from the Modify Item Agent
    
    Contains the parsed modification request with support for complex scenarios
    including quantity-based modifications and item splitting.
    """
    
    # Success indicators
    success: bool = Field(
        ..., description="Whether the modification request was successfully parsed"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence in the modification request"
    )
    
    # Enhanced modification structure
    modifications: List[ModificationInstruction] = Field(
        default_factory=list, description="List of modification instructions for different quantities"
    )
    
    # Item splitting support
    requires_split: bool = Field(
        default=False, description="Whether the original item needs to be split into multiple items"
    )
    remaining_unchanged: int = Field(
        default=0, description="Number of items that remain unchanged (for splitting scenarios)"
    )
    
    # Clarification needed
    clarification_needed: bool = Field(
        default=False, description="Whether clarification is needed from the user"
    )
    clarification_message: Optional[str] = Field(
        None, description="Message to ask user for clarification"
    )
    
    # Validation and errors
    validation_errors: List[str] = Field(
        default_factory=list, description="List of validation errors found during parsing"
    )
    
    # Partial success support (added by service during validation)
    successful_modifications: Optional[List[ModificationInstruction]] = Field(
        default=None, description="Modifications that passed validation (set by service)"
    )
    failed_modifications: Optional[List[ModificationInstruction]] = Field(
        default=None, description="Modifications that failed validation (set by service)"
    )
    
    reasoning: Optional[str] = Field(
        None, description="Explanation of the modification request parsing"
    )

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence score"""
        return v

    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence modification request"""
        return self.confidence >= 0.8

    def has_modifications(self) -> bool:
        """Check if there are any modification instructions"""
        return len(self.modifications) > 0

    def needs_clarification(self) -> bool:
        """Check if clarification is needed"""
        return self.clarification_needed or self.confidence < 0.5

    def is_actionable(self) -> bool:
        """Check if this modification request can be acted upon"""
        return (
            self.success and 
            not self.needs_clarification() and
            self.has_modifications()
        )

    def get_total_modified_quantity(self) -> int:
        """Get the total quantity of items that will be modified"""
        return sum(mod.quantity for mod in self.modifications)

    def get_target_item_ids(self) -> List[str]:
        """Get all unique target item IDs"""
        return list(set(mod.item_id for mod in self.modifications))

    def has_splitting_required(self) -> bool:
        """Check if item splitting is required"""
        return self.requires_split or self.remaining_unchanged > 0
