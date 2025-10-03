"""
Order configuration constants

These constants control order behavior and can be easily adjusted.
In the future, these could be moved to a configuration system or feature flags.
"""

# Maximum quantity that can be ordered for any single item
MAX_ITEM_QUANTITY = 10

# Maximum total number of items in an order
MAX_TOTAL_ITEMS = 20

# Maximum number of different items in an order
MAX_UNIQUE_ITEMS = 15

# Default quantity when not specified
DEFAULT_ITEM_QUANTITY = 1

# Minimum quantity for any item
MIN_ITEM_QUANTITY = 1
