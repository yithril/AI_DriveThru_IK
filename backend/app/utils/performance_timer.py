"""
Performance timing utilities for tracking execution time of various operations
"""

import time
import asyncio
from functools import wraps
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, step_name: str, session_id: Optional[str] = None, session_service=None, metadata: Optional[dict] = None):
        self.step_name = step_name
        self.session_id = session_id
        self.session_service = session_service
        self.metadata = metadata or {}
        self.start_time = None
        self.duration_ms = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.duration_ms = (time.time() - self.start_time) * 1000
            logger.info(f"Performance: {self.step_name} took {self.duration_ms:.2f}ms")
            
            # Log to session if available
            if self.session_id and self.session_service:
                asyncio.create_task(
                    self.session_service.add_performance_log(
                        self.session_id,
                        self.step_name,
                        self.duration_ms,
                        self.metadata
                    )
                )


def time_operation(step_name: str, session_id: Optional[str] = None, session_service=None, metadata: Optional[dict] = None):
    """
    Decorator for timing async operations
    
    Usage:
        @time_operation("speech_to_text", session_id, session_service)
        async def transcribe_audio(audio_file):
            # ... operation code
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with PerformanceTimer(step_name, session_id, session_service, metadata):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceTimer(step_name, session_id, session_service, metadata):
                return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def time_sync_operation(step_name: str, session_id: Optional[str] = None, session_service=None, metadata: Optional[dict] = None):
    """
    Decorator for timing sync operations
    
    Usage:
        @time_sync_operation("data_processing", session_id, session_service)
        def process_data(data):
            # ... operation code
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceTimer(step_name, session_id, session_service, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience functions for common operations
def time_speech_to_text(session_id: str, session_service, audio_duration_seconds: float = None):
    """Time speech-to-text operations"""
    metadata = {}
    if audio_duration_seconds:
        metadata["audio_duration_seconds"] = audio_duration_seconds
    return time_operation("speech_to_text", session_id, session_service, metadata)


def time_intent_classification(session_id: str, session_service, text_length: int = None):
    """Time intent classification operations"""
    metadata = {}
    if text_length:
        metadata["text_length"] = text_length
    return time_operation("intent_classification", session_id, session_service, metadata)


def time_workflow_execution(session_id: str, session_service, workflow_type: str):
    """Time workflow execution"""
    metadata = {"workflow_type": workflow_type}
    return time_operation(f"{workflow_type}_workflow", session_id, session_service, metadata)


def time_voice_generation(session_id: str, session_service, text_length: int = None, voice_type: str = None):
    """Time voice generation operations"""
    metadata = {}
    if text_length:
        metadata["text_length"] = text_length
    if voice_type:
        metadata["voice_type"] = voice_type
    return time_operation("voice_generation", session_id, session_service, metadata)
