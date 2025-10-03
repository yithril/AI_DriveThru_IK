"""
Tortoise ORM configuration for Aerich migrations
"""

# Use the actual database URL for migrations
# This should match your .env file: postgresql://postgres:postgres@localhost:5433/ai_drivethru
TORTOISE_ORM = {
    "connections": {"default": "postgres://postgres:postgres@localhost:5433/ai_drivethru"},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
