#!/usr/bin/env python3
"""
Clear database script - removes all data from the database
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.ingredient import Ingredient
from app.models.menu_item import MenuItem
from app.models.menu_item_ingredient import MenuItemIngredient


async def init_database():
    """Initialize database connection"""
    # Get database URL from environment
    db_url = os.getenv('POSTGRES_URL', 'postgres://postgres:postgres@localhost:5433/ai_drivethru')
    
    # Convert postgresql:// to postgres:// for Tortoise ORM
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgres://', 1)
    
    print(f"Connecting to database: {db_url}")
    
    await Tortoise.init(
        db_url=db_url,
        modules={'models': ['app.models']}
    )


async def close_database():
    """Close database connections"""
    await Tortoise.close_connections()


async def clear_database():
    """Clear all data from the database"""
    print("Clearing database...")
    
    # Delete in reverse order of dependencies
    print("   Deleting menu item ingredients...")
    await MenuItemIngredient.all().delete()
    
    print("   Deleting menu items...")
    await MenuItem.all().delete()
    
    print("   Deleting ingredients...")
    await Ingredient.all().delete()
    
    print("   Deleting categories...")
    await Category.all().delete()
    
    print("   Deleting restaurants...")
    await Restaurant.all().delete()
    
    print("Database cleared successfully!")


async def main():
    """Main clear function"""
    print("Starting database clear...")
    
    try:
        # Initialize database
        await init_database()
        print("Database connected")
        
        # Clear all data
        await clear_database()
        
        print("\nDatabase cleared successfully!")
        print("All data has been removed from the database")
        
    except Exception as e:
        print(f"Error during clear: {e}")
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
