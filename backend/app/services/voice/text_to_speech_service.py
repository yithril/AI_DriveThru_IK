"""
Text-to-Speech service
"""

from typing import AsyncGenerator
from .tts_provider import TTSProvider
import logging

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """
    TTS service that handles text-to-speech generation
    """
    
    def __init__(self, provider: TTSProvider):
        self.provider = provider
    
    async def generate_audio_stream(self, text: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate audio stream from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        logger.info(f"Generating audio for text: '{text[:50]}...' with voice: {voice}")
        
        try:
            async for chunk in self.provider.generate_audio_stream(text, voice):
                yield chunk
                
        except Exception as e:
            logger.error(f"TTS generation failed: {str(e)}")
            raise Exception(f"Failed to generate audio: {str(e)}")

