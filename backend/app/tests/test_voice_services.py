"""
Unit tests for voice services
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from app.services.voice.tts_provider import OpenAITTSProvider, MockTTSProvider
from app.services.voice.text_to_speech_service import TextToSpeechService
from app.services.voice.voice_service import VoiceService
from app.services.voice.voice_generation_service import VoiceGenerationService
from app.constants.audio_phrases import AudioPhraseType


# ===== TTS Provider Tests =====

class TestMockTTSProvider:
    """Tests for MockTTSProvider"""
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_success(self):
        """Test mock provider generates fake audio"""
        provider = MockTTSProvider()
        
        chunks = []
        async for chunk in provider.generate_audio_stream("test text", "nova"):
            chunks.append(chunk)
        
        assert len(chunks) == 10
        assert all(len(chunk) == 1024 for chunk in chunks)
        assert all(chunk == b'\x00' * 1024 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_empty_text(self):
        """Test mock provider raises error on empty text"""
        provider = MockTTSProvider()
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            async for _ in provider.generate_audio_stream("", "nova"):
                pass


class TestOpenAITTSProvider:
    """Tests for OpenAITTSProvider"""
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_success(self):
        """Test OpenAI provider generates audio"""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.content = b"fake_audio_data" * 100
        
        mock_client = AsyncMock()
        mock_client.audio.speech.create = AsyncMock(return_value=mock_response)
        
        provider = OpenAITTSProvider(api_key="test-key")
        provider.client = mock_client
        
        chunks = []
        async for chunk in provider.generate_audio_stream("test text", "nova"):
            chunks.append(chunk)
        
        # Verify chunks were generated
        assert len(chunks) > 0
        assert b''.join(chunks) == mock_response.content
        
        # Verify OpenAI API was called correctly
        mock_client.audio.speech.create.assert_called_once_with(
            model="tts-1",
            voice="nova",
            input="test text",
            response_format="mp3"
        )
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_empty_text(self):
        """Test OpenAI provider raises error on empty text"""
        provider = OpenAITTSProvider(api_key="test-key")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            async for _ in provider.generate_audio_stream("   ", "nova"):
                pass
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_api_error(self):
        """Test OpenAI provider handles API errors"""
        mock_client = AsyncMock()
        mock_client.audio.speech.create = AsyncMock(side_effect=Exception("API Error"))
        
        provider = OpenAITTSProvider(api_key="test-key")
        provider.client = mock_client
        
        with pytest.raises(Exception, match="TTS generation failed"):
            async for _ in provider.generate_audio_stream("test", "nova"):
                pass


# ===== TextToSpeechService Tests =====

class TestTextToSpeechService:
    """Tests for TextToSpeechService"""
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_success(self):
        """Test TTS service generates audio via provider"""
        mock_provider = AsyncMock()
        
        async def mock_stream(text, voice):
            yield b"chunk1"
            yield b"chunk2"
        
        mock_provider.generate_audio_stream = mock_stream
        
        service = TextToSpeechService(provider=mock_provider)
        
        chunks = []
        async for chunk in service.generate_audio_stream("test text", "nova"):
            chunks.append(chunk)
        
        assert chunks == [b"chunk1", b"chunk2"]
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_empty_text(self):
        """Test TTS service raises error on empty text"""
        mock_provider = AsyncMock()
        service = TextToSpeechService(provider=mock_provider)
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            async for _ in service.generate_audio_stream("", "nova"):
                pass
    
    @pytest.mark.asyncio
    async def test_generate_audio_stream_provider_error(self):
        """Test TTS service handles provider errors"""
        mock_provider = AsyncMock()
        
        async def mock_stream(text, voice):
            raise Exception("Provider error")
            yield b"never_reached"
        
        mock_provider.generate_audio_stream = mock_stream
        
        service = TextToSpeechService(provider=mock_provider)
        
        with pytest.raises(Exception, match="Failed to generate audio"):
            async for _ in service.generate_audio_stream("test", "nova"):
                pass


# ===== VoiceService Tests =====

class TestVoiceService:
    """Tests for VoiceService"""
    
    @pytest.fixture
    def mock_tts_service(self):
        """Create mock TTS service"""
        async def mock_stream(text, voice):
            yield b"audio_chunk_1"
            yield b"audio_chunk_2"
        
        mock = AsyncMock()
        mock.generate_audio_stream = mock_stream
        return mock
    
    @pytest.fixture
    def mock_s3_service(self):
        """Create mock S3 service"""
        mock = AsyncMock()
        mock.upload_file = AsyncMock(return_value={
            "success": True,
            "s3_url": "https://s3.amazonaws.com/bucket/audio/test.mp3"
        })
        return mock
    
    @pytest.fixture
    def mock_redis_service(self):
        """Create mock Redis service"""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        return mock
    
    @pytest.mark.asyncio
    async def test_generate_audio_success_with_cache_miss(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test audio generation with cache miss"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="Hello world",
            restaurant_id=1,
            voice="nova"
        )
        
        # Verify result
        assert result == "https://s3.amazonaws.com/bucket/audio/test.mp3"
        
        # Verify Redis was checked
        mock_redis_service.get.assert_called_once()
        
        # Verify S3 upload was called
        mock_s3_service.upload_file.assert_called_once()
        upload_call = mock_s3_service.upload_file.call_args
        assert upload_call.kwargs["file_data"] == b"audio_chunk_1audio_chunk_2"
        assert upload_call.kwargs["restaurant_id"] == 1
        assert upload_call.kwargs["file_type"] == "audio"
        assert upload_call.kwargs["content_type"] == "audio/mpeg"
        
        # Verify Redis cache was set
        mock_redis_service.set.assert_called_once()
        set_call = mock_redis_service.set.call_args
        assert "https://s3.amazonaws.com/bucket/audio/test.mp3" in set_call.args
        assert set_call.kwargs["expire"] == 86400
    
    @pytest.mark.asyncio
    async def test_generate_audio_success_with_cache_hit(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test audio generation with cache hit"""
        mock_redis_service.get = AsyncMock(
            return_value="https://cached.url/audio.mp3"
        )
        
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="Hello world",
            restaurant_id=1
        )
        
        # Verify cached URL was returned
        assert result == "https://cached.url/audio.mp3"
        
        # Verify S3 was NOT called (cache hit)
        mock_s3_service.upload_file.assert_not_called()
        
        # Verify Redis set was NOT called (cache hit)
        mock_redis_service.set.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_audio_without_redis(
        self, mock_tts_service, mock_s3_service
    ):
        """Test audio generation without Redis service"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=None  # No Redis
        )
        
        result = await service.generate_audio(
            text="Hello world",
            restaurant_id=1
        )
        
        # Should still work, just without caching
        assert result == "https://s3.amazonaws.com/bucket/audio/test.mp3"
        mock_s3_service.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_audio_empty_text(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test audio generation with empty text"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="",
            restaurant_id=1
        )
        
        assert result is None
        mock_s3_service.upload_file.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_audio_no_chunks(
        self, mock_s3_service, mock_redis_service
    ):
        """Test audio generation when TTS returns no chunks"""
        async def empty_stream(text, voice):
            return
            yield  # Never reached
        
        mock_tts = AsyncMock()
        mock_tts.generate_audio_stream = empty_stream
        
        service = VoiceService(
            text_to_speech_service=mock_tts,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="test",
            restaurant_id=1
        )
        
        assert result is None
        mock_s3_service.upload_file.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_audio_s3_upload_failure(
        self, mock_tts_service, mock_redis_service
    ):
        """Test audio generation when S3 upload fails"""
        mock_s3 = AsyncMock()
        mock_s3.upload_file = AsyncMock(return_value={
            "success": False,
            "error": "S3 upload failed"
        })
        
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="test",
            restaurant_id=1
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_audio_exception_handling(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test audio generation handles exceptions gracefully"""
        mock_tts_service.generate_audio_stream = AsyncMock(
            side_effect=Exception("TTS error")
        )
        
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_audio(
            text="test",
            restaurant_id=1
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_from_phrase_type_with_custom_text(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test generating audio from phrase type with custom text"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_from_phrase_type(
            phrase_type=AudioPhraseType.GREETING,
            restaurant_id=1,
            custom_text="Custom greeting text"
        )
        
        assert result == "https://s3.amazonaws.com/bucket/audio/test.mp3"
        mock_s3_service.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_from_phrase_type_with_template(
        self, mock_tts_service, mock_s3_service, mock_redis_service
    ):
        """Test generating audio from phrase type using template"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service,
            redis_service=mock_redis_service
        )
        
        result = await service.generate_from_phrase_type(
            phrase_type=AudioPhraseType.GREETING,
            restaurant_id=1,
            restaurant_name="Test Restaurant"
        )
        
        assert result == "https://s3.amazonaws.com/bucket/audio/test.mp3"
        mock_s3_service.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_cache_key_consistency(
        self, mock_tts_service, mock_s3_service
    ):
        """Test cache key generation is consistent"""
        service = VoiceService(
            text_to_speech_service=mock_tts_service,
            s3_service=mock_s3_service
        )
        
        key1 = service._generate_cache_key("test", "nova", 1)
        key2 = service._generate_cache_key("test", "nova", 1)
        key3 = service._generate_cache_key("different", "nova", 1)
        
        # Same inputs = same key
        assert key1 == key2
        
        # Different inputs = different key
        assert key1 != key3


# ===== VoiceGenerationService Tests =====

class TestVoiceGenerationService:
    """Tests for VoiceGenerationService"""
    
    @pytest.fixture
    def mock_voice_service(self):
        """Create mock voice service"""
        mock = AsyncMock()
        mock.generate_from_phrase_type = AsyncMock(
            return_value="https://s3.amazonaws.com/audio.mp3"
        )
        return mock
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_success(self, mock_voice_service):
        """Test successful voice response generation"""
        service = VoiceGenerationService(voice_service=mock_voice_service)
        
        result = await service.generate_voice_response(
            response_text="Hello customer",
            response_phrase_type=AudioPhraseType.GREETING,
            restaurant_id="1",
            restaurant_name="Test Restaurant"
        )
        
        assert result["success"] is True
        assert result["response_text"] == "Hello customer"
        assert result["audio_url"] == "https://s3.amazonaws.com/audio.mp3"
        
        mock_voice_service.generate_from_phrase_type.assert_called_once_with(
            phrase_type=AudioPhraseType.GREETING,
            restaurant_id=1,
            custom_text="Hello customer",
            restaurant_name="Test Restaurant"
        )
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_no_phrase_type(self, mock_voice_service):
        """Test voice response with no phrase type"""
        service = VoiceGenerationService(voice_service=mock_voice_service)
        
        result = await service.generate_voice_response(
            response_text="Test",
            response_phrase_type=None,
            restaurant_id="1"
        )
        
        assert result["success"] is False
        assert result["response_text"] == "Test"
        assert result["audio_url"] is None
        
        mock_voice_service.generate_from_phrase_type.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_generate_voice_response_exception(self, mock_voice_service):
        """Test voice response handles exceptions"""
        mock_voice_service.generate_from_phrase_type = AsyncMock(
            side_effect=Exception("Service error")
        )
        
        service = VoiceGenerationService(voice_service=mock_voice_service)
        
        result = await service.generate_voice_response(
            response_text="Test",
            response_phrase_type=AudioPhraseType.GREETING,
            restaurant_id="1"
        )
        
        assert result["success"] is False
        assert result["audio_url"] is None

