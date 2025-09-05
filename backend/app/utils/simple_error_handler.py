"""
Simple Error Handler - YAGNI Compliant
Only handles errors actually encountered in CSV upload
"""
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimpleError:
    """Single Responsibility: Hold error information only"""
    code: str
    message: str
    suggestions: List[str]


class SimpleErrorHandler:
    """
    Single Responsibility: Handle CSV upload errors only
    YAGNI: Only implement error types we actually encounter
    """
    
    # Only errors we actually need for CSV upload
    ERROR_MESSAGES = {
        'FILE_TOO_LARGE': {
            'message': 'File size exceeds 50MB limit',
            'suggestions': ['Try splitting the CSV file', 'Remove unnecessary columns']
        },
        'INVALID_CSV_FORMAT': {
            'message': 'Invalid CSV file format',
            'suggestions': ['Check file is properly formatted CSV', 'Ensure UTF-8 encoding']
        },
        'MISSING_COLUMNS': {
            'message': 'Required columns are missing',
            'suggestions': ['Check CSV has required column headers', 'Verify column names match eBay format']
        },
        'PERMISSION_DENIED': {
            'message': 'Access denied to this account',
            'suggestions': ['Contact administrator for access', 'Check account permissions']
        }
    }
    
    @classmethod
    def create_error(cls, error_code: str, custom_message: str = None) -> SimpleError:
        """Create error with recovery suggestions"""
        error_def = cls.ERROR_MESSAGES.get(error_code, {
            'message': 'Unknown error occurred',
            'suggestions': ['Please try again or contact support']
        })
        
        return SimpleError(
            code=error_code,
            message=custom_message or error_def['message'],
            suggestions=error_def['suggestions']
        )
    
    @classmethod
    def format_error_response(cls, error: SimpleError) -> Dict[str, Any]:
        """Format error for API response"""
        return {
            'success': False,
            'error': {
                'code': error.code,
                'message': error.message,
                'suggestions': error.suggestions
            }
        }