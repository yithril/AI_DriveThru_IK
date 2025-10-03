"""
Pydantic models for Intent Classification Agent responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.constants.intent_types import IntentType


class IntentClassificationResult(BaseModel):
    """
    Response from the Intent Classification Agent
    """
    intent: IntentType = Field(
        ..., description="The classified intent type"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in the classification (0.0 to 1.0)"
    )
    reasoning: Optional[str] = Field(
        None, description="Optional explanation for why this intent was chosen"
    )


    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Warn if confidence is very low"""
        if v < 0.3:
            # Very low confidence - should probably be UNKNOWN
            pass
        return v

    def is_high_confidence(self) -> bool:
        """Check if this is a high confidence classification"""
        return self.confidence >= 0.8

    def is_actionable(self) -> bool:
        """Check if this intent is actionable (not UNKNOWN or low confidence)"""
        return self.intent != IntentType.UNKNOWN and self.confidence >= 0.6


