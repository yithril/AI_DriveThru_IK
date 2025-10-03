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
from app.workflow.nodes.clarification_workflow import ClarificationWorkflow

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
        conversation_history: list,
        command_history: list,
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
            
            # Step 1: Noise filtering
            cleaned_input = await self.noise_filter_agent.filter_noise(text_input)
            self.logger.info(f"Noise filtering: '{text_input}' → '{cleaned_input}'")
            
            # Step 2: Intent classification
            intent_result = await intent_classification_agent(cleaned_input)
            self.logger.info(f"Intent classification: {intent_result.intent.value}")
            
            # Step 3: Check if context resolution is needed
            if self.context_service.check_eligibility(cleaned_input, intent_result.intent.value):
                self.logger.info("Context resolution needed")
                
                # Step 4: Context resolution
                context_result = await self.context_agent.resolve_context(
                    utterance=cleaned_input,
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
                        workflow_type=WorkflowType.PREPROCESSING,
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
                workflow_type=WorkflowType.PREPROCESSING,
                processed_input=cleaned_input,
                intent=intent_result.intent,
                needs_clarification=False
            )
            
        except Exception as e:
            self.logger.error(f"Preprocessing workflow failed: {e}", exc_info=True)
            
            # Return error result
            return WorkflowResult(
                success=False,
                workflow_type=WorkflowType.PREPROCESSING,
                error_message=f"Preprocessing failed: {str(e)}",
                needs_clarification=False
            )
