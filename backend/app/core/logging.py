"""
Logging Configuration
Following SOLID principles - Single Responsibility for logging setup
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Following SOLID: Single Responsibility for JSON log formatting
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry, ensure_ascii=False)

class StandardFormatter(logging.Formatter):
    """
    Standard text formatter for human-readable logs
    Following SOLID: Single Responsibility for text log formatting
    """
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

def setup_logging() -> logging.Logger:
    """
    Setup application logging configuration
    Following SOLID: Single function responsibility for complete logging setup
    """
    
    # Get root logger
    logger = logging.getLogger("ebay_manager")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler for development
    if settings.is_development or settings.DEBUG:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(StandardFormatter())
        logger.addHandler(console_handler)
    
    # File handler for all environments
    if settings.LOG_FILE:
        # Ensure log directory exists
        log_file_path = Path(settings.LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse log file max size
        max_bytes = 50 * 1024 * 1024  # Default 50MB
        if isinstance(settings.LOG_MAX_SIZE, str):
            if settings.LOG_MAX_SIZE.upper().endswith("MB"):
                max_bytes = int(settings.LOG_MAX_SIZE[:-2]) * 1024 * 1024
            elif settings.LOG_MAX_SIZE.upper().endswith("GB"):
                max_bytes = int(settings.LOG_MAX_SIZE[:-2]) * 1024 * 1024 * 1024
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE,
            maxBytes=max_bytes,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        
        # Use JSON format for file logs
        if settings.LOG_FORMAT.lower() == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(StandardFormatter())
            
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        logger.addHandler(file_handler)
    
    # Configure uvicorn loggers to use our logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = logger.handlers
    uvicorn_logger.setLevel(logger.level)
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")  
    uvicorn_access_logger.handlers = logger.handlers
    uvicorn_access_logger.setLevel(logger.level)
    
    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get logger instance for specific module
    Following SOLID: Single function responsibility
    """
    if name:
        return logging.getLogger(f"ebay_manager.{name}")
    return logging.getLogger("ebay_manager")

def log_request(method: str, path: str, status_code: int, duration_ms: float, **extra):
    """
    Log HTTP request information
    Following SOLID: Single responsibility for request logging
    """
    logger = get_logger("requests")
    
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **extra
    }
    
    level = logging.INFO
    if status_code >= 400:
        level = logging.WARNING
    if status_code >= 500:
        level = logging.ERROR
        
    logger.log(level, f"{method} {path} - {status_code} ({duration_ms:.2f}ms)", extra=log_data)

def log_database_query(query: str, duration_ms: float, **extra):
    """
    Log database query information
    Following SOLID: Single responsibility for database logging
    """
    logger = get_logger("database")
    
    log_data = {
        "query": query[:200] + "..." if len(query) > 200 else query,  # Truncate long queries
        "duration_ms": duration_ms,
        **extra
    }
    
    level = logging.INFO
    if duration_ms > 1000:  # Slow query warning
        level = logging.WARNING
        
    logger.log(level, f"Database query executed ({duration_ms:.2f}ms)", extra=log_data)

def log_csv_processing(filename: str, rows_processed: int, duration_ms: float, errors: int = 0, **extra):
    """
    Log CSV processing information
    Following SOLID: Single responsibility for CSV processing logging
    """
    logger = get_logger("csv_processing")
    
    log_data = {
        "filename": filename,
        "rows_processed": rows_processed,
        "duration_ms": duration_ms,
        "errors": errors,
        **extra
    }
    
    level = logging.INFO
    if errors > 0:
        level = logging.WARNING
        
    logger.log(
        level,
        f"CSV processing completed: {filename} ({rows_processed} rows, {duration_ms:.2f}ms)",
        extra=log_data
    )

def log_background_job(job_id: str, job_type: str, status: str, duration_ms: float = None, **extra):
    """
    Log background job information
    Following SOLID: Single responsibility for job logging
    """
    logger = get_logger("background_jobs")
    
    log_data = {
        "job_id": job_id,
        "job_type": job_type,
        "status": status,
        **extra
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    level = logging.INFO
    if status == "failed":
        level = logging.ERROR
    elif status == "retrying":
        level = logging.WARNING
        
    message = f"Background job {status}: {job_type} ({job_id})"
    if duration_ms:
        message += f" ({duration_ms:.2f}ms)"
        
    logger.log(level, message, extra=log_data)

def log_security_event(event_type: str, user_id: str = None, ip_address: str = None, **extra):
    """
    Log security-related events
    Following SOLID: Single responsibility for security logging
    """
    logger = get_logger("security")
    
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        **extra
    }
    
    # Security events are always important
    level = logging.WARNING
    if event_type in ["login_failed", "unauthorized_access", "token_abuse"]:
        level = logging.ERROR
        
    logger.log(level, f"Security event: {event_type}", extra=log_data)