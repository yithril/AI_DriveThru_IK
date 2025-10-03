"""
Tortoise ORM database configuration
"""

from tortoise import Tortoise
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize Tortoise ORM database connection"""
    try:
        logger.info(f"Initializing database with URL: {settings.postgres_url}")
        await Tortoise.init(
            db_url=settings.postgres_url,
            modules={'models': ['app.models']}
        )
        logger.info("Tortoise ORM initialized successfully")
        
        await Tortoise.generate_schemas()
        logger.info("Database schemas generated successfully")
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


async def close_database():
    """Close database connections"""
    await Tortoise.close_connections()
    logger.info("Database connections closed")


# Database dependency for FastAPI
async def get_db():
    """Get database connection for FastAPI dependency injection"""
    return Tortoise.get_connection("default")
