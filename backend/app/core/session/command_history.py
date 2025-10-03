"""
Command History - Tracks all commands in a session

Enables "undo", "that", "last item" references by maintaining
an ordered history of all commands executed in the session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class CommandType(Enum):
    """Types of commands that can be executed"""
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"
    MODIFY_ITEM = "modify_item"
    CLEAR_ORDER = "clear_order"
    CONFIRM_ORDER = "confirm_order"


class CommandStatus(Enum):
    """Status of command execution"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CLARIFICATION_NEEDED = "clarification_needed"


@dataclass
class Command:
    """
    Single command in the history.
    
    Represents one user action (add item, remove item, etc.)
    """
    command_type: CommandType
    timestamp: datetime
    status: CommandStatus
    
    # Item details (if applicable)
    item_name: Optional[str] = None
    item_id: Optional[int] = None
    quantity: int = 1
    modifiers: List[str] = field(default_factory=list)
    
    # Execution details
    user_input: Optional[str] = None
    result_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"Command({self.command_type.value}, {self.item_name}, qty={self.quantity}, status={self.status.value})"


class CommandHistory:
    """
    Maintains ordered history of all commands in a session.
    
    Supports:
    - Adding new commands
    - Querying last command
    - Querying last command of specific type
    - Finding commands by item name
    - Getting full history
    """
    
    def __init__(self):
        """Initialize empty command history"""
        self.commands: List[Command] = []
    
    def add_command(
        self,
        command_type: CommandType,
        status: CommandStatus,
        item_name: Optional[str] = None,
        item_id: Optional[int] = None,
        quantity: int = 1,
        modifiers: Optional[List[str]] = None,
        user_input: Optional[str] = None,
        result_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Command:
        """
        Add a command to the history.
        
        Args:
            command_type: Type of command
            status: Execution status
            item_name: Name of item (if applicable)
            item_id: ID of item (if applicable)
            quantity: Quantity
            modifiers: List of modifiers
            user_input: Original user input
            result_message: Result message
            metadata: Additional metadata
            
        Returns:
            The created Command object
        """
        command = Command(
            command_type=command_type,
            timestamp=datetime.now(),
            status=status,
            item_name=item_name,
            item_id=item_id,
            quantity=quantity,
            modifiers=modifiers or [],
            user_input=user_input,
            result_message=result_message,
            metadata=metadata or {}
        )
        
        self.commands.append(command)
        return command
    
    def get_last_command(self) -> Optional[Command]:
        """
        Get the most recent command.
        
        Returns:
            Last command or None if history is empty
        """
        return self.commands[-1] if self.commands else None
    
    def get_last_successful_command(self) -> Optional[Command]:
        """
        Get the most recent successful command.
        
        Returns:
            Last successful command or None
        """
        for command in reversed(self.commands):
            if command.status == CommandStatus.SUCCESS:
                return command
        return None
    
    def get_last_command_of_type(self, command_type: CommandType) -> Optional[Command]:
        """
        Get the most recent command of a specific type.
        
        Args:
            command_type: Type of command to find
            
        Returns:
            Last command of that type or None
        """
        for command in reversed(self.commands):
            if command.command_type == command_type:
                return command
        return None
    
    def get_last_add_command(self) -> Optional[Command]:
        """
        Get the most recent ADD_ITEM command.
        Convenience method for common use case.
        
        Returns:
            Last ADD_ITEM command or None
        """
        return self.get_last_command_of_type(CommandType.ADD_ITEM)
    
    def find_commands_by_item_name(self, item_name: str) -> List[Command]:
        """
        Find all commands involving a specific item.
        
        Args:
            item_name: Name of item to search for (case-insensitive)
            
        Returns:
            List of commands involving that item
        """
        item_name_lower = item_name.lower()
        return [
            cmd for cmd in self.commands
            if cmd.item_name and item_name_lower in cmd.item_name.lower()
        ]
    
    def get_successful_add_commands(self) -> List[Command]:
        """
        Get all successful ADD_ITEM commands.
        Useful for showing what's in the order.
        
        Returns:
            List of successful ADD_ITEM commands
        """
        return [
            cmd for cmd in self.commands
            if cmd.command_type == CommandType.ADD_ITEM and cmd.status == CommandStatus.SUCCESS
        ]
    
    def get_all_commands(self) -> List[Command]:
        """
        Get full command history.
        
        Returns:
            All commands in chronological order
        """
        return self.commands.copy()
    
    def get_recent_commands(self, limit: int = 5) -> List[Command]:
        """
        Get recent commands.
        
        Args:
            limit: Number of recent commands to return
            
        Returns:
            Recent commands (most recent last)
        """
        return self.commands[-limit:] if self.commands else []
    
    def clear(self):
        """Clear all command history"""
        self.commands = []
    
    def count(self) -> int:
        """Get total number of commands"""
        return len(self.commands)
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convert history to dictionary for serialization.
        
        Returns:
            List of command dictionaries
        """
        return [
            {
                "command_type": cmd.command_type.value,
                "timestamp": cmd.timestamp.isoformat(),
                "status": cmd.status.value,
                "item_name": cmd.item_name,
                "item_id": cmd.item_id,
                "quantity": cmd.quantity,
                "modifiers": cmd.modifiers,
                "user_input": cmd.user_input,
                "result_message": cmd.result_message,
                "metadata": cmd.metadata
            }
            for cmd in self.commands
        ]

