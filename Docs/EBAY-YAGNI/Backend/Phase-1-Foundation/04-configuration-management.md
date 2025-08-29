# Configuration Management - Environment Variables & Settings

## Overview
Complete configuration management system for eBay Management System following YAGNI/SOLID principles. Implements secure environment variable handling, application settings, and configuration validation optimized for 30-account scale.

## SOLID Principles Applied
- **Single Responsibility**: Each configuration class manages one domain of settings
- **Open/Closed**: Configuration system extensible for new settings without modifying core
- **Liskov Substitution**: All configuration classes implement common validation interface
- **Interface Segregation**: Separate interfaces for different configuration concerns
- **Dependency Inversion**: Application depends on configuration abstractions, not concrete values

## YAGNI Compliance
✅ **Essential Configuration Only**: Core database, auth, file handling, and logging settings  
✅ **Simple Validation**: Pydantic-based validation with essential checks only  
✅ **Environment-based**: 12-factor app methodology with .env files  
✅ **Minimal Secrets**: Only necessary secrets (database, JWT, Redis passwords)  
❌ **Eliminated**: Complex config management, external config stores, dynamic reloading, encryption at rest

---

## Configuration Architecture

### Configuration Structure
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Environment Variables                             │   │
│  │                                                                         │   │
│  │  .env                    .env.production               .env.test         │   │
│  │  ├── DATABASE_URL        ├── DATABASE_URL             ├── DATABASE_URL   │   │
│  │  ├── JWT_SECRET_KEY      ├── JWT_SECRET_KEY           ├── JWT_SECRET_KEY │   │
│  │  ├── REDIS_URL           ├── REDIS_URL                ├── REDIS_URL      │   │
│  │  ├── DEBUG=true          ├── DEBUG=false              ├── DEBUG=true     │   │
│  │  └── LOG_LEVEL=DEBUG     └── LOG_LEVEL=INFO           └── LOG_LEVEL=DEBUG│   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                     │
│                                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Pydantic Settings Classes                            │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │   │
│  │  │  DatabaseConfig │  │    AuthConfig   │  │  LoggingConfig  │         │   │
│  │  │                 │  │                 │  │                 │         │   │
│  │  │ • database_url  │  │ • jwt_secret    │  │ • log_level     │         │   │
│  │  │ • pool_size     │  │ • token_expire  │  │ • log_format    │         │   │
│  │  │ • max_overflow  │  │ • cors_origins  │  │ • log_file      │         │   │
│  │  │ • pool_timeout  │  │ • rate_limit    │  │ • max_size      │         │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │   │
│  │  │   FileConfig    │  │   RedisConfig   │  │   AppConfig     │         │   │
│  │  │                 │  │                 │  │                 │         │   │
│  │  │ • upload_path   │  │ • redis_url     │  │ • app_name      │         │   │
│  │  │ • max_file_size │  │ • connection_   │  │ • version       │         │   │
│  │  │ • allowed_types │  │   pool_size     │  │ • environment   │         │   │
│  │  │ • temp_cleanup  │  │ • timeout       │  │ • debug_mode    │         │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                     │
│                                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      Unified Settings Class                             │   │
│  │                                                                         │   │
│  │  class Settings:                                                        │   │
│  │      database: DatabaseConfig                                           │   │
│  │      auth: AuthConfig                                                   │   │
│  │      redis: RedisConfig                                                 │   │
│  │      files: FileConfig                                                  │   │
│  │      logging: LoggingConfig                                             │   │
│  │      app: AppConfig                                                     │   │
│  │                                                                         │   │
│  │      def validate_all() -> None                                         │   │
│  │      def get_database_url() -> str                                      │   │
│  │      def is_production() -> bool                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                           │                                     │
│                                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    Application Components                               │   │
│  │                                                                         │   │
│  │  FastAPI App ──→ Database Engine ──→ Redis Client ──→ File Handler     │   │
│  │              ──→ JWT Manager     ──→ Logger       ──→ Background Jobs   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Configuration Flow
```
Environment Variables (.env files)
         ↓
Pydantic Settings (validation & type conversion)
         ↓
Application Configuration (dependency injection)
         ↓
Runtime Services (database, auth, logging, etc.)
```

---

## Complete Configuration Implementation

