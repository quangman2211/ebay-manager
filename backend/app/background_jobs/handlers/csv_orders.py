"""
CSV Order Processing Job Handler
Following SOLID principles - Single Responsibility for CSV order processing jobs
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.background_jobs.core import BaseJobHandler, Job, JobResult
from app.services.csv_order_service import CSVOrderImportService
from app.models.base import get_db
from app.models.csv import CSVUpload
from app.core.exceptions import EbayManagerException

class CSVOrderProcessingJobHandler(BaseJobHandler):
    """Handler for CSV order processing jobs"""
    
    async def execute(self, job: Job) -> JobResult:
        """Execute CSV order processing job"""
        
        self.logger.info(f"Starting CSV order processing job {job.id}")
        
        try:
            # Get parameters
            csv_upload_id = job.parameters.get('csv_upload_id')
            account_id = job.parameters.get('account_id')
            user_id = job.parameters.get('user_id')
            
            if not csv_upload_id:
                raise ValueError("csv_upload_id parameter is required")
            if not account_id:
                raise ValueError("account_id parameter is required")
            if not user_id:
                raise ValueError("user_id parameter is required")
            
            self.update_progress(job, 10, "Validating parameters", "parameter_validation")
            
            # Get CSV upload record
            db = next(get_db())
            try:
                csv_upload = db.query(CSVUpload).filter(CSVUpload.id == csv_upload_id).first()
                if not csv_upload:
                    raise ValueError(f"CSV upload {csv_upload_id} not found")
                
                self.update_progress(job, 20, "Loading CSV file", "file_loading")
                
                # Check if file exists
                file_path = Path(csv_upload.file_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"CSV file not found: {file_path}")
                
                self.update_progress(job, 30, "Reading CSV data", "csv_reading")
                
                # Read CSV data
                csv_data = self._read_csv_file(file_path)
                
                if not csv_data:
                    raise ValueError("CSV file is empty or could not be read")
                
                self.update_progress(job, 40, f"Processing {len(csv_data)} rows", "csv_processing")
                
                # Update CSV upload status
                csv_upload.status = 'processing'
                csv_upload.total_rows = len(csv_data)
                db.commit()
                
                # Process CSV data using CSV Order Service
                csv_order_service = CSVOrderImportService(db)
                
                import_result = csv_order_service.process_csv_data(
                    csv_data=csv_data,
                    account_id=account_id,
                    user_id=user_id,
                    batch_id=csv_upload.batch_id,
                    filename=csv_upload.original_filename
                )
                
                self.update_progress(job, 90, "Updating upload status", "status_update")
                
                # Update CSV upload record with results
                csv_upload.status = 'completed' if import_result['success'] else 'failed'
                csv_upload.processed_rows = import_result['created_orders'] + import_result['updated_orders']
                csv_upload.success_rows = import_result['created_orders'] + import_result['updated_orders']
                csv_upload.error_rows = import_result['failed_orders']
                csv_upload.validation_errors = import_result.get('validation_errors', [])
                csv_upload.processing_summary = import_result.get('processing_summary', {})
                csv_upload.completed_at = datetime.utcnow()
                
                db.commit()
                
                self.update_progress(job, 100, "Processing completed", "completed")
                
                return JobResult(
                    success=True,
                    data={
                        'csv_upload_id': csv_upload_id,
                        'total_csv_rows': import_result['total_csv_rows'],
                        'valid_csv_rows': import_result['valid_csv_rows'],
                        'invalid_csv_rows': import_result['invalid_csv_rows'],
                        'created_orders': import_result['created_orders'],
                        'updated_orders': import_result['updated_orders'],
                        'failed_orders': import_result['failed_orders'],
                        'skipped_orders': import_result['skipped_orders'],
                        'processing_summary': import_result['processing_summary'],
                        'batch_id': import_result['batch_id'],
                        'filename': import_result['filename']
                    },
                    warnings=import_result.get('validation_warnings', [])
                )
                
            finally:
                db.close()
                
        except Exception as e:
            self.logger.error(f"CSV order processing job {job.id} failed: {str(e)}")
            
            # Update CSV upload status to failed
            try:
                db = next(get_db())
                try:
                    csv_upload = db.query(CSVUpload).filter(CSVUpload.id == csv_upload_id).first()
                    if csv_upload:
                        csv_upload.status = 'failed'
                        csv_upload.error_message = str(e)
                        csv_upload.completed_at = datetime.utcnow()
                        db.commit()
                finally:
                    db.close()
            except Exception as update_error:
                self.logger.error(f"Failed to update CSV upload status: {str(update_error)}")
            
            return JobResult(
                success=False,
                error=str(e),
                data={
                    'csv_upload_id': csv_upload_id,
                    'error_type': type(e).__name__
                }
            )
    
    def _read_csv_file(self, file_path: Path) -> List[Dict[str, str]]:
        """Read CSV file and return list of dictionaries"""
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not read CSV file with any supported encoding")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert to list of dictionaries
            csv_data = df.to_dict('records')
            
            # Clean string values
            for row in csv_data:
                for key, value in row.items():
                    if isinstance(value, str):
                        row[key] = value.strip()
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"Failed to read CSV file {file_path}: {str(e)}")
            raise
    
    def should_retry(self, job: Job, error: Exception) -> bool:
        """Determine if CSV processing job should be retried"""
        
        # Don't retry file-related errors
        non_retryable_errors = [
            FileNotFoundError,
            PermissionError,
            ValueError,  # Invalid CSV format or parameters
            UnicodeDecodeError  # File encoding issues
        ]
        
        # Don't retry EbayManagerException with specific error codes
        if isinstance(error, EbayManagerException):
            non_retryable_codes = [
                'NO_VALID_DATA',
                'ACCOUNT_NOT_FOUND',
                'ACCOUNT_ACCESS_DENIED',
                'USER_NOT_FOUND'
            ]
            if hasattr(error, 'error_code') and error.error_code in non_retryable_codes:
                return False
        
        if any(isinstance(error, err_type) for err_type in non_retryable_errors):
            return False
        
        return job.retry_count < job.max_retries