"""
Question Answer Workflow - Handles customer questions about menu, ingredients, restaurant info, etc.

Uses the existing question_agent to process questions and return structured responses.
"""

import logging
from typing import Dict, Any, Optional, List
from app.workflow.agents.question_agent import question_agent
from app.workflow.response.workflow_result import QuestionAnswerWorkflowResult, WorkflowType
from app.constants.audio_phrases import AudioPhraseType
from app.dto.conversation_dto import ConversationHistory

logger = logging.getLogger(__name__)


class QuestionAnswerWorkflow:
    """
    Workflow for handling customer questions.
    
    This workflow uses the existing question_agent which has tools to search
    menu items, ingredients, and restaurant information.
    """
    
    def __init__(
        self, 
        restaurant_id: int,
        menu_service,
        ingredient_service,
        restaurant_service,
        category_service=None
    ):
        self.restaurant_id = restaurant_id
        self.menu_service = menu_service
        self.ingredient_service = ingredient_service
        self.restaurant_service = restaurant_service
        self.category_service = category_service
    
    async def execute(
        self, 
        user_input: str,
        conversation_history: Optional[ConversationHistory] = None,
        current_order: Optional[Dict[str, Any]] = None
    ) -> QuestionAnswerWorkflowResult:
        """
        Execute the question-answer workflow.
        
        Args:
            user_input: The customer's question
            conversation_history: Recent conversation turns (optional)
            current_order: Current order state (optional)
            
        Returns:
            QuestionAnswerWorkflowResult with the answer and metadata
        """
        try:
            logger.info(f"Processing question: {user_input}")
            
            # Call the question agent
            agent_result = await question_agent(
                user_input=user_input,
                restaurant_id=self.restaurant_id,
                menu_service=self.menu_service,
                ingredient_service=self.ingredient_service,
                restaurant_service=self.restaurant_service,
                category_service=self.category_service,
                conversation_history=conversation_history or ConversationHistory(session_id=""),
                current_order=current_order or {}
            )
            
            # Map agent result to workflow result
            audio_phrase_type = self._map_category_to_audio_phrase(agent_result.category)
            
            return QuestionAnswerWorkflowResult(
                success=True,
                message=agent_result.response_text,
                question_category=agent_result.category,
                confidence_score=agent_result.confidence,
                relevant_data=agent_result.relevant_data,
                audio_phrase_type=audio_phrase_type
            )
            
        except Exception as e:
            logger.error(f"Question workflow failed: {e}", exc_info=True)
            return QuestionAnswerWorkflowResult(
                success=False,
                message="I'm sorry, I couldn't process your question. Please try again.",
                question_category="general",
                error=str(e),
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
    
    def _map_category_to_audio_phrase(self, category: str) -> AudioPhraseType:
        """
        Map question category to appropriate audio phrase type.
        
        Args:
            category: The question category from the agent
            
        Returns:
            Appropriate AudioPhraseType for voice generation
        """
        if category == "restaurant_info":
            return AudioPhraseType.RESTAURANT_INFO
        elif category in ["menu", "order"]:
            return AudioPhraseType.QUESTION_ANSWERED
        elif category == "general":
            return AudioPhraseType.QUESTION_NOT_FOUND
        else:
            return AudioPhraseType.CUSTOM_RESPONSE
