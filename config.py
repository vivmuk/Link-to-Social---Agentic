"""Configuration settings for Link-to-Social Agent."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Venice.ai API Configuration
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""
        # Support both VENICE_API_KEY and venice_api_key
        fields = {
            'venice_api_key': {'env': 'VENICE_API_KEY'}
        }


settings = Settings()

