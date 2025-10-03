"""
Voice Controller - Handles voice input processing for AI drive-thru
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.voice.text_to_speech_service import TextToSpeechService
from app.services.session_service import SessionService
from app.utils.performance_timer import PerformanceTimer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Voice Processing"])


@router.post("/process-audio")
@inject
async def process_audio(
    audio_file: UploadFile = File(...),
    session_id: str = Form(...),
    restaurant_id: int = Form(...),
    language: str = Form(default="en"),
    workflow_orchestrator: WorkflowOrchestrator = Depends(Provide[Container.workflow_orchestrator]),
    tts_service: TextToSpeechService = Depends(Provide[Container.text_to_speech_service]),
    session_service: SessionService = Depends(Provide[Container.session_service])
) -> Dict[str, Any]:
    """
    Process voice input and return AI response with audio.
    
    Expected by frontend:
    - audio_file: Audio file (WebM format)
    - session_id: Customer session ID
    - restaurant_id: Restaurant ID
    - language: Language code (default: "en")
    
    Returns:
    {
        "success": bool,
        "session_id": str,
        "audio_url": str,
        "response_text": str,
        "order_state_changed": bool,
        "metadata": {
            "processing_time": number,
            "cached": bool,
            "errors": string[] | null
        }
    }
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Processing audio for session {session_id}, restaurant {restaurant_id}")
        
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file type")
        
        # Read audio file content
        audio_content = await audio_file.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        logger.info(f"Audio file received: {len(audio_content)} bytes, type: {audio_file.content_type}")
        
        # Process through workflow orchestrator with performance timing
        with PerformanceTimer("total_voice_processing", session_id, session_service, {
            "audio_size_bytes": len(audio_content),
            "content_type": audio_file.content_type,
            "language": language
        }):
            result = await workflow_orchestrator.process_voice_input(
                audio_content=audio_content,
                session_id=session_id,
                restaurant_id=restaurant_id,
                language=language
            )
        
        processing_time = time.time() - start_time
        
        # Build response matching frontend expectations
        # Note: We consider it "success" if we have a response (even validation errors)
        # The frontend should handle validation errors as normal responses with audio
        response = {
            "success": True,  # Always True if we have a response with audio
            "session_id": session_id,
            "audio_url": result.audio_url or "",
            "response_text": result.message,
            "order_state_changed": result.order_updated,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "cached": False,
                "errors": result.validation_errors if result.validation_errors else None,
                "workflow_success": result.success,  # Include the actual workflow success status
                "workflow_type": result.workflow_type
            }
        }
        
        logger.info(f"DEBUG: Response data: {getattr(result, 'data', 'No data attribute')}")
        logger.info(f"Voice processing completed in {processing_time:.2f}s for session {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice processing failed for session {session_id}: {e}", exc_info=True)
        processing_time = time.time() - start_time
        
        # Return error response in expected format
        return {
            "success": False,
            "session_id": session_id,
            "audio_url": "",
            "response_text": "Sorry, I couldn't process your request. Please try again.",
            "order_state_changed": False,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "cached": False,
                "errors": [str(e)]
            }
        }


@router.post("/create-session")
@inject
async def create_session(
    restaurant_id: int = Form(...),
    workflow_orchestrator: WorkflowOrchestrator = Depends(Provide[Container.workflow_orchestrator])
) -> Dict[str, Any]:
    """
    Create a new customer session.
    
    Returns:
    {
        "session_id": str,
        "greeting_audio_url": str | null
    }
    """
    try:
        result = await workflow_orchestrator.create_session(restaurant_id)
        
        return {
            "session_id": result.session_id,
            "greeting_audio_url": result.greeting_audio_url
        }
        
    except Exception as e:
        logger.error(f"Session creation failed for restaurant {restaurant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.get("/health")
async def health_check():
    """Health check for voice processing"""
    return {"status": "healthy", "service": "voice_processing"}
