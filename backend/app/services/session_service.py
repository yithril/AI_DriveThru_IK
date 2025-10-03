"""
Session Service - Redis-based session management for drive-thru workflow
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing drive-thru sessions in Redis.
    Sessions represent active customers at the drive-thru window.
    """
    
    def __init__(self, redis_service):
        """
        Initialize with Redis service dependency
        
        Args:
            redis_service: Redis service instance
        """
        self.redis = redis_service
    
    async def is_redis_available(self) -> bool:
        """Check if Redis is available"""
        try:
            # Simple ping test
            await self.redis.get("health_check")
            return True
        except Exception as e:
            logger.error(f"Redis not available: {e}")
            return False
    
    async def create_session(
        self, 
        restaurant_id: int, 
        ttl: int = 900  # 15 minutes default
    ) -> Optional[str]:
        """
        Create a new drive-thru session
        
        Args:
            restaurant_id: Restaurant ID
            ttl: Time to live in seconds
            
        Returns:
            str: Session ID if successful, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot create session")
            return None
        
        try:
            # Generate unique session ID
            session_id = f"session_{int(datetime.now().timestamp() * 1000)}"
            
            # Create session data
            session_data = {
                "id": session_id,
                "restaurant_id": restaurant_id,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "state": "thinking",  # Start in thinking state
                "order_id": None,  # Will be set when order is created
                "last_activity": datetime.now().isoformat()
            }
            
            # Store in Redis
            success = await self.redis.set_json(f"session:{session_id}", session_data, expire=ttl)
            
            if success:
                # Set as current session
                await self.redis.set("current:session", session_id, ttl)
                logger.info(f"Created session {session_id} for restaurant {restaurant_id}")
                return session_id
            else:
                logger.error(f"Failed to store session {session_id} in Redis")
                return None
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data by ID
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            dict: Session data if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get session")
            return None
        
        try:
            return await self.redis.get_json(f"session:{session_id}")
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get the current active session
        
        Returns:
            dict: Current session data if exists, None otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get current session")
            return None
        
        try:
            current_session_id = await self.redis.get("current:session")
            if current_session_id:
                return await self.get_session(current_session_id)
            return None
        except Exception as e:
            logger.error(f"Error getting current session: {e}")
            return None
    
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any],
        ttl: int = 900
    ) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID to update
            updates: Data to merge into session
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot update session")
            return False
        
        try:
            # Get existing session data
            session_data = await self.get_session(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found for update")
                return False
            
            # Merge updates
            session_data.update(updates)
            session_data["last_activity"] = datetime.now().isoformat()
            
            # Store updated data
            success = await self.redis.set_json(f"session:{session_id}", session_data, expire=ttl)
            
            if success:
                logger.info(f"Updated session {session_id}")
                return True
            else:
                logger.error(f"Failed to update session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    async def set_session_state(self, session_id: str, state: str) -> bool:
        """
        Set the conversation state for a session
        
        Args:
            session_id: Session ID
            state: New state (thinking, ordering, clarifying, confirming, closing, idle)
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.update_session(session_id, {"state": state})
    
    async def link_order_to_session(self, session_id: str, order_id: str) -> bool:
        """
        Link an order to a session
        
        Args:
            session_id: Session ID
            order_id: Order ID to link
            
        Returns:
            bool: True if successful, False otherwise
        """
        return await self.update_session(session_id, {"order_id": order_id})
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot delete session")
            return False
        
        try:
            # Check if this is the current session
            current_session_id = await self.redis.get("current:session")
            if current_session_id == session_id:
                await self.redis.delete("current:session")
            
            # Delete session data
            success = await self.redis.delete(f"session:{session_id}")
            
            if success:
                logger.info(f"Deleted session {session_id}")
                return True
            else:
                logger.error(f"Failed to delete session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def clear_current_session(self) -> bool:
        """
        Clear the current active session
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot clear current session")
            return False
        
        try:
            return await self.redis.delete("current:session")
        except Exception as e:
            logger.error(f"Error clearing current session: {e}")
            return False
    
    async def add_conversation_entry(
        self, 
        session_id: str, 
        user_input: str, 
        ai_response: str,
        ttl: int = 900
    ) -> bool:
        """
        Add a conversation entry to session history
        
        Args:
            session_id: Session ID
            user_input: What the user said
            ai_response: What the AI responded
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot add conversation entry")
            return False
        
        try:
            # Get existing conversation history
            conversation_key = f"session:{session_id}:conversation"
            existing_history = await self.redis.get_json(conversation_key) or []
            
            # Add new entry
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "ai_response": ai_response
            }
            existing_history.append(new_entry)
            
            # Store updated history
            success = await self.redis.set_json(conversation_key, existing_history, expire=ttl)
            
            if success:
                logger.info(f"Added conversation entry for session {session_id}")
                return True
            else:
                logger.error(f"Failed to store conversation history for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding conversation entry for session {session_id}: {e}")
            return False
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of conversation entries
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get conversation history")
            return []
        
        try:
            conversation_key = f"session:{session_id}:conversation"
            return await self.redis.get_json(conversation_key) or []
        except Exception as e:
            logger.error(f"Error getting conversation history for session {session_id}: {e}")
            return []
    
    async def get_command_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get command history for a session (subset of conversation focused on actions)
        
        Args:
            session_id: Session ID
            
        Returns:
            List of command entries
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get command history")
            return []
        
        try:
            command_key = f"session:{session_id}:commands"
            return await self.redis.get_json(command_key) or []
        except Exception as e:
            logger.error(f"Error getting command history for session {session_id}: {e}")
            return []
    
    async def add_command_entry(
        self, 
        session_id: str, 
        command_type: str, 
        command_data: Dict[str, Any],
        ttl: int = 900
    ) -> bool:
        """
        Add a command entry to session history
        
        Args:
            session_id: Session ID
            command_type: Type of command (add_item, remove_item, etc.)
            command_data: Command-specific data
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot add command entry")
            return False
        
        try:
            # Get existing command history
            command_key = f"session:{session_id}:commands"
            existing_commands = await self.redis.get_json(command_key) or []
            
            # Add new command entry
            new_command = {
                "timestamp": datetime.now().isoformat(),
                "command_type": command_type,
                "command_data": command_data
            }
            existing_commands.append(new_command)
            
            # Store updated command history
            success = await self.redis.set_json(command_key, existing_commands, expire=ttl)
            
            if success:
                logger.info(f"Added command entry for session {session_id}: {command_type}")
                return True
            else:
                logger.error(f"Failed to store command history for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding command entry for session {session_id}: {e}")
            return False
    
    async def add_performance_log(
        self, 
        session_id: str, 
        step_name: str, 
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: int = 900
    ) -> bool:
        """
        Add a performance timing entry to session logs
        
        Args:
            session_id: Session ID
            step_name: Name of the step (e.g., 'speech_to_text', 'intent_classification', 'add_item_workflow')
            duration_ms: Duration in milliseconds
            metadata: Additional metadata about the step
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot add performance log")
            return False
        
        try:
            # Get existing performance logs
            performance_key = f"session:{session_id}:performance"
            existing_logs = await self.redis.get_json(performance_key) or []
            
            # Add new performance log
            new_log = {
                "timestamp": datetime.now().isoformat(),
                "step_name": step_name,
                "duration_ms": round(duration_ms, 2),
                "metadata": metadata or {}
            }
            existing_logs.append(new_log)
            
            # Store updated performance logs
            success = await self.redis.set_json(performance_key, existing_logs, expire=ttl)
            
            if success:
                logger.info(f"Performance log for session {session_id}: {step_name} took {duration_ms}ms")
                return True
            else:
                logger.error(f"Failed to store performance log for session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding performance log for session {session_id}: {e}")
            return False
    
    async def get_performance_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get performance logs for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of performance log entries
        """
        if not await self.is_redis_available():
            logger.error("Redis not available - cannot get performance logs")
            return []
        
        try:
            performance_key = f"session:{session_id}:performance"
            return await self.redis.get_json(performance_key) or []
        except Exception as e:
            logger.error(f"Error getting performance logs for session {session_id}: {e}")
            return []