"""
Workflow Orchestrator - Main entry point for voice processing

Handles the complete flow:
1. Speech-to-Text (OpenAI Whisper)
2. Intent Classification
3. Workflow Routing
4. Voice Generation (TTS)
"""

import logging
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.dto.conversation_dto import ConversationHistory

from app.workflow.nodes.preprocessing_workflow import PreprocessingWorkflow
from app.workflow.nodes.add_item_workflow import AddItemWorkflow
from app.workflow.nodes.modify_item_workflow import ModifyItemWorkflow
from app.workflow.nodes.remove_item_workflow import RemoveItemWorkflow
from app.workflow.nodes.clear_order_workflow import ClearOrderWorkflow
from app.workflow.nodes.confirm_order_workflow import ConfirmOrderWorkflow
from app.workflow.nodes.question_answer_workflow import QuestionAnswerWorkflow
from app.workflow.nodes.clarification_workflow import ClarificationWorkflow
from app.services.voice.voice_service import VoiceService
from app.services.order_session_service import OrderSessionService
from app.services.session_service import SessionService
from app.services.menu_resolution_service import MenuResolutionService
from app.services.menu_service import MenuService
from app.services.ingredient_service import IngredientService
from app.services.restaurant_service import RestaurantService
from app.constants.intent_types import IntentType
from app.constants.audio_phrases import AudioPhraseType, AudioPhraseConstants
from app.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class VoiceProcessingResult:
    """Result of voice processing workflow"""
    success: bool
    message: str
    audio_url: Optional[str] = None
    order_updated: bool = False
    validation_errors: List[str] = None
    workflow_type: str = "unknown"
    confidence_score: Optional[float] = None


@dataclass
class SessionCreationResult:
    """Result of session creation"""
    session_id: str
    greeting_audio_url: Optional[str] = None


