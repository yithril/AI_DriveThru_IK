"""
Menu Search Data Transfer Objects (DTOs)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class MenuItemSearchResultDto(BaseModel):
    """DTO for menu item search results"""
    menu_item_id: int = Field(..., description="Menu item ID")
    menu_item_name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: float = Field(..., description="Menu item price")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    category_id: int = Field(..., description="Category ID")
    is_special: bool = Field(..., description="Whether this item is special")
    is_upsell: bool = Field(..., description="Whether this item is for upselling")
    prep_time_minutes: int = Field(..., description="Preparation time in minutes")
    match_score: float = Field(..., description="Fuzzy match score (0-100)")
    ingredients: Optional[List[Dict[str, any]]] = Field(None, description="Associated ingredients")


class IngredientSearchResultDto(BaseModel):
    """DTO for ingredient search results"""
    ingredient_id: int = Field(..., description="Ingredient ID")
    ingredient_name: str = Field(..., description="Ingredient name")
    description: Optional[str] = Field(None, description="Ingredient description")
    is_allergen: bool = Field(..., description="Whether this ingredient is an allergen")
    allergen_type: Optional[str] = Field(None, description="Type of allergen")
    is_optional: bool = Field(..., description="Whether this ingredient is optional")
    match_score: float = Field(..., description="Fuzzy match score (0-100)")


class MenuItemWithIngredientsDto(BaseModel):
    """DTO for menu item with ingredients"""
    menu_item_id: int = Field(..., description="Menu item ID")
    menu_item_name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: float = Field(..., description="Menu item price")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    category_id: int = Field(..., description="Category ID")
    is_special: bool = Field(..., description="Whether this item is special")
    is_upsell: bool = Field(..., description="Whether this item is for upselling")
    prep_time_minutes: int = Field(..., description="Preparation time in minutes")
    ingredients: List[Dict[str, any]] = Field(..., description="Associated ingredients")


class MenuItemByIngredientDto(BaseModel):
    """DTO for menu items found by ingredient"""
    menu_item_id: int = Field(..., description="Menu item ID")
    menu_item_name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Menu item description")
    price: float = Field(..., description="Menu item price")
    image_url: Optional[str] = Field(None, description="URL to menu item image")
    category_id: int = Field(..., description="Category ID")
    is_special: bool = Field(..., description="Whether this item is special")
    is_upsell: bool = Field(..., description="Whether this item is for upselling")
    prep_time_minutes: int = Field(..., description="Preparation time in minutes")
    matching_ingredient: str = Field(..., description="The ingredient that matched")
    ingredient_match_score: float = Field(..., description="Ingredient fuzzy match score")


class MenuSearchResponseDto(BaseModel):
    """DTO for menu search responses"""
    search_type: str = Field(..., description="Type of search performed")
    query: str = Field(..., description="Original search query")
    results: List[dict] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    max_results: int = Field(..., description="Maximum results requested")