### 1. Base Configuration Classes
```python
# core/config/base.py - Base configuration classes

from pydantic import BaseSettings, validator, Field
from typing import List, Optional, Union
import os
from pathlib import Path

class BaseConfig(BaseSettings):
    """Base configuration class with common functionality"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        validate_assignment = True
        
    def validate_required_env_vars(self) -> None:
        """Validate that all required environment variables are set"""
        pass  # Override in subclasses

class DatabaseConfig(BaseConfig):
    """Database configuration settings"""
    
    # Connection Settings
    DATABASE_URL: str = Field(..., description="PostgreSQL database URL")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, description="Max overflow connections")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Pool recycle time in seconds")
    DATABASE_POOL_PRE_PING: bool = Field(default=True, description="Enable connection pre-ping")
    
    # Query Settings
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries to logs")
    DATABASE_ECHO_POOL: bool = Field(default=False, description="Echo pool events to logs")
    
    # Migration Settings
    DATABASE_MIGRATE_ON_START: bool = Field(default=False, description="Run migrations on startup")
    DATABASE_DROP_ALL: bool = Field(default=False, description="Drop all tables on startup (DANGER)")
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://')):
            raise ValueError('DATABASE_URL must be a valid PostgreSQL URL')
        return v
    
    @validator('DATABASE_POOL_SIZE', 'DATABASE_MAX_OVERFLOW', 'DATABASE_POOL_TIMEOUT')
    def validate_positive_integers(cls, v):
        """Validate positive integer values"""
        if v <= 0:
            raise ValueError('Database pool settings must be positive integers')
        return v
    
    def get_engine_config(self) -> dict:
        """Get SQLAlchemy engine configuration"""
        return {
            'pool_size': self.DATABASE_POOL_SIZE,
            'max_overflow': self.DATABASE_MAX_OVERFLOW,
            'pool_timeout': self.DATABASE_POOL_TIMEOUT,
            'pool_recycle': self.DATABASE_POOL_RECYCLE,
            'pool_pre_ping': self.DATABASE_POOL_PRE_PING,
            'echo': self.DATABASE_ECHO,
            'echo_pool': self.DATABASE_ECHO_POOL,
        }

class RedisConfig(BaseConfig):
    """Redis configuration settings"""
    
    # Connection Settings
    REDIS_URL: str = Field(..., description="Redis connection URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_CONNECTION_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    REDIS_CONNECTION_TIMEOUT: int = Field(default=5, description="Connection timeout in seconds")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Socket timeout in seconds")
    REDIS_SOCKET_KEEPALIVE: bool = Field(default=True, description="Enable socket keepalive")
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    
    # Database Allocation
    REDIS_SESSION_DB: int = Field(default=1, description="Redis DB for user sessions")
    REDIS_CACHE_DB: int = Field(default=2, description="Redis DB for caching")
    REDIS_JOB_DB: int = Field(default=3, description="Redis DB for background jobs")
    REDIS_RATE_LIMIT_DB: int = Field(default=4, description="Redis DB for rate limiting")
    
    # Cache Settings
    REDIS_DEFAULT_TTL: int = Field(default=3600, description="Default TTL in seconds")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Maximum connections")
    
    @validator('REDIS_URL')
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('REDIS_URL must be a valid Redis URL')
        return v
    
    @validator('REDIS_SESSION_DB', 'REDIS_CACHE_DB', 'REDIS_JOB_DB', 'REDIS_RATE_LIMIT_DB')
    def validate_db_numbers(cls, v):
        """Validate Redis database numbers"""
        if not 0 <= v <= 15:
            raise ValueError('Redis database numbers must be between 0 and 15')
        return v
    
    def get_connection_config(self) -> dict:
        """Get Redis connection configuration"""
        return {
            'connection_pool_kwargs': {
                'max_connections': self.REDIS_CONNECTION_POOL_SIZE,
                'socket_timeout': self.REDIS_SOCKET_TIMEOUT,
                'socket_connect_timeout': self.REDIS_CONNECTION_TIMEOUT,
                'socket_keepalive': self.REDIS_SOCKET_KEEPALIVE,
                'health_check_interval': self.REDIS_HEALTH_CHECK_INTERVAL,
            }
        }

class AuthConfig(BaseConfig):
    """Authentication configuration settings"""
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., description="JWT signing secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiry in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiry in days")
    
    # Password Settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_HASH_ROUNDS: int = Field(default=12, description="bcrypt hash rounds")
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, description="Session timeout in minutes")
    MAX_CONCURRENT_SESSIONS: int = Field(default=5, description="Max concurrent sessions per user")
    
    # Security Settings
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed hosts")
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Enable API rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Requests per minute per IP")
    
    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key strength"""
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters long')
        return v
    
    @validator('JWT_ALGORITHM')
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm"""
        allowed_algorithms = ['HS256', 'HS384', 'HS512']
        if v not in allowed_algorithms:
            raise ValueError(f'JWT_ALGORITHM must be one of {allowed_algorithms}')
        return v
    
    @validator('PASSWORD_HASH_ROUNDS')
    def validate_hash_rounds(cls, v):
        """Validate bcrypt rounds"""
        if not 10 <= v <= 15:
            raise ValueError('PASSWORD_HASH_ROUNDS must be between 10 and 15 for security/performance balance')
        return v

class FileConfig(BaseConfig):
    """File handling configuration settings"""
    
    # Upload Settings
    UPLOAD_PATH: str = Field(default="./uploads", description="Base upload directory path")
    UPLOAD_MAX_SIZE: int = Field(default=100 * 1024 * 1024, description="Max upload size in bytes (100MB)")
    ALLOWED_FILE_TYPES: List[str] = Field(default=["csv", "xlsx", "xls"], description="Allowed file extensions")
    
    # Storage Settings
    FILE_STORAGE_TYPE: str = Field(default="local", description="File storage type")
    TEMP_FILE_CLEANUP_HOURS: int = Field(default=24, description="Hours to keep temp files")
    MAX_FILES_PER_USER: int = Field(default=100, description="Max files per user")
    
    # Processing Settings
    CSV_MAX_ROWS: int = Field(default=10000, description="Maximum CSV rows to process")
    CSV_CHUNK_SIZE: int = Field(default=1000, description="CSV processing chunk size")
    ENABLE_FILE_COMPRESSION: bool = Field(default=True, description="Enable file compression")
    
    @validator('UPLOAD_PATH')
    def validate_upload_path(cls, v):
        """Validate and create upload path"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        
        # Check write permissions
        if not os.access(path, os.W_OK):
            raise ValueError(f'Upload path {v} is not writable')
        
        return str(path.resolve())
    
    @validator('UPLOAD_MAX_SIZE')
    def validate_max_size(cls, v):
        """Validate max upload size"""
        if v <= 0 or v > 1024 * 1024 * 1024:  # Max 1GB
            raise ValueError('UPLOAD_MAX_SIZE must be between 1 byte and 1GB')
        return v
    
    @validator('ALLOWED_FILE_TYPES')
    def validate_file_types(cls, v):
        """Validate allowed file types"""
        allowed_extensions = {'csv', 'xlsx', 'xls', 'txt', 'json'}
        invalid_types = set(v) - allowed_extensions
        
        if invalid_types:
            raise ValueError(f'Invalid file types: {invalid_types}. Allowed: {allowed_extensions}')
        
        return v
    
    def get_upload_config(self) -> dict:
        """Get file upload configuration"""
        return {
            'upload_path': self.UPLOAD_PATH,
            'max_size': self.UPLOAD_MAX_SIZE,
            'allowed_types': self.ALLOWED_FILE_TYPES,
            'temp_cleanup_hours': self.TEMP_FILE_CLEANUP_HOURS,
        }

class LoggingConfig(BaseConfig):
    """Logging configuration settings"""
    
    # Log Level Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format (json or text)")
    
    # File Settings  
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_MAX_SIZE: int = Field(default=50 * 1024 * 1024, description="Max log file size in bytes (50MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backup files")
    
    # Console Settings
    LOG_TO_CONSOLE: bool = Field(default=True, description="Enable console logging")
    LOG_CONSOLE_LEVEL: Optional[str] = Field(default=None, description="Console log level (defaults to LOG_LEVEL)")
    
    # Component Settings
    LOG_SQL_QUERIES: bool = Field(default=False, description="Log SQL queries")
    LOG_REQUEST_DETAILS: bool = Field(default=False, description="Log request details")
    LOG_RESPONSE_DETAILS: bool = Field(default=False, description="Log response details")
    
    @validator('LOG_LEVEL', 'LOG_CONSOLE_LEVEL')
    def validate_log_levels(cls, v):
        """Validate log levels"""
        if v is None:
            return v
            
        valid_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('LOG_FORMAT')
    def validate_log_format(cls, v):
        """Validate log format"""
        valid_formats = ['json', 'text', 'structured']
        if v.lower() not in valid_formats:
            raise ValueError(f'Log format must be one of {valid_formats}')
        return v.lower()
    
    def get_logging_config(self) -> dict:
        """Get logging configuration dictionary"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                },
                'text': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
            'handlers': self._get_handlers(),
            'root': {
                'level': self.LOG_LEVEL,
                'handlers': list(self._get_handlers().keys())
            }
        }
    
    def _get_handlers(self) -> dict:
        """Get logging handlers configuration"""
        handlers = {}
        
        if self.LOG_TO_CONSOLE:
            handlers['console'] = {
                'class': 'logging.StreamHandler',
                'level': self.LOG_CONSOLE_LEVEL or self.LOG_LEVEL,
                'formatter': self.LOG_FORMAT,
                'stream': 'ext://sys.stdout'
            }
        
        if self.LOG_FILE:
            handlers['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.LOG_LEVEL,
                'formatter': self.LOG_FORMAT,
                'filename': self.LOG_FILE,
                'maxBytes': self.LOG_MAX_SIZE,
                'backupCount': self.LOG_BACKUP_COUNT,
                'encoding': 'utf8'
            }
        
        return handlers

class AppConfig(BaseConfig):
    """Application configuration settings"""
    
    # Application Identity
    APP_NAME: str = Field(default="eBay Manager Pro", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_DESCRIPTION: str = Field(default="eBay Multi-Account Management System", description="App description")
    
    # Environment Settings
    ENVIRONMENT: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    TESTING: bool = Field(default=False, description="Testing mode")
    
    # API Settings
    API_HOST: str = Field(default="127.0.0.1", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")
    
    # Background Jobs
    ENABLE_BACKGROUND_JOBS: bool = Field(default=True, description="Enable background job processing")
    MAX_WORKER_THREADS: int = Field(default=4, description="Max worker threads for background jobs")
    JOB_TIMEOUT_SECONDS: int = Field(default=300, description="Background job timeout")
    JOB_RETRY_ATTEMPTS: int = Field(default=3, description="Job retry attempts")
    
    # Maintenance
    MAINTENANCE_MODE: bool = Field(default=False, description="Enable maintenance mode")
    MAINTENANCE_MESSAGE: str = Field(default="System under maintenance", description="Maintenance message")
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_environments = ['development', 'testing', 'production']
        if v.lower() not in valid_environments:
            raise ValueError(f'ENVIRONMENT must be one of {valid_environments}')
        return v.lower()
    
    @validator('API_PORT')
    def validate_api_port(cls, v):
        """Validate API port"""
        if not 1024 <= v <= 65535:
            raise ValueError('API_PORT must be between 1024 and 65535')
        return v
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == 'development'
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == 'production'
    
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.ENVIRONMENT == 'testing' or self.TESTING
```

