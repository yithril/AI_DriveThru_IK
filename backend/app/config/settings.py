from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database
    postgres_url: str = "postgresql://user:password@localhost:5432/ik_aidrivethru"
    database_url: str = "postgresql://user:password@localhost:5432/ik_aidrivethru"  # Alias for compatibility
    redis_url: str = "redis://localhost:6379/0"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # AI/LLM
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # TTS (Text-to-Speech)
    tts_voice: str = "nova"  # OpenAI TTS voice (nova, alloy, echo, fable, onyx, shimmer)
    tts_language: str = "english"
    
    # AWS
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_region: str = "us-east-1"  # Alias for compatibility
    aws_endpoint_url: Optional[str] = None  # For LocalStack/MinIO
    s3_bucket: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-here"
    jwt_secret: str = "your-jwt-secret-here"  # Alias for compatibility
    nextauth_secret: str = "your-nextauth-secret-here"  # For NextAuth compatibility
    nextauth_url: str = "http://localhost:3000"  # For NextAuth compatibility
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "your-secure-password-here"
    
    # Business Logic
    enable_inventory_checking: bool = True
    enable_customization_validation: bool = True
    enable_order_limits: bool = True
    max_quantity_per_item: int = 10
    max_order_total: float = 200.00
    max_items_per_order: int = 50
    allow_negative_inventory: bool = False
    ai_confidence_threshold: float = 0.8
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields from .env
    )


settings = Settings()
