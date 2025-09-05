"""
Enhanced Error Handling Utilities for Upload Operations
Provides detailed error categorization, recovery suggestions, and logging
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import traceback
import logging

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Error categories for better error handling"""
    FILE_FORMAT = "file_format"
    FILE_SIZE = "file_size"
    VALIDATION = "validation"
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    SYSTEM = "system"
    USER_INPUT = "user_input"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Warning, operation can continue
    MEDIUM = "medium"    # Error, but recoverable
    HIGH = "high"        # Critical error, operation must stop
    CRITICAL = "critical"  # System error, needs immediate attention


@dataclass
class DetailedError:
    """Structured error information"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: str
    recovery_suggestions: List[str]
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'code': self.code,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'user_message': self.user_message,
            'technical_details': self.technical_details,
            'recovery_suggestions': self.recovery_suggestions,
            'context': self.context
        }


class UploadErrorHandler:
    """
    Centralized error handling for upload operations
    Provides categorization, logging, and recovery suggestions
    """
    
    # Error definitions with codes and recovery suggestions
    ERROR_DEFINITIONS = {
        'FILE_TOO_LARGE': {
            'category': ErrorCategory.FILE_SIZE,
            'severity': ErrorSeverity.HIGH,
            'message': 'File size exceeds maximum allowed limit',
            'recovery_suggestions': [
                'Try splitting the file into smaller chunks',
                'Compress the file if possible',
                'Contact administrator to increase size limit'
            ]
        },
        'INVALID_FILE_FORMAT': {
            'category': ErrorCategory.FILE_FORMAT,
            'severity': ErrorSeverity.HIGH,
            'message': 'File format is not supported or corrupted',
            'recovery_suggestions': [
                'Ensure file is in CSV format',
                'Check file is not corrupted',
                'Try re-exporting from original source',
                'Remove any special characters from filename'
            ]
        },
        'MISSING_REQUIRED_COLUMNS': {
            'category': ErrorCategory.VALIDATION,
            'severity': ErrorSeverity.HIGH,
            'message': 'Required columns are missing from CSV file',
            'recovery_suggestions': [
                'Check CSV has all required columns',
                'Verify column names match expected format',
                'Ensure first row contains column headers',
                'Remove any empty rows at the top of file'
            ]
        },
        'DATABASE_CONNECTION_ERROR': {
            'category': ErrorCategory.DATABASE,
            'severity': ErrorSeverity.CRITICAL,
            'message': 'Unable to connect to database',
            'recovery_suggestions': [
                'Check internet connection',
                'Try again in a few minutes',
                'Contact support if problem persists'
            ]
        },
        'AUTHENTICATION_FAILED': {
            'category': ErrorCategory.AUTHENTICATION,
            'severity': ErrorSeverity.HIGH,
            'message': 'Authentication failed or session expired',
            'recovery_suggestions': [
                'Please log in again',
                'Check your credentials',
                'Clear browser cache and cookies'
            ]
        },
        'INSUFFICIENT_PERMISSIONS': {
            'category': ErrorCategory.PERMISSION,
            'severity': ErrorSeverity.HIGH,
            'message': 'Insufficient permissions for this operation',
            'recovery_suggestions': [
                'Contact administrator for required permissions',
                'Check if you have access to this account',
                'Try with a different account'
            ]
        },
        'DUPLICATE_DATA_DETECTED': {
            'category': ErrorCategory.VALIDATION,
            'severity': ErrorSeverity.MEDIUM,
            'message': 'Duplicate records detected in upload',
            'recovery_suggestions': [
                'Review duplicate records before proceeding',
                'Choose to skip or update duplicates',
                'Clean data source to avoid duplicates'
            ]
        },
        'NETWORK_TIMEOUT': {
            'category': ErrorCategory.NETWORK,
            'severity': ErrorSeverity.MEDIUM,
            'message': 'Network timeout during upload',
            'recovery_suggestions': [
                'Check internet connection',
                'Try uploading smaller files',
                'Retry the upload operation'
            ]
        },
        'INVALID_DATA_FORMAT': {
            'category': ErrorCategory.VALIDATION,
            'severity': ErrorSeverity.MEDIUM,
            'message': 'Data format validation failed',
            'recovery_suggestions': [
                'Check date formats (YYYY-MM-DD expected)',
                'Verify numeric fields contain only numbers',
                'Remove special characters from text fields',
                'Ensure required fields are not empty'
            ]
        }
    }
    
    @classmethod
    def create_error(
        self,
        error_code: str,
        context: Optional[Dict[str, Any]] = None,
        technical_details: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> DetailedError:
        """Create a detailed error object"""
        if context is None:
            context = {}
        
        definition = self.ERROR_DEFINITIONS.get(error_code, {
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.HIGH,
            'message': 'Unknown error occurred',
            'recovery_suggestions': ['Please try again or contact support']
        })
        
        user_message = custom_message or definition['message']
        
        return DetailedError(
            code=error_code,
            category=definition['category'],
            severity=definition['severity'],
            message=definition['message'],
            user_message=user_message,
            technical_details=technical_details or '',
            recovery_suggestions=definition['recovery_suggestions'],
            context=context
        )
    
    @classmethod
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: str = "upload"
    ) -> DetailedError:
        """Handle unexpected exceptions with proper categorization"""
        if context is None:
            context = {}
        
        exception_type = type(exception).__name__
        exception_message = str(exception)
        technical_details = traceback.format_exc()
        
        # Map common exceptions to error codes
        error_code = "SYSTEM_ERROR"
        if "connection" in exception_message.lower():
            error_code = "DATABASE_CONNECTION_ERROR"
        elif "permission" in exception_message.lower():
            error_code = "INSUFFICIENT_PERMISSIONS"
        elif "timeout" in exception_message.lower():
            error_code = "NETWORK_TIMEOUT"
        elif "csv" in exception_message.lower() or "parsing" in exception_message.lower():
            error_code = "INVALID_FILE_FORMAT"
        
        context.update({
            'operation': operation,
            'exception_type': exception_type,
            'exception_message': exception_message
        })
        
        error = self.create_error(
            error_code,
            context=context,
            technical_details=technical_details,
            custom_message=f"{operation.title()} failed: {exception_message}"
        )
        
        # Log the error
        logger.error(f"Exception in {operation}: {exception_message}", 
                    extra={'context': context}, exc_info=True)
        
        return error
    
    @classmethod
    def validate_upload_file(
        self,
        file_size: int,
        filename: str,
        max_size: int = 50 * 1024 * 1024  # 50MB default
    ) -> List[DetailedError]:
        """Validate upload file and return any errors"""
        errors = []
        
        # Check file size
        if file_size > max_size:
            errors.append(self.create_error(
                'FILE_TOO_LARGE',
                context={
                    'file_size': file_size,
                    'max_size': max_size,
                    'filename': filename
                },
                custom_message=f"File size ({file_size:,} bytes) exceeds maximum of {max_size:,} bytes"
            ))
        
        # Check file extension
        if not filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            errors.append(self.create_error(
                'INVALID_FILE_FORMAT',
                context={'filename': filename},
                custom_message=f"File type not supported: {filename}"
            ))
        
        return errors
    
    @classmethod
    def validate_csv_data(
        self,
        data: List[Dict[str, Any]],
        required_columns: List[str],
        data_type: str
    ) -> List[DetailedError]:
        """Validate CSV data and return any errors"""
        errors = []
        
        if not data:
            errors.append(self.create_error(
                'INVALID_FILE_FORMAT',
                context={'data_type': data_type},
                custom_message="CSV file appears to be empty or unreadable"
            ))
            return errors
        
        # Check for required columns
        if data:
            first_row = data[0]
            missing_columns = [col for col in required_columns if col not in first_row]
            
            if missing_columns:
                errors.append(self.create_error(
                    'MISSING_REQUIRED_COLUMNS',
                    context={
                        'missing_columns': missing_columns,
                        'available_columns': list(first_row.keys()),
                        'data_type': data_type
                    },
                    custom_message=f"Missing required columns: {', '.join(missing_columns)}"
                ))
        
        return errors
    
    @classmethod
    def format_error_response(
        self,
        errors: List[DetailedError],
        include_technical_details: bool = False
    ) -> Dict[str, Any]:
        """Format errors for API response"""
        formatted_errors = []
        
        for error in errors:
            error_dict = {
                'code': error.code,
                'category': error.category.value,
                'severity': error.severity.value,
                'message': error.user_message,
                'recovery_suggestions': error.recovery_suggestions
            }
            
            if include_technical_details:
                error_dict['technical_details'] = error.technical_details
                error_dict['context'] = error.context
            
            formatted_errors.append(error_dict)
        
        return {
            'success': False,
            'errors': formatted_errors,
            'error_count': len(errors),
            'has_critical_errors': any(e.severity == ErrorSeverity.CRITICAL for e in errors),
            'has_recoverable_errors': any(e.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM] for e in errors)
        }