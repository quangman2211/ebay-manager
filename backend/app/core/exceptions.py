"""
Custom Exceptions and Error Handling
Following SOLID principles - Single Responsibility for error management
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("exceptions")

class EbayManagerException(Exception):
    """
    Base exception for eBay Manager application
    Following SOLID: Single Responsibility for base exception handling
    """
    
    def __init__(
        self,
        message: str,
        code: str = "EBAY_MANAGER_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationException(EbayManagerException):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)

class AuthorizationException(EbayManagerException):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)

class ValidationException(EbayManagerException):
    """Exception for validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundError(EbayManagerException):
    """Exception for resource not found errors"""
    
    def __init__(self, resource: str = "Resource", resource_id: str = "", details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message, "NOT_FOUND", details)

class DatabaseException(EbayManagerException):
    """Exception for database operation errors"""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class FileProcessingException(EbayManagerException):
    """Exception for file processing errors"""
    
    def __init__(self, message: str = "File processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FILE_PROCESSING_ERROR", details)

class ExternalServiceException(EbayManagerException):
    """Exception for external service errors"""
    
    def __init__(self, service: str, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        full_message = f"{service}: {message}"
        super().__init__(full_message, "EXTERNAL_SERVICE_ERROR", details)

class RateLimitException(EbayManagerException):
    """Exception for rate limit exceeded errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)

# Error response formatters
def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format error response consistently
    Following SOLID: Single Responsibility for error formatting
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"  # This would be current timestamp in real implementation
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    # Add debug info in development
    if settings.DEBUG:
        response["error"]["debug"] = True
    
    return response

# Exception handlers
async def ebay_manager_exception_handler(request: Request, exc: EbayManagerException) -> JSONResponse:
    """
    Handler for custom eBay Manager exceptions
    Following SOLID: Single Responsibility for custom exception handling
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(f"EbayManagerException: {exc.code} - {exc.message}")
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Map exception types to appropriate HTTP status codes
    if isinstance(exc, AuthenticationException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ValidationException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, RateLimitException):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    
    return JSONResponse(
        status_code=status_code,
        content=format_error_response(
            error_code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for FastAPI HTTP exceptions
    Following SOLID: Single Responsibility for HTTP exception handling
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id
        ),
        headers=getattr(exc, "headers", None)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for Pydantic validation errors
    Following SOLID: Single Responsibility for validation error handling
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(f"ValidationError: {exc.errors()}")
    
    # Format validation errors for user-friendly response
    validation_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": validation_errors},
            request_id=request_id
        )
    )

async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler for Starlette HTTP exceptions
    Following SOLID: Single Responsibility for Starlette exception handling
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(f"StarletteHTTPException: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id
        )
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions
    Following SOLID: Single Responsibility for generic exception handling
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(f"Unhandled exception: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.DEBUG:
        message = f"{type(exc).__name__}: {str(exc)}"
        details = {"type": type(exc).__name__, "args": exc.args}
    else:
        message = "Internal server error"
        details = None
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            details=details,
            request_id=request_id
        )
    )