### 2. Unified Settings Manager
```python
# core/config/settings.py - Main settings manager

from typing import Optional
import os
from pydantic import validator, Field
from core.config.base import (
    BaseConfig, DatabaseConfig, RedisConfig, AuthConfig,
    FileConfig, LoggingConfig, AppConfig
)

class Settings(BaseConfig):
    """Main application settings combining all configuration domains"""
    
    # Configuration Domains
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    files: FileConfig = Field(default_factory=FileConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    
    def __init__(self, **kwargs):
        """Initialize settings with environment-specific overrides"""
        super().__init__(**kwargs)
        self._load_environment_overrides()
        self.validate_all_settings()
    
    def _load_environment_overrides(self):
        """Load environment-specific configuration files"""
        env = self.app.ENVIRONMENT
        
        # Load environment-specific .env file if it exists
        env_file = f".env.{env}"
        if os.path.exists(env_file):
            # Reload configurations with environment-specific values
            self.database = DatabaseConfig(_env_file=env_file)
            self.redis = RedisConfig(_env_file=env_file)
            self.auth = AuthConfig(_env_file=env_file)
            self.files = FileConfig(_env_file=env_file)
            self.logging = LoggingConfig(_env_file=env_file)
            self.app = AppConfig(_env_file=env_file)
    
    def validate_all_settings(self):
        """Validate all configuration settings"""
        self._validate_database_redis_consistency()
        self._validate_file_logging_paths()
        self._validate_security_settings()
        self._validate_environment_consistency()
    
    def _validate_database_redis_consistency(self):
        """Ensure database and Redis configurations are consistent"""
        if self.app.is_production():
            if 'localhost' in self.database.DATABASE_URL or '127.0.0.1' in self.database.DATABASE_URL:
                raise ValueError("Production environment should not use localhost database")
            
            if 'localhost' in self.redis.REDIS_URL or '127.0.0.1' in self.redis.REDIS_URL:
                raise ValueError("Production environment should not use localhost Redis")
    
    def _validate_file_logging_paths(self):
        """Validate file and logging path accessibility"""
        # Ensure upload directory is writable
        upload_path = Path(self.files.UPLOAD_PATH)
        if not upload_path.exists():
            upload_path.mkdir(parents=True, exist_ok=True)
        
        # Ensure log directory is writable if log file is specified
        if self.logging.LOG_FILE:
            log_path = Path(self.logging.LOG_FILE).parent
            if not log_path.exists():
                log_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_security_settings(self):
        """Validate security-related settings"""
        if self.app.is_production():
            if self.app.DEBUG:
                raise ValueError("DEBUG should be False in production")
            
            if self.auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 60:
                print("WARNING: Long access token expiry in production")
            
            if len(self.auth.JWT_SECRET_KEY) < 64:
                print("WARNING: Consider using longer JWT secret key in production")
    
    def _validate_environment_consistency(self):
        """Validate environment-specific settings consistency"""
        if self.app.is_development():
            # Development-specific validations
            if not self.app.DEBUG:
                print("INFO: Debug mode is disabled in development")
        
        elif self.app.is_production():
            # Production-specific validations
            required_env_vars = [
                'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY'
            ]
            
            for var in required_env_vars:
                if not os.getenv(var):
                    raise ValueError(f"Required environment variable {var} not set in production")
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.database.DATABASE_URL
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        return self.redis.REDIS_URL
    
    def get_cors_origins(self) -> list:
        """Get CORS origins list"""
        if self.app.is_development():
            # Include localhost variations in development
            dev_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000", 
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ]
            return list(set(self.auth.CORS_ORIGINS + dev_origins))
        
        return self.auth.CORS_ORIGINS
    
    def get_log_config(self) -> dict:
        """Get complete logging configuration"""
        return self.logging.get_logging_config()
    
    def export_config_summary(self) -> dict:
        """Export non-sensitive configuration summary"""
        return {
            "app": {
                "name": self.app.APP_NAME,
                "version": self.app.APP_VERSION,
                "environment": self.app.ENVIRONMENT,
                "debug": self.app.DEBUG,
                "api_host": self.app.API_HOST,
                "api_port": self.app.API_PORT
            },
            "database": {
                "pool_size": self.database.DATABASE_POOL_SIZE,
                "max_overflow": self.database.DATABASE_MAX_OVERFLOW,
                "echo": self.database.DATABASE_ECHO
            },
            "redis": {
                "connection_pool_size": self.redis.REDIS_CONNECTION_POOL_SIZE,
                "session_db": self.redis.REDIS_SESSION_DB,
                "cache_db": self.redis.REDIS_CACHE_DB
            },
            "auth": {
                "jwt_algorithm": self.auth.JWT_ALGORITHM,
                "access_token_expire_minutes": self.auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
                "password_min_length": self.auth.PASSWORD_MIN_LENGTH,
                "rate_limiting": self.auth.ENABLE_RATE_LIMITING
            },
            "files": {
                "upload_path": self.files.UPLOAD_PATH,
                "max_size_mb": self.files.UPLOAD_MAX_SIZE // (1024 * 1024),
                "allowed_types": self.files.ALLOWED_FILE_TYPES
            },
            "logging": {
                "level": self.logging.LOG_LEVEL,
                "format": self.logging.LOG_FORMAT,
                "to_console": self.logging.LOG_TO_CONSOLE,
                "to_file": bool(self.logging.LOG_FILE)
            }
        }

# Create global settings instance
def create_settings() -> Settings:
    """Create and validate settings instance"""
    return Settings()

# Global settings instance
settings = create_settings()
```

