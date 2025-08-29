"""
Unit Tests for Authentication Utilities
Following SOLID principles - Single Responsibility for each test
"""

import pytest
from datetime import datetime, timedelta
from app.utils.auth import PasswordManager, JWTManager, SecurityUtils
from app.core.config import settings

class TestPasswordManager:
    """Test password management utilities"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60+ characters
        assert hashed.startswith("$2b$")
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(wrong_password, hashed) is False
    
    def test_generate_random_password(self):
        """Test random password generation"""
        password1 = PasswordManager.generate_random_password(12)
        password2 = PasswordManager.generate_random_password(12)
        
        assert len(password1) >= 12
        assert len(password2) >= 12
        assert password1 != password2  # Should be different
    
    def test_generate_random_password_different_lengths(self):
        """Test random password generation with different lengths"""
        short_password = PasswordManager.generate_random_password(8)
        long_password = PasswordManager.generate_random_password(20)
        
        assert len(short_password) >= 8
        assert len(long_password) >= 20

class TestJWTManager:
    """Test JWT token management utilities"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        token = JWTManager.create_access_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        assert token.count(".") == 2  # JWT format: header.payload.signature
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        token = JWTManager.create_refresh_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 100
        assert token.count(".") == 2
    
    def test_verify_valid_access_token(self):
        """Test verification of valid access token"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        token = JWTManager.create_access_token(token_data)
        payload = JWTManager.verify_token(token, token_type="access")
        
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Test verification of valid refresh token"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        token = JWTManager.create_refresh_token(token_data)
        payload = JWTManager.verify_token(token, token_type="refresh")
        
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        payload = JWTManager.verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_wrong_token_type(self):
        """Test verification with wrong token type"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        access_token = JWTManager.create_access_token(token_data)
        payload = JWTManager.verify_token(access_token, token_type="refresh")
        
        assert payload is None
    
    def test_extract_user_id_valid_token(self):
        """Test extracting user ID from valid token"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        token = JWTManager.create_access_token(token_data)
        user_id = JWTManager.extract_user_id(token)
        
        assert user_id == 123
    
    def test_extract_user_id_invalid_token(self):
        """Test extracting user ID from invalid token"""
        invalid_token = "invalid.token.here"
        user_id = JWTManager.extract_user_id(invalid_token)
        
        assert user_id is None
    
    def test_token_expiration(self):
        """Test that tokens have expiration"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "user"
        }
        
        # Create token with very short expiration
        token = JWTManager.create_access_token(
            token_data, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        payload = JWTManager.verify_token(token)
        assert payload is None  # Should be None due to expiration

class TestSecurityUtils:
    """Test general security utilities"""
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        token1 = SecurityUtils.generate_secure_token(32)
        token2 = SecurityUtils.generate_secure_token(32)
        
        assert len(token1) > 30  # URL-safe base64 encoding
        assert len(token2) > 30
        assert token1 != token2
    
    def test_is_password_strong_valid(self):
        """Test strong password validation with valid passwords"""
        strong_passwords = [
            "Password123!",
            "MySecure2Pass@",
            "Complex1$Password",
            "StrongP@ssw0rd"
        ]
        
        for password in strong_passwords:
            assert SecurityUtils.is_password_strong(password) is True
    
    def test_is_password_strong_invalid(self):
        """Test strong password validation with invalid passwords"""
        weak_passwords = [
            "short",  # Too short
            "lowercase123",  # No uppercase
            "UPPERCASE123",  # No lowercase
            "NoNumbers!",  # No digits
            "NoSpecial123",  # No special characters
            "",  # Empty
            "12345678"  # Only numbers
        ]
        
        for password in weak_passwords:
            assert SecurityUtils.is_password_strong(password) is False
    
    def test_get_password_strength_message_strong(self):
        """Test password strength message for strong password"""
        strong_password = "StrongP@ssw0rd"
        message = SecurityUtils.get_password_strength_message(strong_password)
        
        assert message == "Password is strong"
    
    def test_get_password_strength_message_weak(self):
        """Test password strength message for weak password"""
        weak_password = "weak"
        message = SecurityUtils.get_password_strength_message(weak_password)
        
        assert "must contain" in message
        assert len(message) > 20  # Should provide detailed feedback
    
    @pytest.mark.parametrize("length", [8, 16, 32, 64])
    def test_generate_secure_token_lengths(self, length):
        """Test secure token generation with different lengths"""
        token = SecurityUtils.generate_secure_token(length)
        # URL-safe base64 encoding makes the output longer than input
        assert len(token) >= length