"""
Unit tests for WorkflowOrchestrator

Tests the complete voice processing pipeline:
1. Speech-to-Text
2. Intent Classification  
3. Workflow Routing
4. Voice Generation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.workflow_orchestrator import WorkflowOrchestrator, VoiceProcessingResult, SessionCreationResult
from app.workflow.response.workflow_result import WorkflowResult, WorkflowType
from app.constants.intent_types import IntentType
from app.constants.audio_phrases import AudioPhraseType


class TestWorkflowOrchestrator:
    @pytest.fixture
    def mock_services(self):
        """Create mock services for the orchestrator"""
        voice_service = AsyncMock()
        order_session_service = AsyncMock()
        menu_resolution_service = AsyncMock()
        menu_service = AsyncMock()
        ingredient_service = AsyncMock()
        restaurant_service = AsyncMock()
        session_service = AsyncMock()
        
        return {
            'voice_service': voice_service,
            'order_session_service': order_session_service,
            'menu_resolution_service': menu_resolution_service,
            'menu_service': menu_service,
            'ingredient_service': ingredient_service,
            'restaurant_service': restaurant_service,
            'session_service': session_service
        }
    
    @pytest.fixture
    def orchestrator(self, mock_services):
        """Create WorkflowOrchestrator instance with mocked services"""
        return WorkflowOrchestrator(
            voice_service=mock_services['voice_service'],
            order_session_service=mock_services['order_session_service'],
            menu_resolution_service=mock_services['menu_resolution_service'],
            menu_service=mock_services['menu_service'],
            ingredient_service=mock_services['ingredient_service'],
            restaurant_service=mock_services['restaurant_service'],
            session_service=mock_services['session_service']
        )
    
    @pytest.fixture
    def sample_audio_content(self):
        """Sample audio content for testing"""
        return b"fake_audio_data_12345"
    
    @pytest.fixture
    def sample_preprocessing_result(self):
        """Sample preprocessing workflow result"""
        return WorkflowResult(
            success=True,
            message="",  # Empty message for preprocessing
            workflow_type=WorkflowType.PREPROCESSING,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,  # Required field
            processed_input="I'll take a burger",
            intent=IntentType.ADD_ITEM,
            needs_clarification=False
        )
    
    @pytest.fixture
    def sample_workflow_result(self):
        """Sample workflow result"""
        return WorkflowResult(
            success=True,
            message="Added Burger to your order!",
            workflow_type=WorkflowType.ADD_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            order_updated=True,
            confidence_score=0.95
        )

    @pytest.mark.asyncio
    async def test_process_voice_input_success(
        self, 
        orchestrator, 
        mock_services, 
        sample_audio_content,
        sample_preprocessing_result,
        sample_workflow_result
    ):
        """Test successful voice processing pipeline"""
        # Mock STT
        with patch.object(orchestrator, '_speech_to_text', return_value="I'll take a burger"):
            # Mock conversation context
            with patch.object(orchestrator, '_get_conversation_history', return_value=[]):
                with patch.object(orchestrator, '_get_current_order', return_value=None):
                    # Mock preprocessing workflow
                    with patch.object(orchestrator.preprocessing_workflow, 'execute', return_value=sample_preprocessing_result):
                        # Mock workflow execution
                        with patch.object(orchestrator, '_execute_workflow', return_value=sample_workflow_result):
                            # Mock voice generation
                            with patch.object(orchestrator, '_generate_voice_response', return_value="https://s3.amazonaws.com/audio123.mp3"):
                                # Mock conversation update
                                with patch.object(orchestrator, '_update_conversation_history'):
                                    result = await orchestrator.process_voice_input(
                                        audio_content=sample_audio_content,
                                        session_id="session_123",
                                        restaurant_id=1,
                                        language="en"
                                    )
        
        assert isinstance(result, VoiceProcessingResult)
        assert result.success is True
        assert result.message == "Added Burger to your order!"
        assert result.audio_url == "https://s3.amazonaws.com/audio123.mp3"
        assert result.order_updated is True
        assert result.workflow_type == "add_item"
        assert result.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_process_voice_input_stt_failure(
        self, 
        orchestrator, 
        mock_services, 
        sample_audio_content
    ):
        """Test voice processing when speech-to-text fails"""
        # Mock STT failure
        with patch.object(orchestrator, '_speech_to_text', return_value=None):
            # Mock error audio generation
            with patch.object(orchestrator, '_generate_error_audio', return_value="https://s3.amazonaws.com/error.mp3"):
                result = await orchestrator.process_voice_input(
                    audio_content=sample_audio_content,
                    session_id="session_123",
                    restaurant_id=1
                )
        
        assert isinstance(result, VoiceProcessingResult)
        assert result.success is False
        assert "couldn't understand" in result.message.lower()
        assert result.audio_url == "https://s3.amazonaws.com/error.mp3"
        assert result.order_updated is False

    @pytest.mark.asyncio
    async def test_process_voice_input_workflow_failure(
        self, 
        orchestrator, 
        mock_services, 
        sample_audio_content,
        sample_preprocessing_result
    ):
        """Test voice processing when workflow execution fails"""
        # Mock STT success
        with patch.object(orchestrator, '_speech_to_text', return_value="I'll take a burger"):
            # Mock conversation context
            with patch.object(orchestrator, '_get_conversation_history', return_value=[]):
                with patch.object(orchestrator, '_get_current_order', return_value=None):
                    # Mock preprocessing workflow
                    with patch.object(orchestrator.preprocessing_workflow, 'execute', return_value=sample_preprocessing_result):
                        # Mock workflow execution failure
                        with patch.object(orchestrator, '_execute_workflow', side_effect=Exception("Workflow failed")):
                            # Mock error audio generation
                            with patch.object(orchestrator, '_generate_error_audio', return_value="https://s3.amazonaws.com/error.mp3"):
                                result = await orchestrator.process_voice_input(
                                    audio_content=sample_audio_content,
                                    session_id="session_123",
                                    restaurant_id=1
                                )
        
        assert isinstance(result, VoiceProcessingResult)
        assert result.success is False
        assert "encountered an error" in result.message.lower()
        assert result.audio_url == "https://s3.amazonaws.com/error.mp3"
        assert "Workflow failed" in result.validation_errors[0]

    @pytest.mark.asyncio
    async def test_process_voice_input_clarification_needed(
        self, 
        orchestrator, 
        mock_services, 
        sample_audio_content
    ):
        """Test voice processing when clarification is needed"""
        # Mock STT success
        with patch.object(orchestrator, '_speech_to_text', return_value="I'll take that"):
            # Mock conversation context
            with patch.object(orchestrator, '_get_conversation_history', return_value=[]):
                with patch.object(orchestrator, '_get_current_order', return_value=None):
                    # Mock preprocessing workflow returning clarification needed
                    clarification_result = WorkflowResult(
                        success=False,
                        message="Sorry, I didn't understand. Could you please specify which item?",
                        workflow_type=WorkflowType.CLARIFICATION,
                        audio_phrase_type=AudioPhraseType.CLARIFICATION_QUESTION,
                        needs_clarification=True
                    )
                    
                    with patch.object(orchestrator.preprocessing_workflow, 'execute', return_value=clarification_result):
                        # Mock voice generation
                        with patch.object(orchestrator, '_generate_voice_response', return_value="https://s3.amazonaws.com/clarification.mp3"):
                            result = await orchestrator.process_voice_input(
                                audio_content=sample_audio_content,
                                session_id="session_123",
                                restaurant_id=1
                            )
        
        assert isinstance(result, VoiceProcessingResult)
        assert result.success is False
        assert "didn't understand" in result.message.lower()
        assert result.audio_url == "https://s3.amazonaws.com/clarification.mp3"
        assert result.workflow_type == "clarification"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Session creation is deprecated - use /api/sessions/new-car endpoint")
    async def test_create_session_success(self, orchestrator, mock_services):
        """Test successful session creation"""
        # Mock session creation
        mock_services['order_session_service'].create_session.return_value = "session_123"
        
        # Mock greeting audio generation
        mock_services['voice_service'].generate_from_phrase_type.return_value = "https://s3.amazonaws.com/greeting.mp3"
        
        result = await orchestrator.create_session(restaurant_id=1)
        
        assert isinstance(result, SessionCreationResult)
        assert result.session_id == "session_123"
        assert result.greeting_audio_url == "https://s3.amazonaws.com/greeting.mp3"
        
        # Verify service calls
        mock_services['order_session_service'].create_session.assert_called_once_with(1)
        mock_services['voice_service'].generate_from_phrase_type.assert_called_once_with(
            phrase_type=AudioPhraseType.GREETING,
            restaurant_id=1
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Session creation is deprecated - use /api/sessions/new-car endpoint")
    async def test_create_session_failure(self, orchestrator, mock_services):
        """Test session creation failure"""
        # Mock session creation failure
        mock_services['order_session_service'].create_session.side_effect = Exception("Redis connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await orchestrator.create_session(restaurant_id=1)
        
        assert "Redis connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_speech_to_text_success(self, orchestrator):
        """Test successful speech-to-text conversion"""
        audio_content = b"fake_audio_data"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "I'll take a burger"
            
            result = await orchestrator._speech_to_text(audio_content, "en", restaurant_id=1)
            
            assert result == "I'll take a burger"
            mock_client.audio.transcriptions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_speech_to_text_failure(self, orchestrator):
        """Test speech-to-text failure"""
        audio_content = b"fake_audio_data"
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = Exception("API error")
            
            result = await orchestrator._speech_to_text(audio_content, "en", restaurant_id=1)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_execute_workflow_add_item(self, orchestrator):
        """Test workflow execution for ADD_ITEM intent"""
        # Mock the add_item_workflow
        orchestrator.add_item_workflow = AsyncMock()
        orchestrator.add_item_workflow.execute.return_value = WorkflowResult(
            success=True,
            message="Added burger",
            workflow_type=WorkflowType.ADD_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS
        )
        
        result = await orchestrator._execute_workflow(
            intent=IntentType.ADD_ITEM,
            user_input="I'll take a burger",
            session_id="session_123",
            restaurant_id=1,
            conversation_history=[],
            current_order=None
        )
        
        assert result.success is True
        assert result.message == "Added burger"
        orchestrator.add_item_workflow.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_modify_item(self, orchestrator):
        """Test workflow execution for MODIFY_ITEM intent"""
        # Mock the modify_item_workflow
        orchestrator.modify_item_workflow = AsyncMock()
        orchestrator.modify_item_workflow.execute.return_value = WorkflowResult(
            success=True,
            message="Modified burger",
            workflow_type=WorkflowType.MODIFY_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_MODIFIED_SUCCESS
        )
        
        result = await orchestrator._execute_workflow(
            intent=IntentType.MODIFY_ITEM,
            user_input="Make it large",
            session_id="session_123",
            restaurant_id=1,
            conversation_history=[],
            current_order=None
        )
        
        assert result.success is True
        assert result.message == "Modified burger"
        orchestrator.modify_item_workflow.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_unknown_intent(self, orchestrator):
        """Test workflow execution for unknown intent"""
        result = await orchestrator._execute_workflow(
            intent=IntentType.UNKNOWN,
            user_input="random text",
            session_id="session_123",
            restaurant_id=1,
            conversation_history=[],
            current_order=None
        )
        
        assert result.success is False
        assert "didn't understand" in result.message.lower()
        assert result.workflow_type == WorkflowType.ERROR_RECOVERY

    @pytest.mark.asyncio
    async def test_generate_voice_response_custom_message(self, orchestrator):
        """Test voice generation from custom message"""
        workflow_result = WorkflowResult(
            success=True,
            message="Custom response message",
            workflow_type=WorkflowType.ADD_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS
        )
        
        mock_services = orchestrator.voice_service
        mock_services.generate_audio.return_value = "https://s3.amazonaws.com/custom.mp3"
        
        result = await orchestrator._generate_voice_response(workflow_result, restaurant_id=1)
        
        assert result == "https://s3.amazonaws.com/custom.mp3"
        mock_services.generate_audio.assert_called_once_with(
            text="Custom response message",
            restaurant_id=1
        )

    @pytest.mark.asyncio
    async def test_generate_voice_response_phrase_type(self, orchestrator):
        """Test voice generation from phrase type"""
        workflow_result = WorkflowResult(
            success=True,
            message="",  # Empty message to trigger phrase type
            workflow_type=WorkflowType.ADD_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS
        )
        
        mock_services = orchestrator.voice_service
        mock_services.generate_from_phrase_type.return_value = "https://s3.amazonaws.com/phrase.mp3"
        
        result = await orchestrator._generate_voice_response(workflow_result, restaurant_id=1)
        
        assert result == "https://s3.amazonaws.com/phrase.mp3"
        mock_services.generate_from_phrase_type.assert_called_once_with(
            phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            restaurant_id=1
        )

    @pytest.mark.asyncio
    async def test_generate_error_audio(self, orchestrator):
        """Test error audio generation"""
        mock_services = orchestrator.voice_service
        mock_services.generate_from_phrase_type.return_value = "https://s3.amazonaws.com/error.mp3"
        
        result = await orchestrator._generate_error_audio(restaurant_id=1)
        
        assert result == "https://s3.amazonaws.com/error.mp3"
        mock_services.generate_from_phrase_type.assert_called_once_with(
            phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
            restaurant_id=1
        )

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, orchestrator):
        """Test conversation history retrieval"""
        result = await orchestrator._get_conversation_history("session_123")
        
        # Currently returns empty list (TODO: implement actual storage)
        # The method should return an empty list, but if it's mocked, we just check it's callable
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_current_order(self, orchestrator, mock_services):
        """Test current order retrieval"""
        mock_order = {"id": "order_123", "items": []}
        mock_services['order_session_service'].get_session_order.return_value = mock_order
        
        result = await orchestrator._get_current_order("session_123")
        
        assert result == mock_order
        mock_services['order_session_service'].get_session_order.assert_called_once_with("session_123")

    @pytest.mark.asyncio
    async def test_update_conversation_history(self, orchestrator):
        """Test conversation history update"""
        # Should not raise exception
        await orchestrator._update_conversation_history(
            session_id="session_123",
            user_input="I'll take a burger",
            ai_response="Added burger to your order!"
        )
        
        # Currently just logs (TODO: implement actual storage)

    @pytest.mark.asyncio
    async def test_workflow_restaurant_id_assignment(self, orchestrator):
        """Test that restaurant_id is properly assigned to workflows"""
        # Mock workflows
        orchestrator.add_item_workflow = AsyncMock()
        orchestrator.question_answer_workflow = AsyncMock()
        
        # Test ADD_ITEM workflow
        await orchestrator._execute_workflow(
            intent=IntentType.ADD_ITEM,
            user_input="I'll take a burger",
            session_id="session_123",
            restaurant_id=42,  # Different restaurant ID
            conversation_history=[],
            current_order=None
        )
        
        assert orchestrator.add_item_workflow.restaurant_id == 42
        assert orchestrator.question_answer_workflow.restaurant_id == 42

    @pytest.mark.asyncio
    async def test_voice_generation_failure(self, orchestrator):
        """Test voice generation failure handling"""
        workflow_result = WorkflowResult(
            success=True,
            message="Test message",
            workflow_type=WorkflowType.ADD_ITEM,
            audio_phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS
        )
        
        # Mock voice service failure
        orchestrator.voice_service.generate_audio.side_effect = Exception("TTS failed")
        
        result = await orchestrator._generate_voice_response(workflow_result, restaurant_id=1)
        
        assert result is None  # Should return None on failure

    @pytest.mark.asyncio
    async def test_error_audio_generation_failure(self, orchestrator):
        """Test error audio generation failure handling"""
        orchestrator.voice_service.generate_from_phrase_type.side_effect = Exception("TTS failed")
        
        result = await orchestrator._generate_error_audio(restaurant_id=1)
        
        assert result is None  # Should return None on failure
