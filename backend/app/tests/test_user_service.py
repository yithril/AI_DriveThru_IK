"""
Unit tests for User Service
"""

import pytest
from app.services.user_service import UserService
from app.models.user import User
from app.dto import UserCreateDto


@pytest.fixture
async def db():
    """Initialize test database"""
    from tortoise import Tortoise
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={'models': ['app.models']}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def user_service(db):
    return UserService()


class TestUserService:
    """Test User Service operations"""
    
    async def test_create_user(self, db, user_service):
        """Test creating a user"""
        data = UserCreateDto(
            email="test@example.com",
            name="John Doe"
        )
        
        user = await user_service.create(data)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "John Doe"
    
    async def test_get_by_id(self, db, user_service):
        """Test getting user by ID"""
        # Create a user first
        created_user = await User.create(
            email="get@example.com",
            name="Jane Smith"
        )
        
        # Get by ID
        found_user = await user_service.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.email == "get@example.com"
        assert found_user.name == "Jane Smith"
    
    async def test_get_by_id_not_found(self, db, user_service):
        """Test getting non-existent user"""
        result = await user_service.get_by_id(999)
        assert result is None
    
    async def test_get_by_email(self, db, user_service):
        """Test getting user by email"""
        # Create a user first
        await User.create(
            email="email@example.com",
            name="Email Test"
        )
        
        # Get by email
        found_user = await user_service.get_by_email("email@example.com")
        
        assert found_user is not None
        assert found_user.email == "email@example.com"
        assert found_user.name == "Email Test"
    
    async def test_get_by_email_not_found(self, db, user_service):
        """Test getting non-existent user by email"""
        result = await user_service.get_by_email("nonexistent@example.com")
        assert result is None
    
    async def test_delete_user(self, db, user_service):
        """Test deleting a user"""
        # Create a user
        created_user = await User.create(
            email="delete@example.com",
            name="Delete Test"
        )
        
        # Delete it
        result = await user_service.delete(created_user.id)
        
        assert result.success is True
        assert "deleted successfully" in result.message
        
        # Verify it's deleted
        deleted_user = await user_service.get_by_id(created_user.id)
        assert deleted_user is None
    
    async def test_delete_user_not_found(self, db, user_service):
        """Test deleting non-existent user"""
        result = await user_service.delete(999)
        assert result.success is False
        assert "not found" in result.message
