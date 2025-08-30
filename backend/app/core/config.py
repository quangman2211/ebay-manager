"""
Application Configuration Management
Following SOLID principles - Single Responsibility for configuration
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """
    Application settings with environment variable support
    Following SOLID: Single Responsibility for configuration management
    """
    
    # Application Configuration
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_USER: str = Field(default="ebay_user", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="", env="DATABASE_PASSWORD") 
    DATABASE_NAME: str = Field(default="ebay_manager", env="DATABASE_NAME")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
    # Redis Configuration
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST") 
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    REDIS_SESSION_DB: int = Field(default=1, env="REDIS_SESSION_DB")
    REDIS_CACHE_DB: int = Field(default=2, env="REDIS_CACHE_DB") 
    REDIS_JOB_DB: int = Field(default=3, env="REDIS_JOB_DB")
    
    # Security Configuration
    JWT_SECRET_KEY: str = Field(default="test_jwt_secret_key_32_characters_long", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # File Upload Configuration
    UPLOAD_PATH: str = Field(default="./uploads", env="UPLOAD_PATH")
    UPLOAD_MAX_SIZE: str = Field(default="100MB", env="UPLOAD_MAX_SIZE")
    ALLOWED_FILE_TYPES: List[str] = Field(default=["csv", "xlsx", "xls"], env="ALLOWED_FILE_TYPES")
    
    # Background Jobs Configuration  
    MAX_WORKER_THREADS: int = Field(default=4, env="MAX_WORKER_THREADS")
    JOB_TIMEOUT_SECONDS: int = Field(default=300, env="JOB_TIMEOUT_SECONDS")
    JOB_RETRY_ATTEMPTS: int = Field(default=3, env="JOB_RETRY_ATTEMPTS")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: str = Field(default="./logs/api.log", env="LOG_FILE")
    LOG_MAX_SIZE: str = Field(default="50MB", env="LOG_MAX_SIZE")
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], 
        env="CORS_ORIGINS"
    )
    CORS_CREDENTIALS: bool = Field(default=True, env="CORS_CREDENTIALS")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    MAX_SESSIONS_PER_USER: int = Field(default=3, env="MAX_SESSIONS_PER_USER")
    
    # CSV Processing Configuration
    MAX_CSV_ROWS: int = Field(default=50000, env="MAX_CSV_ROWS")
    CSV_CHUNK_SIZE: int = Field(default=1000, env="CSV_CHUNK_SIZE")
    MAX_CONCURRENT_JOBS: int = Field(default=5, env="MAX_CONCURRENT_JOBS")
    
    # Email Configuration (for future notifications)
    EMAIL_ENABLED: bool = Field(default=False, env="EMAIL_ENABLED")
    EMAIL_HOST: str = Field(default="smtp.gmail.com", env="EMAIL_HOST")
    EMAIL_PORT: int = Field(default=587, env="EMAIL_PORT")
    EMAIL_USE_TLS: bool = Field(default=True, env="EMAIL_USE_TLS")
    EMAIL_FROM: str = Field(default="noreply@ebaymanager.local", env="EMAIL_FROM")
    SMTP_USERNAME: str = Field(default="", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    
    # Gmail API Configuration
    GMAIL_CREDENTIALS_PATH: str = Field(default="./credentials/gmail_credentials.json", env="GMAIL_CREDENTIALS_PATH")
    GMAIL_TOKEN_PATH: str = Field(default="./credentials/tokens", env="GMAIL_TOKEN_PATH")
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True) 
    def parse_file_types(cls, v):
        """Parse allowed file types from string"""
        if isinstance(v, str):
            return [ft.strip() for ft in v.split(",")]
        return v
        
    @validator("UPLOAD_MAX_SIZE")
    def parse_upload_size(cls, v):
        """Parse upload size with units (MB, GB, etc.)"""
        if isinstance(v, str) and v.upper().endswith("MB"):
            return int(v[:-2]) * 1024 * 1024
        elif isinstance(v, str) and v.upper().endswith("GB"):
            return int(v[:-2]) * 1024 * 1024 * 1024
        return int(v) if isinstance(v, str) else v
    
    @validator("LOG_MAX_SIZE")
    def parse_log_size(cls, v):
        """Parse log file max size with units"""
        if isinstance(v, str) and v.upper().endswith("MB"):
            return int(v[:-2]) * 1024 * 1024
        return v
        
    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret key is secure enough"""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("DATABASE_PASSWORD") 
    def validate_database_password(cls, v, values):
        """Ensure database password is secure in production"""
        if values.get("ENVIRONMENT") == "production" and len(v) < 12:
            raise ValueError("DATABASE_PASSWORD must be at least 12 characters in production")
        return v
    
    @validator("REDIS_PASSWORD")
    def validate_redis_password(cls, v, values):
        """Ensure Redis password is secure in production"""  
        if values.get("ENVIRONMENT") == "production" and len(v) < 12:
            raise ValueError("REDIS_PASSWORD must be at least 12 characters in production")
        return v
        
    @property
    def database_url_constructed(self) -> str:
        """Construct database URL if not provided directly"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    @property 
    def redis_url_constructed(self) -> str:
        """Construct Redis URL if not provided directly"""
        if self.REDIS_URL:
            return self.REDIS_URL
        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"
        
    @property 
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
        
    @property
    def log_file_path(self) -> Path:
        """Get log file path as Path object"""
        return Path(self.LOG_FILE)
        
    @property
    def upload_path_obj(self) -> Path:
        """Get upload path as Path object"""
        return Path(self.UPLOAD_PATH)
    
    @property
    def gmail_credentials_path_obj(self) -> Path:
        """Get Gmail credentials path as Path object"""
        return Path(self.GMAIL_CREDENTIALS_PATH)
    
    @property
    def gmail_token_path_obj(self) -> Path:
        """Get Gmail token path as Path object"""
        return Path(self.GMAIL_TOKEN_PATH)
    
    def ensure_directories(self):
        """
        Ensure required directories exist
        Following SOLID: Single method responsibility
        """
        # Create upload directory
        self.upload_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Create log directory  
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create Gmail credentials directory
        self.gmail_credentials_path_obj.parent.mkdir(parents=True, exist_ok=True)
        self.gmail_token_path_obj.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()