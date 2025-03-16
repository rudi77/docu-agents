"""
Configuration management for the document processing system.
Uses pydantic-settings for settings validation and python-dotenv for environment variable loading.
"""
from functools import lru_cache
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import base64

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class Settings(BaseSettings):
    """Application settings."""
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Azure OCR
    AZURE_OCR_ENDPOINT: Optional[str] = None
    AZURE_OCR_KEY: Optional[str] = None
    AZURE_OCR_REGION: str = "westeurope"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    # Retry and timeout settings
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    
    # OpenTelemetry settings
    OTEL_SERVICE_NAME: str = "docu-agents"
    OTEL_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_HEADERS: Optional[str] = None
    
    # Langfuse settings
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    
    @field_validator("AZURE_OCR_ENDPOINT", "AZURE_OCR_KEY", "OPENAI_API_KEY")
    @classmethod
    def validate_required_settings(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that required settings are set."""
        if info.field_name in ["AZURE_OCR_ENDPOINT", "AZURE_OCR_KEY"] and not v:
            raise ValueError(f"{info.field_name} is required")
        return v
    
    @field_validator("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
    @classmethod
    def setup_langfuse_auth(cls, v: Optional[str], info) -> Optional[str]:
        """Set up Langfuse authentication headers if keys are provided."""
        if info.field_name == "LANGFUSE_PUBLIC_KEY" and v and cls.LANGFUSE_SECRET_KEY:
            auth = base64.b64encode(f"{v}:{cls.LANGFUSE_SECRET_KEY}".encode()).decode()
            cls.OTEL_EXPORTER_OTLP_HEADERS = f"Authorization=Basic {auth}"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.
    Uses lru_cache to cache the settings and avoid reading the .env file multiple times.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()

# Create a global settings instance
settings = get_settings() 