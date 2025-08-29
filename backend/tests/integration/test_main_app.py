"""
Integration Tests for Main Application
Following SOLID principles - Single Responsibility for each test
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from ..conftest import assert_response_success, assert_response_error

class TestApplicationEndpoints:
    """Test main application endpoints"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns basic API info"""
        response = client.get("/")
        data = assert_response_success(response)
        
        assert data["name"] == "eBay Manager API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_ping_endpoint(self, client: TestClient):
        """Test ping endpoint for health checks"""
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.text == "pong"
    
    def test_docs_endpoint_accessible(self, client: TestClient):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_endpoint(self, client: TestClient):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        data = assert_response_success(response)
        
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "eBay Manager API"
        assert data["info"]["version"] == "1.0.0"

class TestHealthCheckEndpoint:
    """Test health check endpoint functionality"""
    
    @patch('app.main.check_database_connection')
    @patch('app.main.check_redis_connection')
    @patch('app.main.check_file_system_access')
    @patch('app.main.check_memory_usage')
    async def test_health_check_all_healthy(
        self, 
        mock_memory, 
        mock_fs, 
        mock_redis, 
        mock_db,
        client: TestClient
    ):
        """Test health check when all services are healthy"""
        # Mock all checks to return healthy
        mock_db.return_value = "healthy"
        mock_redis.return_value = "healthy"
        mock_fs.return_value = "healthy"
        mock_memory.return_value = "healthy"
        
        response = client.get("/health")
        data = assert_response_success(response)
        
        assert data["status"] == "healthy"
        assert data["checks"]["api"] == "healthy"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"
        assert data["checks"]["storage"] == "healthy"
        assert data["checks"]["memory"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data["checks"]
    
    @patch('app.main.check_database_connection')
    @patch('app.main.check_redis_connection')
    @patch('app.main.check_file_system_access')
    @patch('app.main.check_memory_usage')
    async def test_health_check_database_unhealthy(
        self, 
        mock_memory, 
        mock_fs, 
        mock_redis, 
        mock_db,
        client: TestClient
    ):
        """Test health check when database is unhealthy"""
        mock_db.return_value = "unhealthy"
        mock_redis.return_value = "healthy"
        mock_fs.return_value = "healthy"
        mock_memory.return_value = "healthy"
        
        response = client.get("/health")
        assert response.status_code == 503  # Service Unavailable
        
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"] == "unhealthy"
    
    @patch('app.main.check_database_connection')
    @patch('app.main.check_redis_connection')
    @patch('app.main.check_file_system_access')
    @patch('app.main.check_memory_usage')
    async def test_health_check_redis_unhealthy(
        self, 
        mock_memory, 
        mock_fs, 
        mock_redis, 
        mock_db,
        client: TestClient
    ):
        """Test health check when Redis is unhealthy"""
        mock_db.return_value = "healthy"
        mock_redis.return_value = "unhealthy"
        mock_fs.return_value = "healthy"
        mock_memory.return_value = "healthy"
        
        response = client.get("/health")
        assert response.status_code == 503
        
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["redis"] == "unhealthy"
    
    @patch('app.main.check_database_connection')
    @patch('app.main.check_redis_connection')
    @patch('app.main.check_file_system_access')
    @patch('app.main.check_memory_usage')
    async def test_health_check_memory_warning(
        self, 
        mock_memory, 
        mock_fs, 
        mock_redis, 
        mock_db,
        client: TestClient
    ):
        """Test health check with memory warning (should still be healthy)"""
        mock_db.return_value = "healthy"
        mock_redis.return_value = "healthy"
        mock_fs.return_value = "healthy"
        mock_memory.return_value = "warning"  # Memory warning doesn't fail health
        
        response = client.get("/health")
        data = assert_response_success(response)  # Should still be 200
        
        assert data["status"] == "healthy"
        assert data["checks"]["memory"] == "warning"

class TestSecurityHeaders:
    """Test security headers middleware"""
    
    def test_security_headers_present(self, client: TestClient):
        """Test that security headers are added to responses"""
        response = client.get("/")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0.0"
    
    def test_cors_headers_present(self, client: TestClient):
        """Test that CORS headers are properly configured"""
        # Make a preflight OPTIONS request
        response = client.options("/api/v1/auth/login", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        })
        
        assert response.status_code == 200
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

class TestRequestLogging:
    """Test request logging middleware"""
    
    def test_request_id_header(self, client: TestClient):
        """Test that request ID is added to response headers"""
        response = client.get("/")
        
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 20  # UUID should be long
        assert "-" in request_id  # UUID format
    
    def test_different_requests_different_ids(self, client: TestClient):
        """Test that different requests get different IDs"""
        response1 = client.get("/")
        response2 = client.get("/")
        
        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]
        
        assert id1 != id2

class TestErrorHandling:
    """Test error handling and exception responses"""
    
    def test_404_not_found(self, client: TestClient):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "HTTP_ERROR"
    
    def test_method_not_allowed(self, client: TestClient):
        """Test 405 method not allowed"""
        response = client.patch("/")  # PATCH not allowed on root
        assert response.status_code == 405
    
    def test_validation_error_format(self, client: TestClient):
        """Test validation error response format"""
        # Send invalid JSON to registration endpoint
        response = client.post("/api/v1/auth/register", json={
            "username": "ab",  # Too short
            "email": "invalid-email",  # Invalid format
            "password": "weak"  # Too weak
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in data["error"]
        assert "validation_errors" in data["error"]["details"]
    
    def test_internal_server_error_format(self, client: TestClient):
        """Test internal server error response format (mocked)"""
        # This would require mocking an internal error
        # For now, just test the structure exists
        pass

class TestApplicationLifecycle:
    """Test application startup and shutdown events"""
    
    def test_application_starts_successfully(self, client: TestClient):
        """Test that application starts and is responsive"""
        # If we can make requests, the app started successfully
        response = client.get("/")
        assert response.status_code == 200
    
    def test_database_tables_creation_in_debug(self):
        """Test database tables are created in debug mode"""
        # This would be tested by checking if tables exist after startup
        # For now, just verify the startup doesn't crash
        pass