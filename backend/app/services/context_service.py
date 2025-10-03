"""
Context Service for resolving ambiguous user input using conversation and order history.

This service handles pronoun resolution and context disambiguation to transform
ambiguous input like "I'll take two" into explicit text like "I'll take two veggie wraps".
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ContextResolutionResult:
    """Result of context resolution attempt"""
    needs_resolution: bool
    resolved_text: str
    confidence: float
    rationale: str
    original_text: str


class ContextService:
    """
    Service for resolving context in ambiguous user input.
    
    This service:
    1. Checks if input needs context resolution (eligibility check)
    2. Resolves context using conversation and order history
    3. Returns resolved text with confidence score
    """
    
    def __init__(self):
        """Initialize the context service"""
        self.logger = logger
        
        # Generic patterns for eligibility check (restaurant-agnostic)
        self.pronoun_patterns = [
            r'\b(it|that|this|them|one)\b',
            r'\b(the|that|those)\s+\w+',
        ]
        
        self.quantity_patterns = [
            r'\b(two|three|four|five|a couple|some)\b',
        ]
        
        self.demonstrative_patterns = [
            r'\b(the|that|those)\s+\w+',
        ]
        
        # Additional generic patterns for common drive-thru scenarios
        self.temporal_patterns = [
            r'\b(same|again|more|another)\b',
            r'\b(like that|like this)\b',
        ]
        
        self.action_patterns = [
            r'\b(make it|change it|switch it)\b',
            r'\b(instead|rather)\b',
        ]
        
        # Compile regex patterns for efficiency
        self.pronoun_regex = re.compile('|'.join(self.pronoun_patterns), re.IGNORECASE)
        self.quantity_regex = re.compile('|'.join(self.quantity_patterns), re.IGNORECASE)
        self.demonstrative_regex = re.compile('|'.join(self.demonstrative_patterns), re.IGNORECASE)
        self.temporal_regex = re.compile('|'.join(self.temporal_patterns), re.IGNORECASE)
        self.action_regex = re.compile('|'.join(self.action_patterns), re.IGNORECASE)
    
    def check_eligibility(self, user_input: str, intent: str) -> bool:
        """
        Check if input needs context resolution.
        
        Args:
            user_input: The user's input text
            intent: The classified intent (ADD_ITEM, MODIFY_ITEM, etc.)
            
        Returns:
            bool: True if input needs context resolution
        """
        # Run on order-related intents and questions that might have ambiguous references
        eligible_intents = ['ADD_ITEM', 'MODIFY_ITEM', 'REPEAT_ITEM', 'QUESTION']
        if intent not in eligible_intents:
            self.logger.debug(f"Intent '{intent}' not in eligible intents, skipping context resolution")
            return False
        
        # Check for deictic cues
        has_pronouns = bool(self.pronoun_regex.search(user_input))
        has_quantities = bool(self.quantity_regex.search(user_input))
        has_demonstratives = bool(self.demonstrative_regex.search(user_input))
        has_temporal = bool(self.temporal_regex.search(user_input))
        has_actions = bool(self.action_regex.search(user_input))
        
        needs_resolution = (has_pronouns or has_quantities or has_demonstratives or 
                           has_temporal or has_actions)
        
        self.logger.debug(f"Eligibility check: pronouns={has_pronouns}, quantities={has_quantities}, "
                         f"demonstratives={has_demonstratives}, temporal={has_temporal}, actions={has_actions}, "
                         f"needs_resolution={needs_resolution}")
        
        return needs_resolution
    
    def resolve_context(
        self, 
        user_input: str, 
        conversation_history: List[Dict[str, Any]], 
        current_order: Dict[str, Any],
        command_history: List[Dict[str, Any]]
    ) -> ContextResolutionResult:
        """
        Resolve context for ambiguous user input.
        
        Args:
            user_input: The user's input text
            conversation_history: Recent conversation turns
            current_order: Current order state
            command_history: Recent command history
            
        Returns:
            ContextResolutionResult: Resolution result with confidence
        """
        try:
            self.logger.info(f"Resolving context for input: '{user_input}'")
            
            # Build context for LLM
            context_text = self._build_context_text(conversation_history, current_order, command_history)
            
            # Use LLM to resolve context
            resolved_text, confidence, rationale = self._llm_resolve_context(
                user_input, context_text
            )
            
            result = ContextResolutionResult(
                needs_resolution=True,
                resolved_text=resolved_text,
                confidence=confidence,
                rationale=rationale,
                original_text=user_input
            )
            
            self.logger.info(f"Context resolution result: confidence={confidence:.2f}, "
                           f"resolved='{resolved_text}', rationale='{rationale}'")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Context resolution failed: {e}")
            return ContextResolutionResult(
                needs_resolution=True,
                resolved_text=user_input,
                confidence=0.0,
                rationale=f"Resolution failed: {str(e)}",
                original_text=user_input
            )
    
    def _build_context_text(
        self, 
        conversation_history: List[Dict[str, Any]], 
        current_order: Dict[str, Any],
        command_history: List[Dict[str, Any]]
    ) -> str:
        """Build context text for LLM"""
        context_parts = []
        
        # Add conversation history (last 3 turns)
        if conversation_history:
            recent_conversation = conversation_history[-3:]
            conv_text = "\n".join([
                f"{turn.get('role', 'unknown')}: {turn.get('content', '')}" 
                for turn in recent_conversation
            ])
            context_parts.append(f"Recent conversation:\n{conv_text}")
        
        # Add current order summary
        if current_order and current_order.get('items'):
            order_items = current_order['items']
            order_text = ", ".join([
                f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}" 
                for item in order_items
            ])
            context_parts.append(f"Current order: {order_text}")
        
        # Add command history (last 3 commands)
        if command_history:
            recent_commands = command_history[-3:]
            cmd_text = "\n".join([
                f"Command: {cmd.get('action', 'unknown')} - {cmd.get('description', '')}" 
                for cmd in recent_commands
            ])
            context_parts.append(f"Recent commands:\n{cmd_text}")
        
        return "\n\n".join(context_parts)
    
    def _llm_resolve_context(self, user_input: str, context_text: str) -> tuple[str, float, str]:
        """
        Use LLM to resolve context.
        
        Args:
            user_input: The user's input text
            context_text: Built context from conversation/order history
            
        Returns:
            tuple: (resolved_text, confidence, rationale)
        """
        # TODO: Implement LLM-based context resolution
        # For now, return mock implementation
        self.logger.debug("Using mock LLM resolution (TODO: implement real LLM)")
        
        # Mock resolution logic
        if "two" in user_input.lower():
            resolved_text = user_input.replace("two", "two veggie wraps")
            confidence = 0.9
            rationale = "Resolved 'two' to 'two veggie wraps' based on recent conversation"
        else:
            resolved_text = user_input
            confidence = 0.5
            rationale = "No clear resolution found"
        
        return resolved_text, confidence, rationale
    
    def should_use_resolution(self, result: ContextResolutionResult, threshold: float = 0.8) -> bool:
        """
        Determine if resolved text should be used based on confidence threshold.
        
        Args:
            result: Context resolution result
            threshold: Confidence threshold (default 0.8)
            
        Returns:
            bool: True if resolved text should be used
        """
        should_use = result.confidence >= threshold
        
        self.logger.debug(f"Resolution decision: confidence={result.confidence:.2f}, "
                         f"threshold={threshold}, use_resolution={should_use}")
        
        return should_use
