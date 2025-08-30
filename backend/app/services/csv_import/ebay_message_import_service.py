"""
eBay Message Import Service for coordinating CSV import process
Following SOLID principles - Single Responsibility for import coordination
YAGNI compliance: Simple import logic, no complex message threading algorithms
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import pandas as pd
from pathlib import Path

from app.services.csv_import.ebay_message_csv_detector import (
    EbayMessageFormatDetector, 
    EbayMessageValidator, 
    EbayMessageCSVFormat
)
from app.services.csv_import.ebay_message_transformer import (
    EbayMessageTransformer, 
    MessageDirection, 
    MessageType, 
    MessagePriority
)
from app.repositories.ebay_message_repository import EbayMessageRepository, MessageThreadRepository
from app.schemas.communication import (
    EbayMessageCreate, 
    MessageThreadCreate, 
    MessageThreadUpdate,
    MessageTypeEnum,
    MessagePriorityEnum
)
from app.core.exceptions import ValidationError, NotFoundError, DatabaseError


class EbayMessageImportService:
    """
    SOLID: Single Responsibility - Coordinate eBay message import process
    YAGNI: Simple import logic, no complex message threading algorithms
    """
    
    def __init__(
        self,
        ebay_message_repository: EbayMessageRepository,
        thread_repository: MessageThreadRepository
    ):
        self.ebay_message_repository = ebay_message_repository
        self.thread_repository = thread_repository
        self.format_detector = EbayMessageFormatDetector()
        self.validator = EbayMessageValidator()
        self.transformer = EbayMessageTransformer()
    
    async def import_messages_from_csv(
        self,
        file_path: str,
        account_id: int,
        account_username: str,
        expected_format: Optional[EbayMessageCSVFormat] = None
    ) -> Dict[str, Any]:
        """
        Import eBay messages from CSV file
        YAGNI: Simple CSV processing, no complex deduplication algorithms
        """
        results = {
            'total_rows': 0,
            'messages_created': 0,
            'messages_skipped': 0,
            'threads_created': 0,
            'threads_updated': 0,
            'validation_errors': 0,
            'processing_errors': 0,
            'errors': []
        }
        
        try:
            # Verify file exists
            if not Path(file_path).exists():
                raise NotFoundError(f"CSV file not found: {file_path}")
            
            # Load and validate CSV
            df = pd.read_csv(file_path)
            results['total_rows'] = len(df)
            
            if df.empty:
                return results
            
            # Detect format if not specified
            if expected_format:
                detected_format = expected_format
                confidence = 1.0
            else:
                detected_format, confidence = self.format_detector.detect_format(df)
            
            if detected_format == EbayMessageCSVFormat.UNKNOWN or confidence < 0.7:
                raise ValidationError(f"Unrecognized CSV format (confidence: {confidence:.2f})")
            
            # Validate format compatibility
            format_validation = self.format_detector.validate_format_compatibility(df, detected_format)
            if not format_validation['valid']:
                raise ValidationError(f"CSV format validation failed: {format_validation['errors']}")
            
            # Process each message
            for index, row in df.iterrows():
                try:
                    await self._process_message_row(
                        row.to_dict(), 
                        index, 
                        detected_format, 
                        account_id,
                        account_username,
                        results
                    )
                except Exception as e:
                    results['processing_errors'] += 1
                    results['errors'].append(f"Row {index + 1}: Processing failed - {str(e)}")
        
        except Exception as e:
            results['errors'].append(f"Import failed: {str(e)}")
            raise
        
        return results
    
    async def _process_message_row(
        self,
        row_data: Dict[str, Any],
        row_index: int,
        csv_format: EbayMessageCSVFormat,
        account_id: int,
        account_username: str,
        results: Dict[str, Any]
    ):
        """Process a single message row"""
        # Validate row
        validation_errors = self.validator.validate_row(row_data, row_index, csv_format)
        if validation_errors:
            results['validation_errors'] += 1
            results['errors'].extend(validation_errors)
            return
        
        # Check if message already exists
        ebay_message_id = row_data.get('Message ID')
        if ebay_message_id:
            existing_message = await self.ebay_message_repository.get_by_ebay_id(str(ebay_message_id))
            if existing_message:
                results['messages_skipped'] += 1
                return
        
        # Transform to message object
        message_data = self.transformer.transform_row_to_message(
            row_data, csv_format, account_id, account_username
        )
        
        # Get or create thread
        thread = await self._get_or_create_thread(
            row_data, csv_format, account_id, message_data, results
        )
        
        # Set thread ID and create message
        message_data['thread_id'] = thread.id
        
        # Determine if requires response
        if (message_data['direction'] == MessageDirection.INCOMING.value and 
            not message_data.get('has_response', False)):
            message_data['requires_response'] = True
        
        # Create message create schema
        message_create = EbayMessageCreate(**message_data)
        
        # Create message
        await self.ebay_message_repository.create(message_create)
        results['messages_created'] += 1
        
        # Update thread activity
        await self.thread_repository.update(thread.id, MessageThreadUpdate(
            last_message_date=message_data['message_date'],
            last_activity_date=datetime.utcnow()
        ))
    
    async def _get_or_create_thread(
        self,
        row_data: Dict[str, Any],
        csv_format: EbayMessageCSVFormat,
        account_id: int,
        message_data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> MessageThread:
        """Get existing thread or create new one - YAGNI: Simple thread matching"""
        
        # Extract thread context
        thread_context = self.transformer.extract_thread_context(row_data, csv_format)
        
        # Try to find existing thread by item_id and participants
        item_id = thread_context.get('item_id')
        customer_username = None
        
        if message_data['direction'] == MessageDirection.INCOMING.value:
            customer_username = message_data['sender_username']
        else:
            customer_username = message_data['recipient_username']
        
        # Look for existing thread
        if item_id and customer_username:
            existing_thread = await self.thread_repository.find_by_item_and_customer(
                account_id, item_id, customer_username
            )
            
            if existing_thread:
                results['threads_updated'] += 1
                return existing_thread
        
        # Create new thread
        thread_subject = thread_context.get('item_title', f"Item #{item_id}")
        
        thread_create = MessageThreadCreate(
            account_id=account_id,
            external_thread_id=None,  # No external thread ID for eBay messages
            thread_type='ebay_message',
            item_id=item_id,
            item_title=thread_context.get('item_title'),
            order_id=thread_context.get('order_id'),
            customer_username=customer_username,
            subject=thread_subject,
            message_type=MessageTypeEnum(message_data['message_type']) if message_data.get('message_type') else None,
            priority=MessagePriorityEnum(message_data['priority']) if message_data.get('priority') else MessagePriorityEnum.NORMAL,
            first_message_date=message_data['message_date'],
            last_message_date=message_data['message_date']
        )
        
        thread = await self.thread_repository.create(thread_create)
        results['threads_created'] += 1
        
        # Set requires_response if incoming message
        if message_data['direction'] == MessageDirection.INCOMING.value:
            await self.thread_repository.update(thread.id, MessageThreadUpdate(
                requires_response=True,
                status='open'
            ))
        
        return thread
    
    async def get_import_summary(self, account_id: int, days_back: int = 30) -> Dict[str, Any]:
        """Get import summary for account - YAGNI: Basic statistics only"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        try:
            # Get message counts by type
            message_counts = await self.ebay_message_repository.get_counts_by_type(
                account_id, cutoff_date
            )
            
            # Get thread counts by status
            thread_counts = await self.thread_repository.get_counts_by_status(
                account_id, cutoff_date
            )
            
            # Get messages requiring response
            pending_response_count = await self.ebay_message_repository.get_pending_response_count(
                account_id
            )
            
            return {
                'total_messages': sum(message_counts.values()),
                'message_counts_by_type': message_counts,
                'thread_counts_by_status': thread_counts,
                'pending_responses': pending_response_count,
                'period_days': days_back
            }
        except Exception as e:
            raise DatabaseError(f"Failed to get import summary: {str(e)}")
    
    async def validate_csv_format(self, file_path: str) -> Dict[str, Any]:
        """Validate CSV file format without importing"""
        try:
            if not Path(file_path).exists():
                raise NotFoundError(f"CSV file not found: {file_path}")
            
            # Load CSV
            df = pd.read_csv(file_path)
            
            if df.empty:
                return {
                    'valid': False,
                    'errors': ['CSV file is empty'],
                    'detected_format': 'unknown',
                    'confidence': 0.0
                }
            
            # Detect format
            detected_format, confidence = self.format_detector.detect_format(df)
            
            # Validate format compatibility
            format_validation = self.format_detector.validate_format_compatibility(df, detected_format)
            
            return {
                'valid': format_validation['valid'],
                'detected_format': detected_format.value,
                'confidence': confidence,
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'errors': format_validation.get('errors', []),
                'warnings': []
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"File validation failed: {str(e)}"],
                'detected_format': 'unknown',
                'confidence': 0.0
            }