### 3. Configuration Validation & Health Checks
```python
# core/config/validator.py - Configuration validation utilities

import asyncio
import sys
from typing import Dict, List, Tuple, Optional
from sqlalchemy import create_engine, text
import redis
import os
from pathlib import Path
import logging
from core.config.settings import settings

logger = logging.getLogger(__name__)

class ConfigurationValidator:
    """Comprehensive configuration validation"""
    
    def __init__(self, config: Settings):
        self.config = config
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    async def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Validate all configuration components"""
        
        # Run all validation checks
        await asyncio.gather(
            self._validate_database_connection(),
            self._validate_redis_connection(),
            self._validate_file_system_access(),
            self._validate_environment_variables(),
            self._validate_security_settings(),
            return_exceptions=True
        )
        
        return (
            len(self.validation_errors) == 0,
            self.validation_errors,
            self.validation_warnings
        )
    
    async def _validate_database_connection(self):
        """Test database connectivity and configuration"""
        try:
            engine = create_engine(
                self.config.database.DATABASE_URL,
                **self.config.database.get_engine_config()
            )
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if result[0] != 1:
                    self.validation_errors.append("Database connection test failed")
            
            # Test pool configuration
            if self.config.database.DATABASE_POOL_SIZE < 5:
                self.validation_warnings.append("Database pool size is very small")
            
            engine.dispose()
            
        except Exception as e:
            self.validation_errors.append(f"Database connection failed: {str(e)}")
    
    async def _validate_redis_connection(self):
        """Test Redis connectivity and configuration"""
        try:
            # Test basic connection
            redis_client = redis.Redis.from_url(
                self.config.redis.REDIS_URL,
                **self.config.redis.get_connection_config()
            )
            
            # Test ping
            if not redis_client.ping():
                self.validation_errors.append("Redis ping test failed")
            
            # Test database access
            for db_num in [
                self.config.redis.REDIS_SESSION_DB,
                self.config.redis.REDIS_CACHE_DB,
                self.config.redis.REDIS_JOB_DB
            ]:
                test_client = redis.Redis.from_url(
                    self.config.redis.REDIS_URL,
                    db=db_num
                )
                test_client.set("test_key", "test_value", ex=1)
                if test_client.get("test_key") != b"test_value":
                    self.validation_errors.append(f"Redis database {db_num} access failed")
                test_client.close()
            
            redis_client.close()
            
        except Exception as e:
            self.validation_errors.append(f"Redis connection failed: {str(e)}")
    
    async def _validate_file_system_access(self):
        """Validate file system permissions and paths"""
        try:
            # Test upload directory
            upload_path = Path(self.config.files.UPLOAD_PATH)
            
            if not upload_path.exists():
                try:
                    upload_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.validation_errors.append(f"Cannot create upload directory: {str(e)}")
                    return
            
            # Test write permissions
            test_file = upload_path / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                self.validation_errors.append(f"Upload directory not writable: {str(e)}")
            
            # Test log file directory
            if self.config.logging.LOG_FILE:
                log_path = Path(self.config.logging.LOG_FILE).parent
                
                if not log_path.exists():
                    try:
                        log_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        self.validation_errors.append(f"Cannot create log directory: {str(e)}")
                
                # Test log file write permissions
                if log_path.exists():
                    try:
                        test_log = log_path / "test_log.tmp"
                        test_log.write_text("test")
                        test_log.unlink()
                    except Exception as e:
                        self.validation_errors.append(f"Log directory not writable: {str(e)}")
            
        except Exception as e:
            self.validation_errors.append(f"File system validation failed: {str(e)}")
    
    async def _validate_environment_variables(self):
        """Validate required environment variables"""
        required_vars = {
            'development': [
                'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY'
            ],
            'production': [
                'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY',
                'POSTGRES_PASSWORD', 'REDIS_PASSWORD'
            ],
            'testing': [
                'DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY'
            ]
        }
        
        env = self.config.app.ENVIRONMENT
        required = required_vars.get(env, required_vars['development'])
        
        for var in required:
            if not os.getenv(var):
                self.validation_errors.append(f"Required environment variable {var} not set")
        
        # Validate secret strength
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        if len(jwt_secret) < 32:
            self.validation_warnings.append("JWT_SECRET_KEY should be at least 32 characters")
    
    async def _validate_security_settings(self):
        """Validate security-related configuration"""
        
        # Production security checks
        if self.config.app.is_production():
            if self.config.app.DEBUG:
                self.validation_errors.append("DEBUG should be False in production")
            
            if 'localhost' in self.config.auth.CORS_ORIGINS:
                self.validation_warnings.append("Localhost in CORS origins for production")
            
            if self.config.auth.JWT_ACCESS_TOKEN_EXPIRE_MINUTES > 60:
                self.validation_warnings.append("Long JWT access token expiry in production")
        
        # Password settings
        if self.config.auth.PASSWORD_MIN_LENGTH < 8:
            self.validation_warnings.append("Minimum password length is less than 8")
        
        if self.config.auth.PASSWORD_HASH_ROUNDS < 12:
            self.validation_warnings.append("bcrypt rounds less than 12 may be insecure")
        
        # Rate limiting
        if not self.config.auth.ENABLE_RATE_LIMITING and self.config.app.is_production():
            self.validation_warnings.append("Rate limiting disabled in production")

async def validate_configuration(config: Optional[Settings] = None) -> bool:
    """Validate complete application configuration"""
    
    if config is None:
        config = settings
    
    validator = ConfigurationValidator(config)
    is_valid, errors, warnings = await validator.validate_all()
    
    # Log validation results
    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
    
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    if is_valid:
        logger.info("Configuration validation passed successfully")
    
    return is_valid

def validate_startup_configuration():
    """Synchronous wrapper for startup configuration validation"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    is_valid = loop.run_until_complete(validate_configuration())
    
    if not is_valid:
        print("CRITICAL: Configuration validation failed. Exiting.")
        sys.exit(1)
    
    return is_valid
```

