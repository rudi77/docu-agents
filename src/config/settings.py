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

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Azure OCR
        self.AZURE_OCR_ENDPOINT = os.getenv("AZURE_OCR_ENDPOINT")
        self.AZURE_OCR_KEY = os.getenv("AZURE_OCR_KEY")
        
        # OpenAI
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME")

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