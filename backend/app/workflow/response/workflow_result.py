"""
Standardized Workflow Result Model

All workflows should return this standardized format for consistent
consumption by voice generation services and other downstream consumers.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from enum import Enum
from app.constants.audio_phrases import AudioPhraseType


class WorkflowType(str, Enum):
    """Supported workflow types"""
    MODIFY_ITEM = "modify_item"
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"
    CLEAR_ORDER = "clear_order"
    QUESTION_ANSWER = "question_answer"
    CONFIRM_ORDER = "confirm_order"
    ADD_ITEM_CLARIFICATION = "add_item_clarification"
    MODIFY_ITEM_CLARIFICATION = "modify_item_clarification"
    REMOVE_ITEM_CLARIFICATION = "remove_item_clarification"
    ERROR_RECOVERY = "error_recovery"


class WorkflowResult(BaseModel):
    """
    Standardized result format for all workflows
    
    This ensures consistent consumption by voice generation services
    and other downstream consumers.
    """
    
    # Core fields - always present
    success: bool = Field(..., description="Whether the workflow succeeded")
    message: str = Field(..., description="Human-readable message for user")
    workflow_type: WorkflowType = Field(..., description="Type of workflow that executed")
    
    # Voice generation fields
    audio_phrase_type: AudioPhraseType = Field(..., description="Type of audio phrase to generate")
    requires_confirmation: bool = Field(default=False, description="Whether user confirmation is needed")
    
    # Order state fields
    order_updated: bool = Field(default=False, description="Whether the order was modified")
    order_summary: Optional[str] = Field(None, description="Current order summary")
    total_cost: Optional[float] = Field(None, description="Total order cost")
    
    # Error handling fields
    error: Optional[str] = Field(None, description="Error message if success=False")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    
    # Clarification fields
    needs_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_options: List[str] = Field(default_factory=list, description="Available clarification options")
    
    # Workflow-specific data (flexible for different workflow types)
    data: Dict[str, Any] = Field(default_factory=dict, description="Workflow-specific data")
    
    # Metadata
    execution_time_ms: Optional[int] = Field(None, description="Workflow execution time in milliseconds")
    confidence_score: Optional[float] = Field(None, description="Confidence in the result (0.0 to 1.0)")
    
    def is_voice_ready(self) -> bool:
        """Check if this result is ready for voice generation"""
        return self.success or self.needs_clarification
    
    def get_voice_context(self) -> Dict[str, Any]:
        """Get context data for voice generation service"""
        return {
            "workflow_type": self.workflow_type.value,
            "audio_phrase_type": self.audio_phrase_type.value,
            "requires_confirmation": self.requires_confirmation,
            "order_updated": self.order_updated,
            "confidence_score": self.confidence_score,
            "clarification_options": self.clarification_options,
            "order_summary": self.order_summary,
            "total_cost": self.total_cost,
            "data": self.data
        }


# Convenience classes for common workflow types
class ModifyItemWorkflowResult(WorkflowResult):
    """Result specifically for modify item workflows"""
    
    def __init__(
        self,
        success: bool,
        message: str,
        modified_fields: Optional[List[str]] = None,
        additional_cost: Optional[float] = None,
        target_item_name: Optional[str] = None,
        **kwargs
    ):
        data = {
            "modified_fields": modified_fields or [],
            "additional_cost": additional_cost or 0.0,
            "target_item_name": target_item_name
        }
        
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.MODIFY_ITEM,
            data=data,
            **kwargs
        )


class AddItemWorkflowResult(WorkflowResult):
    """Result specifically for add item workflows"""
    
    def __init__(
        self,
        success: bool,
        message: str,
        added_items: Optional[List[Dict[str, Any]]] = None,
        total_cost: Optional[float] = None,
        **kwargs
    ):
        data = {
            "added_items": added_items or [],
            "total_cost": total_cost or 0.0
        }
        
        # Debug
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"AddItemWorkflowResult.__init__: data={data}, kwargs.keys()={list(kwargs.keys())}")
        
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.ADD_ITEM,
            data=data,
            **kwargs
        )
        
        logger.debug(f"AddItemWorkflowResult.__init__: After super().__init__, self.data={self.data}")


class RemoveItemWorkflowResult(WorkflowResult):
    """Result specifically for remove item workflows"""
    
    def __init__(
        self,
        success: bool,
        message: str,
        removed_items: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        data = {
            "removed_items": removed_items or []
        }
        
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.REMOVE_ITEM,
            data=data,
            **kwargs
        )


class QuestionAnswerWorkflowResult(WorkflowResult):
    """Result specifically for question/answer workflows"""
    
    def __init__(
        self,
        success: bool,
        message: str,
        answer_type: Optional[str] = None,
        related_items: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        data = {
            "answer_type": answer_type,
            "related_items": related_items or []
        }
        
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.QUESTION_ANSWER,
            data=data,
            **kwargs
        )


class ClarificationWorkflowResult(WorkflowResult):
    """Result specifically for clarification workflows"""
    
    def __init__(
        self,
        message: str,
        clarification_type: str,
        clarification_options: List[str],
        workflow_type: WorkflowType,
        **kwargs
    ):
        super().__init__(
            success=False,
            message=message,
            workflow_type=workflow_type,
            needs_clarification=True,
            clarification_type=clarification_type,
            clarification_options=clarification_options,
            **kwargs
        )


class ErrorRecoveryWorkflowResult(WorkflowResult):
    """Result specifically for error recovery workflows"""
    
    def __init__(
        self,
        message: str,
        error: str,
        suggested_actions: Optional[List[str]] = None,
        **kwargs
    ):
        data = {
            "suggested_actions": suggested_actions or []
        }
        
        super().__init__(
            success=False,
            message=message,
            workflow_type=WorkflowType.ERROR_RECOVERY,
            error=error,
            data=data,
            audio_phrase_type=AudioPhraseType.SYSTEM_ERROR_RETRY,
            **kwargs
        )


class QuestionAnswerWorkflowResult(WorkflowResult):
    """Result specifically for question-answer workflows"""
    
    def __init__(
        self,
        success: bool,
        message: str,
        question_category: str,
        confidence_score: Optional[float] = None,
        relevant_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        data = {
            "question_category": question_category,
            "relevant_data": relevant_data or {}
        }
        
        super().__init__(
            success=success,
            message=message,
            workflow_type=WorkflowType.QUESTION_ANSWER,
            confidence_score=confidence_score,
            data=data,
            **kwargs
        )
