"""
Upload Strategy Interface - SOLID Compliant
Defines contracts for upload processing strategies
Interface Segregation: Clean, focused interfaces
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class UploadSourceType(Enum):
    """Upload source types - only what we actually use"""
    CSV = "csv"
    UNKNOWN = "unknown"


@dataclass
class UploadContext:
    """
    Upload context - Single Responsibility
    Contains only essential upload information
    """
    account_id: int
    data_type: str
    user_id: int
    filename: Optional[str] = None


@dataclass
class UploadResult:
    """
    Upload processing result - Single Responsibility
    Contains only essential result information
    """
    success: bool
    message: str
    errors: List[str] = None
    inserted_count: int = 0
    duplicate_count: int = 0
    total_records: int = 0
    detected_username: Optional[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class IUploadStrategy(ABC):
    """
    Strategy interface for different upload types
    Interface Segregation: Only essential methods
    """
    
    @abstractmethod
    def validate(self, content: Any, context: UploadContext) -> Tuple[bool, List[str]]:
        """Validate upload content"""
        pass
    
    @abstractmethod
    def parse(self, content: Any, context: UploadContext) -> List[Dict[str, Any]]:
        """Parse upload content into records"""
        pass
    
    @abstractmethod
    def process(self, content: Any, context: UploadContext) -> UploadResult:
        """Process the upload"""
        pass