"""
Audio phrase constants for voice generation
"""
from enum import Enum
from typing import List


class AudioPhraseType(Enum):
    """Types of audio phrases for voice generation"""
    # Core phrases
    GREETING = "greeting"
    COME_AGAIN = "come_again"
    THANK_YOU = "thank_you"
    
    # State machine phrases
    ORDER_SUMMARY = "order_summary"
    CONTINUE_ORDERING = "continue_ordering"
    NO_ORDER_YET = "no_order_yet"
    TAKE_YOUR_TIME = "take_your_time"
    READY_TO_ORDER = "ready_to_order"
    HOW_CAN_I_HELP = "how_can_i_help"
    DIDNT_UNDERSTAND = "didnt_understand"
    ORDER_READY = "order_ready"
    DRIVE_TO_WINDOW = "drive_to_window"
    
    # Command-specific phrases
    ITEM_ADDED_SUCCESS = "item_added_success"
    ITEM_REMOVED_SUCCESS = "item_removed_success"
    ITEM_UNAVAILABLE = "item_unavailable"
    ORDER_CLEARED_SUCCESS = "order_cleared_success"
    SYSTEM_ERROR_RETRY = "system_error_retry"
    
    # Modification-specific phrases
    ITEM_MODIFIED_SUCCESS = "item_modified_success"
    MODIFICATION_CLARIFICATION = "modification_clarification"
    MODIFICATION_ERROR = "modification_error"
    
    # Question-answer phrases
    QUESTION_ANSWERED = "question_answered"
    QUESTION_NOT_FOUND = "question_not_found"
    RESTAURANT_INFO = "restaurant_info"
    
    # Order management phrases
    ORDER_ALREADY_EMPTY = "order_already_empty"
    ORDER_CONFIRMED = "order_confirmed"
    ITEM_ADD_CLARIFICATION = "item_add_clarification"
    ITEM_ADD_ERROR = "item_add_error"
    
    # Item removal phrases
    ITEM_REMOVE_CLARIFICATION = "item_remove_clarification"
    ITEM_REMOVE_ERROR = "item_remove_error"
    ITEM_NOT_FOUND = "item_not_found"
    
    # Dynamic phrases (require custom text)
    CUSTOM_RESPONSE = "custom_response"
    CLARIFICATION_QUESTION = "clarification_question"
    ERROR_MESSAGE = "error_message"
    LLM_GENERATED = "llm_generated"


class AudioPhraseConstants:
    """Constants for audio phrase generation and storage"""
    
    # Standard voice for all canned audio (from settings)
    @staticmethod
    def get_standard_voice():
        """Get the standard voice from settings"""
        from app.config.settings import settings
        return settings.tts_voice
    
    # For backward compatibility
    STANDARD_VOICE = property(lambda self: AudioPhraseConstants.get_standard_voice())
    
    # Audio file format
    AUDIO_FORMAT = "mp3"
    
    # Cache TTL (24 hours)
    CACHE_TTL = 86400
    
    @staticmethod
    def get_phrase_text(phrase_type: AudioPhraseType, restaurant_name: str = None) -> str:
        """Get the text for a specific phrase type"""
        phrases = {
            AudioPhraseType.GREETING: f"Welcome to {restaurant_name or 'our restaurant'}, may I take your order?",
            AudioPhraseType.COME_AGAIN: "I'm sorry, I didn't catch that. Could you please repeat your order?",
            AudioPhraseType.THANK_YOU: "Thank you! Please pull forward to the window.",
            
            # State machine phrases
            AudioPhraseType.ORDER_SUMMARY: "Let me confirm your order",
            AudioPhraseType.CONTINUE_ORDERING: "No problem! What else would you like to order?",
            AudioPhraseType.NO_ORDER_YET: "You don't have an order yet. What would you like to order?",
            AudioPhraseType.TAKE_YOUR_TIME: "Take your time! Let me know when you're ready to order.",
            AudioPhraseType.READY_TO_ORDER: "I'm here when you're ready to order!",
            AudioPhraseType.HOW_CAN_I_HELP: "What can I help you with today?",
            AudioPhraseType.DIDNT_UNDERSTAND: "I'm sorry, I didn't understand. Could you please try again?",
            AudioPhraseType.ORDER_READY: "Is this order correct?",
            AudioPhraseType.DRIVE_TO_WINDOW: "Drive up to the next window please!",
            
            # Command-specific phrases
            AudioPhraseType.ITEM_ADDED_SUCCESS: "Added that to your order. Would you like anything else?",
            AudioPhraseType.ITEM_REMOVED_SUCCESS: "Removed that from your order. Would you like anything else?",
            AudioPhraseType.ITEM_UNAVAILABLE: "Sorry, we don't have that on our menu. Would you like to try something else?",
            AudioPhraseType.ORDER_CLEARED_SUCCESS: "Your order has been cleared.",
            AudioPhraseType.SYSTEM_ERROR_RETRY: "I'm sorry, I'm having some technical difficulties. Please try again.",
            
            # Modification-specific phrases
            AudioPhraseType.ITEM_MODIFIED_SUCCESS: "Updated your order. Would you like anything else?",
            AudioPhraseType.MODIFICATION_CLARIFICATION: "I need more information about your modification.",
            AudioPhraseType.MODIFICATION_ERROR: "I couldn't make that change. Please try again.",
            
            # Question-answer phrases
            AudioPhraseType.QUESTION_ANSWERED: "Here's what I found for you.",
            AudioPhraseType.QUESTION_NOT_FOUND: "I'm not sure about that. Let me help you with something else.",
            AudioPhraseType.RESTAURANT_INFO: "Here's our restaurant information.",
            
            # Order management phrases
            AudioPhraseType.ORDER_ALREADY_EMPTY: "Your order is already empty. What would you like to order?",
            AudioPhraseType.ORDER_CONFIRMED: "Perfect! If everything looks correct on your screen, that'll be {total}. Pull around to the next window!",
            AudioPhraseType.ITEM_ADD_CLARIFICATION: "I need more information about what you'd like to add.",
            AudioPhraseType.ITEM_ADD_ERROR: "Sorry, I couldn't add that to your order. Please try again.",
            
            # Item removal phrases
            AudioPhraseType.ITEM_REMOVE_CLARIFICATION: "I need more information about what you'd like to remove.",
            AudioPhraseType.ITEM_REMOVE_ERROR: "Sorry, I couldn't remove that from your order. Please try again.",
            AudioPhraseType.ITEM_NOT_FOUND: "I don't see that item in your order. Could you check what you'd like to remove?",
            
            # Dynamic phrases (fallback text)
            AudioPhraseType.CUSTOM_RESPONSE: "Custom response",
            AudioPhraseType.CLARIFICATION_QUESTION: "I need more information to help you.",
            AudioPhraseType.ERROR_MESSAGE: "I'm sorry, there was an error processing your request.",
            AudioPhraseType.LLM_GENERATED: "LLM generated response"
        }
        return phrases.get(phrase_type, "")
    
    @staticmethod
    def get_all_phrase_types() -> List[AudioPhraseType]:
        """Get all available phrase types"""
        return list(AudioPhraseType)

