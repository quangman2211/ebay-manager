"""
Upload Strategy Interface following SOLID principles
Single Responsibility: Each strategy handles only one upload type
Interface Segregation: Clean interface with only necessary methods
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum


class UploadSourceType(Enum):
    """Supported upload source types"""
    CSV_FILE = "csv_file"
    EXCEL_FILE = "excel_file"
    GOOGLE_SHEETS = "google_sheets"
    HTTP_URL = "http_url"
    FTP = "ftp"


@dataclass
class UploadContext:
    """Context data for upload processing"""
    account_id: int
    data_type: str  # 'order' or 'listing'
    user_id: int
    filename: Optional[str] = None
    source_url: Optional[str] = None
    auth_token: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UploadResult:
    """Result of upload processing"""
    success: bool
    message: str
    inserted_count: int = 0
    duplicate_count: int = 0
    error_count: int = 0
    total_records: int = 0
    detected_username: Optional[str] = None
    errors: Optional[List[str]] = None
    processed_data: Optional[List[Dict[str, Any]]] = None


class IUploadStrategy(ABC):
    """
    Abstract base class for upload strategies
    Following Open/Closed Principle: Open for extension, closed for modification
    """
    
    @abstractmethod
    def validate(self, content: Any, context: UploadContext) -> Tuple[bool, List[str]]:
        """
        Validate the upload content
        Returns: (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def parse(self, content: Any, context: UploadContext) -> List[Dict[str, Any]]:
        """
        Parse content into standardized format
        Returns: List of dictionaries with parsed data
        """
        pass
    
    @abstractmethod
    def detect_account_info(self, content: Any, context: UploadContext) -> Optional[str]:
        """
        Detect platform username or account identifier from content
        Returns: Detected username or None
        """
        pass
    
    @abstractmethod
    def process(self, content: Any, context: UploadContext) -> UploadResult:
        """
        Main processing method that orchestrates validation, parsing, and detection
        Returns: UploadResult with processing details
        """
        pass
    
    @property
    @abstractmethod
    def supported_types(self) -> List[UploadSourceType]:
        """
        Return list of source types this strategy supports
        """
        pass
    
    @property
    @abstractmethod
    def max_file_size(self) -> int:
        """
        Maximum file size in bytes this strategy can handle
        """
        pass