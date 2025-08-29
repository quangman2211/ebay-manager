"""
Core Middleware
Following SOLID principles - Single Responsibility for each middleware
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger, log_request

logger = get_logger("middleware")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses
    Following SOLID: Single Responsibility for request logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            log_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                client_ip=request.client.host,
                user_agent=request.headers.get("User-Agent", "Unknown")
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request error
            logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
            log_request(
                method=request.method,
                path=str(request.url.path),
                status_code=500,
                duration_ms=duration_ms,
                request_id=request_id,
                client_ip=request.client.host,
                user_agent=request.headers.get("User-Agent", "Unknown"),
                error=str(e)
            )
            
            # Re-raise the exception
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers
    Following SOLID: Single Responsibility for security headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add API version header
        response.headers["X-API-Version"] = "1.0.0"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic rate limiting middleware (placeholder for Redis implementation)
    Following SOLID: Single Responsibility for rate limiting
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting (placeholder implementation)"""
        # TODO: Implement Redis-based rate limiting
        # For now, just pass through
        
        client_ip = request.client.host
        
        # Placeholder rate limit check
        # if self._is_rate_limited(client_ip):
        #     return Response(
        #         content="Too Many Requests",
        #         status_code=429,
        #         headers={"Retry-After": "60"}
        #     )
        
        return await call_next(request)

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling health check requests efficiently
    Following SOLID: Single Responsibility for health checks
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle health check requests with minimal overhead"""
        
        # Quick health check for load balancers (bypass normal processing)
        if request.url.path == "/ping":
            return Response(content="pong", status_code=200)
        
        return await call_next(request)