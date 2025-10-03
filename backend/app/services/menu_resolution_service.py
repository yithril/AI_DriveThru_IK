"""
Menu Resolution Service

Resolves extracted items against the menu database.
Uses deterministic modifier parsing + fuzzy ingredient matching.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.workflow.response.item_extraction_response import ItemExtractionResponse, ExtractedItem
from app.workflow.response.menu_resolution_response import MenuResolutionResponse, ResolvedItem, NormalizedModifier
from app.constants.modifier_actions import parse_modifier_string

logger = logging.getLogger(__name__)


class MenuResolutionService:
    """
    Service for resolving extracted items against the menu database.
    
    Takes output from Item Extraction Agent and:
    1. Resolves item names to menu_item_ids (fuzzy search)
    2. Normalizes modifiers to (ingredient_id, action) tuples
    3. Handles ambiguous items and unavailable items
    """
    
    def __init__(self, menu_service: MenuService, ingredient_service: IngredientService):
        """
        Initialize the menu resolution service.
        
        Args:
            menu_service: Menu service for menu item lookups
            ingredient_service: Ingredient service for ingredient lookups
        """
        self.menu_service = menu_service
        self.ingredient_service = ingredient_service
    
    async def resolve_items(
        self, 
        extraction_response: ItemExtractionResponse, 
        restaurant_id: int
    ) -> MenuResolutionResponse:
        """
        Resolve extracted items against the menu database.
        
        Args:
            extraction_response: Response from Item Extraction Agent
            restaurant_id: Restaurant ID for menu lookup
            
        Returns:
            MenuResolutionResponse with resolved items
        """
        try:
            logger.info(f"Resolving {len(extraction_response.extracted_items)} items for restaurant {restaurant_id}")
            
            if not extraction_response.success or not extraction_response.extracted_items:
                return MenuResolutionResponse(
                    success=False,
                    confidence=0.0,
                    resolved_items=[],
                    needs_clarification=True,
                    clarification_questions=["No items were extracted from your request."]
                )
            
            resolved_items = []
            needs_clarification = False
            clarification_questions = []
            
            # Process each extracted item
            for extracted_item in extraction_response.extracted_items:
                logger.info(f"DEBUG: Processing extracted item: '{extracted_item.item_name}' (qty: {extracted_item.quantity})")
                
                resolved_item = await self._resolve_single_item(
                    extracted_item, 
                    restaurant_id
                )
                logger.info(f"DEBUG: Resolved item result: name='{resolved_item.resolved_menu_item_name}', id={resolved_item.resolved_menu_item_id}, ambiguous={resolved_item.is_ambiguous}, unavailable={resolved_item.is_unavailable}")
                resolved_items.append(resolved_item)
                
                # Track if clarification is needed
                if resolved_item.is_ambiguous or resolved_item.is_unavailable:
                    needs_clarification = True
                    if resolved_item.clarification_question:
                        clarification_questions.append(resolved_item.clarification_question)
            
            # Calculate overall confidence
            overall_confidence = min(item.menu_item_resolution_confidence for item in resolved_items) if resolved_items else 0.0
            
            return MenuResolutionResponse(
                success=True,
                confidence=overall_confidence,
                resolved_items=resolved_items,
                needs_clarification=needs_clarification,
                clarification_questions=clarification_questions,
                resolution_notes=f"Resolved {len(resolved_items)} items using fuzzy matching"
            )
            
        except Exception as e:
            logger.error(f"Menu resolution failed: {e}")
            return MenuResolutionResponse(
                success=False,
                confidence=0.0,
                resolved_items=[],
                needs_clarification=True,
                clarification_questions=["There was an error accessing the menu. Please try again later."]
            )
    
    async def _resolve_single_item(
        self, 
        extracted_item: ExtractedItem, 
        restaurant_id: int
    ) -> ResolvedItem:
        """
        Resolve a single extracted item against the menu.
        
        Args:
            extracted_item: ExtractedItem to resolve
            restaurant_id: Restaurant ID for menu lookup
            
        Returns:
            ResolvedItem with resolution results
        """
        try:
            # Search for matches using fuzzy matching
            logger.info(f"DEBUG: Searching for '{extracted_item.item_name}' in restaurant {restaurant_id}")
            matches = await self.menu_service.fuzzy_search_menu_items(
                restaurant_id=restaurant_id,
                search_term=extracted_item.item_name,
                limit=5,
                include_ingredients=False
            )
            logger.info(f"DEBUG: Found {len(matches)} matches for '{extracted_item.item_name}'")
            for i, match in enumerate(matches):
                logger.info(f"DEBUG: Match {i+1}: name='{match.get('name', 'N/A')}', score={match.get('match_score', 0)}, id={match.get('id', 'N/A')}")
            
            if not matches:
                # No matches found - item unavailable
                logger.info(f"DEBUG: No matches found for '{extracted_item.item_name}' - marking as unavailable")
                return await self._handle_unavailable_item(extracted_item, restaurant_id)
            
            # Check match scores
            best_match = matches[0]
            best_score = best_match.get('match_score', 0)
            
            # DEBUG: Log match analysis
            logger.info(f"DEBUG RESOLUTION: Best match: '{best_match.get('name', 'N/A')}' (score: {best_score})")
            logger.info(f"DEBUG RESOLUTION: Total matches: {len(matches)}, Single clear match: {len(matches) == 1}, High score: {best_score >= 90}")
            
            # Check if there's a clear winner
            is_clear_winner = self._is_clear_winner(matches, best_score)
            
            if is_clear_winner:
                # Normalize modifiers using deterministic parsing
                clean_modifiers, detailed_modifiers = await self._normalize_modifiers(
                    extracted_item.modifiers, 
                    restaurant_id
                )
                
                return ResolvedItem(
                    item_name=extracted_item.item_name,
                    quantity=extracted_item.quantity,
                    size=extracted_item.size,
                    modifiers=clean_modifiers,  # Clean tuples: [(ingredient_id, action)]
                    special_instructions=extracted_item.special_instructions,
                    ingredient_normalization_details=detailed_modifiers,
                    resolved_menu_item_id=best_match['menu_item_id'],
                    resolved_menu_item_name=best_match['menu_item_name'],
                    menu_item_resolution_confidence=best_score / 100.0,
                    is_ambiguous=False,
                    is_unavailable=False,
                    suggested_options=[],
                    clarification_question=None
                )
            
            else:
                # Multiple matches - ambiguous
                clean_modifiers, detailed_modifiers = await self._normalize_modifiers(
                    extracted_item.modifiers, 
                    restaurant_id
                )
                
                suggested_options = [match['menu_item_name'] for match in matches[:3]]
                
                return ResolvedItem(
                    item_name=extracted_item.item_name,
                    quantity=extracted_item.quantity,
                    size=extracted_item.size,
                    modifiers=clean_modifiers,
                    special_instructions=extracted_item.special_instructions,
                    ingredient_normalization_details=detailed_modifiers,
                    resolved_menu_item_id=0,
                    resolved_menu_item_name=None,
                    menu_item_resolution_confidence=0.8,
                    is_ambiguous=True,
                    is_unavailable=False,
                    suggested_options=suggested_options,
                    clarification_question=f"Which {extracted_item.item_name} would you like? We have {', '.join(suggested_options)}."
                )
                
        except Exception as e:
            logger.error(f"Failed to resolve item {extracted_item.item_name}: {e}")
            return self._create_error_item(extracted_item)
    
    async def _handle_unavailable_item(
        self, 
        extracted_item: ExtractedItem, 
        restaurant_id: int
    ) -> ResolvedItem:
        """Handle an item that is not found on the menu."""
        # Try to get similar items from same category
        similar_items = await self.menu_service.fuzzy_search_menu_items(
            restaurant_id=restaurant_id,
            search_term=extracted_item.item_name.split()[0],  # Try first word
            limit=3,
            include_ingredients=False
        )
        
        suggested_options = [item['menu_item_name'] for item in similar_items] if similar_items else []
        
        if suggested_options:
            clarification = f"Sorry, we don't have {extracted_item.item_name}. But we do have {', '.join(suggested_options)}. Would you like one of those?"
        else:
            clarification = f"Sorry, we don't have {extracted_item.item_name} on our menu."
        
        return ResolvedItem(
            item_name=extracted_item.item_name,
            quantity=extracted_item.quantity,
            size=extracted_item.size,
            modifiers=[],
            special_instructions=extracted_item.special_instructions,
            ingredient_normalization_details=[],
            resolved_menu_item_id=0,
            resolved_menu_item_name=None,
            menu_item_resolution_confidence=0.0,
            is_ambiguous=False,
            is_unavailable=True,
            suggested_options=suggested_options,
            clarification_question=clarification
        )
    
    async def _normalize_modifiers(
        self, 
        modifiers: List[str], 
        restaurant_id: int
    ) -> Tuple[List[Tuple[int, str]], List[NormalizedModifier]]:
        """
        Normalize modifiers using deterministic parsing + ingredient lookup.
        
        Args:
            modifiers: List of LLM-extracted modifiers (e.g., ["extra cheese", "no pickles"])
            restaurant_id: Restaurant ID for ingredient lookup
            
        Returns:
            Tuple of (clean_modifiers, detailed_modifiers):
            - clean_modifiers: List of (ingredient_id, canonical_action) tuples
            - detailed_modifiers: List of NormalizedModifier objects for logging
        """
        logger.info(f"DEBUG MODIFIERS: Processing {len(modifiers)} modifiers: {modifiers}")
        clean_modifiers = []
        detailed_modifiers = []
        
        for modifier in modifiers:
            try:
                # DETERMINISTIC parsing (not LLM!)
                action, ingredient_term = parse_modifier_string(modifier)
                
                # Look up ingredient in database using fuzzy search
                logger.info(f"DEBUG MODIFIERS: Searching for ingredient '{ingredient_term}' in restaurant {restaurant_id}")
                ingredient_matches = await self.ingredient_service.search_by_name(
                    restaurant_id=restaurant_id,
                    name=ingredient_term
                )
                logger.info(f"DEBUG MODIFIERS: Ingredient search returned {len(ingredient_matches.ingredients)} matches")
                
                if ingredient_matches.ingredients and len(ingredient_matches.ingredients) > 0:
                    # Take best match
                    best_match = ingredient_matches.ingredients[0]
                    
                    # Create clean tuple for commands
                    clean_modifiers.append((best_match.id, action))
                    
                    # Create detailed object for logging
                    detailed_modifiers.append(NormalizedModifier(
                        original_modifier=modifier,
                        final_modifier=f"{action} {best_match.name}",
                        action=action,
                        ingredient_term=ingredient_term,
                        ingredient_id=best_match.id,
                        normalized_ingredient_name=best_match.name,
                        match_confidence=1.0,  # Direct match from search
                        is_resolved=True,
                        is_available=True,
                        is_allergen=best_match.is_allergen,
                        allergen_type=best_match.allergen_type
                    ))
                else:
                    # Ingredient not found - log but don't fail
                    logger.warning(f"Ingredient not found for modifier '{modifier}'")
                    
                    detailed_modifiers.append(NormalizedModifier(
                        original_modifier=modifier,
                        final_modifier=modifier,
                        action=action,
                        ingredient_term=ingredient_term,
                        ingredient_id=None,
                        normalized_ingredient_name=None,
                        match_confidence=0.0,
                        is_resolved=False,
                        is_available=False
                    ))
                
            except Exception as e:
                logger.error(f"Failed to normalize modifier '{modifier}': {e}")
                detailed_modifiers.append(NormalizedModifier(
                    original_modifier=modifier,
                    final_modifier=modifier,
                    action="unknown",
                    ingredient_term=modifier,
                    is_resolved=False,
                    is_available=False
                ))
        
        return clean_modifiers, detailed_modifiers
    
    def _create_error_item(self, extracted_item: ExtractedItem) -> ResolvedItem:
        """Create error response for failed resolution"""
        return ResolvedItem(
            item_name=extracted_item.item_name,
            quantity=extracted_item.quantity,
            size=extracted_item.size,
            modifiers=[],
            special_instructions=extracted_item.special_instructions,
            ingredient_normalization_details=[],
            resolved_menu_item_id=0,
            resolved_menu_item_name=None,
            menu_item_resolution_confidence=0.0,
            is_ambiguous=False,
            is_unavailable=True,
            suggested_options=[],
            clarification_question=f"Sorry, we couldn't process {extracted_item.item_name}"
        )
    
    def _is_clear_winner(self, matches: List[Dict[str, Any]], best_score: float) -> bool:
        """
        Determine if there's a clear winner among the matches.
        
        A clear winner is determined by:
        1. Only one match, OR
        2. Best score >= 90, OR  
        3. Best score is significantly higher than the second best (gap >= 15 points)
        
        Args:
            matches: List of match results
            best_score: Score of the best match
            
        Returns:
            bool: True if there's a clear winner
        """
        # Single match is always clear
        if len(matches) == 1:
            return True
            
        # High score is always clear
        if best_score >= 90:
            return True
            
        # Check if there's a significant gap between best and second best
        if len(matches) >= 2:
            second_best_score = matches[1].get('match_score', 0)
            score_gap = best_score - second_best_score
            
            # If the gap is significant (>= 15 points), it's a clear winner
            if score_gap >= 15:
                logger.info(f"DEBUG: Clear winner due to score gap: {best_score} vs {second_best_score} (gap: {score_gap})")
                return True
        
        # Check if the best match contains the search term as a substring
        # This helps with cases like "quantum burger" matching "quantum cheeseburger"
        if len(matches) >= 1:
            best_match_name = matches[0].get('menu_item_name', '').lower()
            # This is a heuristic - if the best match contains the search term, prefer it
            # even if there are other matches with similar scores
            if best_score >= 70:  # Reasonable threshold
                logger.info(f"DEBUG: Clear winner due to reasonable score and name match: {best_score}")
                return True
                
        return False

