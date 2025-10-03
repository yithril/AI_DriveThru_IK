"""
Clarification Workflow

Handles clarification scenarios where the system needs to ask the customer
for more information before proceeding with their request.
"""

import logging
from typing import Dict, Any, Optional, List
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


class ClarificationWorkflow:
    """
    Workflow for handling clarification scenarios.
    
    This workflow is triggered when the system needs to ask the customer
    for clarification before processing their request.
    """
    
    def __init__(self):
        """Initialize the clarification workflow"""
        self.logger = logger
    
    async def execute(
        self,
        clarification_message: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> WorkflowResult:
        """
        Execute clarification workflow.
        
        Args:
            clarification_message: The message to ask the customer
            session_id: Customer session ID
            conversation_history: Recent conversation history (optional)
            
        Returns:
            WorkflowResult with clarification message
        """
        try:
            self.logger.info(f"Clarification workflow executing for session {session_id}")
            self.logger.info(f"Clarification message: {clarification_message}")
            
            # Return clarification result
            return WorkflowResult(
                success=False,  # Not a successful completion, needs customer response
                message=clarification_message,
                workflow_type=WorkflowType.CLARIFICATION,
                audio_phrase_type=AudioPhraseType.LLM_GENERATED,  # Use custom message
                order_updated=False,
                validation_errors=None
            )
            
        except Exception as e:
            self.logger.error(f"Clarification workflow failed: {e}", exc_info=True)
            return WorkflowResult(
                success=False,
                message="I'm sorry, I didn't understand that. Could you please try again?",
                workflow_type=WorkflowType.ERROR_RECOVERY,
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
                order_updated=False,
                validation_errors=[str(e)]
            )
