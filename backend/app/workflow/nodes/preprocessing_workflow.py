"""
Preprocessing Workflow

Handles the initial processing pipeline:
1. Noise filtering (remove background noise)
2. Intent classification 
3. Context resolution (if needed)

This keeps the orchestrator clean and modular.
"""

import logging
from typing import Dict, Any, Optional
from app.workflow.agents.noise_filter_agent import NoiseFilterAgent
from app.workflow.agents.intent_classification_agent import intent_classification_agent
from app.workflow.agents.context_agent import ContextAgent
from app.services.context_service import ContextService
from app.workflow.response.intent_classification_response import IntentClassificationResult
from app.workflow.agents.context_agent import ContextAgentResult
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.constants.audio_phrases import AudioPhraseType
from app.workflow.nodes.clarification_workflow import ClarificationWorkflow
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class PreprocessingWorkflow:
    """
    Workflow for preprocessing user input through noise filtering,
    intent classification, and context resolution.
    """
    
    def __init__(self):
        """Initialize the preprocessing workflow"""
        self.logger = logger
        self.noise_filter_agent = NoiseFilterAgent()
        self.context_agent = ContextAgent()
        self.context_service = ContextService()
        self.clarification_workflow = ClarificationWorkflow()
    
    async def execute(
        self,
        text_input: str,
        session_id: str,
        conversation_history: ConversationHistory,
        command_history: ConversationHistory,
        current_order: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute the preprocessing pipeline.
        
        Args:
            text_input: Raw user input
            session_id: Session identifier
            conversation_history: Previous conversation turns
            command_history: Previous command history
            current_order: Current order state
            
        Returns:
            WorkflowResult with processed input and intent, or clarification needed
        """
        try:
            self.logger.info(f"Preprocessing workflow starting for: '{text_input}'")
            
            # DEBUG: Log input data
            self.logger.info(f"DEBUG PREPROCESSING WORKFLOW:")
            self.logger.info(f"  Text input: '{text_input}'")
            self.logger.info(f"  Session ID: {session_id}")
            self.logger.info(f"  Conversation history length: {len(conversation_history)}")
            self.logger.info(f"  Command history length: {len(command_history)}")
            if not conversation_history.is_empty():
                self.logger.info(f"  Conversation history format:")
                for i, entry in enumerate(conversation_history.get_recent_entries(2)):
                    self.logger.info(f"    {i+1}. {entry.role.value}: {entry.content[:50]}...")
            else:
                self.logger.info(f"  Conversation history: EMPTY")
            
            # Step 1: Noise filtering
            cleaned_input = await self.noise_filter_agent.filter_noise(text_input)
            self.logger.info(f"Noise filtering: '{text_input}' → '{cleaned_input}'")
            
            # Step 2: Intent classification
            intent_result = await intent_classification_agent(
                user_input=cleaned_input,
                conversation_history=conversation_history,
                order_items=current_order.get('items', []) if current_order else []
            )
            self.logger.info(f"Intent classification: {intent_result.intent.value}")
            
            # Step 3: Check if context resolution is needed
            if self.context_service.check_eligibility(cleaned_input, intent_result.intent.value):
                self.logger.info("Context resolution needed")
                
                # Step 4: Context resolution
                context_result = await self.context_agent.resolve_context(
                    user_input=cleaned_input,
                    conversation_history=conversation_history,
                    command_history=command_history,
                    current_order=current_order
                )
                
                if context_result.status == "SUCCESS":
                    # Use resolved text for workflow execution
                    resolved_input = context_result.resolved_text
                    self.logger.info(f"Context resolved: '{cleaned_input}' → '{resolved_input}'")
                    
                    return WorkflowResult(
                        success=True,
                        message="",  # Empty message for preprocessing
                        workflow_type=WorkflowType.PREPROCESSING,
                        audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,  # Default phrase type
                        processed_input=resolved_input,
                        intent=intent_result.intent,
                        needs_clarification=False
                    )
                
                elif context_result.status in ["CLARIFICATION_NEEDED", "UNRESOLVABLE"]:
                    # Handle clarification scenario
                    self.logger.info(f"Clarification needed: {context_result.status}")
                    
                    clarification_result = await self.clarification_workflow.execute(
                        clarification_message=context_result.clarification_message,
                        session_id=session_id,
                        conversation_history=conversation_history
                    )
                    
                    return clarification_result
            
            # No context resolution needed, use cleaned input
            self.logger.info("No context resolution needed, using cleaned input")
            
            return WorkflowResult(
                success=True,
                message="",  # Empty message for preprocessing
                workflow_type=WorkflowType.PREPROCESSING,
                audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,  # Default phrase type
                processed_input=cleaned_input,
                intent=intent_result.intent,
                needs_clarification=False
            )
            
        except Exception as e:
            self.logger.error(f"Preprocessing workflow failed: {e}", exc_info=True)
            
            # Return error result
            return WorkflowResult(
                success=False,
                message=f"Preprocessing failed: {str(e)}",
                workflow_type=WorkflowType.PREPROCESSING,
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
                error=f"Preprocessing failed: {str(e)}",
                needs_clarification=False
            )
