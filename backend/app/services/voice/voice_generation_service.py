"""
Voice Generation Service - Thin wrapper for conversation workflows
"""

import logging
from typing import Dict, Any, Optional
from .voice_service import VoiceService
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


class VoiceGenerationService:
    """
    Wrapper for voice service used in conversation workflows.
    Just provides a more convenient interface.
    """
    
    def __init__(self, voice_service: VoiceService):
        self.voice_service = voice_service
    
    async def generate_voice_response(
        self,
        response_text: str,
        response_phrase_type: Optional[AudioPhraseType],
        restaurant_id: str,
        restaurant_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate audio for conversation response.
        
        Args:
            response_text: Text to speak
            response_phrase_type: Type of phrase (optional)
            restaurant_id: Restaurant ID
            restaurant_name: Restaurant name for templates
            
        Returns:
            Dict with audio_url and response_text
        """
        try:
            if not response_phrase_type:
                logger.warning("No phrase type provided")
                return {
                    "success": False,
                    "response_text": response_text or "I'm sorry, please try again.",
                    "audio_url": None
                }
            
            # Generate audio
            audio_url = await self.voice_service.generate_from_phrase_type(
                phrase_type=response_phrase_type,
                restaurant_id=int(restaurant_id),
                custom_text=response_text if response_text else None,
                restaurant_name=restaurant_name
            )
            
            return {
                "success": True,
                "response_text": response_text,
                "audio_url": audio_url
            }
            
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return {
                "success": False,
                "response_text": response_text or "I'm sorry, please try again.",
                "audio_url": None
            }
