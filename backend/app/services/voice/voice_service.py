"""
Voice Service - Text-to-Speech generation with caching

Simple service that:
1. Generates audio from text using OpenAI TTS
2. Caches results in Redis and S3
3. Returns audio URL
"""

import hashlib
import logging
from typing import Optional
from .text_to_speech_service import TextToSpeechService
from app.services.database.redis_service import RedisService
from app.services.storage.s3_service import S3Service
from app.constants.audio_phrases import AudioPhraseType, AudioPhraseConstants
from app.config.settings import settings

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Simple voice service with TTS generation and caching.
    """
    
    def __init__(
        self, 
        text_to_speech_service: TextToSpeechService,
        s3_service: S3Service,
        redis_service: Optional[RedisService] = None
    ):
        self.tts_service = text_to_speech_service
        self.s3_service = s3_service
        self.redis_service = redis_service
    
    async def generate_audio(
        self, 
        text: str,
        restaurant_id: int,
        voice: str = None
    ) -> Optional[str]:
        """
        Generate audio from text with caching.
        
        Args:
            text: Text to convert to speech
            restaurant_id: Restaurant ID for multitenancy
            voice: Voice to use (defaults to config)
            
        Returns:
            S3 URL to audio file or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided")
            return None
        
        voice = voice or settings.tts_voice
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(text, voice, restaurant_id)
            
            # Check Redis cache first
            if self.redis_service:
                cached_url = await self.redis_service.get(f"voice:{cache_key}")
                if cached_url:
                    return cached_url
            
            # Generate new audio
            logger.info(f"Generating TTS for: {text[:50]}...")
            audio_chunks = []
            async for chunk in self.tts_service.generate_audio_stream(text, voice):
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                logger.error("No audio chunks generated")
                return None
            
            # Upload to S3
            audio_data = b''.join(audio_chunks)
            s3_result = await self.s3_service.upload_file(
                file_data=audio_data,
                file_name=f"{cache_key}.mp3",
                restaurant_id=restaurant_id,
                file_type="audio",
                content_type="audio/mpeg"
            )
            
            if not s3_result.get("success"):
                logger.error(f"S3 upload failed: {s3_result.get('error')}")
                return None
            
            audio_url = s3_result["s3_url"]
            
            # Cache in Redis
            if self.redis_service:
                await self.redis_service.set(f"voice:{cache_key}", audio_url, expire=86400)
            
            return audio_url
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None
    
    async def generate_from_phrase_type(
        self,
        phrase_type: AudioPhraseType,
        restaurant_id: int,
        custom_text: Optional[str] = None,
        restaurant_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate audio from phrase type (convenience method).
        
        Args:
            phrase_type: Type of audio phrase
            restaurant_id: Restaurant ID
            custom_text: Override text (for dynamic phrases)
            restaurant_name: Restaurant name for templates
            
        Returns:
            S3 URL to audio file or None if failed
        """
        # Use custom text if provided, otherwise get template
        if custom_text:
            text = custom_text
        else:
            text = AudioPhraseConstants.get_phrase_text(phrase_type, restaurant_name)
        
        if not text:
            logger.error(f"No text for phrase type: {phrase_type.value}")
            return None
        
        return await self.generate_audio(
            text=text,
            restaurant_id=restaurant_id,
            voice=AudioPhraseConstants.get_standard_voice()
        )
    
    def _generate_cache_key(self, text: str, voice: str, restaurant_id: int) -> str:
        """Generate MD5 cache key from text + voice + restaurant."""
        content = f"{text}_{voice}_{restaurant_id}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
