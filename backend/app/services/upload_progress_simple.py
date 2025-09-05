"""
Simple Upload Progress Tracking - YAGNI Compliant
Only implements what's actually needed for CSV upload enhancement
"""
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class UploadState(Enum):
    """Simple upload states - only what we actually need"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SimpleUploadProgress:
    """Simple progress tracking - Single Responsibility"""
    upload_id: str
    filename: str
    state: UploadState
    message: str
    progress_percent: float = 0.0
    started_at: datetime = None
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now()


class SimpleProgressTracker:
    """
    Single Responsibility: Track upload progress only
    YAGNI: Only features actually needed for CSV upload
    """
    
    def __init__(self):
        self._uploads: Dict[str, SimpleUploadProgress] = {}
    
    def create_upload(self, filename: str) -> str:
        """Create new upload tracking"""
        upload_id = str(uuid.uuid4())
        progress = SimpleUploadProgress(
            upload_id=upload_id,
            filename=filename,
            state=UploadState.PROCESSING,
            message="Processing upload..."
        )
        self._uploads[upload_id] = progress
        return upload_id
    
    def update_progress(self, upload_id: str, percent: float, message: str):
        """Update upload progress"""
        if upload_id in self._uploads:
            self._uploads[upload_id].progress_percent = percent
            self._uploads[upload_id].message = message
    
    def complete_upload(self, upload_id: str, success: bool, message: str):
        """Complete upload"""
        if upload_id in self._uploads:
            self._uploads[upload_id].state = UploadState.COMPLETED if success else UploadState.FAILED
            self._uploads[upload_id].message = message
            self._uploads[upload_id].progress_percent = 100.0
    
    def get_progress(self, upload_id: str) -> Optional[SimpleUploadProgress]:
        """Get upload progress"""
        return self._uploads.get(upload_id)


# Single instance - simple and sufficient
progress_tracker = SimpleProgressTracker()