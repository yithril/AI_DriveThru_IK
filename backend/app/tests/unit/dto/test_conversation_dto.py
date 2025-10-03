"""
Unit tests for conversation DTOs
"""

import pytest
from datetime import datetime
from app.dto.conversation_dto import ConversationEntry, ConversationHistory, ConversationRole


class TestConversationEntry:
    """Test ConversationEntry dataclass"""
    
    def test_create_conversation_entry(self):
        """Test creating a conversation entry"""
        entry = ConversationEntry(
            role=ConversationRole.USER,
            content="Hello, I'd like to order a burger",
            timestamp=datetime.now(),
            session_id="session_123"
        )
        
        assert entry.role == ConversationRole.USER
        assert entry.content == "Hello, I'd like to order a burger"
        assert entry.session_id == "session_123"
    
    def test_conversation_entry_validation(self):
        """Test validation of conversation entry"""
        # Test empty content
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ConversationEntry(
                role=ConversationRole.USER,
                content="",
                timestamp=datetime.now(),
                session_id="session_123"
            )
        
        # Test empty session_id
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            ConversationEntry(
                role=ConversationRole.USER,
                content="Hello",
                timestamp=datetime.now(),
                session_id=""
            )
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        timestamp = datetime.now()
        entry = ConversationEntry(
            role=ConversationRole.ASSISTANT,
            content="I can help you with that",
            timestamp=timestamp,
            session_id="session_123"
        )
        
        result = entry.to_dict()
        expected = {
            "role": "assistant",
            "content": "I can help you with that",
            "timestamp": timestamp.isoformat(),
            "session_id": "session_123"
        }
        
        assert result == expected
    
    def test_from_dict(self):
        """Test creating from dictionary"""
        timestamp = datetime.now()
        data = {
            "role": "user",
            "content": "Hello",
            "timestamp": timestamp.isoformat(),
            "session_id": "session_123"
        }
        
        entry = ConversationEntry.from_dict(data)
        
        assert entry.role == ConversationRole.USER
        assert entry.content == "Hello"
        assert entry.timestamp == timestamp
        assert entry.session_id == "session_123"


class TestConversationHistory:
    """Test ConversationHistory dataclass"""
    
    def test_create_empty_conversation_history(self):
        """Test creating an empty conversation history"""
        history = ConversationHistory(session_id="session_123")
        
        assert history.session_id == "session_123"
        assert len(history.entries) == 0
        assert history.is_empty()
    
    def test_add_entry(self):
        """Test adding entries to conversation history"""
        history = ConversationHistory(session_id="session_123")
        
        entry = history.add_entry(ConversationRole.USER, "Hello")
        
        assert len(history.entries) == 1
        assert entry.role == ConversationRole.USER
        assert entry.content == "Hello"
        assert entry.session_id == "session_123"
    
    def test_get_recent_entries(self):
        """Test getting recent entries"""
        history = ConversationHistory(session_id="session_123")
        
        # Add multiple entries
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi there")
        history.add_entry(ConversationRole.USER, "I want a burger")
        history.add_entry(ConversationRole.ASSISTANT, "What kind of burger?")
        
        # Get last 2 entries
        recent = history.get_recent_entries(2)
        assert len(recent) == 2
        assert recent[0].content == "I want a burger"
        assert recent[1].content == "What kind of burger?"
    
    def test_get_user_entries(self):
        """Test getting only user entries"""
        history = ConversationHistory(session_id="session_123")
        
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi")
        history.add_entry(ConversationRole.USER, "I want food")
        
        user_entries = history.get_user_entries()
        assert len(user_entries) == 2
        assert all(entry.role == ConversationRole.USER for entry in user_entries)
    
    def test_get_assistant_entries(self):
        """Test getting only assistant entries"""
        history = ConversationHistory(session_id="session_123")
        
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi")
        history.add_entry(ConversationRole.USER, "I want food")
        history.add_entry(ConversationRole.ASSISTANT, "What would you like?")
        
        assistant_entries = history.get_assistant_entries()
        assert len(assistant_entries) == 2
        assert all(entry.role == ConversationRole.ASSISTANT for entry in assistant_entries)
    
    def test_get_last_user_message(self):
        """Test getting the last user message"""
        history = ConversationHistory(session_id="session_123")
        
        # Empty history
        assert history.get_last_user_message() is None
        
        # Add messages
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi")
        history.add_entry(ConversationRole.USER, "I want food")
        
        last_user = history.get_last_user_message()
        assert last_user is not None
        assert last_user.content == "I want food"
    
    def test_get_last_assistant_message(self):
        """Test getting the last assistant message"""
        history = ConversationHistory(session_id="session_123")
        
        # Empty history
        assert history.get_last_assistant_message() is None
        
        # Add messages
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi")
        history.add_entry(ConversationRole.USER, "I want food")
        history.add_entry(ConversationRole.ASSISTANT, "What would you like?")
        
        last_assistant = history.get_last_assistant_message()
        assert last_assistant is not None
        assert last_assistant.content == "What would you like?"
    
    def test_to_dict(self):
        """Test converting to dictionary"""
        history = ConversationHistory(session_id="session_123")
        history.add_entry(ConversationRole.USER, "Hello")
        history.add_entry(ConversationRole.ASSISTANT, "Hi")
        
        result = history.to_dict()
        
        assert result["session_id"] == "session_123"
        assert len(result["entries"]) == 2
        assert result["entries"][0]["role"] == "user"
        assert result["entries"][0]["content"] == "Hello"
        assert result["entries"][1]["role"] == "assistant"
        assert result["entries"][1]["content"] == "Hi"
    
    def test_from_dict(self):
        """Test creating from dictionary"""
        data = {
            "session_id": "session_123",
            "entries": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2025-01-01T12:00:00",
                    "session_id": "session_123"
                },
                {
                    "role": "assistant",
                    "content": "Hi",
                    "timestamp": "2025-01-01T12:01:00",
                    "session_id": "session_123"
                }
            ]
        }
        
        history = ConversationHistory.from_dict(data)
        
        assert history.session_id == "session_123"
        assert len(history.entries) == 2
        assert history.entries[0].content == "Hello"
        assert history.entries[1].content == "Hi"
    
    def test_length_and_empty(self):
        """Test length and empty checks"""
        history = ConversationHistory(session_id="session_123")
        
        assert len(history) == 0
        assert history.is_empty()
        
        history.add_entry(ConversationRole.USER, "Hello")
        
        assert len(history) == 1
        assert not history.is_empty()
