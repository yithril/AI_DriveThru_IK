"""
Unit tests for Command History
"""

import pytest
from datetime import datetime
from app.core.session.command_history import (
    CommandHistory,
    Command,
    CommandType,
    CommandStatus
)


class TestCommand:
    """Tests for Command dataclass"""
    
    def test_command_creation(self):
        """Test creating a command"""
        cmd = Command(
            command_type=CommandType.ADD_ITEM,
            timestamp=datetime.now(),
            status=CommandStatus.SUCCESS,
            item_name="Burger",
            item_id=1,
            quantity=2,
            modifiers=["no pickles", "extra cheese"],
            user_input="I want two burgers with no pickles and extra cheese",
            result_message="Added 2x Burger to order"
        )
        
        assert cmd.command_type == CommandType.ADD_ITEM
        assert cmd.status == CommandStatus.SUCCESS
        assert cmd.item_name == "Burger"
        assert cmd.quantity == 2
        assert len(cmd.modifiers) == 2
    
    def test_command_repr(self):
        """Test command string representation"""
        cmd = Command(
            command_type=CommandType.ADD_ITEM,
            timestamp=datetime.now(),
            status=CommandStatus.SUCCESS,
            item_name="Burger",
            quantity=2
        )
        
        repr_str = repr(cmd)
        assert "add_item" in repr_str  # Enum value, not name
        assert "Burger" in repr_str
        assert "qty=2" in repr_str


