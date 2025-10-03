"""
Session State - Manages session data including command history

Represents a single customer session with order state and command history.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .command_history import CommandHistory


@dataclass
class SessionState:
    """
    State for a single customer session.
    
    Includes:
    - Session metadata (ID, restaurant)
    - Current order state
    - Command history
    - Conversation history
    """
    session_id: str
    restaurant_id: int
    
    # Command history
    command_history: CommandHistory = field(default_factory=CommandHistory)
    
    # Order state (to be defined by order models)
    current_order: Optional[Dict[str, Any]] = None
    
    # Conversation tracking
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session metadata
    language: str = "en"
    created_at: Optional[str] = None
    last_activity: Optional[str] = None
    
    def add_conversation_turn(self, user_input: str, ai_response: str):
        """Add a conversation turn to history"""
        self.conversation_history.append({
            "user": user_input,
            "ai": ai_response
        })
    
    def get_recent_conversation(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation turns"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session state to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "restaurant_id": self.restaurant_id,
            "command_history": self.command_history.to_dict(),
            "current_order": self.current_order,
            "conversation_history": self.conversation_history,
            "language": self.language,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }

