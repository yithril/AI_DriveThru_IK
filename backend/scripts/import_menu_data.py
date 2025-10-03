#!/usr/bin/env python3
"""
Import script for menu data from JSON file
Imports restaurants, categories, ingredients, and menu items
"""

import asyncio
import json
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
    await Tortoise.generate_schemas()


async def close_database():
    """Close database connections"""
    await Tortoise.close_connections()


async def import_restaurant(data):
    """Import restaurant data"""
    print(f"Importing restaurant: {data['name']}")
    
    # Check if restaurant already exists
    existing_restaurant = await Restaurant.get_or_none(name=data['name'])
    if existing_restaurant:
        print(f"Warning: Restaurant '{data['name']}' already exists (ID: {existing_restaurant.id})")
        return existing_restaurant
    
    restaurant = await Restaurant.create(
        id=1,  # Force restaurant ID to be 1
        name=data['name'],
        description=data.get('description', ''),
        primary_color=data['primary_color'],
        secondary_color=data['secondary_color'],
        logo_url=data.get('logo_url'),
        phone=data.get('phone'),
        hours=data.get('hours'),
        address=data.get('address'),
        is_active=data.get('is_active', True)
    )
    
    print(f"Created restaurant: {restaurant.name} (ID: {restaurant.id})")
    return restaurant


async def import_categories(categories_data, restaurant_id):
    """Import categories for a restaurant"""
    print(f"Importing {len(categories_data)} categories...")
    
    category_map = {}
    
    for cat_data in categories_data:
        # Check if category already exists for this restaurant
        existing_category = await Category.get_or_none(
            name=cat_data['name'],
            restaurant_id=restaurant_id
        )
        
        if existing_category:
            print(f"Warning: Category '{cat_data['name']}' already exists (ID: {existing_category.id})")
            category_map[cat_data['name']] = existing_category.id
            continue
        
        category = await Category.create(
            name=cat_data['name'],
            description=cat_data.get('description', ''),
            restaurant_id=restaurant_id,
            display_order=cat_data.get('display_order', 0),
            is_active=cat_data.get('is_active', True)
        )
        
        category_map[cat_data['name']] = category.id
        print(f"Created category: {category.name} (ID: {category.id})")
    
    return category_map


async def import_ingredients(ingredients_data, restaurant_id):
    """Import ingredients for a restaurant"""
    print(f"Importing {len(ingredients_data)} ingredients...")
    
    ingredient_map = {}
    
    for ing_data in ingredients_data:
        # Check if ingredient already exists for this restaurant
        existing_ingredient = await Ingredient.get_or_none(
            name=ing_data['name'],
            restaurant_id=restaurant_id
        )
        
        if existing_ingredient:
            print(f"Warning: Ingredient '{ing_data['name']}' already exists (ID: {existing_ingredient.id})")
            ingredient_map[ing_data['name']] = existing_ingredient.id
            continue
        
        ingredient = await Ingredient.create(
            name=ing_data['name'],
            description=ing_data.get('description', ''),
            restaurant_id=restaurant_id,
            is_allergen=ing_data.get('is_allergen', False),
            allergen_type=ing_data.get('allergen_type'),
            unit_cost=ing_data.get('unit_cost', 0.0)
        )
        
        ingredient_map[ing_data['name']] = ingredient.id
        print(f"Created ingredient: {ingredient.name} (ID: {ingredient.id})")
    
    return ingredient_map


