"""
Enhanced Upload Service - SOLID Compliant
Extends existing UniversalUploadService with progress tracking
Single Responsibility: Add progress tracking to existing upload flow
"""
from typing import Dict, Any
import logging

from app.services.upload_service import UniversalUploadService
from app.services.upload_progress_simple import progress_tracker
from app.utils.simple_error_handler import SimpleErrorHandler
from app.interfaces.upload_strategy import UploadContext, UploadSourceType

logger = logging.getLogger(__name__)


class EnhancedUploadService:
    """
    Single Responsibility: Add progress tracking to upload process
    Open/Closed: Extends existing service without modification
    Dependency Inversion: Depends on existing abstractions
    """
    
    def __init__(self, upload_service: UniversalUploadService):
        """Depend on abstraction (existing service)"""
        self.upload_service = upload_service
    
    def upload_with_progress(
        self,
        content: str,
        filename: str,
        source_type: UploadSourceType,
        context: UploadContext
    ) -> Dict[str, Any]:
        """
        Process upload with progress tracking
        YAGNI: Only adds progress to existing proven functionality
        """
        # Create progress tracking
        upload_id = progress_tracker.create_upload(filename)
        
        try:
            # Validate file size (YAGNI: Only check what we actually need)
            max_size = 50 * 1024 * 1024  # 50MB - realistic for CSV
            if len(content.encode('utf-8')) > max_size:
                error = SimpleErrorHandler.create_error('FILE_TOO_LARGE')
                progress_tracker.complete_upload(upload_id, False, error.message)
                return SimpleErrorHandler.format_error_response(error)
            
            progress_tracker.update_progress(upload_id, 25, "Validating file...")
            
            # Use existing upload service (Dependency Inversion)
            result = self.upload_service.process_upload(content, source_type, context)
            
            progress_tracker.update_progress(upload_id, 75, "Processing data...")
            
            if result.success:
                progress_tracker.complete_upload(
                    upload_id, 
                    True, 
                    f"Successfully processed {result.total_records} records"
                )
                
                return {
                    'success': True,
                    'upload_id': upload_id,
                    'message': result.message,
                    'inserted_count': result.inserted_count,
                    'duplicate_count': result.duplicate_count,
                    'total_records': result.total_records,
                    'detected_username': result.detected_username
                }
            else:
                progress_tracker.complete_upload(upload_id, False, result.message)
                return {
                    'success': False,
                    'upload_id': upload_id,
                    'message': result.message,
                    'errors': result.errors
                }
                
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            error = SimpleErrorHandler.create_error(
                'INVALID_CSV_FORMAT',
                custom_message=f"Processing failed: {str(e)}"
            )
            progress_tracker.complete_upload(upload_id, False, error.message)
            return SimpleErrorHandler.format_error_response(error)
    
    def get_upload_progress(self, upload_id: str) -> Dict[str, Any]:
        """Get upload progress - Single Responsibility"""
        progress = progress_tracker.get_progress(upload_id)
        
        if not progress:
            return {'success': False, 'error': 'Upload not found'}
        
        return {
            'success': True,
            'upload_id': progress.upload_id,
            'filename': progress.filename,
            'state': progress.state.value,
            'message': progress.message,
            'progress_percent': progress.progress_percent,
            'started_at': progress.started_at.isoformat()
        }