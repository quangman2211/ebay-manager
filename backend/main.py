"""
eBay Manager FastAPI Application
Main application entry point following SOLID/YAGNI principles
"""

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
import asyncpg
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import (
    RequestLoggingMiddleware, SecurityHeadersMiddleware, 
    RateLimitMiddleware, HealthCheckMiddleware
)
from app.core.exceptions import (
    EbayManagerException, ebay_manager_exception_handler,
    http_exception_handler, validation_exception_handler,
    starlette_http_exception_handler, generic_exception_handler
)
from app.api.auth import router as auth_router
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import psutil
import os

# Initialize logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="eBay Manager API",
    description="Multi-account eBay management system following YAGNI/SOLID principles",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add custom middleware (order matters!)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_REQUESTS)
app.add_middleware(HealthCheckMiddleware)

# CORS middleware configuration (should be last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")

# Application startup time
startup_time = datetime.utcnow()

def get_uptime_seconds() -> float:
    """Calculate application uptime in seconds"""
    return (datetime.utcnow() - startup_time).total_seconds()

async def check_database_connection() -> str:
    """Check PostgreSQL database connectivity"""
    try:
        # Parse DATABASE_URL or construct from components
        if settings.DATABASE_URL:
            conn = await asyncpg.connect(settings.DATABASE_URL)
        else:
            conn = await asyncpg.connect(
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                database=settings.DATABASE_NAME,
            )
        await conn.execute('SELECT 1')
        await conn.close()
        return "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return "unhealthy"

async def check_redis_connection() -> str:
    """Check Redis connectivity"""
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        redis_client.ping()
        redis_client.close()
        return "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return "unhealthy"

def check_file_system_access() -> str:
    """Check file system access for uploads and logs"""
    try:
        # Check upload directory
        if not os.path.exists(settings.UPLOAD_PATH):
            os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
        
        # Test write access
        test_file = os.path.join(settings.UPLOAD_PATH, "health_check.tmp")
        with open(test_file, "w") as f:
            f.write("health_check")
        os.remove(test_file)
        
        return "healthy"
    except Exception as e:
        logger.error(f"File system health check failed: {str(e)}")
        return "unhealthy"

def check_memory_usage() -> str:
    """Check system memory usage"""
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 90:  # More than 90% memory usage
            return "warning"
        elif memory.percent > 95:  # Critical memory usage
            return "critical"
        return "healthy"
    except Exception as e:
        logger.error(f"Memory check failed: {str(e)}")
        return "unknown"

@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": "eBay Manager API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/ping")
async def ping():
    """Simple ping endpoint for health checks"""
    return "pong"

@app.get("/health")
async def health_check():
    """
    Comprehensive health check for all services
    Following SOLID principle: Single Responsibility for health monitoring
    """
    checks = {
        "api": "healthy",
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "storage": check_file_system_access(),
        "memory": check_memory_usage(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Determine overall health
    critical_services = ["database", "redis", "storage"]
    all_critical_healthy = all(
        checks[service] == "healthy" 
        for service in critical_services
    )
    
    overall_status = "healthy" if all_critical_healthy else "unhealthy"
    
    response_data = {
        "status": overall_status,
        "checks": checks,
        "version": "1.0.0",
        "uptime_seconds": get_uptime_seconds(),
        "environment": settings.ENVIRONMENT
    }
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_status == "healthy" else 503
    
    return JSONResponse(
        content=response_data,
        status_code=status_code
    )

# Exception handlers (specific to generic order)
app.add_exception_handler(EbayManagerException, ebay_manager_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("eBay Manager API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.database_url_constructed}")
    logger.info(f"Redis URL: {settings.redis_url_constructed}")
    logger.info("SOLID/YAGNI principles enforced")
    
    # Ensure database tables exist
    try:
        from app.models import Base, engine
        # In production, use proper migrations instead
        if settings.DEBUG:
            logger.info("Creating database tables in debug mode...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("eBay Manager API shutting down...")
    try:
        # Clean up resources
        from app.models import engine
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )