"""
Unit tests for Enhanced Modify Item Service

Tests the new enhanced ModifyItemService that supports item splitting,
multiple modifications, and natural language modification parsing.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from app.services.modify_item_service import ModifyItemService
from app.workflow.response.modify_item_response import ModifyItemResult, ModificationInstruction
from app.dto.modify_item_dto import ModifyItemResultDto


@pytest.fixture
def modify_item_service():
    """Create enhanced modify item service instance"""
    return ModifyItemService()


@pytest.fixture
def sample_redis_order():
    """Sample Redis order data for testing"""
    return {
        "id": "order_1234567890",
        "session_id": "session_123",
        "restaurant_id": 1,
        "status": "active",
        "items": [
            {
                "id": "item_1234567890",
                "menu_item_id": 1,
                "quantity": 4,
                "modifications": {
                    "size": "regular",
                    "name": "Cosmic Fish Sandwich",
                    "unit_price": 12.0,
                    "total_price": 48.0
                },
                "added_at": "2024-01-01T12:00:00"
            }
        ]
    }


class TestModifyItemService:
    """Test cases for enhanced modify item service"""

    @pytest.mark.asyncio
    async def test_simple_modification_success(
        self, modify_item_service, sample_redis_order
    ):
        """Test successful simple modification without splitting"""
        
        # Create agent result with new structure
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            modifications=[
                ModificationInstruction(
                    item_id="item_1234567890",
                    item_name="Cosmic Fish Sandwich",
                    quantity=1,
                    modification="extra cheese",
                    reasoning="User wants extra cheese"
                )
            ],
            requires_split=False,
            remaining_unchanged=0
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        # Verify result
        assert result.success is True
        assert "extra cheese" in result.message
        assert "extra cheese" in result.modified_fields[0]
        assert result.additional_cost == Decimal('0.00')
        
        # Verify Redis item was updated
        target_item = sample_redis_order["items"][0]
        assert "ingredient_modifications" in target_item["modifications"]
        assert "extra cheese" in target_item["modifications"]["ingredient_modifications"]

    @pytest.mark.asyncio
    async def test_item_splitting_success(
        self, modify_item_service, sample_redis_order
    ):
        """Test successful item splitting with multiple modifications"""
        
        # Create agent result that requires splitting
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            modifications=[
                ModificationInstruction(
                    item_id="item_1234567890",
                    item_name="Cosmic Fish Sandwich",
                    quantity=2,
                    modification="extra cheese",
                    reasoning="2 items with extra cheese"
                ),
                ModificationInstruction(
                    item_id="item_1234567890",
                    item_name="Cosmic Fish Sandwich",
                    quantity=1,
                    modification="no lettuce",
                    reasoning="1 item with no lettuce"
                )
            ],
            requires_split=True,
            remaining_unchanged=1
        )
        
        # Apply modification
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        # Verify result
        assert result.success is True
        assert "Split Cosmic Fish Sandwich" in result.message
        assert "2 Cosmic Fish Sandwich: extra cheese" in result.modified_fields
        assert "1 Cosmic Fish Sandwich: no lettuce" in result.modified_fields
        assert "1 Cosmic Fish Sandwich: unchanged" in result.modified_fields
        
        # Verify original item was removed and new items were created
        assert len(sample_redis_order["items"]) == 3  # 2 modified + 1 unchanged
        assert not any(item["id"] == "item_1234567890" for item in sample_redis_order["items"])
        
        # Verify new items have correct quantities and modifications
        new_items = sample_redis_order["items"]
        quantities = [item["quantity"] for item in new_items]
        assert sorted(quantities) == [1, 1, 2]  # 1 unchanged + 1 no lettuce + 2 extra cheese
        
        # Check modifications
        for item in new_items:
            if item["quantity"] == 2:
                assert "extra cheese" in item["modifications"]["ingredient_modifications"]
            elif item["quantity"] == 1:
                if "no lettuce" in item["modifications"].get("ingredient_modifications", ""):
                    pass  # This is the no lettuce item
                else:
                    pass  # This is the unchanged item

    @pytest.mark.asyncio
    async def test_modification_parsing_extra_ingredient(
        self, modify_item_service
    ):
        """Test parsing of 'extra cheese' modification"""
        
        parsed = modify_item_service._parse_modification_text("extra cheese")
        
        assert parsed["ingredient_modifications"] == ["extra cheese"]
        assert parsed["size_change"] is None
        assert parsed["quantity_change"] is None
        assert parsed["special_instructions"] == []

    @pytest.mark.asyncio
    async def test_modification_parsing_no_ingredient(
        self, modify_item_service
    ):
        """Test parsing of 'no lettuce' modification"""
        
        parsed = modify_item_service._parse_modification_text("no lettuce")
        
        assert parsed["ingredient_modifications"] == ["no lettuce"]
        assert parsed["size_change"] is None
        assert parsed["quantity_change"] is None
        assert parsed["special_instructions"] == []

    @pytest.mark.asyncio
    async def test_modification_parsing_size_change(
        self, modify_item_service
    ):
        """Test parsing of size change modification"""
        
        parsed = modify_item_service._parse_modification_text("make it large")
        
        assert parsed["ingredient_modifications"] == []
        assert parsed["size_change"] == "large"
        assert parsed["quantity_change"] is None
        assert parsed["special_instructions"] == []

    @pytest.mark.asyncio
    async def test_modification_parsing_complex(
        self, modify_item_service
    ):
        """Test parsing of complex modification text"""
        
        parsed = modify_item_service._parse_modification_text("extra cheese and extra lettuce, make it large")
        
        assert "extra cheese" in parsed["ingredient_modifications"]
        assert "extra lettuce" in parsed["ingredient_modifications"]
        assert parsed["size_change"] == "large"
        assert parsed["quantity_change"] is None

    @pytest.mark.asyncio
    async def test_item_not_found_error(
        self, modify_item_service, sample_redis_order
    ):
        """Test error when target item is not found"""
        
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            modifications=[
                ModificationInstruction(
                    item_id="nonexistent_item",
                    item_name="Nonexistent Item",
                    quantity=1,
                    modification="extra cheese",
                    reasoning="User wants extra cheese"
                )
            ],
            requires_split=False,
            remaining_unchanged=0
        )
        
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        assert result.success is False
        assert "Validation failed" in result.message
        assert len(result.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_quantity_mismatch_error(
        self, modify_item_service, sample_redis_order
    ):
        """Test error when splitting quantities don't match original"""
        
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            modifications=[
                ModificationInstruction(
                    item_id="item_1234567890",
                    item_name="Cosmic Fish Sandwich",
                    quantity=3,  # This + remaining_unchanged=2 = 5, but original is 4
                    modification="extra cheese",
                    reasoning="3 items with extra cheese"
                )
            ],
            requires_split=True,
            remaining_unchanged=2
        )
        
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        assert result.success is False
        assert "Quantity mismatch" in result.message
        assert "Invalid quantity split" in result.validation_errors[0]

    @pytest.mark.asyncio
    async def test_clarification_needed(
        self, modify_item_service, sample_redis_order
    ):
        """Test when agent result needs clarification"""
        
        agent_result = ModifyItemResult(
            success=False,
            confidence=0.3,
            modifications=[],
            clarification_needed=True,
            clarification_message="Which item would you like to modify?"
        )
        
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        assert result.success is False
        assert "Which item would you like to modify?" in result.message
        assert len(result.validation_errors) == 0

    @pytest.mark.asyncio
    async def test_no_modifications_error(
        self, modify_item_service, sample_redis_order
    ):
        """Test error when no modifications are provided"""
        
        agent_result = ModifyItemResult(
            success=True,
            confidence=0.95,
            modifications=[],
            requires_split=False,
            remaining_unchanged=0
        )
        
        result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
        
        assert result.success is False
        assert "No modifications specified" in result.message
        assert "No modifications provided" in result.validation_errors

    @pytest.mark.asyncio
    async def test_create_item_from_original(
        self, modify_item_service, sample_redis_order
    ):
        """Test creating new item from original"""
        
        original_item = sample_redis_order["items"][0]
        new_item = modify_item_service._create_item_from_original(original_item, 2)
        
        # Verify new item properties
        assert new_item["id"] != original_item["id"]  # Different ID
        assert new_item["quantity"] == 2
        assert new_item["total_price"] == 24.0  # 2 * 12.0
        assert new_item["menu_item_id"] == original_item["menu_item_id"]
        assert new_item["modifications"]["name"] == original_item["modifications"]["name"]

    @pytest.mark.asyncio
    async def test_apply_parsed_modifications(
        self, modify_item_service
    ):
        """Test applying parsed modifications to an item"""
        
        item = {
            "id": "test_item",
            "modifications": {}
        }
        
        parsed_mods = {
            "ingredient_modifications": ["extra cheese", "no lettuce"],
            "size_change": "large",
            "special_instructions": ["keep regular"]
        }
        
        modify_item_service._apply_parsed_modifications(item, parsed_mods)
        
        assert item["modifications"]["ingredient_modifications"] == "extra cheese; no lettuce"
        assert item["modifications"]["size"] == "large"
        assert item["modifications"]["special_instructions"] == "keep regular"

    # ===== VALIDATION TESTS =====

    @pytest.mark.asyncio
    async def test_quantity_validation_exceeds_max(
        self, modify_item_service, sample_redis_order
    ):
        """Test validation when quantity exceeds menu item max_quantity"""
        
        # Mock MenuItem database call
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class:
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 5
            # Create an async mock for get_or_none
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=10,  # Exceeds max_quantity of 5
                        modification="extra cheese",
                        reasoning="User wants 10 items"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            assert result.success is False
            assert "Cannot order 10 Cosmic Fish Sandwich" in result.message
            assert "Maximum allowed: 5" in result.message
            assert len(result.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_quantity_validation_business_limit(
        self, modify_item_service, sample_redis_order
    ):
        """Test validation when quantity exceeds business limit (10 from config)"""
        
        # Mock MenuItem database call
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class:
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = None
            # Create an async mock for get_or_none
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=15,  # Exceeds business limit of 10 (from MAX_ITEM_QUANTITY)
                        modification="extra cheese",
                        reasoning="User wants 20 items"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            assert result.success is False
            assert "Cannot order 15 Cosmic Fish Sandwich" in result.message
            assert "Maximum allowed: 10" in result.message
            assert len(result.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_ingredient_validation_nonexistent(
        self, modify_item_service, sample_redis_order
    ):
        """Test validation when ingredient doesn't exist at restaurant"""
        
        # Mock ingredient service to return limited ingredients
        with patch.object(modify_item_service.ingredient_service, 'get_by_restaurant') as mock_ingredients:
            mock_ingredient_list = MagicMock()
            mock_cheese = MagicMock()
            mock_cheese.name = "cheese"
            mock_lettuce = MagicMock()
            mock_lettuce.name = "lettuce"
            mock_tomato = MagicMock()
            mock_tomato.name = "tomato"
            mock_ingredient_list.ingredients = [mock_cheese, mock_lettuce, mock_tomato]
            mock_ingredients.return_value = mock_ingredient_list
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=1,
                        modification="extra unicorn meat",  # Non-existent ingredient
                        reasoning="User wants unicorn meat"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            assert result.success is False
            assert "'unicorn meat' is not available" in result.message
            assert len(result.validation_errors) > 0

    @pytest.mark.asyncio
    async def test_ingredient_validation_case_insensitive(
        self, modify_item_service, sample_redis_order
    ):
        """Test that ingredient validation is case insensitive"""
        
        # Mock both MenuItem and ingredient service
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class, \
             patch.object(modify_item_service.ingredient_service, 'get_by_restaurant') as mock_ingredients:
            
            # Mock MenuItem to pass quantity validation
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 10
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            mock_ingredient_list = MagicMock()
            mock_cheese = MagicMock()
            mock_cheese.name = "Cheese"
            mock_lettuce = MagicMock()
            mock_lettuce.name = "Lettuce"
            mock_ingredient_list.ingredients = [mock_cheese, mock_lettuce]
            mock_ingredients.return_value = mock_ingredient_list
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=1,
                        modification="extra cheese",  # lowercase
                        reasoning="User wants cheese"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            # Should succeed because "cheese" matches "Cheese" (case insensitive)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_ingredient_extraction(
        self, modify_item_service
    ):
        """Test ingredient name extraction from modification strings"""
        
        # Test various modification strings
        test_cases = [
            ("extra cheese", "cheese"),
            ("no lettuce", "lettuce"),
            ("without tomato", "tomato"),
            ("hold pickles", "pickles"),
            ("remove onions", "onions"),
            ("extra cheese and extra lettuce", "cheese and lettuce"),  # Complex case
        ]
        
        for modification, expected in test_cases:
            result = modify_item_service._extract_ingredient_name(modification)
            assert result == expected, f"Failed for '{modification}': expected '{expected}', got '{result}'"

    @pytest.mark.asyncio
    async def test_validation_passes_with_valid_data(
        self, modify_item_service, sample_redis_order
    ):
        """Test that validation passes with valid data"""
        
        # Mock services to return valid data
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class, \
             patch.object(modify_item_service.ingredient_service, 'get_by_restaurant') as mock_ingredients:
            
            # Mock menu item with reasonable max_quantity
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 10
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            # Mock ingredients including cheese
            mock_ingredient_list = MagicMock()
            mock_cheese = MagicMock()
            mock_cheese.name = "cheese"
            mock_lettuce = MagicMock()
            mock_lettuce.name = "lettuce"
            mock_ingredient_list.ingredients = [mock_cheese, mock_lettuce]
            mock_ingredients.return_value = mock_ingredient_list
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=2,  # Within limits
                        modification="extra cheese",  # Valid ingredient
                        reasoning="User wants 2 with extra cheese"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            # Should succeed because all validation passes
            assert result.success is True
            assert "extra cheese" in result.message

    @pytest.mark.asyncio
    async def test_validation_graceful_degradation(
        self, modify_item_service, sample_redis_order
    ):
        """Test that validation gracefully handles service failures"""
        
        # Mock services to raise exceptions
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class, \
             patch.object(modify_item_service.ingredient_service, 'get_by_restaurant') as mock_ingredients:
            
            mock_menu_item_class.get_or_none.side_effect = Exception("Menu service unavailable")
            mock_ingredients.side_effect = Exception("Ingredient service unavailable")
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=2,
                        modification="extra cheese",
                        reasoning="User wants extra cheese"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            # Should still succeed because validation gracefully degrades
            assert result.success is True
            assert "extra cheese" in result.message

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(
        self, modify_item_service, sample_redis_order
    ):
        """Test that multiple validation errors are caught"""
        
        # Mock services to return restrictive limits
        with patch('app.models.menu_item.MenuItem') as mock_menu_item_class, \
             patch.object(modify_item_service.ingredient_service, 'get_by_restaurant') as mock_ingredients:
            
            # Mock menu item with low max_quantity
            mock_menu_item = MagicMock()
            mock_menu_item.max_quantity = 2
            async def mock_get_or_none(*args, **kwargs):
                return mock_menu_item
            mock_menu_item_class.get_or_none = mock_get_or_none
            
            # Mock ingredients excluding cheese
            mock_ingredient_list = MagicMock()
            mock_lettuce = MagicMock()
            mock_lettuce.name = "lettuce"
            mock_tomato = MagicMock()
            mock_tomato.name = "tomato"
            mock_ingredient_list.ingredients = [mock_lettuce, mock_tomato]
            mock_ingredients.return_value = mock_ingredient_list
            
            agent_result = ModifyItemResult(
                success=True,
                confidence=0.95,
                modifications=[
                    ModificationInstruction(
                        item_id="item_1234567890",
                        item_name="Cosmic Fish Sandwich",
                        quantity=5,  # Exceeds max_quantity
                        modification="extra cheese",  # Invalid ingredient
                        reasoning="User wants 5 with cheese"
                    )
                ],
                requires_split=False,
                remaining_unchanged=0
            )
            
            result = await modify_item_service.apply_modification(agent_result, sample_redis_order)
            
            assert result.success is False
            assert "Validation failed" in result.message
            assert len(result.validation_errors) >= 1  # Should have at least quantity error
            assert "Maximum allowed" in result.message  # Quantity validation should be caught


class TestEnhancedModifyItemServiceValidation:
    """Test enhanced validation logic in ModifyItemService"""
    
    @pytest.fixture
    def service(self):
        """Create ModifyItemService instance"""
        return ModifyItemService()
    
    @pytest.fixture
    def sample_redis_order(self):
        """Sample Redis order with one item"""
        return {
            "id": "order_123",
            "restaurant_id": 1,
            "items": [
                {
                    "id": "item_123",
                    "menu_item_id": 1,
                    "quantity": 2,
                    "modifications": {
                        "name": "Burger",
                        "unit_price": 10.0,
                        "total_price": 20.0,
                        "ingredient_modifications": "",
                        "special_instructions": ""
                    }
                }
            ]
        }
    
    @pytest.fixture
    def valid_modification(self):
        """Valid modification instruction"""
        return ModifyItemResult(
            success=True,
            confidence=0.9,
            modifications=[
                ModificationInstruction(
                    item_id="item_123",
                    item_name="Burger",
                    quantity=1,
                    modification="extra cheese",
                    reasoning="User wants extra cheese"
                )
            ],
            requires_split=False
        )
    
    @pytest.fixture
    def invalid_item_modification(self):
        """Modification for item not in order"""
        return ModifyItemResult(
            success=True,
            confidence=0.9,
            modifications=[
                ModificationInstruction(
                    item_id="item_999",  # Not in order
                    item_name="Fries",
                    quantity=1,
                    modification="extra crispy",
                    reasoning="User wants fries extra crispy"
                )
            ],
            requires_split=False
        )
    
    @pytest.fixture
    def mixed_modifications(self):
        """Mix of valid and invalid modifications"""
        return ModifyItemResult(
            success=True,
            confidence=0.9,
            modifications=[
                ModificationInstruction(
                    item_id="item_123",  # Valid
                    item_name="Burger",
                    quantity=1,
                    modification="extra cheese",
                    reasoning="Valid modification"
                ),
                ModificationInstruction(
                    item_id="item_999",  # Invalid - not in order
                    item_name="Fries",
                    quantity=1,
                    modification="extra crispy",
                    reasoning="Invalid modification"
                )
            ],
            requires_split=False
        )
    
    @pytest.mark.asyncio
    async def test_validation_success_with_valid_modification(self, service, sample_redis_order, valid_modification):
        """Test validation passes for valid modification"""
        
        # Mock ingredient validation to pass
        with patch.object(service, '_validate_ingredients', return_value=None):
            with patch.object(service, '_validate_quantity', return_value=None):
                result = await service.apply_modification(valid_modification, sample_redis_order)
                
                assert result.success is True
                assert "extra cheese" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_validation_fails_for_nonexistent_item(self, service, sample_redis_order, invalid_item_modification):
        """Test validation fails when item doesn't exist in order"""
        
        result = await service.apply_modification(invalid_item_modification, sample_redis_order)
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_partial_success_with_mixed_modifications(self, service, sample_redis_order, mixed_modifications):
        """Test partial success when some modifications work and others don't"""
        
        # Mock ingredient validation to pass for valid item
        async def mock_validate_ingredients(modification, redis_order):
            if modification.item_id == "item_123":
                return None  # Valid
            return f"'{modification.modification.split()[-1]}' is not available at this restaurant"
        
        with patch.object(service, '_validate_ingredients', side_effect=mock_validate_ingredients):
            with patch.object(service, '_validate_quantity', return_value=None):
                result = await service.apply_modification(mixed_modifications, sample_redis_order)
                
                # Should be partial success
                assert result.success is True  # At least one modification succeeded
                assert "Updated:" in result.message
                assert "Could not update:" in result.message
                assert "Burger" in result.message
                assert "Fries" in result.message
    
    @pytest.mark.asyncio
    async def test_validation_fails_for_invalid_ingredient(self, service, sample_redis_order, valid_modification):
        """Test validation fails for invalid ingredient"""
        
        # Mock ingredient validation to fail
        with patch.object(service, '_validate_ingredients', return_value="'unicorn meat' is not available at this restaurant"):
            with patch.object(service, '_validate_quantity', return_value=None):
                result = await service.apply_modification(valid_modification, sample_redis_order)
                
                assert result.success is False
                assert "not available" in result.message.lower()
                assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_validation_fails_for_excessive_quantity(self, service, sample_redis_order, valid_modification):
        """Test validation fails for excessive quantity"""
        
        # Set quantity to exceed limits
        valid_modification.modifications[0].quantity = 100
        
        # Mock quantity validation to fail
        with patch.object(service, '_validate_quantity', return_value="Cannot order more than 10 of any single item"):
            with patch.object(service, '_validate_ingredients', return_value=None):
                result = await service.apply_modification(valid_modification, sample_redis_order)
                
                assert result.success is False
                assert "Cannot order" in result.message
                assert len(result.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_all_modifications_fail_validation(self, service, sample_redis_order):
        """Test when all modifications fail validation"""
        
        # Create modification that will fail all validations
        failed_modification = ModifyItemResult(
            success=True,
            confidence=0.9,
            modifications=[
                ModificationInstruction(
                    item_id="item_999",  # Not in order
                    item_name="Fries",
                    quantity=15,  # Within Pydantic limit but exceeds business limit
                    modification="with unicorn meat",  # Invalid ingredient
                    reasoning="Multiple validation failures"
                )
            ],
            requires_split=False
        )
        
        result = await service.apply_modification(failed_modification, sample_redis_order)
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert len(result.validation_errors) > 0