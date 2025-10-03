"""
Conversation Data Transfer Objects for standardized conversation history management
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ConversationRole(Enum):
    """Roles in a conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ConversationEntry:
    """
    A single entry in a conversation history.
    
    Attributes:
        role: The role of the speaker (user, assistant, system)
        content: The text content of the message
        timestamp: When the message was created
        session_id: The session this entry belongs to
    """
    role: ConversationRole
    content: str
    timestamp: datetime
    session_id: str
    
    def __post_init__(self):
        """Validate the entry after initialization"""
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        if not self.session_id.strip():
            raise ValueError("Session ID cannot be empty")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationEntry":
        """Create from dictionary"""
        return cls(
            role=ConversationRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data["session_id"]
        )


@dataclass
class ConversationHistory:
    """
    Complete conversation history for a session.
    
    Attributes:
        entries: List of conversation entries
        session_id: The session this history belongs to
    """
    entries: List[ConversationEntry] = field(default_factory=list)
    session_id: str = ""
    
    def add_entry(self, role: ConversationRole, content: str) -> ConversationEntry:
        """
        Add a new conversation entry.
        
        Args:
            role: The role of the speaker
            content: The message content
            
        Returns:
            The created ConversationEntry
        """
        entry = ConversationEntry(
            role=role,
            content=content,
            timestamp=datetime.now(),
            session_id=self.session_id
        )
        self.entries.append(entry)
        return entry
    
    def get_recent_entries(self, count: int = 5) -> List[ConversationEntry]:
        """
        Get the most recent conversation entries.
        
        Args:
            count: Number of recent entries to return
            
        Returns:
            List of recent ConversationEntry objects
        """
        return self.entries[-count:] if self.entries else []
    
    def get_user_entries(self) -> List[ConversationEntry]:
        """Get all user entries"""
        return [entry for entry in self.entries if entry.role == ConversationRole.USER]
    
    def get_assistant_entries(self) -> List[ConversationEntry]:
        """Get all assistant entries"""
        return [entry for entry in self.entries if entry.role == ConversationRole.ASSISTANT]
    
    def get_last_user_message(self) -> Optional[ConversationEntry]:
        """Get the last message from the user"""
        user_entries = self.get_user_entries()
        return user_entries[-1] if user_entries else None
    
    def get_last_assistant_message(self) -> Optional[ConversationEntry]:
        """Get the last message from the assistant"""
        assistant_entries = self.get_assistant_entries()
        return assistant_entries[-1] if assistant_entries else None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ConversationHistory":
        """Create from dictionary"""
        entries = [ConversationEntry.from_dict(entry_data) for entry_data in data.get("entries", [])]
        return cls(
            entries=entries,
            session_id=data.get("session_id", "")
        )
    
    def __len__(self) -> int:
        """Return the number of entries"""
        return len(self.entries)
    
    def is_empty(self) -> bool:
        """Check if the conversation history is empty"""
        return len(self.entries) == 0
