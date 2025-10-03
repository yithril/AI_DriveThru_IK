"""
Unit tests for SessionService - Redis-based session management
"""

import pytest
from unittest.mock import AsyncMock, Mock
from app.services.session_service import SessionService


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing"""
    redis_service = AsyncMock()
    redis_service.get.return_value = None
    redis_service.set.return_value = True
    redis_service.set_json.return_value = True
    redis_service.get_json.return_value = None
    redis_service.delete.return_value = True
    return redis_service


@pytest.fixture
def session_service(mock_redis_service):
    """Fixture for SessionService"""
    return SessionService(mock_redis_service)


class TestSessionService:
    """Test SessionService operations"""

    async def test_is_redis_available_success(self, session_service, mock_redis_service):
        """Test Redis availability check when Redis is available"""
        mock_redis_service.get.return_value = "ok"
        
        result = await session_service.is_redis_available()
        
        assert result is True
        mock_redis_service.get.assert_called_once_with("health_check")

    async def test_is_redis_available_failure(self, session_service, mock_redis_service):
        """Test Redis availability check when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Connection failed")
        
        result = await session_service.is_redis_available()
        
        assert result is False

    async def test_create_session_success(self, session_service, mock_redis_service):
        """Test successful session creation"""
        mock_redis_service.set_json.return_value = True
        mock_redis_service.set.return_value = True
        
        session_id = await session_service.create_session(
            restaurant_id=1
        )
        
        assert session_id is not None
        assert session_id.startswith("session_")
        
        # Verify Redis calls
        mock_redis_service.set_json.assert_called_once()
        mock_redis_service.set.assert_called_once()
        
        # Check the session data structure
        call_args = mock_redis_service.set_json.call_args
        session_data = call_args[0][1]  # Second argument is the data
        assert session_data["restaurant_id"] == 1
        assert session_data["status"] == "active"
        assert session_data["state"] == "thinking"

    async def test_create_session_redis_unavailable(self, session_service, mock_redis_service):
        """Test session creation when Redis is unavailable"""
        mock_redis_service.get.side_effect = Exception("Redis unavailable")
        
        session_id = await session_service.create_session(restaurant_id=1)
        
        assert session_id is None

    async def test_get_session_success(self, session_service, mock_redis_service):
        """Test successful session retrieval"""
        expected_data = {
            "id": "session_123",
            "restaurant_id": 1,
            "customer_name": "John Doe",
            "status": "active"
        }
        mock_redis_service.get_json.return_value = expected_data
        
        result = await session_service.get_session("session_123")
        
        assert result == expected_data
        mock_redis_service.get_json.assert_called_once_with("session:session_123")

    async def test_get_session_not_found(self, session_service, mock_redis_service):
        """Test session retrieval when session doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        result = await session_service.get_session("nonexistent")
        
        assert result is None

    async def test_get_current_session_success(self, session_service, mock_redis_service):
        """Test successful current session retrieval"""
        expected_data = {
            "id": "session_123",
            "restaurant_id": 1,
            "customer_name": "John Doe",
            "status": "active"
        }
        
        # Mock the get method to return different values for different keys
        def mock_get(key):
            if key == "health_check":
                return "ok"
            elif key == "current:session":
                return "session_123"
            return None
        
        mock_redis_service.get.side_effect = mock_get
        mock_redis_service.get_json.return_value = expected_data
        
        result = await session_service.get_current_session()
        
        assert result == expected_data
        mock_redis_service.get_json.assert_called_once_with("session:session_123")

    async def test_get_current_session_no_current(self, session_service, mock_redis_service):
        """Test current session retrieval when no current session exists"""
        mock_redis_service.get.return_value = None
        
        result = await session_service.get_current_session()
        
        assert result is None

    async def test_update_session_success(self, session_service, mock_redis_service):
        """Test successful session update"""
        existing_data = {
            "id": "session_123",
            "restaurant_id": 1,
            "customer_name": "John Doe",
            "status": "active",
            "state": "thinking"
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        updates = {"state": "ordering", "customer_name": "Jane Doe"}
        result = await session_service.update_session("session_123", updates)
        
        assert result is True
        
        # Verify the updated data
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]  # Second argument is the data
        assert updated_data["state"] == "ordering"
        assert updated_data["customer_name"] == "Jane Doe"
        assert "last_activity" in updated_data

    async def test_update_session_not_found(self, session_service, mock_redis_service):
        """Test session update when session doesn't exist"""
        mock_redis_service.get_json.return_value = None
        
        updates = {"state": "ordering"}
        result = await session_service.update_session("nonexistent", updates)
        
        assert result is False

    async def test_set_session_state(self, session_service, mock_redis_service):
        """Test setting session state"""
        existing_data = {
            "id": "session_123",
            "restaurant_id": 1,
            "status": "active",
            "state": "thinking"
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await session_service.set_session_state("session_123", "ordering")
        
        assert result is True
        
        # Verify the state was updated
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert updated_data["state"] == "ordering"

    async def test_link_order_to_session(self, session_service, mock_redis_service):
        """Test linking order to session"""
        existing_data = {
            "id": "session_123",
            "restaurant_id": 1,
            "status": "active"
        }
        mock_redis_service.get_json.return_value = existing_data
        mock_redis_service.set_json.return_value = True
        
        result = await session_service.link_order_to_session("session_123", "order_456")
        
        assert result is True
        
        # Verify the order was linked
        call_args = mock_redis_service.set_json.call_args
        updated_data = call_args[0][1]
        assert updated_data["order_id"] == "order_456"

    async def test_delete_session_success(self, session_service, mock_redis_service):
        """Test successful session deletion"""
        mock_redis_service.get.return_value = "session_123"  # Current session
        mock_redis_service.delete.return_value = True
        
        result = await session_service.delete_session("session_123")
        
        assert result is True
        mock_redis_service.delete.assert_any_call("current:session")
        mock_redis_service.delete.assert_any_call("session:session_123")

    async def test_delete_session_not_current(self, session_service, mock_redis_service):
        """Test deleting a session that is not the current session"""
        mock_redis_service.get.return_value = "session_456"  # Different current session
        mock_redis_service.delete.return_value = True
        
        result = await session_service.delete_session("session_123")
        
        assert result is True
        # Should not delete current:session since it's a different session
        mock_redis_service.delete.assert_called_once_with("session:session_123")

    async def test_clear_current_session(self, session_service, mock_redis_service):
        """Test clearing current session"""
        mock_redis_service.delete.return_value = True
        
        result = await session_service.clear_current_session()
        
        assert result is True
        mock_redis_service.delete.assert_called_once_with("current:session")

    async def test_redis_error_handling(self, session_service, mock_redis_service):
        """Test error handling when Redis operations fail"""
        mock_redis_service.get.side_effect = Exception("Redis error")
        
        # Test various operations that should handle Redis errors gracefully
        assert await session_service.is_redis_available() is False
        assert await session_service.create_session(restaurant_id=1) is None
        assert await session_service.get_session("test") is None
        assert await session_service.get_current_session() is None
        assert await session_service.update_session("test", {}) is False
        assert await session_service.delete_session("test") is False
        assert await session_service.clear_current_session() is False