class TestCommandHistory:
    """Tests for CommandHistory"""
    
    def test_initialization(self):
        """Test creating empty command history"""
        history = CommandHistory()
        
        assert history.count() == 0
        assert history.get_last_command() is None
        assert history.get_all_commands() == []
    
    def test_add_command(self):
        """Test adding a command to history"""
        history = CommandHistory()
        
        cmd = history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger",
            item_id=1,
            quantity=1
        )
        
        assert history.count() == 1
        assert cmd.command_type == CommandType.ADD_ITEM
        assert cmd.item_name == "Burger"
    
    def test_get_last_command(self):
        """Test getting the last command"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Fries"
        )
        
        last = history.get_last_command()
        assert last is not None
        assert last.item_name == "Fries"
    
    def test_get_last_successful_command(self):
        """Test getting last successful command"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.FAILED,
            item_name="Pizza"
        )
        
        last_success = history.get_last_successful_command()
        assert last_success is not None
        assert last_success.item_name == "Burger"
        assert last_success.status == CommandStatus.SUCCESS
    
    def test_get_last_command_of_type(self):
        """Test getting last command of specific type"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        history.add_command(
            command_type=CommandType.REMOVE_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Fries"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Shake"
        )
        
        last_add = history.get_last_command_of_type(CommandType.ADD_ITEM)
        assert last_add is not None
        assert last_add.item_name == "Shake"
        
        last_remove = history.get_last_command_of_type(CommandType.REMOVE_ITEM)
        assert last_remove is not None
        assert last_remove.item_name == "Fries"
    
    def test_get_last_add_command(self):
        """Test convenience method for getting last ADD command"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        history.add_command(
            command_type=CommandType.REMOVE_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Fries"
        )
        
        last_add = history.get_last_add_command()
        assert last_add is not None
        assert last_add.item_name == "Burger"
        assert last_add.command_type == CommandType.ADD_ITEM
    
    def test_find_commands_by_item_name(self):
        """Test finding commands by item name"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Cosmic Burger"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Galaxy Burger"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Fries"
        )
        
        # Find by partial match (case-insensitive)
        burger_commands = history.find_commands_by_item_name("burger")
        assert len(burger_commands) == 2
        assert all("burger" in cmd.item_name.lower() for cmd in burger_commands)
        
        # Find specific item
        cosmic_commands = history.find_commands_by_item_name("cosmic")
        assert len(cosmic_commands) == 1
        assert cosmic_commands[0].item_name == "Cosmic Burger"
    
    def test_get_successful_add_commands(self):
        """Test getting all successful ADD commands"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.FAILED,
            item_name="Pizza"
        )
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Fries"
        )
        
        history.add_command(
            command_type=CommandType.REMOVE_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Coke"
        )
        
        successful_adds = history.get_successful_add_commands()
        assert len(successful_adds) == 2
        assert all(cmd.command_type == CommandType.ADD_ITEM for cmd in successful_adds)
        assert all(cmd.status == CommandStatus.SUCCESS for cmd in successful_adds)
        assert successful_adds[0].item_name == "Burger"
        assert successful_adds[1].item_name == "Fries"
    
    def test_get_recent_commands(self):
        """Test getting recent commands"""
        history = CommandHistory()
        
        # Add 10 commands
        for i in range(10):
            history.add_command(
                command_type=CommandType.ADD_ITEM,
                status=CommandStatus.SUCCESS,
                item_name=f"Item{i}"
            )
        
        # Get last 5
        recent = history.get_recent_commands(limit=5)
        assert len(recent) == 5
        assert recent[0].item_name == "Item5"
        assert recent[-1].item_name == "Item9"
    
    def test_clear_history(self):
        """Test clearing command history"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger"
        )
        
        assert history.count() == 1
        
        history.clear()
        
        assert history.count() == 0
        assert history.get_last_command() is None
    
    def test_to_dict_serialization(self):
        """Test converting history to dictionary"""
        history = CommandHistory()
        
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Burger",
            item_id=1,
            quantity=2,
            modifiers=["no pickles"],
            user_input="Two burgers no pickles",
            result_message="Added 2x Burger",
            metadata={"price": 12.99}
        )
        
        dict_list = history.to_dict()
        
        assert len(dict_list) == 1
        assert dict_list[0]["command_type"] == "add_item"
        assert dict_list[0]["status"] == "success"
        assert dict_list[0]["item_name"] == "Burger"
        assert dict_list[0]["quantity"] == 2
        assert dict_list[0]["modifiers"] == ["no pickles"]
        assert dict_list[0]["metadata"]["price"] == 12.99
    
    def test_multiple_operations_scenario(self):
        """Test realistic scenario with multiple operations"""
        history = CommandHistory()
        
        # Customer adds burger
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Cosmic Burger",
            item_id=1,
            quantity=1,
            user_input="I want a burger"
        )
        
        # Customer modifies to 2
        history.add_command(
            command_type=CommandType.MODIFY_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Cosmic Burger",
            item_id=1,
            quantity=2,
            user_input="Actually make that two"
        )
        
        # Customer adds fries
        history.add_command(
            command_type=CommandType.ADD_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Galaxy Fries",
            item_id=2,
            quantity=1,
            user_input="And fries"
        )
        
        # Customer removes fries ("remove that")
        history.add_command(
            command_type=CommandType.REMOVE_ITEM,
            status=CommandStatus.SUCCESS,
            item_name="Galaxy Fries",
            item_id=2,
            user_input="Remove that"
        )
        
        # Verify history
        assert history.count() == 4
        
        # Last command should be REMOVE
        last = history.get_last_command()
        assert last.command_type == CommandType.REMOVE_ITEM
        assert last.item_name == "Galaxy Fries"
        
        # Last ADD should be fries
        last_add = history.get_last_add_command()
        assert last_add.item_name == "Galaxy Fries"
        
        # Successful adds should be 2 (burger and fries)
        successful_adds = history.get_successful_add_commands()
        assert len(successful_adds) == 2
    
    def test_empty_history_edge_cases(self):
        """Test edge cases with empty history"""
        history = CommandHistory()
        
        assert history.get_last_command() is None
        assert history.get_last_successful_command() is None
        assert history.get_last_add_command() is None
        assert history.get_last_command_of_type(CommandType.ADD_ITEM) is None
        assert history.find_commands_by_item_name("burger") == []
        assert history.get_successful_add_commands() == []
        assert history.get_recent_commands() == []
        assert history.to_dict() == []

