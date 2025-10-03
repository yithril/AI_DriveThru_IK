"""
Dependency Injection Container
"""

from dependency_injector import containers, providers
from app.config.settings import settings

# Core services
from app.services.restaurant_service import RestaurantService
from app.services.user_service import UserService
from app.services.category_service import CategoryService
from app.services.menu_item_service import MenuItemService
from app.services.ingredient_service import IngredientService
from app.services.order_service import OrderService
from app.services.order_item_service import OrderItemService
from app.services.menu_service import MenuService

# Database services
from app.services.database.postgres_service import PostgresService
from app.services.database.redis_service import RedisService

# Storage services
from app.services.storage.s3_service import S3Service

# Redis-based services
from app.services.session_service import SessionService
from app.services.order_session_service import OrderSessionService
from app.services.menu_cache_service import MenuCacheService
from app.services.startup_service import StartupService

# Voice services
from app.services.voice.text_to_speech_service import TextToSpeechService
from app.services.voice.voice_service import VoiceService
from app.services.voice.tts_provider import OpenAITTSProvider

# Workflow services
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.menu_resolution_service import MenuResolutionService


class Container(containers.DeclarativeContainer):
    """Application container with dependency injection"""
    
    # Configuration
    config = providers.Configuration()
    
    # Database services
    postgres_service = providers.Singleton(
        PostgresService,
        postgres_url=settings.postgres_url
    )
    
    redis_service = providers.Singleton(
        RedisService,
        redis_url=settings.redis_url
    )
    
    # Storage services
    s3_service = providers.Singleton(
        S3Service,
        bucket_name=settings.s3_bucket,
        region=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url
    )
    
    # Core business services
    restaurant_service = providers.Factory(RestaurantService)
    user_service = providers.Factory(UserService)
    category_service = providers.Factory(CategoryService)
    menu_item_service = providers.Factory(MenuItemService)
    ingredient_service = providers.Factory(IngredientService)
    order_service = providers.Factory(OrderService)
    order_item_service = providers.Factory(OrderItemService)
    
    # Menu service with cache support
    menu_cache_service = providers.Factory(
        MenuCacheService,
        redis_service=redis_service,
        menu_service=providers.Factory(MenuService),
        restaurant_service=restaurant_service
    )
    
    menu_service = providers.Factory(
        MenuService,
        menu_cache_service=menu_cache_service
    )
    
    # Redis-based services
    session_service = providers.Factory(
        SessionService,
        redis_service=redis_service
    )
    
    order_session_service = providers.Factory(
        OrderSessionService,
        redis_service=redis_service,
        order_service=order_service,
        menu_item_service=menu_item_service
    )
    
    # Startup service
    startup_service = providers.Factory(
        StartupService,
        menu_cache_service=menu_cache_service,
        restaurant_service=restaurant_service
    )
    
    # Voice services
    tts_provider = providers.Factory(
        OpenAITTSProvider,
        api_key=settings.openai_api_key
    )
    text_to_speech_service = providers.Factory(
        TextToSpeechService,
        provider=tts_provider
    )
    
    voice_service = providers.Factory(
        VoiceService,
        text_to_speech_service=text_to_speech_service,
        s3_service=s3_service,
        redis_service=redis_service
    )
    
    # Workflow services
    menu_resolution_service = providers.Factory(
        MenuResolutionService,
        menu_service=menu_service,
        ingredient_service=ingredient_service
    )
    
    workflow_orchestrator = providers.Factory(
        WorkflowOrchestrator,
        voice_service=voice_service,
        order_session_service=order_session_service,
        session_service=session_service,
        menu_resolution_service=menu_resolution_service,
        menu_service=menu_service,
        ingredient_service=ingredient_service,
        restaurant_service=restaurant_service
    )
