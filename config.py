"""Configuration settings for Link-to-Social Agent."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Venice.ai API Configuration
    # Supports both VENICE_API_KEY (uppercase) and venice_api_key (lowercase)
    # due to case_sensitive=False in model_config
    venice_api_key: str
    venice_base_url: str = "https://api.venice.ai/api/v1"
    
    # LLM Configuration
    llm_model: str = "llama-3.2-3b"  # Fast and affordable
    llm_temperature: float = 0.7
    
    # Image Generation Configuration
    image_model: str = "venice-sd35"  # Default image model
    image_width: int = 1080
    image_height: int = 1080
    image_steps: int = 25
    image_cfg_scale: float = 7.5
    
    # Scraping Configuration
    max_content_length: int = 50000  # Max chars to extract
    request_timeout: int = 30
    
    # Application Settings
    app_name: str = "Link-to-Social Agent"
    app_version: str = "0.1.0"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,  # This allows both VENICE_API_KEY and venice_api_key
        "env_prefix": "",
        # Pydantic V2 uses model_config instead of Config class
    }
    
    def __init__(self, **kwargs):
        """Initialize settings with explicit support for VENICE_API_KEY (uppercase)."""
        # BaseSettings with case_sensitive=False should handle this automatically,
        # but we explicitly check uppercase first for compatibility
        if "venice_api_key" not in kwargs:
            # Check uppercase first (Railway convention), then lowercase
            venice_key = os.getenv("VENICE_API_KEY") or os.getenv("venice_api_key")
            if venice_key:
                kwargs["venice_api_key"] = venice_key
        super().__init__(**kwargs)


settings = Settings()

