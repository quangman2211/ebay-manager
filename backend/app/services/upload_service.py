"""
Universal Upload Service - Orchestrates upload strategies
Dependency Inversion: Depends on IUploadStrategy abstraction
Single Responsibility: Only handles strategy selection and orchestration
"""
from typing import Dict, Any, Optional, List, Type
from fastapi import UploadFile
import logging

from app.interfaces.upload_strategy import (
    IUploadStrategy, UploadContext, UploadResult, UploadSourceType
)
from app.strategies.ebay_csv_strategy import EBayCSVStrategy
from sqlalchemy.orm import Session
from app.models import CSVData, Account

logger = logging.getLogger(__name__)


class StrategyFactory:
    """
    Factory for creating upload strategies
    Open/Closed Principle: Easy to add new strategies without modifying existing code
    """
    
    _strategies: Dict[UploadSourceType, Type[IUploadStrategy]] = {
        UploadSourceType.CSV_FILE: EBayCSVStrategy,
        # Future strategies will be added here:
        # UploadSourceType.EXCEL_FILE: ExcelStrategy,
        # UploadSourceType.GOOGLE_SHEETS: GoogleSheetsStrategy,
        # UploadSourceType.HTTP_URL: HTTPUploadStrategy,
    }
    
    @classmethod
    def create_strategy(cls, source_type: UploadSourceType) -> IUploadStrategy:
        """Create appropriate strategy based on source type"""
        strategy_class = cls._strategies.get(source_type)
        if not strategy_class:
            raise ValueError(f"No strategy available for {source_type.value}")
        return strategy_class()
    
    @classmethod
    def register_strategy(cls, source_type: UploadSourceType, strategy_class: Type[IUploadStrategy]):
        """Register new strategy (for extending functionality)"""
        cls._strategies[source_type] = strategy_class


class UniversalUploadService:
    """
    Main upload service that coordinates strategies
    Single Responsibility: Orchestrates upload process
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.factory = StrategyFactory()
    
    def process_upload(
        self,
        content: Any,
        source_type: UploadSourceType,
        context: UploadContext
    ) -> UploadResult:
        """
        Process upload using appropriate strategy
        """
        try:
            # Create strategy
            strategy = self.factory.create_strategy(source_type)
            
            # Check file size limit
            if hasattr(content, '__len__'):
                if len(content) > strategy.max_file_size:
                    return UploadResult(
                        success=False,
                        message=f"File size exceeds maximum of {strategy.max_file_size} bytes"
                    )
            
            # Process with strategy
            result = strategy.process(content, context)
            
            # If successful, save to database
            if result.success and result.processed_data:
                self._save_to_database(result.processed_data, context)
                
                # Update account with detected username if found
                if result.detected_username:
                    self._update_account_username(context.account_id, result.detected_username)
            
            return result
            
        except Exception as e:
            logger.error(f"Upload processing error: {str(e)}")
            return UploadResult(
                success=False,
                message=f"Processing failed: {str(e)}",
                errors=[str(e)]
            )
    
    def detect_source_type(self, file: UploadFile) -> UploadSourceType:
        """
        Detect source type from file
        """
        filename = file.filename.lower() if file.filename else ""
        
        if filename.endswith('.csv'):
            return UploadSourceType.CSV_FILE
        elif filename.endswith(('.xlsx', '.xls')):
            return UploadSourceType.EXCEL_FILE
        else:
            # Default to CSV for now
            return UploadSourceType.CSV_FILE
    
    def get_account_suggestions(
        self,
        content: str,
        source_type: UploadSourceType,
        context: UploadContext
    ) -> Dict[str, Any]:
        """
        Get account suggestions based on detected username
        """
        try:
            strategy = self.factory.create_strategy(source_type)
            detected_username = strategy.detect_account_info(content, context)
            
            if not detected_username:
                return {
                    'detected_username': None,
                    'suggested_accounts': [],
                    'total_suggestions': 0
                }
            
            # Find matching accounts
            suggested_accounts = self._find_matching_accounts(detected_username)
            
            return {
                'detected_username': detected_username,
                'suggested_accounts': suggested_accounts,
                'total_suggestions': len(suggested_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return {
                'detected_username': None,
                'suggested_accounts': [],
                'total_suggestions': 0
            }
    
    def _save_to_database(self, data: List[Dict[str, Any]], context: UploadContext):
        """Save processed data to database"""
        try:
            inserted_count = 0
            duplicate_count = 0
            
            for record in data:
                # Extract item_id for duplicate checking
                if context.data_type == 'order':
                    item_id = record.get('order_number')
                else:
                    item_id = record.get('item_number')
                
                # Check for duplicates
                existing = self.db.query(CSVData).filter(
                    CSVData.account_id == context.account_id,
                    CSVData.data_type == context.data_type,
                    CSVData.item_id == item_id
                ).first()
                
                if not existing:
                    # Create CSVData record
                    csv_data = CSVData(
                        account_id=context.account_id,
                        data_type=context.data_type,
                        csv_row=record,
                        item_id=item_id
                    )
                    self.db.add(csv_data)
                    
                    # Create order status if it's an order
                    if context.data_type == 'order':
                        self.db.flush()  # Get the CSV data ID
                        from app.models import OrderStatus
                        order_status = OrderStatus(
                            csv_data_id=csv_data.id,
                            status='pending',
                            updated_by=context.user_id
                        )
                        self.db.add(order_status)
                    
                    inserted_count += 1
                else:
                    duplicate_count += 1
            
            self.db.commit()
            logger.info(f"Saved {inserted_count} new records, {duplicate_count} duplicates")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database save error: {str(e)}")
            raise
    
    
    def _update_account_username(self, account_id: int, username: str):
        """Update account with detected username"""
        try:
            account = self.db.query(Account).filter(Account.id == account_id).first()
            if account and not account.platform_username:
                account.platform_username = username
                self.db.commit()
                logger.info(f"Updated account {account_id} with username {username}")
        except Exception as e:
            logger.error(f"Error updating account username: {str(e)}")
    
    def _find_matching_accounts(self, username: str) -> List[Dict[str, Any]]:
        """Find accounts matching detected username"""
        accounts = []
        
        # Exact match on platform_username
        exact_matches = self.db.query(Account).filter(
            Account.platform_username == username,
            Account.is_active == True
        ).all()
        
        for account in exact_matches:
            accounts.append({
                'id': account.id,
                'name': account.name,
                'ebay_username': account.ebay_username,
                'platform_username': account.platform_username,
                'match_type': 'exact'
            })
        
        # Partial match on ebay_username if no exact matches
        if not accounts:
            partial_matches = self.db.query(Account).filter(
                Account.ebay_username.contains(username),
                Account.is_active == True
            ).all()
            
            for account in partial_matches:
                accounts.append({
                    'id': account.id,
                    'name': account.name,
                    'ebay_username': account.ebay_username,
                    'platform_username': account.platform_username,
                    'match_type': 'partial'
                })
        
        return accounts