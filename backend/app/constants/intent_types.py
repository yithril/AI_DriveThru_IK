"""
Intent types for intent classification
"""

from enum import Enum


class IntentType(str, Enum):
    """Supported intent types for drive-thru ordering"""
    ADD_ITEM = "ADD_ITEM"
    REMOVE_ITEM = "REMOVE_ITEM"
    CLEAR_ORDER = "CLEAR_ORDER"
    MODIFY_ITEM = "MODIFY_ITEM"
    CONFIRM_ORDER = "CONFIRM_ORDER"
    QUESTION = "QUESTION"
    UNKNOWN = "UNKNOWN"


