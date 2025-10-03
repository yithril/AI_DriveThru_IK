"""
Context Agent for resolving ambiguous user input using conversation and command history.

This agent transforms ambiguous utterances like "I'll take two" into explicit text like
"I'll take two veggie wraps" using conversation context.
"""

import logging
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from app.workflow.prompts.context_prompts import get_context_resolution_prompt
from app.config.settings import settings
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


@dataclass
class ContextAgentResult:
    """Result from context agent"""
    status: Literal["SUCCESS", "CLARIFICATION_NEEDED", "UNRESOLVABLE", "SYSTEM_ERROR"]
    resolved_text: Optional[str] = None
    clarification_message: Optional[str] = None
    confidence: float = 0.0
    rationale: str = ""


class ContextAgent:
    """
    Agent for resolving context in ambiguous user input.
    
    This agent:
    1. Takes ambiguous input + conversation/command history
    2. Uses LLM to resolve context
    3. Returns either resolved text or clarification request
    """
    
    def __init__(self):
        """Initialize the context agent"""
        self.logger = logger
    
    async def resolve_context(
        self,
        user_input: str,
        conversation_history: ConversationHistory,
        command_history: ConversationHistory,
        current_order: Optional[Dict[str, Any]] = None
    ) -> ContextAgentResult:
        """
        Resolve context for ambiguous user input.
        
        Args:
            user_input: The ambiguous user input
            conversation_history: Recent conversation turns
            command_history: Recent command history
            current_order: Current order state (optional)
            
        Returns:
            ContextAgentResult: Either resolved text or clarification request
        """
        try:
            self.logger.info(f"Resolving context for input: '{user_input}'")
            
            # DEBUG: Log the input data
            self.logger.info(f"DEBUG CONTEXT INPUT:")
            self.logger.info(f"  User input: '{user_input}'")
            self.logger.info(f"  Conversation history length: {len(conversation_history)}")
            self.logger.info(f"  Command history length: {len(command_history)}")
            self.logger.info(f"  Current order: {current_order}")
            
            # DEBUG: Log conversation history details
            if not conversation_history.is_empty():
                self.logger.info(f"  Conversation history:")
                for i, entry in enumerate(conversation_history.get_recent_entries(3)):  # Last 3 entries
                    self.logger.info(f"    {i+1}. {entry.role.value}: {entry.content[:100]}...")
            else:
                self.logger.info(f"  Conversation history: EMPTY")
            
            # DEBUG: Log command history details
            if not command_history.is_empty():
                self.logger.info(f"  Command history:")
                for i, entry in enumerate(command_history.get_recent_entries(3)):  # Last 3 entries
                    self.logger.info(f"    {i+1}. {entry.role.value}: {entry.content[:100]}...")
            else:
                self.logger.info(f"  Command history: EMPTY")
            
            # Build context for LLM
            context_data = self._build_context_data(
                conversation_history, command_history, current_order
            )
            
            # Get prompt for LLM
            prompt = get_context_resolution_prompt(
                user_input=user_input,
                conversation_history=conversation_history,
                command_history=command_history,
                current_order=current_order
            )
            
            # Use LLM to resolve context
            result = await self._llm_resolve_context(prompt, context_data, user_input)
            
            self.logger.info(f"Context resolution result: status={result.status}, "
                           f"confidence={result.confidence:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Context agent failed: {e}")
            return ContextAgentResult(
                status="SYSTEM_ERROR",
                rationale=f"Agent failed: {str(e)}"
            )
    
    def _build_context_data(
        self,
        conversation_history: ConversationHistory,
        command_history: ConversationHistory,
        current_order: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build context data for LLM"""
        return {
            "conversation_history": conversation_history.get_recent_entries(5),
            "command_history": command_history.get_recent_entries(5),
            "current_order": current_order or {},
            "context_summary": self._build_context_summary(
                conversation_history, command_history, current_order
            )
        }
    
    def _build_context_summary(
        self,
        conversation_history: ConversationHistory,
        command_history: ConversationHistory,
        current_order: Optional[Dict[str, Any]]
    ) -> str:
        """Build a summary of context for the LLM"""
        summary_parts = []
        
        # Recent conversation (last 3 turns)
        if not conversation_history.is_empty():
            recent_conv = conversation_history.get_recent_entries(3)
            conv_text = "\n".join([
                f"{entry.role.value}: {entry.content}" 
                for entry in recent_conv
            ])
            summary_parts.append(f"Recent conversation:\n{conv_text}")
        
        # Current order summary
        if current_order and current_order.get('items'):
            order_items = current_order['items']
            order_text = ", ".join([
                f"{item.get('quantity', 1)}x {item.get('name', 'Unknown')}" 
                for item in order_items
            ])
            summary_parts.append(f"Current order: {order_text}")
        
        # Recent commands (last 3 commands)
        if not command_history.is_empty():
            recent_commands = command_history.get_recent_entries(3)
            cmd_text = "\n".join([
                f"Command: {entry.role.value} - {entry.content}" 
                for entry in recent_commands
            ])
            summary_parts.append(f"Recent commands:\n{cmd_text}")
        
        return "\n\n".join(summary_parts)
    
    async def _llm_resolve_context(
        self, 
        prompt: str, 
        context_data: Dict[str, Any],
        user_input: str
    ) -> ContextAgentResult:
        """
        Use LLM to resolve context.
        
        Args:
            prompt: The formatted prompt for the LLM
            context_data: Context data for the LLM
            
        Returns:
            ContextAgentResult: Resolution result
        """
        # Use real LLM for context resolution
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
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = response_text
            
            try:
                result_data = json.loads(json_text)
                
                return ContextAgentResult(
                    status=result_data.get("status", "CLARIFICATION_NEEDED"),
                    resolved_text=result_data.get("resolved_text"),
                    clarification_message=result_data.get("clarification_message"),
                    confidence=result_data.get("confidence", 0.5),
                    rationale=result_data.get("rationale", "LLM-based resolution")
                )
                
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse LLM response as JSON: {response_text}")
                return ContextAgentResult(
                    status="SYSTEM_ERROR",
                    rationale=f"Failed to parse LLM response: {response_text}"
                )
                
        except Exception as e:
            self.logger.error(f"LLM context resolution failed: {e}")
            return ContextAgentResult(
                status="SYSTEM_ERROR",
                rationale=f"LLM resolution failed: {str(e)}"
            )
