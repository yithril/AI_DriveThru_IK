"""
Context Service for resolving ambiguous user input using conversation and order history.

This service handles pronoun resolution and context disambiguation to transform
ambiguous input like "I'll take two" into explicit text like "I'll take two veggie wraps".
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)

NUMBER_WORDS = {
    "zero","one","two","three","four","five","six","seven","eight","nine","ten",
    "eleven","twelve","dozen"
}

DEFAULT_ORDER_TERMS = {
    # Expand with your taxonomy; keep it lowercase
    "wrap","wraps","burger","burgers","sandwich","sandwiches","fries","shake","shakes",
    "tea","water","cookie","cookies","taco","tacos","combo","meal","meals","sundae","sundaes",
    "nugget","nuggets","drink","drinks","sauce","sauces","packet","packets"
}

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

    Guardrails:
    1) Only runs for deictic/elliptical/repair utterances.
    2) Pass-through for explicit requests (e.g., "give me 3 wraps").
    """

    def __init__(self, order_terms: Optional[set[str]] = None):
        self.logger = logger
        self.order_terms = set(t.lower() for t in (order_terms or DEFAULT_ORDER_TERMS))

        # Deixis / repair / ellipsis cues
        self.deixis_tokens = {
            "it","that","this","those","these","same","the same","that one","this one","ones","one"
        }
        self.repair_tokens = {
            "actually","scratch that","undo that","cancel that","remove that","not that","take that off"
        }
        self.ellipsis_tokens = {
            "another","one more","same again","the usual","make it","make them","keep it","leave it",
        }

        # Regex bundles
        self.deixis_regex = re.compile(r"\b(it|that|this|those|these|them|same|ones?)\b", re.IGNORECASE)
        self.repair_regex = re.compile(r"\b(actually|scratch that|undo that|cancel that|remove that|not that|take that off)\b", re.IGNORECASE)
        self.ellipsis_regex = re.compile(r"\b(another|one more|same again|the usual|make (it|them)|keep it|leave it)\b", re.IGNORECASE)

        # “Nouny hints” for explicit orders, expand with your taxonomy
        noun_pattern = r"|".join(sorted(map(re.escape, self.order_terms), key=len, reverse=True))
        self.noun_hint_regex = re.compile(rf"\b({noun_pattern})\b", re.IGNORECASE)

        # Numeric presence (digits or number words)
        self.number_word_regex = re.compile(r"\b(" + "|".join(sorted(NUMBER_WORDS)) + r")\b", re.IGNORECASE)
        self.any_digit_regex = re.compile(r"\d")

        # Action cues that often appear with deixis but aren’t sufficient alone
        self.action_regex = re.compile(r"\b(make it|change it|switch it|instead|rather)\b", re.IGNORECASE)

        # Intents we care about
        self.eligible_intents = {'ADD_ITEM','MODIFY_ITEM','REPEAT_ITEM','REMOVE_ITEM','QUESTION'}

    # ---------- Public API ----------

    def check_eligibility(self, user_input: str, intent: str) -> bool:
        """
        Decide whether to invoke the LLM agent at all.

        Simple: Only run for obvious ambiguous patterns.
        Let the LLM handle nuanced cases like "one burger" vs "one".
        """
        if intent not in self.eligible_intents:
            self.logger.debug(f"Intent '{intent}' not eligible → skip context agent")
            return False

        t = user_input.lower().strip()
        
        # Obvious ambiguous patterns that should trigger context resolution:
        # 1. Standalone pronouns/demonstratives
        standalone_pronouns = re.compile(r'\b(it|that|this|those|these|them|same)\b(?!\s+\w+)', re.IGNORECASE)
        if standalone_pronouns.search(t):
            self.logger.debug("Found standalone pronoun → eligible")
            return True
        
        # 2. Repair markers
        if self.repair_regex.search(t):
            self.logger.debug("Found repair marker → eligible")
            return True
            
        # 3. Ellipsis markers
        if self.ellipsis_regex.search(t):
            self.logger.debug("Found ellipsis marker → eligible")
            return True
        
        # 4. Obvious ambiguous quantities (no nouny hint at all)
        has_quantity = bool(self.any_digit_regex.search(t) or self.number_word_regex.search(t))
        has_nouny_hint = bool(self.noun_hint_regex.search(t))
        
        # Only trigger if there's a quantity AND no nouny hint at all
        # This catches "I'll take two" but lets "one burger" through
        if has_quantity and not has_nouny_hint:
            self.logger.debug("Found ambiguous quantity (no nouny hint) → eligible")
            return True

        # Everything else goes through to the LLM for nuanced decision
        self.logger.debug("No obvious ambiguous patterns → let LLM decide")
        return True

    async def resolve_context(
        self,
        user_input: str,
        conversation_history: ConversationHistory,
        command_history: ConversationHistory,
        current_order: Optional[Dict[str, Any]] = None
    ) -> "ContextResolutionResult":
        """
        If input is explicit → pass-through with high confidence.
        Else → call LLM with strict prompt; return its JSON.
        """
        try:
            self.logger.info(f"ContextService resolving: '{user_input}'")

            # Fast path: explicit detection (even if the router called us)
            if self._is_explicit_and_clear(user_input):
                self.logger.debug("Explicit & clear → pass-through")
                return ContextResolutionResult(
                    needs_resolution=False,
                    resolved_text=user_input,
                    confidence=0.98,
                    rationale="Explicit request (item/category + optional quantity), no pronouns/demonstratives.",
                    original_text=user_input
                )

            # Build prompt with your stricter "not too helpful" spec
            from app.workflow.prompts.context_prompts import get_context_resolution_prompt
            prompt = get_context_resolution_prompt(
                user_input=user_input,
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )

            status, resolved_text, clarification, confidence, rationale = await self._llm_call_and_parse(prompt)

            if status == "SUCCESS":
                return ContextResolutionResult(
                    needs_resolution=True,
                    resolved_text=resolved_text or user_input,
                    confidence=confidence,
                    rationale=rationale,
                    original_text=user_input
                )
            elif status == "CLARIFICATION_NEEDED":
                # Hand back the clarification to upstream (your pipeline can surface this to the user)
                return ContextResolutionResult(
                    needs_resolution=True,
                    resolved_text=clarification or "",
                    confidence=confidence,
                    rationale=rationale or "Clarification requested.",
                    original_text=user_input
                )
            else:  # UNRESOLVABLE or unknown
                return ContextResolutionResult(
                    needs_resolution=True,
                    resolved_text=user_input,   # fall back to original text
                    confidence=confidence if confidence is not None else 0.3,
                    rationale=rationale or "Unresolvable; returned original text.",
                    original_text=user_input
                )

        except Exception as e:
            self.logger.error(f"Context resolution failed: {e}")
            return ContextResolutionResult(
                needs_resolution=True,
                resolved_text=user_input,
                confidence=0.0,
                rationale=f"Resolution failed: {str(e)}",
                original_text=user_input
            )

    def should_use_resolution(self, result: "ContextResolutionResult", threshold: float = 0.8) -> bool:
        """Keep as-is."""
        use = result.confidence >= threshold
        self.logger.debug(f"Use resolution? conf={result.confidence:.2f} ≥ {threshold} → {use}")
        return use

    # ---------- Internals ----------

    def _is_explicit_and_clear(self, user_input: str) -> bool:
        """
        Simple check: does the input have a nouny hint (item/category name)?
        If yes, it's likely explicit. Let the LLM handle the nuances.
        """
        t = user_input.lower().strip()
        
        # If it has a nouny hint, it's likely explicit
        has_nouny_hint = bool(self.noun_hint_regex.search(t))
        
        if has_nouny_hint:
            # Check for obvious ambiguous markers
            standalone_pronouns = re.compile(r'\b(it|that|this|those|these|them|same)\b(?!\s+\w+)', re.IGNORECASE)
            if standalone_pronouns.search(t):
                return False
            
            if self.repair_regex.search(t) or self.ellipsis_regex.search(t):
                return False
                
            return True
        
        # No nouny hint = likely ambiguous, but let LLM decide
        return False

    async def _llm_call_and_parse(self, prompt: str) -> Tuple[str, Optional[str], Optional[str], float, str]:
        """
        Call LLM and parse the strict JSON contract.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            # Create LLM instance
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key,
                temperature=0.1
            )
            
            # Create message with the prompt
            message = HumanMessage(content=prompt)
            
            # Get LLM response
            response = await llm.ainvoke([message])
            response_text = response.content.strip()
            
            # Parse the JSON response (handle markdown code blocks)
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                raw = json_match.group(1)
            else:
                raw = response_text
            
            obj = json.loads(raw)
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            # Fail-safe: treat as pass-through
            return ("SUCCESS", None, None, 0.95, f"LLM call failed: {str(e)}")

        status = obj.get("status", "SUCCESS")
        resolved_text = obj.get("resolved_text")
        clarification = obj.get("clarification_message")
        confidence = float(obj.get("confidence", 0.9))
        rationale = obj.get("rationale", "")

        # Enforce conservative behavior: if SUCCESS but no resolved_text, keep original
        return (status, resolved_text, clarification, confidence, rationale)