class WorkflowOrchestrator:
    """
    Main orchestrator for voice processing workflows.
    
    Coordinates the complete flow from speech-to-text to text-to-speech.
    """
    
    def __init__(
        self,
        voice_service: VoiceService,
        order_session_service: OrderSessionService,
        menu_resolution_service: MenuResolutionService,
        menu_service: MenuService,
        ingredient_service: IngredientService,
        restaurant_service: RestaurantService,
        session_service: SessionService
    ):
        self.voice_service = voice_service
        self.order_session_service = order_session_service
        self.session_service = session_service
        self.menu_resolution_service = menu_resolution_service
        self.menu_service = menu_service
        self.ingredient_service = ingredient_service
        self.restaurant_service = restaurant_service
        
        # Initialize preprocessing workflow
        self.preprocessing_workflow = PreprocessingWorkflow()
        
        # Initialize workflows
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """Initialize all workflow instances"""
        self.add_item_workflow = AddItemWorkflow(
            restaurant_id=None,  # Will be set per request
            menu_resolution_service=self.menu_resolution_service,
            order_session_service=self.order_session_service,
            ingredient_service=self.ingredient_service
        )
        
        self.modify_item_workflow = ModifyItemWorkflow(
            order_session_service=self.order_session_service
        )
        
        self.remove_item_workflow = RemoveItemWorkflow(
            order_session_service=self.order_session_service
        )
        
        self.clear_order_workflow = ClearOrderWorkflow(
            order_session_service=self.order_session_service
        )
        
        self.confirm_order_workflow = ConfirmOrderWorkflow(
            order_session_service=self.order_session_service
        )
        
        self.question_answer_workflow = QuestionAnswerWorkflow(
            restaurant_id=None,  # Will be set per request
            menu_service=self.menu_service,
            ingredient_service=self.ingredient_service,
            restaurant_service=self.restaurant_service
        )
        
        self.clarification_workflow = ClarificationWorkflow()
    
    async def process_voice_input(
        self,
        audio_content: bytes,
        session_id: str,
        restaurant_id: int,
        language: str = "en"
    ) -> VoiceProcessingResult:
        """
        Process voice input through the complete workflow pipeline.
        
        Args:
            audio_content: Raw audio bytes
            session_id: Customer session ID
            restaurant_id: Restaurant ID
            language: Language code for STT
            
        Returns:
            VoiceProcessingResult with response and audio URL
        """
        try:
            logger.info(f"Starting voice processing for session {session_id}")
            
            # Step 1: Speech-to-Text
            text_input = await self._speech_to_text(audio_content, language, restaurant_id)
            if not text_input:
                return VoiceProcessingResult(
                    success=False,
                    message="Sorry, I couldn't understand what you said. Please try again.",
                    audio_url=await self._generate_error_audio(restaurant_id)
                )
            
            logger.info(f"STT result: '{text_input}'")
            
            # Step 2: Get conversation context
            conversation_history = await self._get_conversation_history(session_id)
            current_order = await self._get_current_order(session_id)
            
            # DEBUG: Log conversation history format
            logger.info(f"DEBUG WORKFLOW ORCHESTRATOR:")
            logger.info(f"  Session ID: {session_id}")
            logger.info(f"  Conversation history length: {len(conversation_history)}")
            if not conversation_history.is_empty():
                logger.info(f"  Conversation history format:")
                for i, entry in enumerate(conversation_history.get_recent_entries(2)):
                    logger.info(f"    {i+1}. {entry.role.value}: {entry.content[:50]}...")
            else:
                logger.info(f"  Conversation history: EMPTY")
            
            # Step 3: Preprocessing (noise filter + intent classification + context resolution)
            preprocessing_result = await self.preprocessing_workflow.execute(
                text_input=text_input,
                session_id=session_id,
                conversation_history=conversation_history,
                command_history=conversation_history,  # Use conversation as command history
                current_order=current_order
            )
            
            # Check if clarification is needed
            if preprocessing_result.needs_clarification:
                # Generate voice response for clarification
                audio_url = await self._generate_voice_response(
                    workflow_result=preprocessing_result,
                    restaurant_id=restaurant_id
                )
                
                return VoiceProcessingResult(
                    success=preprocessing_result.success,
                    message=preprocessing_result.message,
                    audio_url=audio_url,
                    order_updated=preprocessing_result.order_updated,
                    validation_errors=preprocessing_result.validation_errors,
                    workflow_type=preprocessing_result.workflow_type.value,
                    confidence_score=None
                )
            
            # Step 4: Route to appropriate workflow
            workflow_result = await self._execute_workflow(
                intent=preprocessing_result.intent,
                user_input=preprocessing_result.processed_input,
                session_id=session_id,
                restaurant_id=restaurant_id,
                conversation_history=conversation_history,
                current_order=current_order
            )
            
            # Step 5: Generate voice response
            audio_url = await self._generate_voice_response(
                workflow_result=workflow_result,
                restaurant_id=restaurant_id
            )
            
            # Step 6: Update conversation history
            await self._update_conversation_history(
                session_id=session_id,
                user_input=text_input,
                ai_response=workflow_result.message
            )
            
            return VoiceProcessingResult(
                success=workflow_result.success,
                message=workflow_result.message,
                audio_url=audio_url,
                order_updated=workflow_result.order_updated,
                validation_errors=workflow_result.validation_errors,
                workflow_type=workflow_result.workflow_type.value,
                confidence_score=workflow_result.confidence_score
            )
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}", exc_info=True)
            return VoiceProcessingResult(
                success=False,
                message="Sorry, I encountered an error. Please try again.",
                audio_url=await self._generate_error_audio(restaurant_id),
                validation_errors=[str(e)]
            )
    
    async def create_session(self, restaurant_id: int) -> SessionCreationResult:
        """Create a new customer session with greeting"""
        try:
            # This method should not be used - sessions are created via the sessions API
            # This is a legacy method that should be removed
            raise NotImplementedError("Session creation should be done via /api/sessions/new-car endpoint")
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}", exc_info=True)
            raise
    
    async def _speech_to_text(self, audio_content: bytes, language: str, restaurant_id: int) -> Optional[str]:
        """Convert audio to text using OpenAI Whisper with menu context"""
        try:
            import openai
            import io
            from app.workflow.prompts.stt_prompts import build_stt_prompt, get_basic_stt_prompt
            
            # Get menu items for context
            menu_items = []
            restaurant_name = "restaurant"
            
            try:
                # Get menu items for the restaurant
                menu_items = await self.menu_service.get_menu_items(restaurant_id)
                
                # Get restaurant name for context
                restaurant = await self.restaurant_service.get_by_id(restaurant_id)
                if restaurant:
                    restaurant_name = restaurant.name
                    
            except Exception as e:
                logger.warning(f"Could not get menu context for STT: {e}")
                # Continue with basic prompt if menu data unavailable
            
            # Build STT prompt with menu context
            if menu_items:
                stt_prompt = build_stt_prompt(menu_items, restaurant_name)
                logger.info(f"Using STT prompt with {len(menu_items)} menu items")
            else:
                stt_prompt = get_basic_stt_prompt()
                logger.info("Using basic STT prompt (no menu context)")
            
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_content)
            audio_file.name = "audio.webm"  # Set filename for OpenAI
            
            # Call OpenAI Whisper API with prompt
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                prompt=stt_prompt,
                temperature=0.0  # Explicit for consistency
            )
            
            return response.strip() if response else None
            
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            return None
    
    async def _execute_workflow(
        self,
        intent: IntentType,
        user_input: str,
        session_id: str,
        restaurant_id: int,
        conversation_history: List[Dict[str, Any]],
        current_order: Optional[Dict[str, Any]]
    ):
        """Execute the appropriate workflow based on intent"""
        
        # Set restaurant ID for workflows that need it
        self.add_item_workflow.restaurant_id = restaurant_id
        self.question_answer_workflow.restaurant_id = restaurant_id
        
        if intent == IntentType.ADD_ITEM:
            return await self.add_item_workflow.execute(
                user_input=user_input,
                session_id=session_id,
                conversation_history=conversation_history,
                current_order=current_order
            )
        
        elif intent == IntentType.MODIFY_ITEM:
            return await self.modify_item_workflow.execute(
                user_input=user_input,
                session_id=session_id,
                conversation_history=conversation_history,
                command_history=conversation_history  # Use conversation as command history
            )
        
        elif intent == IntentType.REMOVE_ITEM:
            return await self.remove_item_workflow.execute(
                user_input=user_input,
                session_id=session_id,
                conversation_history=conversation_history,
                command_history=conversation_history
            )
        
        elif intent == IntentType.CLEAR_ORDER:
            return await self.clear_order_workflow.execute(
                session_id=session_id,
                conversation_history=conversation_history
            )
        
        elif intent == IntentType.CONFIRM_ORDER:
            return await self.confirm_order_workflow.execute(
                session_id=session_id,
                conversation_history=conversation_history
            )
        
        elif intent == IntentType.QUESTION:
            return await self.question_answer_workflow.execute(
                user_input=user_input,
                conversation_history=conversation_history,
                current_order=current_order
            )
        
        else:
            # Unknown intent - return error response
            from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
            return WorkflowResult(
                success=False,
                message="Sorry, I didn't understand that. Could you please try again?",
                workflow_type=WorkflowType.ERROR_RECOVERY,
                audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY
            )
    
    async def _generate_voice_response(
        self,
        workflow_result,
        restaurant_id: int
    ) -> Optional[str]:
        """Generate voice response from workflow result"""
        try:
            # Use custom message if available, otherwise use phrase type
            if hasattr(workflow_result, 'message') and workflow_result.message:
                # For custom messages, generate TTS directly
                return await self.voice_service.generate_audio(
                    text=workflow_result.message,
                    restaurant_id=restaurant_id
                )
            else:
                # Use phrase type for standard responses
                return await self.voice_service.generate_from_phrase_type(
                    phrase_type=workflow_result.audio_phrase_type,
                    restaurant_id=restaurant_id
                )
                
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return None
    
    async def _generate_error_audio(self, restaurant_id: int) -> Optional[str]:
        """Generate error audio response"""
        try:
            return await self.voice_service.generate_from_phrase_type(
                phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
                restaurant_id=restaurant_id
            )
        except Exception as e:
            logger.error(f"Error audio generation failed: {e}")
            return None
    
    async def _generate_voice_response_from_text(self, text: str, restaurant_id: int) -> Optional[str]:
        """Generate voice response from text"""
        try:
            return await self.voice_service.generate_audio(
                text=text,
                restaurant_id=restaurant_id
            )
        except Exception as e:
            logger.error(f"Voice generation from text failed: {e}")
            return None
    
    async def _get_conversation_history(self, session_id: str) -> ConversationHistory:
        """Get conversation history for session"""
        try:
            return await self.session_service.get_conversation_history(session_id)
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return ConversationHistory(session_id=session_id)
    
    async def _get_current_order(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current order for session"""
        try:
            return await self.order_session_service.get_session_order(session_id)
        except Exception as e:
            logger.error(f"Failed to get current order: {e}")
            return None
    
    async def _update_conversation_history(
        self,
        session_id: str,
        user_input: str,
        ai_response: str
    ):
        """Update conversation history for session"""
        try:
            await self.session_service.add_conversation_entry(
                session_id=session_id,
                user_input=user_input,
                ai_response=ai_response
            )
            logger.info(f"Conversation update for {session_id}: User: '{user_input}' -> AI: '{ai_response}'")
        except Exception as e:
            logger.error(f"Failed to update conversation history: {e}")
