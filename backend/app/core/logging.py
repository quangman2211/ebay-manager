"""
Ultra-simplified Logging - YAGNI compliant
90% complexity reduction: 244 → 20 lines
Following successful Phases 2-4 pattern
"""

import logging

def setup_logging() -> logging.Logger:
    """YAGNI: Simple logging setup"""
    logger = logging.getLogger("ebay_manager")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """YAGNI: Simple logger getter"""
    return logging.getLogger(f"ebay_manager.{name}" if name else "ebay_manager")

def log_security_event(event_type: str, **kwargs):
    """YAGNI: Simple security logging"""
    logger = get_logger("security")
    logger.warning(f"Security event: {event_type}")