"""
Noise Filter Agent

Filters background noise from user input while preserving all order-related content.
This agent removes obvious background noise (phone calls, passenger chatter) but preserves
natural speech patterns and all semantic information related to ordering.
"""

import logging
from typing import Optional
from app.workflow.prompts.noise_filter_prompts import get_noise_filter_prompt
from app.config.settings import settings

logger = logging.getLogger(__name__)


class NoiseFilterAgent:
    """
    Agent for filtering background noise from user input.
    
    This agent:
    1. Takes raw user input (potentially with background noise)
    2. Uses LLM to identify and remove background noise
    3. Returns cleaned input with all order-related content preserved
    """
    
    def __init__(self):
        """Initialize the noise filter agent"""
        self.logger = logger
    
    async def filter_noise(self, user_input: str) -> str:
        """
        Filter background noise from user input.
        
        Args:
            user_input: Raw user input that may contain background noise
            
        Returns:
            str: Cleaned input with background noise removed but order content preserved
        """
        try:
            self.logger.info(f"Noise filter processing: '{user_input}'")
            
            # Get the prompt for noise filtering
            prompt = get_noise_filter_prompt(user_input)
            
            # Use real LLM for noise filtering
            result = await self._llm_filter_noise(prompt, user_input)
            
            self.logger.info(f"Noise filter result: '{user_input}' → '{result}'")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Noise filter failed: {e}", exc_info=True)
            # Return original input if filtering fails
            return user_input
    
    async def _llm_filter_noise(self, prompt: str, user_input: str) -> str:
        """
        Use LLM to filter background noise.
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            # Create LLM instance
            llm = ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key,
                temperature=0.1  # Low temperature for consistent filtering
            )
            
            # Create message with the prompt
            message = HumanMessage(content=prompt)
            
            # Get LLM response
            response = await llm.ainvoke([message])
            result = response.content.strip()
            
            # If LLM returns empty or just whitespace, return original input
            if not result or result.isspace():
                self.logger.warning("LLM returned empty result, using original input")
                return user_input
            
            return result
            
        except Exception as e:
            self.logger.error(f"LLM noise filtering failed: {e}")
            # Return original input if LLM fails
            return user_input
