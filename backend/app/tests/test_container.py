"""
Test the DI Container integration
"""

import pytest
from app.core.container import Container


@pytest.fixture
def container():
    """Create container instance"""
    container = Container()
    container.config.from_dict({
        "postgres_url": "sqlite://:memory:"
    })
    return container


class TestContainer:
    """Test DI Container functionality"""
    
    def test_container_creation(self, container):
        """Test container can be created"""
        assert container is not None
        assert container.config is not None
    
    def test_restaurant_service_provider(self, container):
        """Test restaurant service can be provided"""
        service = container.restaurant_service()
        assert service is not None
        from app.services.restaurant_service import RestaurantService
        assert isinstance(service, RestaurantService)
    
    def test_postgres_service_provider(self, container):
        """Test postgres service can be provided"""
        service = container.postgres_service()
        assert service is not None
        from app.services.database.postgres_service import PostgresService
        assert isinstance(service, PostgresService)
    
    async def test_restaurant_service_crud_integration(self, container):
        """Test restaurant service works through container"""
        # Initialize database
        postgres_service = container.postgres_service()
        await postgres_service.initialize()
        await postgres_service.generate_schema()
        
        # Get restaurant service from container
        restaurant_service = container.restaurant_service()
        
        # Test CRUD operations
        from app.dto import RestaurantCreateDto
        data = RestaurantCreateDto(
            name="Container Test Restaurant",
            description="Testing DI container",
            address="123 Container St",
            phone="555-CONTAINER",
            primary_color="#FF0000",
            secondary_color="#00FF00"
        )
        
        # Create
        restaurant = await restaurant_service.create(data)
        assert restaurant.id is not None
        assert restaurant.name == "Container Test Restaurant"
        
        # Read
        retrieved = await restaurant_service.get_by_id(restaurant.id)
        assert retrieved is not None
        assert retrieved.name == "Container Test Restaurant"
        
        # Update
        from app.dto import RestaurantUpdateDto
        update_data = RestaurantUpdateDto(name="Updated Container Restaurant")
        updated = await restaurant_service.update(restaurant.id, update_data)
        assert updated.name == "Updated Container Restaurant"
        
        # Delete
        deleted = await restaurant_service.delete(restaurant.id)
        assert deleted.success is True
        
        # Verify deletion
        not_found = await restaurant_service.get_by_id(restaurant.id)
        assert not_found is None
        
        # Cleanup
        await postgres_service.close()