async def import_menu_items(menu_items_data, restaurant_id, category_map):
    """Import menu items for a restaurant"""
    print(f"Importing {len(menu_items_data)} menu items...")
    
    menu_item_map = {}
    
    for item_data in menu_items_data:
        # Check if menu item already exists for this restaurant
        existing_item = await MenuItem.get_or_none(
            name=item_data['name'],
            restaurant_id=restaurant_id
        )
        
        if existing_item:
            print(f"Warning: Menu item '{item_data['name']}' already exists (ID: {existing_item.id})")
            menu_item_map[item_data['name']] = existing_item.id
            continue
        
        # Get category ID
        category_name = item_data['category_name']
        category_id = category_map.get(category_name)
        
        if not category_id:
            print(f"Warning: Category '{category_name}' not found for menu item '{item_data['name']}'")
            continue
        
        menu_item = await MenuItem.create(
            name=item_data['name'],
            description=item_data.get('description', ''),
            price=item_data['price'],
            image_url=item_data.get('image_url'),
            category_id=category_id,
            restaurant_id=restaurant_id,
            is_available=item_data.get('is_available', True),
            is_upsell=item_data.get('is_upsell', False),
            is_special=item_data.get('is_special', False),
            prep_time_minutes=item_data.get('prep_time_minutes', 10),
            display_order=item_data.get('sort_order', 0)
        )
        
        menu_item_map[item_data['name']] = menu_item.id
        print(f"Created menu item: {menu_item.name} (ID: {menu_item.id})")
    
    return menu_item_map


async def import_menu_item_ingredients(menu_item_ingredients_data, menu_item_map, ingredient_map):
    """Import menu item ingredients relationships"""
    print(f"Importing {len(menu_item_ingredients_data)} menu item ingredients...")
    
    # Track created relationships to avoid duplicates
    created_relationships = set()
    
    for rel_data in menu_item_ingredients_data:
        menu_item_name = rel_data['menu_item_name']
        ingredient_name = rel_data['ingredient_name']
        
        menu_item_id = menu_item_map.get(menu_item_name)
        ingredient_id = ingredient_map.get(ingredient_name)
        
        if not menu_item_id:
            print(f"Warning: Menu item '{menu_item_name}' not found for ingredient relationship")
            continue
            
        if not ingredient_id:
            print(f"Warning: Ingredient '{ingredient_name}' not found for menu item '{menu_item_name}'")
            continue
        
        # Check for duplicate relationship
        relationship_key = (menu_item_id, ingredient_id)
        if relationship_key in created_relationships:
            print(f"Warning: Skipping duplicate relationship: {menu_item_name} -> {ingredient_name}")
            continue
        
        try:
            await MenuItemIngredient.create(
                menu_item_id=menu_item_id,
                ingredient_id=ingredient_id,
                quantity=rel_data.get('quantity', 1),
                unit=rel_data.get('unit', 'piece'),
                is_optional=rel_data.get('is_optional', False),
                additional_cost=rel_data.get('additional_cost', 0.0)
            )
            
            created_relationships.add(relationship_key)
            print(f"Linked ingredient '{ingredient_name}' to menu item '{menu_item_name}'")
            
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                print(f"Warning: Skipping duplicate relationship: {menu_item_name} -> {ingredient_name}")
            else:
                print(f"Error linking {ingredient_name} to {menu_item_name}: {e}")
                raise


async def main():
    """Main import function"""
    print("Starting menu data import...")
    
    # Load JSON data
    json_file = Path(__file__).parent.parent / "imports" / "import_excel_prepared_data.json"
    
    if not json_file.exists():
        print(f"Error: JSON file not found at {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded data from {json_file}")
    
    try:
        # Initialize database
        await init_database()
        print("Database initialized")
        
        # Import restaurant
        restaurant_data = data['restaurant'][0]  # Assuming single restaurant
        restaurant = await import_restaurant(restaurant_data)
        
        # Import categories
        category_map = await import_categories(data['categories'], restaurant.id)
        
        # Import ingredients
        ingredient_map = await import_ingredients(data['ingredients'], restaurant.id)
        
        # Import menu items
        menu_item_map = await import_menu_items(data['menu_items'], restaurant.id, category_map)
        
        # Import menu item ingredients (if present)
        if 'menu_item_ingredients' in data:
            await import_menu_item_ingredients(data['menu_item_ingredients'], menu_item_map, ingredient_map)
        
        print("\nImport completed successfully!")
        print(f"Summary:")
        print(f"   - Restaurant: {restaurant.name}")
        print(f"   - Categories: {len(category_map)}")
        print(f"   - Ingredients: {len(ingredient_map)}")
        print(f"   - Menu Items: {len(menu_item_map)}")
        
    except Exception as e:
        print(f"Error during import: {e}")
        raise
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
