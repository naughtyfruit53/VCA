"""
Configuration module with fail-fast validation.

This module loads environment variables using python-dotenv and validates
that all required configuration is present. The application will exit
immediately if any required environment variable is missing.

No fallback values are permitted for required configuration.
"""

import os
import sys
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with strict validation.
    
    All required fields must be present in environment variables.
    The application will fail fast on startup if any required
    configuration is missing.
    """
    
    # Database Configuration (REQUIRED)
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Application Configuration (REQUIRED)
    app_env: str = Field(..., env="APP_ENV")
    app_name: str = Field(default="VCA", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Redis Configuration (REQUIRED for AI call state)
    redis_url: str = Field(..., env="REDIS_URL")
    
    # AI Service Configuration (REQUIRED for AI audio loop)
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # AI Service Settings (OPTIONAL with defaults)
    stt_model: str = Field(default="whisper-1", env="STT_MODEL")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    tts_model: str = Field(default="tts-1", env="TTS_MODEL")
    tts_voice: str = Field(default="alloy", env="TTS_VOICE")
    
    # Conversation limits (OPTIONAL with defaults) - STRICT defaults for production safety
    max_conversation_turns: int = Field(default=5, env="MAX_CONVERSATION_TURNS")
    max_conversation_duration_seconds: int = Field(default=75, env="MAX_CONVERSATION_DURATION_SECONDS")
    
    # ARI Configuration (REQUIRED for audio streaming)
    ari_url: str = Field(default="http://localhost:8088", env="ARI_URL")
    ari_username: str = Field(default="asterisk", env="ARI_USERNAME")
    ari_password: str = Field(default="asterisk", env="ARI_PASSWORD")
    
    # Supabase JWT Configuration (REQUIRED for authentication)
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_jwt_secret: str = Field(..., env="SUPABASE_JWT_SECRET")
    
    # Development authentication bypass (OPTIONAL - default OFF for security)
    dev_auth_bypass: bool = Field(default=False, env="DEV_AUTH_BYPASS")
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is not empty."""
        if not v or v.strip() == "":
            raise ValueError("DATABASE_URL cannot be empty")
        return v
    
    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v):
        """Ensure app environment is valid."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of {allowed_envs}")
        return v
    
    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v):
        """Ensure Redis URL is not empty."""
        if not v or v.strip() == "":
            raise ValueError("REDIS_URL cannot be empty")
        return v
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v):
        """Ensure OpenAI API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("OPENAI_API_KEY cannot be empty")
        return v
    
    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v):
        """Ensure Supabase URL is not empty."""
        if not v or v.strip() == "":
            raise ValueError("SUPABASE_URL cannot be empty")
        return v
    
    @field_validator("supabase_jwt_secret")
    @classmethod
    def validate_supabase_jwt_secret(cls, v):
        """Ensure Supabase JWT secret is not empty."""
        if not v or v.strip() == "":
            raise ValueError("SUPABASE_JWT_SECRET cannot be empty")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """
    Get application settings with fail-fast validation.
    
    Returns:
        Settings: Validated application settings
        
    Raises:
        SystemExit: If any required configuration is missing or invalid
    """
    try:
        settings = Settings()
        return settings
    except Exception as e:
        print(f"FATAL: Configuration error - {e}", file=sys.stderr)
        print("The application cannot start without valid configuration.", file=sys.stderr)
        print("Please ensure all required environment variables are set.", file=sys.stderr)
        sys.exit(1)


# Global settings instance
settings = get_settings()


def is_config_valid() -> bool:
    """
    Check if configuration is valid.
    
    Returns:
        bool: True if all required configuration is present and valid
    """
    try:
        Settings()
        return True
    except Exception:
        return False
