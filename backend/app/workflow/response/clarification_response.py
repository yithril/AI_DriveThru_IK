"""
Clarification Response Model

Pydantic model for structured LLM output from the clarification agent.
Defines the contract for clarification responses with validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal
from app.constants.audio_phrases import AudioPhraseType


class ClarificationResponse(BaseModel):
    """
    Structured response from the clarification agent.
    
    Defines what the LLM should output when handling order clarification scenarios.
    """
    
    # Response classification
    response_type: Literal["question", "statement"] = Field(
        description="Whether this is asking a question or making a statement"
    )
    
    # Audio generation
    phrase_type: AudioPhraseType = Field(
        description="Which audio phrase type to use for voice generation"
    )
    
    # Response content
    response_text: str = Field(
        min_length=10,
        max_length=200,
        description="The actual text to speak to the customer"
    )
    
    # Confidence scoring
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM confidence in this response (0.0 to 1.0)"
    )
    
    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v):
        """Validate response text is customer-friendly"""
        if not v or not v.strip():
            raise ValueError("Response text cannot be empty")
        
        # Ensure it's not too technical
        technical_terms = ['error_code', 'batch_result', 'validation', 'database']
        if any(term in v.lower() for term in technical_terms):
            raise ValueError("Response text should not contain technical terms")
        
        return v.strip()
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence is reasonable"""
        if v < 0.5:
            raise ValueError("Confidence should be at least 0.5 for clarification responses")
        return v
    
    @field_validator('phrase_type')
    @classmethod
    def validate_phrase_type(cls, v, info):
        """Validate phrase type matches response type"""
        response_type = info.data.get('response_type')
        
        if response_type == "question" and v not in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.LLM_GENERATED]:
            raise ValueError("Questions should use CLARIFICATION_QUESTION or LLM_GENERATED phrase type")
        
        if response_type == "statement" and v not in [AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]:
            raise ValueError("Statements should use CUSTOM_RESPONSE or LLM_GENERATED phrase type")
        
        return v
    
    def to_audio_params(self) -> dict:
        """Convert to parameters for audio generation"""
        return {
            "phrase_type": self.phrase_type,
            "custom_text": self.response_text if self.phrase_type == AudioPhraseType.LLM_GENERATED else None
        }
    
    def is_question(self) -> bool:
        """Check if this is a question response"""
        return self.response_type == "question"
    
    def is_statement(self) -> bool:
        """Check if this is a statement response"""
        return self.response_type == "statement"
    
    def __str__(self) -> str:
        """String representation for logging"""
        return f"ClarificationResponse({self.response_type}): {self.response_text[:50]}..."


class ClarificationContext(BaseModel):
    """
    Context data for clarification agent processing.
    
    Contains all the information needed to generate a helpful clarification response.
    """
    
    # Batch result data
    batch_outcome: str = Field(description="Overall batch outcome")
    error_codes: list[str] = Field(default_factory=list, description="Specific error codes")
    failed_items: list[str] = Field(default_factory=list, description="Items that failed to add")
    successful_items: list[str] = Field(default_factory=list, description="Items that were added successfully")
    
    # Menu context
    available_items: list[str] = Field(default_factory=list, description="All available menu items")
    similar_items: dict[str, list[str]] = Field(default_factory=dict, description="Similar items by category")
    
    # Conversation context
    conversation_history: list[dict] = Field(default_factory=list, description="Recent conversation turns")
    current_order_summary: str = Field(default="", description="Current order summary")
    restaurant_name: str = Field(default="", description="Restaurant name")
    
    # Clarification command data
    clarification_commands: list[dict] = Field(default_factory=list, description="Clarification commands from batch result")
    has_clarification_needed: bool = Field(default=False, description="Whether clarification is needed")
    
    def get_failed_item_suggestions(self, failed_item: str) -> list[str]:
        """Get suggested alternatives for a failed item"""
        suggestions = []
        
        # Look for similar items by name similarity
        failed_lower = failed_item.lower()
        for item in self.available_items:
            if failed_lower in item.lower() or item.lower() in failed_lower:
                suggestions.append(item)
        
        # Look in similar_items mapping
        for category, items in self.similar_items.items():
            if failed_lower in category.lower():
                suggestions.extend(items)
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def has_recent_clarification(self, max_turns: int = 2) -> bool:
        """Check if we've asked for clarification recently"""
        if len(self.conversation_history) < max_turns:
            return False
        
        recent_turns = self.conversation_history[-max_turns:]
        clarification_phrases = [
            "what would you like", "did you mean", "we don't have", 
            "what size", "which option", "could you clarify"
        ]
        
        for turn in recent_turns:
            response_text = turn.get('response_text', '').lower()
            if any(phrase in response_text for phrase in clarification_phrases):
                return True
        
        return False
    
    def get_clarification_questions(self) -> list[str]:
        """Get all clarification questions from clarification commands"""
        questions = []
        for cmd in self.clarification_commands:
            if cmd.get("clarification_question"):
                questions.append(cmd["clarification_question"])
        return questions
    
    def get_suggested_options(self) -> list[str]:
        """Get all suggested options from clarification commands"""
        options = []
        for cmd in self.clarification_commands:
            options.extend(cmd.get("suggested_options", []))
        return options
    
    def get_ambiguous_items(self) -> list[str]:
        """Get all ambiguous items from clarification commands"""
        items = []
        for cmd in self.clarification_commands:
            if cmd.get("ambiguous_item"):
                items.append(cmd["ambiguous_item"])
        return items

