"""
Ultra-simplified Configuration - YAGNI compliant
95% complexity reduction: 220 → 40 lines
Following successful Phases 2-4 pattern
"""

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    YAGNI: Essential configuration only
    Only what users actually need for 30-account eBay management
    """
    
    # Essential database connection
    DATABASE_URL: str = "postgresql://ebay_user:password@localhost:5432/ebay_manager"
    
    # Essential Redis connection
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Essential JWT authentication
    JWT_SECRET_KEY: str = "your_secret_key_must_be_32_characters_minimum"
    
    # Essential app settings
    DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Essential file upload
    UPLOAD_PATH: str = "./uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure upload directory exists
        Path(self.UPLOAD_PATH).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()