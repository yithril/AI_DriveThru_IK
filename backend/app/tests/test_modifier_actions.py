"""
Unit tests for modifier action normalization
"""

import pytest
from app.constants.modifier_actions import (
    canonicalize_action,
    parse_modifier_string,
    get_action_synonyms,
    CANONICAL_ACTIONS
)


class TestCanonicalizeAction:
    """Tests for canonicalize_action function"""
    
    def test_extra_synonyms(self):
        """Test all 'extra' synonyms normalize correctly"""
        extra_synonyms = ["extra", "heavy", "lots of", "double", "more", "additional", "ton of", "loads of"]
        
        for synonym in extra_synonyms:
            result = canonicalize_action(synonym)
            assert result == "extra", f"'{synonym}' should normalize to 'extra'"
    
    def test_no_synonyms(self):
        """Test all 'no' synonyms normalize correctly"""
        no_synonyms = ["no", "without", "hold the", "hold", "remove", "exclude", "omit"]
        
        for synonym in no_synonyms:
            result = canonicalize_action(synonym)
            assert result == "no", f"'{synonym}' should normalize to 'no'"
    
    def test_light_synonyms(self):
        """Test all 'light' synonyms normalize correctly"""
        light_synonyms = ["light", "easy on", "less", "minimal", "reduced", "sparse"]
        
        for synonym in light_synonyms:
            result = canonicalize_action(synonym)
            assert result == "light", f"'{synonym}' should normalize to 'light'"
    
    def test_well_done_synonyms(self):
        """Test 'well_done' synonyms"""
        well_done_synonyms = ["well done", "well-done", "thoroughly cooked", "cooked through"]
        
        for synonym in well_done_synonyms:
            result = canonicalize_action(synonym)
            assert result == "well_done"
    
    def test_rare_synonyms(self):
        """Test 'rare' synonyms"""
        rare_synonyms = ["rare", "pink", "medium rare", "bloody"]
        
        for synonym in rare_synonyms:
            result = canonicalize_action(synonym)
            assert result == "rare"
    
    def test_default_fallback(self):
        """Test unknown actions default to 'add'"""
        unknown_actions = ["random", "weird", "unknown"]
        
        for action in unknown_actions:
            result = canonicalize_action(action)
            assert result == "add"


class TestParseModifierString:
    """Tests for parse_modifier_string function"""
    
    def test_extra_cheese(self):
        """Test parsing 'extra cheese'"""
        action, ingredient = parse_modifier_string("extra cheese")
        assert action == "extra"
        assert ingredient == "cheese"
    
    def test_no_pickles(self):
        """Test parsing 'no pickles'"""
        action, ingredient = parse_modifier_string("no pickles")
        assert action == "no"
        assert ingredient == "pickles"
    
    def test_light_mayo(self):
        """Test parsing 'light mayo'"""
        action, ingredient = parse_modifier_string("light mayo")
        assert action == "light"
        assert ingredient == "mayo"
    
    def test_hold_the_onions(self):
        """Test parsing 'hold the onions'"""
        action, ingredient = parse_modifier_string("hold the onions")
        assert action == "no"
        assert ingredient == "onions"
    
    def test_lots_of_sauce(self):
        """Test parsing 'lots of sauce'"""
        action, ingredient = parse_modifier_string("lots of sauce")
        assert action == "extra"
        assert ingredient == "sauce"
    
    def test_easy_on_the_mayo(self):
        """Test parsing 'easy on the mayo' with 'the' removal"""
        action, ingredient = parse_modifier_string("easy on the mayo")
        assert action == "light"
        assert ingredient == "mayo"
    
    def test_without_tomatoes(self):
        """Test parsing 'without tomatoes'"""
        action, ingredient = parse_modifier_string("without tomatoes")
        assert action == "no"
        assert ingredient == "tomatoes"
    
    def test_double_bacon(self):
        """Test parsing 'double bacon'"""
        action, ingredient = parse_modifier_string("double bacon")
        assert action == "extra"
        assert ingredient == "bacon"
    
    def test_add_lettuce(self):
        """Test parsing 'add lettuce'"""
        action, ingredient = parse_modifier_string("add lettuce")
        assert action == "add"
        assert ingredient == "lettuce"
    
    def test_with_mustard(self):
        """Test parsing 'with mustard'"""
        action, ingredient = parse_modifier_string("with mustard")
        assert action == "add"
        assert ingredient == "mustard"
    
    def test_default_action(self):
        """Test that modifier without prefix defaults to 'add'"""
        action, ingredient = parse_modifier_string("pickles")
        assert action == "add"
        assert ingredient == "pickles"
    
    def test_case_insensitive(self):
        """Test that parsing is case-insensitive"""
        action, ingredient = parse_modifier_string("EXTRA CHEESE")
        assert action == "extra"
        assert ingredient == "cheese"
    
    def test_whitespace_handling(self):
        """Test that extra whitespace is handled"""
        action, ingredient = parse_modifier_string("  extra   cheese  ")
        assert action == "extra"
        assert ingredient == "cheese"


class TestGetActionSynonyms:
    """Tests for get_action_synonyms function"""
    
    def test_get_extra_synonyms(self):
        """Test getting synonyms for 'extra'"""
        synonyms = get_action_synonyms("extra")
        assert "extra" in synonyms
        assert "heavy" in synonyms
        assert "double" in synonyms
    
    def test_get_no_synonyms(self):
        """Test getting synonyms for 'no'"""
        synonyms = get_action_synonyms("no")
        assert "no" in synonyms
        assert "without" in synonyms
        assert "hold the" in synonyms
    
    def test_unknown_action(self):
        """Test getting synonyms for unknown action"""
        synonyms = get_action_synonyms("unknown")
        assert synonyms == ["unknown"]