### 4. Configuration Dependencies for FastAPI
```python
# core/dependencies.py - Configuration dependency injection

from functools import lru_cache
from typing import Generator, Optional
from fastapi import Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import redis
import logging.config
from core.config.settings import Settings, settings

# Database setup
@lru_cache()
def create_database_engine():
    """Create database engine with configuration"""
    return create_engine(
        settings.database.DATABASE_URL,
        **settings.database.get_engine_config()
    )

@lru_cache()
def create_session_factory():
    """Create database session factory"""
    engine = create_database_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection"""
    SessionLocal = create_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis setup
@lru_cache()
def create_redis_client(db: int = 0):
    """Create Redis client with configuration"""
    return redis.Redis.from_url(
        settings.redis.REDIS_URL,
        db=db,
        **settings.redis.get_connection_config()
    )

def get_session_redis() -> redis.Redis:
    """Get Redis client for sessions"""
    return create_redis_client(settings.redis.REDIS_SESSION_DB)

def get_cache_redis() -> redis.Redis:
    """Get Redis client for caching"""
    return create_redis_client(settings.redis.REDIS_CACHE_DB)

def get_job_redis() -> redis.Redis:
    """Get Redis client for background jobs"""
    return create_redis_client(settings.redis.REDIS_JOB_DB)

# Configuration dependencies
def get_settings() -> Settings:
    """Get application settings"""
    return settings

def get_upload_config() -> dict:
    """Get file upload configuration"""
    return settings.files.get_upload_config()

# Logging setup
def setup_logging():
    """Setup logging configuration"""
    if settings.logging.LOG_FILE or settings.logging.LOG_TO_CONSOLE:
        config = settings.logging.get_logging_config()
        logging.config.dictConfig(config)
    
    # Set specific logger levels
    if settings.logging.LOG_SQL_QUERIES:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

# Health check dependencies
async def check_database_health() -> bool:
    """Check database health for health endpoint"""
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def check_redis_health() -> bool:
    """Check Redis health for health endpoint"""
    try:
        client = create_redis_client()
        return client.ping()
    except Exception:
        return False

async def check_file_system_health() -> bool:
    """Check file system health for health endpoint"""
    try:
        from pathlib import Path
        upload_path = Path(settings.files.UPLOAD_PATH)
        return upload_path.exists() and os.access(upload_path, os.W_OK)
    except Exception:
        return False
```

