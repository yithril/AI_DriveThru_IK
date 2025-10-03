"""
Pydantic models for Modify Item Agent responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from decimal import Decimal
from app.constants.item_sizes import ItemSize


class ModifyItemResult(BaseModel):
    """
    Response from the Modify Item Agent
    
    Contains the parsed modification request with target identification
    and modification details. No database changes are made by the agent.
    """
    
    # Success indicators
    success: bool = Field(
        ..., description="Whether the modification request was successfully parsed"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence in the modification request"
    )
    
    # Target identification
    target_item_id: Optional[int] = Field(
        None, description="ID of the order item to modify"
    )
    target_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in target item identification"
    )
    target_reasoning: Optional[str] = Field(
        None, description="Explanation of how the target item was identified"
    )
    
    # Modification details
    modification_type: Optional[str] = Field(
        None, description="Type of modification: 'quantity', 'size', 'ingredient', or 'multiple'"
    )
    
    # Quantity modifications
    new_quantity: Optional[int] = Field(
        None, ge=1, le=20, description="New quantity for the item"
    )
    
    # Size modifications
    new_size: Optional[str] = Field(
        None, description="New size for the item"
    )
    
    # Ingredient modifications (human-readable instructions)
    ingredient_modifications: List[str] = Field(
        default_factory=list, description="List of ingredient modifications as human-readable strings"
    )
    
    # Clarification needed
    clarification_needed: bool = Field(
        default=False, description="Whether clarification is needed from the user"
    )
    clarification_message: Optional[str] = Field(
        None, description="Message to ask user for clarification"
    )
    
    # Additional cost from modifications
    additional_cost: Decimal = Field(
        default=Decimal('0.00'), ge=0, description="Additional cost from modifications"
    )
    
    # Validation and errors
    validation_errors: List[str] = Field(
        default_factory=list, description="List of validation errors found during parsing"
    )
    reasoning: Optional[str] = Field(
        None, description="Explanation of the modification request parsing"
    )

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence score"""
        # Just validate the range, don't access other fields during validation
        return v

    @field_validator('target_confidence')
    @classmethod
    def validate_target_confidence(cls, v):
        """Validate target confidence"""
        # Just validate the range, don't access other fields during validation
        return v

    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence modification request"""
        return self.confidence >= 0.8

    def has_target(self) -> bool:
        """Check if a target item was identified"""
        return self.target_item_id is not None

    def needs_clarification(self) -> bool:
        """Check if clarification is needed"""
        return self.clarification_needed or self.target_confidence < 0.5

    def has_quantity_modification(self) -> bool:
        """Check if this includes a quantity modification"""
        return self.new_quantity is not None

    def has_size_modification(self) -> bool:
        """Check if this includes a size modification"""
        return self.new_size is not None

    def has_ingredient_modifications(self) -> bool:
        """Check if this includes ingredient modifications"""
        return len(self.ingredient_modifications) > 0

    def is_actionable(self) -> bool:
        """Check if this modification request can be acted upon"""
        return (
            self.success and 
            not self.needs_clarification() and
            (self.has_quantity_modification() or 
             self.has_size_modification() or 
             self.has_ingredient_modifications())
        )
