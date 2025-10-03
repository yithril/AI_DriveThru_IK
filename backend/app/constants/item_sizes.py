"""
Item size constants for menu items and orders
"""

from enum import Enum


class ItemSize(str, Enum):
    """Standard item sizes for drive-thru ordering"""
    SMALL = "small"
    MEDIUM = "medium" 
    LARGE = "large"
    EXTRA_LARGE = "extra_large"
    # For items where size doesn't matter (like sandwiches, burgers)
    REGULAR = "regular"
    # For items that only come in one size
    ONE_SIZE = "one_size"
