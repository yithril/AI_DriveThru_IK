"""
TTS Provider interface and implementations
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
import asyncio


class TTSProvider(ABC):
    """
    Abstract base class for Text-to-Speech providers
    """
    
    @abstractmethod
    async def generate_audio_stream(self, text: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate audio stream from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use for generation
            
        Yields:
            bytes: Audio data chunks
        """
        pass


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS implementation
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
    
    async def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            import openai
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        return self.client
    
    async def generate_audio_stream(self, text: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Generate audio stream using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (nova, alloy, echo, fable, onyx, shimmer)
            
        Yields:
            bytes: Audio data chunks
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            client = await self._get_client()
            
            # Generate audio using OpenAI TTS
            response = await client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Get the complete audio data
            audio_data = response.content
            
            # Yield in chunks to simulate streaming
            chunk_size = 1024  # 1KB chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                yield chunk
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)
                    
        except Exception as e:
            # For now, just re-raise - we'll add proper error handling later
            raise Exception(f"TTS generation failed: {str(e)}")


class MockTTSProvider(TTSProvider):
    """
    Mock TTS provider for testing
    """
    
    async def generate_audio_stream(self, text: str, voice: str = "nova") -> AsyncGenerator[bytes, None]:
        """
        Mock implementation that generates fake audio data
        
        Args:
            text: Text to convert to speech
            voice: Voice to use
            
        Yields:
            bytes: Fake audio data chunks
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Generate fake audio data (silence)
        fake_audio = b'\x00' * 1024  # 1KB of silence
        
        # Simulate streaming by yielding chunks
        for i in range(10):  # 10 chunks of 1KB each
            await asyncio.sleep(0.1)  # Simulate processing time
            yield fake_audio

