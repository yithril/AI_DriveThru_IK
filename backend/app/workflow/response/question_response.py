"""
Pydantic models for question agent responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Dict, Any, Optional
from app.constants.audio_phrases import AudioPhraseType


class QuestionResponse(BaseModel):
    """
    Response from the question agent
    """
    response_type: Literal["question", "statement"] = Field(
        ..., description="Whether the response is a question or a statement"
    )
    phrase_type: AudioPhraseType = Field(
        ..., description="The type of audio phrase to use for voice generation"
    )
    response_text: str = Field(
        ..., min_length=10, max_length=200, description="The customer-friendly response text"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="LLM confidence in this response (0.0 to 1.0)"
    )
    category: Literal["menu", "order", "restaurant_info", "general"] = Field(
        ..., description="The category of the question being answered or asked"
    )
    relevant_data: Optional[dict] = Field(
        None, description="Relevant data extracted or generated to answer the question"
    )

    @field_validator('response_text')
    @classmethod
    def validate_response_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Response text cannot be empty")
        technical_terms = ['error_code', 'batch_result', 'validation', 'database', 'api']
        if any(term in v.lower() for term in technical_terms):
            raise ValueError("Response text should not contain technical terms")
        return v.strip()

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0.5:
            raise ValueError("Confidence should be at least 0.5 for question responses")
        return v

    @field_validator('phrase_type')
    @classmethod
    def validate_phrase_type(cls, v, info):
        response_type = info.data.get('response_type')
        if response_type == "question" and v not in [AudioPhraseType.CLARIFICATION_QUESTION, AudioPhraseType.LLM_GENERATED]:
            raise ValueError("Questions should use CLARIFICATION_QUESTION or LLM_GENERATED phrase type")
        if response_type == "statement" and v not in [AudioPhraseType.CUSTOM_RESPONSE, AudioPhraseType.LLM_GENERATED]:
            raise ValueError("Statements should use CUSTOM_RESPONSE or LLM_GENERATED phrase type")
        return v

    def to_audio_params(self) -> Dict[str, Any]:
        """Convert to parameters for audio generation"""
        return {
            "phrase_type": self.phrase_type,
            "custom_text": self.response_text if self.phrase_type == AudioPhraseType.LLM_GENERATED else None
        }


class QuestionContext(BaseModel):
    """
    Context for the question agent
    """
    user_question: str
    restaurant_name: str
    restaurant_hours: Optional[str] = None
    restaurant_location: Optional[str] = None
    available_menu_items: List[str]
    menu_categories: List[str]
    current_order_summary: str
    conversation_history: List[Dict[str, Any]]
    
    def get_context_summary(self) -> str:
        """Get a summary of the context for the prompt"""
        return f"""
Restaurant: {self.restaurant_name}
Hours: {self.restaurant_hours or 'Not specified'}
Location: {self.restaurant_location or 'Not specified'}
Available Items: {', '.join(self.available_menu_items[:10])}{'...' if len(self.available_menu_items) > 10 else ''}
Current Order: {self.current_order_summary}
"""