### 5. Configuration Management CLI
```python
# cli/config.py - Configuration management CLI commands

import asyncio
import json
import sys
from typing import Optional
import click
from core.config.settings import settings
from core.config.validator import validate_configuration, ConfigurationValidator

@click.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json')
@click.option('--output', type=click.Path(), help='Output file path')
def export(format: str, output: Optional[str]):
    """Export configuration summary"""
    
    config_summary = settings.export_config_summary()
    
    if format == 'json':
        content = json.dumps(config_summary, indent=2)
    elif format == 'yaml':
        import yaml
        content = yaml.dump(config_summary, default_flow_style=False)
    
    if output:
        with open(output, 'w') as f:
            f.write(content)
        click.echo(f"Configuration exported to {output}")
    else:
        click.echo(content)

@config.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation results')
async def validate(verbose: bool):
    """Validate current configuration"""
    
    click.echo("Validating configuration...")
    
    validator = ConfigurationValidator(settings)
    is_valid, errors, warnings = await validator.validate_all()
    
    if errors:
        click.echo(click.style("\n❌ Configuration Errors:", fg='red', bold=True))
        for error in errors:
            click.echo(click.style(f"  • {error}", fg='red'))
    
    if warnings:
        click.echo(click.style("\n⚠️  Configuration Warnings:", fg='yellow', bold=True))
        for warning in warnings:
            click.echo(click.style(f"  • {warning}", fg='yellow'))
    
    if is_valid and not warnings:
        click.echo(click.style("\n✅ Configuration validation passed!", fg='green', bold=True))
    elif is_valid:
        click.echo(click.style("\n✅ Configuration is valid with warnings", fg='green', bold=True))
    else:
        click.echo(click.style("\n❌ Configuration validation failed!", fg='red', bold=True))
        sys.exit(1)
    
    if verbose:
        click.echo(f"\nConfiguration Summary:")
        click.echo(json.dumps(settings.export_config_summary(), indent=2))

@config.command()
@click.option('--key', required=True, help='Configuration key to get')
def get(key: str):
    """Get configuration value"""
    
    try:
        # Navigate nested configuration keys
        value = settings
        for part in key.split('.'):
            value = getattr(value, part)
        
        if isinstance(value, (dict, list)):
            click.echo(json.dumps(value, indent=2))
        else:
            click.echo(str(value))
            
    except AttributeError:
        click.echo(f"Configuration key '{key}' not found", err=True)
        sys.exit(1)

@config.command()
def check():
    """Quick configuration health check"""
    
    click.echo("Checking configuration health...")
    
    # Basic checks
    checks = [
        ("Environment", settings.app.ENVIRONMENT),
        ("Debug Mode", settings.app.DEBUG),
        ("Database URL Set", bool(settings.database.DATABASE_URL)),
        ("Redis URL Set", bool(settings.redis.REDIS_URL)),
        ("JWT Secret Set", bool(settings.auth.JWT_SECRET_KEY)),
        ("Upload Path", settings.files.UPLOAD_PATH),
        ("Log Level", settings.logging.LOG_LEVEL)
    ]
    
    for check_name, check_value in checks:
        status = "✅" if check_value else "❌"
        click.echo(f"{status} {check_name}: {check_value}")

# Async command wrapper
@config.command()
@click.option('--verbose', '-v', is_flag=True)
def validate_sync(verbose: bool):
    """Synchronous wrapper for validation command"""
    asyncio.run(validate.callback(verbose))

if __name__ == '__main__':
    config()
```

