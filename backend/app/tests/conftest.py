"""
Pytest configuration and fixtures

Auto-discovered by pytest for all tests.
"""

# Import all fixtures from fixtures module
from app.tests.fixtures.database_fixtures import (
    test_db,
    test_restaurant,
    test_categories,
    test_ingredients,
    test_menu_items,
    test_services
)

__all__ = [
    "test_db",
    "test_restaurant", 
    "test_categories",
    "test_ingredients",
    "test_menu_items",
    "test_services"
]

