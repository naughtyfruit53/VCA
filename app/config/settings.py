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
from pydantic import Field, validator
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
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Ensure database URL is not empty."""
        if not v or v.strip() == "":
            raise ValueError("DATABASE_URL cannot be empty")
        return v
    
    @validator("app_env")
    def validate_app_env(cls, v):
        """Ensure app environment is valid."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of {allowed_envs}")
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