---

## Environment Files Templates

### Development Environment (.env)
```bash
# Development Environment Configuration
# Copy this to .env and customize for your local setup

#=============================================================================
# Application Settings
#=============================================================================
ENVIRONMENT=development
DEBUG=true
APP_NAME=eBay Manager Pro
APP_VERSION=1.0.0
API_HOST=127.0.0.1
API_PORT=8000

#=============================================================================
# Database Configuration
#=============================================================================
DATABASE_URL=postgresql://ebay_user:dev_password@localhost:5432/ebay_manager
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false
DATABASE_MIGRATE_ON_START=true

#=============================================================================
# Redis Configuration  
#=============================================================================
REDIS_URL=redis://localhost:6379/0
REDIS_CONNECTION_POOL_SIZE=10
REDIS_SESSION_DB=1
REDIS_CACHE_DB=2
REDIS_JOB_DB=3
REDIS_RATE_LIMIT_DB=4

#=============================================================================
# Authentication Settings
#=============================================================================
JWT_SECRET_KEY=your_development_jwt_secret_key_at_least_32_characters_long
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
PASSWORD_HASH_ROUNDS=12

#=============================================================================
# Security Settings
#=============================================================================
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:8080"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=100

#=============================================================================
# File Upload Settings
#=============================================================================
UPLOAD_PATH=./uploads
UPLOAD_MAX_SIZE=104857600  # 100MB in bytes
ALLOWED_FILE_TYPES=["csv","xlsx","xls"]
TEMP_FILE_CLEANUP_HOURS=24

#=============================================================================
# Logging Configuration
#=============================================================================
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_TO_CONSOLE=true
LOG_FILE=./logs/app.log
LOG_MAX_SIZE=52428800  # 50MB
LOG_BACKUP_COUNT=5
LOG_SQL_QUERIES=false

#=============================================================================
# Background Jobs
#=============================================================================
ENABLE_BACKGROUND_JOBS=true
MAX_WORKER_THREADS=2
JOB_TIMEOUT_SECONDS=300
JOB_RETRY_ATTEMPTS=3

#=============================================================================
# CSV Processing
#=============================================================================
CSV_MAX_ROWS=10000
CSV_CHUNK_SIZE=1000
```

### Production Environment (.env.production)
```bash
# Production Environment Configuration
# SECURITY WARNING: Keep this file secure and never commit to version control

#=============================================================================
# Application Settings  
#=============================================================================
ENVIRONMENT=production
DEBUG=false
APP_NAME=eBay Manager Pro
APP_VERSION=1.0.0
API_HOST=0.0.0.0
API_PORT=8000

#=============================================================================
# Database Configuration (Use production database)
#=============================================================================
DATABASE_URL=postgresql://ebay_user:${POSTGRES_PASSWORD}@ebay-database:5432/ebay_manager
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_ECHO=false
DATABASE_MIGRATE_ON_START=false

#=============================================================================
# Redis Configuration (Use production Redis)
#=============================================================================
REDIS_URL=redis://:${REDIS_PASSWORD}@ebay-redis:6379/0
REDIS_CONNECTION_POOL_SIZE=20
REDIS_SESSION_DB=1
REDIS_CACHE_DB=2
REDIS_JOB_DB=3
REDIS_RATE_LIMIT_DB=4

#=============================================================================
# Authentication Settings (Use secure keys)
#=============================================================================
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_MIN_LENGTH=8
PASSWORD_HASH_ROUNDS=12

#=============================================================================
# Security Settings (Production domains)
#=============================================================================
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com","app.yourdomain.com"]
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60

#=============================================================================
# File Upload Settings
#=============================================================================
UPLOAD_PATH=/app/uploads
UPLOAD_MAX_SIZE=104857600  # 100MB
ALLOWED_FILE_TYPES=["csv","xlsx","xls"]
TEMP_FILE_CLEANUP_HOURS=24

#=============================================================================
# Logging Configuration (Production logging)
#=============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_TO_CONSOLE=true
LOG_FILE=/app/logs/app.log
LOG_MAX_SIZE=52428800  # 50MB
LOG_BACKUP_COUNT=10
LOG_SQL_QUERIES=false

#=============================================================================
# Background Jobs
#=============================================================================
ENABLE_BACKGROUND_JOBS=true
MAX_WORKER_THREADS=4
JOB_TIMEOUT_SECONDS=300
JOB_RETRY_ATTEMPTS=3

#=============================================================================
# CSV Processing
#=============================================================================
CSV_MAX_ROWS=50000
CSV_CHUNK_SIZE=2000

#=============================================================================
# Production Secrets (Generated automatically)
#=============================================================================
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
```

