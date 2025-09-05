"""
Universal Upload Service - SOLID Compliant
Extracts existing CSV upload logic from main.py
Single Responsibility: Handle CSV upload processing only
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging

from app.models import Account, CSVData, OrderStatus, User
from app.schemas import DataType
from app.csv_service import CSVProcessor
from app.interfaces.upload_strategy import UploadResult, UploadContext, UploadSourceType

logger = logging.getLogger(__name__)


class UniversalUploadService:
    """
    Single Responsibility: Process CSV uploads using existing proven logic
    Open/Closed: Can be extended without modification (used by EnhancedUploadService)
    """
    
    def __init__(self, db: Session):
        """Dependency Injection: Accept database session"""
        self.db = db
    
    def detect_source_type(self, file: UploadFile) -> UploadSourceType:
        """Detect upload source type from file"""
        if file.filename and file.filename.endswith('.csv'):
            return UploadSourceType.CSV
        return UploadSourceType.UNKNOWN
    
    def process_upload(
        self,
        content: str,
        source_type: UploadSourceType,
        context: UploadContext
    ) -> UploadResult:
        """
        Process upload using existing validated logic from main.py
        YAGNI: Reuses existing proven CSV processing code
        """
        try:
            # Convert string data_type to enum (from existing main.py logic)
            try:
                data_type_enum = DataType(context.data_type)
            except ValueError:
                return UploadResult(
                    success=False,
                    message=f"Invalid data_type: {context.data_type}",
                    errors=[f"Invalid data_type: {context.data_type}"]
                )
            
            # Check account access (from existing main.py logic)
            account = self.db.query(Account).filter(Account.id == context.account_id).first()
            if not account:
                return UploadResult(
                    success=False,
                    message="Account not found",
                    errors=["Account not found"]
                )
            
            # Detect platform username (from existing main.py logic)
            detected_username = CSVProcessor.detect_platform_username(
                content,
                filename=context.filename or "",
                account_type=account.account_type or "ebay"
            )
            
            # Auto-update account with detected username (from existing main.py logic)
            if detected_username and not account.platform_username:
                account.platform_username = detected_username
                self.db.commit()
                logger.info(f"Auto-detected and saved platform username: {detected_username} for account {account.name}")
            
            # Process CSV (from existing main.py logic)
            records, errors = CSVProcessor.process_csv_file(content, data_type_enum)
            if errors:
                return UploadResult(
                    success=False,
                    message=f"CSV processing errors: {'; '.join(errors)}",
                    errors=errors
                )
            
            # Check for duplicates (from existing main.py logic)
            duplicate_errors = CSVProcessor.check_duplicates(records, data_type_enum)
            if duplicate_errors:
                return UploadResult(
                    success=False,
                    message=f"Duplicate data errors: {'; '.join(duplicate_errors)}",
                    errors=duplicate_errors
                )
            
            # Process each record (from existing main.py logic with enhanced validation)
            inserted_count = 0
            duplicate_count = 0
            validation_errors = []
            
            for i, record in enumerate(records):
                try:
                    item_id = CSVProcessor.extract_item_id(record, data_type_enum)
                except ValueError as e:
                    validation_errors.append(f"Record {i + 1}: {str(e)}")
                    continue  # Skip invalid records
                
                # Check if record already exists
                existing_record = self.db.query(CSVData).filter(
                    CSVData.account_id == context.account_id,
                    CSVData.data_type == data_type_enum.value,
                    CSVData.item_id == item_id
                ).first()
                
                if existing_record:
                    duplicate_count += 1
                    continue
                
                # Create new CSV data record
                csv_data = CSVData(
                    account_id=context.account_id,
                    data_type=data_type_enum.value,
                    csv_row=record,
                    item_id=item_id
                )
                self.db.add(csv_data)
                
                # If it's an order, create initial status
                if data_type_enum == DataType.ORDER:
                    self.db.flush()  # Get the CSV data ID
                    order_status = OrderStatus(
                        csv_data_id=csv_data.id,
                        status="pending",
                        updated_by=context.user_id
                    )
                    self.db.add(order_status)
                
                inserted_count += 1
            
            # Return validation errors if any records were invalid
            if validation_errors:
                return UploadResult(
                    success=False,
                    message=f"Validation errors found: {'; '.join(validation_errors[:3])}",
                    errors=validation_errors
                )
            
            self.db.commit()
            
            # Build success response (from existing main.py logic)
            message = "CSV uploaded successfully"
            if detected_username:
                message += f" (Auto-detected seller: {detected_username})"
            
            return UploadResult(
                success=True,
                message=message,
                inserted_count=inserted_count,
                duplicate_count=duplicate_count,
                total_records=len(records),
                detected_username=detected_username
            )
            
        except Exception as e:
            logger.error(f"Upload processing failed: {e}", exc_info=True)
            return UploadResult(
                success=False,
                message=f"Upload failed: {str(e)}",
                errors=[str(e)]
            )