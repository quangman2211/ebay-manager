"""
Unit Tests for Configuration Management
Following SOLID principles - Single Responsibility for each test
"""

import pytest
import os
from unittest.mock import patch
from app.core.config import Settings

class TestConfigurationSettings:
    """Test configuration settings validation and functionality"""
    
    def test_default_settings(self):
        """Test default configuration values"""
        settings = Settings()
        
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is False
        assert settings.API_HOST == "0.0.0.0"
        assert settings.API_PORT == 8000
        assert settings.DATABASE_POOL_SIZE == 20
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "JWT_SECRET_KEY": "test_secret_key_32_characters_long",
        "DATABASE_PASSWORD": "secure_production_password",
        "REDIS_PASSWORD": "secure_redis_password_123"
    })
    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        settings = Settings()
        
        assert settings.ENVIRONMENT == "production"
        assert settings.DEBUG is False
        assert settings.JWT_SECRET_KEY == "test_secret_key_32_characters_long"
    
    def test_cors_origins_parsing_string(self):
        """Test CORS origins parsing from string"""
        with patch.dict(os.environ, {
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001,https://example.com"
        }):
            settings = Settings()
            expected = ["http://localhost:3000", "http://localhost:3001", "https://example.com"]
            assert settings.CORS_ORIGINS == expected
    
    def test_cors_origins_parsing_list(self):
        """Test CORS origins when already a list"""
        origins = ["http://localhost:3000", "https://example.com"]
        settings = Settings(CORS_ORIGINS=origins)
        assert settings.CORS_ORIGINS == origins
    
    def test_allowed_file_types_parsing(self):
        """Test allowed file types parsing from string"""
        with patch.dict(os.environ, {"ALLOWED_FILE_TYPES": "csv,xlsx,pdf,txt"}):
            settings = Settings()
            expected = ["csv", "xlsx", "pdf", "txt"]
            assert settings.ALLOWED_FILE_TYPES == expected
    
    def test_upload_size_parsing_mb(self):
        """Test upload size parsing with MB unit"""
        with patch.dict(os.environ, {"UPLOAD_MAX_SIZE": "50MB"}):
            settings = Settings()
            assert settings.UPLOAD_MAX_SIZE == 50 * 1024 * 1024
    
    def test_upload_size_parsing_gb(self):
        """Test upload size parsing with GB unit"""
        with patch.dict(os.environ, {"UPLOAD_MAX_SIZE": "1GB"}):
            settings = Settings()
            assert settings.UPLOAD_MAX_SIZE == 1 * 1024 * 1024 * 1024
    
    def test_jwt_secret_validation_success(self):
        """Test JWT secret key validation with valid key"""
        long_secret = "a" * 32
        settings = Settings(JWT_SECRET_KEY=long_secret)
        assert settings.JWT_SECRET_KEY == long_secret
    
    def test_jwt_secret_validation_failure(self):
        """Test JWT secret key validation with short key"""
        with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters"):
            Settings(JWT_SECRET_KEY="short")
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_database_password_validation_production(self):
        """Test database password validation in production"""
        with pytest.raises(ValueError, match="DATABASE_PASSWORD must be at least 12 characters"):
            Settings(DATABASE_PASSWORD="short", JWT_SECRET_KEY="a" * 32)
    
    def test_database_password_validation_development(self):
        """Test database password validation in development"""
        # Should not raise error in development
        settings = Settings(
            ENVIRONMENT="development",
            DATABASE_PASSWORD="short",
            JWT_SECRET_KEY="a" * 32
        )
        assert settings.DATABASE_PASSWORD == "short"
    
    def test_database_url_construction(self):
        """Test database URL construction from components"""
        settings = Settings(
            DATABASE_HOST="localhost",
            DATABASE_PORT=5432,
            DATABASE_USER="testuser",
            DATABASE_PASSWORD="testpass",
            DATABASE_NAME="testdb",
            JWT_SECRET_KEY="a" * 32
        )
        
        expected = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert settings.database_url_constructed == expected
    
    def test_database_url_direct(self):
        """Test using direct database URL"""
        direct_url = "postgresql://user:pass@host:5432/db"
        settings = Settings(DATABASE_URL=direct_url, JWT_SECRET_KEY="a" * 32)
        
        assert settings.database_url_constructed == direct_url
    
    def test_redis_url_construction(self):
        """Test Redis URL construction from components"""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_PASSWORD="redispass",
            JWT_SECRET_KEY="a" * 32
        )
        
        expected = "redis://:redispass@localhost:6379/0"
        assert settings.redis_url_constructed == expected
    
    def test_redis_url_no_password(self):
        """Test Redis URL construction without password"""
        settings = Settings(
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_PASSWORD="",
            JWT_SECRET_KEY="a" * 32
        )
        
        expected = "redis://localhost:6379/0"
        assert settings.redis_url_constructed == expected
    
    def test_environment_properties(self):
        """Test environment property methods"""
        dev_settings = Settings(ENVIRONMENT="development", JWT_SECRET_KEY="a" * 32)
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False
        
        prod_settings = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="a" * 32)
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True
    
    def test_path_properties(self):
        """Test path property methods"""
        settings = Settings(
            LOG_FILE="/tmp/app.log",
            UPLOAD_PATH="/tmp/uploads",
            JWT_SECRET_KEY="a" * 32
        )
        
        assert str(settings.log_file_path) == "/tmp/app.log"
        assert str(settings.upload_path_obj) == "/tmp/uploads"
    
    @patch("pathlib.Path.mkdir")
    def test_ensure_directories(self, mock_mkdir):
        """Test directory creation"""
        settings = Settings(
            LOG_FILE="/tmp/logs/app.log",
            UPLOAD_PATH="/tmp/uploads",
            JWT_SECRET_KEY="a" * 32
        )
        
        settings.ensure_directories()
        
        # Should call mkdir for both upload and log directories
        assert mock_mkdir.call_count >= 2
    
    def test_currency_format_validation_success(self):
        """Test currency format validation with valid currency"""
        # This would be tested in Account model, but testing the pattern here
        import re
        pattern = "^[A-Z]{3}$"
        
        valid_currencies = ["USD", "EUR", "GBP", "JPY"]
        for currency in valid_currencies:
            assert re.match(pattern, currency) is not None
    
    def test_currency_format_validation_failure(self):
        """Test currency format validation with invalid currency"""
        import re
        pattern = "^[A-Z]{3}$"
        
        invalid_currencies = ["US", "USDX", "usd", "123"]
        for currency in invalid_currencies:
            assert re.match(pattern, currency) is None
    
    def test_email_format_validation(self):
        """Test email format validation pattern"""
        import re
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain"
        ]
        
        for email in valid_emails:
            assert re.match(pattern, email, re.IGNORECASE) is not None
        
        for email in invalid_emails:
            assert re.match(pattern, email, re.IGNORECASE) is None