### Testing Environment (.env.testing)
```bash
# Testing Environment Configuration
# Used for automated testing and CI/CD

#=============================================================================
# Application Settings
#=============================================================================
ENVIRONMENT=testing
DEBUG=true
TESTING=true
APP_NAME=eBay Manager Test
APP_VERSION=1.0.0-test
API_HOST=127.0.0.1
API_PORT=8001

#=============================================================================
# Test Database Configuration
#=============================================================================
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/ebay_manager_test
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_DROP_ALL=true  # WARNING: Drops all tables on startup
DATABASE_MIGRATE_ON_START=true

#=============================================================================
# Test Redis Configuration  
#=============================================================================
REDIS_URL=redis://localhost:6379/15  # Use highest DB number for testing
REDIS_SESSION_DB=14
REDIS_CACHE_DB=13
REDIS_JOB_DB=12

#=============================================================================
# Test Authentication Settings
#=============================================================================
JWT_SECRET_KEY=test_jwt_secret_key_for_testing_only_32_chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=5  # Short expiry for testing
JWT_REFRESH_TOKEN_EXPIRE_DAYS=1
PASSWORD_MIN_LENGTH=6  # Lower for testing convenience
PASSWORD_HASH_ROUNDS=4  # Faster for testing

#=============================================================================
# Test File Settings
#=============================================================================
UPLOAD_PATH=./test_uploads
UPLOAD_MAX_SIZE=10485760  # 10MB for testing
TEMP_FILE_CLEANUP_HOURS=1

#=============================================================================
# Test Logging
#=============================================================================
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_TO_CONSOLE=true
LOG_FILE=./test_logs/test.log

#=============================================================================
# Test Background Jobs
#=============================================================================
MAX_WORKER_THREADS=1
JOB_TIMEOUT_SECONDS=30

#=============================================================================
# Test CSV Processing
#=============================================================================
CSV_MAX_ROWS=1000
CSV_CHUNK_SIZE=100
```

---

## FastAPI Integration

### Application Factory with Configuration
```python
# main.py - FastAPI application with configuration integration

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging.config
from contextlib import asynccontextmanager

from core.config.settings import settings
from core.config.validator import validate_startup_configuration
from core.dependencies import setup_logging
from middleware.security import setup_security_middleware

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info(f"Starting {settings.app.APP_NAME} v{settings.app.APP_VERSION}")
    logger.info(f"Environment: {settings.app.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.app.DEBUG}")
    
    # Validate configuration
    validate_startup_configuration()
    
    # Log configuration summary (non-sensitive)
    config_summary = settings.export_config_summary()
    logger.info(f"Configuration loaded: {config_summary}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

def create_app() -> FastAPI:
    """Create FastAPI application with configuration"""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app.APP_NAME,
        description=settings.app.APP_DESCRIPTION,
        version=settings.app.APP_VERSION,
        debug=settings.app.DEBUG,
        lifespan=lifespan,
        # Disable docs in production
        docs_url="/docs" if not settings.app.is_production() else None,
        redoc_url="/redoc" if not settings.app.is_production() else None,
    )
    
    # Setup security middleware
    setup_security_middleware(app)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Maintenance mode middleware
    @app.middleware("http")
    async def maintenance_mode(request: Request, call_next):
        if settings.app.MAINTENANCE_MODE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": settings.app.MAINTENANCE_MESSAGE}
            )
        return await call_next(request)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Application health check with configuration info"""
        from core.dependencies import check_database_health, check_redis_health, check_file_system_health
        
        health_status = {
            "status": "healthy",
            "app": {
                "name": settings.app.APP_NAME,
                "version": settings.app.APP_VERSION,
                "environment": settings.app.ENVIRONMENT
            },
            "checks": {
                "database": await check_database_health(),
                "redis": await check_redis_health(),
                "file_system": await check_file_system_health()
            }
        }
        
        # Determine overall health
        all_healthy = all(health_status["checks"].values())
        if not all_healthy:
            health_status["status"] = "unhealthy"
        
        return health_status
    
    # Add configuration endpoint (development only)
    if settings.app.is_development():
        @app.get("/config")
        async def get_config_summary():
            """Get configuration summary (development only)"""
            return settings.export_config_summary()
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.app.API_HOST,
        port=settings.app.API_PORT,
        reload=settings.app.is_development(),
        log_level=settings.logging.LOG_LEVEL.lower(),
        access_log=settings.logging.LOG_REQUEST_DETAILS,
    )
```

---

## Success Criteria & Validation

### Configuration Requirements ✅
- [ ] All environment variables properly validated with Pydantic
- [ ] Development, production, and testing configurations separated
- [ ] Configuration validation runs on application startup  
- [ ] Secrets management implemented with environment variables only
- [ ] Configuration health checks working for all components
- [ ] CLI tools available for configuration management
- [ ] Non-sensitive configuration export functionality working

### Security Requirements ✅
- [ ] No secrets hardcoded in configuration files
- [ ] Production configuration enforces security settings
- [ ] JWT secrets meet minimum length requirements (32+ characters)
- [ ] Database and Redis passwords properly protected
- [ ] File system permissions validated on startup
- [ ] CORS origins properly configured per environment
- [ ] Debug mode disabled in production environment

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Each config class manages one domain
- [ ] **Open/Closed**: Configuration extensible without modifying core classes
- [ ] **Liskov Substitution**: All config classes implement common validation interface
- [ ] **Interface Segregation**: Clean separation between config domains
- [ ] **Dependency Inversion**: Application depends on config abstractions
- [ ] **YAGNI Applied**: No complex config management, external stores, or over-engineering
- [ ] Essential configuration only, appropriate for 30-account scale

### Operational Requirements ✅
- [ ] Configuration validation catches common deployment issues
- [ ] Health checks verify all configuration components  
- [ ] Environment-specific settings load correctly
- [ ] Logging configuration works across all environments
- [ ] File upload paths created and verified on startup
- [ ] Background job configuration validated
- [ ] CLI tools provide operational visibility into configuration

**Backend Phase 1 Complete**: All foundation components (infrastructure, database, authentication, configuration) implemented following YAGNI/SOLID principles.

**Next Step**: Proceed to [Phase-2-CSV-Orders/01-csv-processing-engine.md](../Phase-2-CSV-Orders/01-csv-processing-engine.md) for CSV processing and order management implementation.