"""
CSV Order Import Service
Following SOLID principles - Single Responsibility for CSV-to-Order processing
Connects CSV processing infrastructure with Order management system
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from decimal import Decimal

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.models.account import Account
from app.utils.csv_validators import order_csv_validator
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("csv_order_service")

class CSVOrderImportService:
    """
    CSV Order Import Service
    Following SOLID: Single Responsibility for CSV order processing
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_csv_data(
        self, 
        csv_data: List[Dict[str, str]], 
        account_id: int, 
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Process CSV data and import orders
        Following SOLID: Single method responsibility
        """
        
        try:
            # Validate account access
            self._validate_account_access(account_id, user_id)
            
            logger.info(f"Starting CSV order import: {len(csv_data)} rows for account {account_id}")
            
            # Validate CSV data
            validation_result = order_csv_validator.validate_batch(csv_data)
            
            if validation_result['valid_rows'] == 0:
                raise EbayManagerException(
                    "No valid orders found in CSV data",
                    error_code="NO_VALID_DATA"
                )
            
            # Import valid orders
            import_result = self._import_orders(
                validation_result['validated_data'],
                account_id,
                user_id,
                batch_id,
                filename
            )
            
            # Combine validation and import results
            final_result = {
                'success': True,
                'total_csv_rows': validation_result['total_rows'],
                'valid_csv_rows': validation_result['valid_rows'],
                'invalid_csv_rows': validation_result['invalid_rows'],
                'created_orders': import_result['created_count'],
                'updated_orders': import_result['updated_count'],
                'failed_orders': import_result['failed_count'],
                'skipped_orders': import_result['skipped_count'],
                'validation_errors': validation_result['errors'],
                'validation_warnings': validation_result['warnings'],
                'import_errors': import_result['errors'],
                'duplicate_orders': validation_result['duplicate_orders'],
                'batch_id': batch_id,
                'filename': filename,
                'processing_summary': {
                    'success_rate': (import_result['created_count'] + import_result['updated_count']) / 
                                   validation_result['valid_rows'] * 100 if validation_result['valid_rows'] > 0 else 0,
                    'validation_success_rate': validation_result['summary']['success_rate'],
                    'total_errors': len(validation_result['errors']) + len(import_result['errors']),
                    'total_warnings': len(validation_result['warnings'])
                }
            }
            
            logger.info(f"CSV order import completed: {import_result['created_count']} created, "
                       f"{import_result['updated_count']} updated, {import_result['failed_count']} failed")
            
            return final_result
            
        except Exception as e:
            logger.error(f"CSV order import failed: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"CSV order import failed: {str(e)}")
    
    def _validate_account_access(self, account_id: int, user_id: int) -> None:
        """Validate user access to account"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EbayManagerException("User not found", error_code="USER_NOT_FOUND")
        
        # Admin can access any account
        if user.role == 'admin':
            # Just verify account exists
            account = self.db.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise EbayManagerException("Account not found", error_code="ACCOUNT_NOT_FOUND")
            return
        
        # Regular users can only access their own accounts
        account = self.db.query(Account).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()
        
        if not account:
            raise EbayManagerException(
                "Account not found or access denied", 
                error_code="ACCOUNT_ACCESS_DENIED"
            )
    
    def _import_orders(
        self, 
        validated_data: List[Dict[str, Any]], 
        account_id: int,
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """Import validated order data into database"""
        
        result = {
            'created_count': 0,
            'updated_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'errors': []
        }
        
        # Process orders in batches for better performance
        batch_size = 100
        total_batches = (len(validated_data) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(validated_data))
            batch_data = validated_data[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_data)} orders)")
            
            batch_result = self._process_order_batch(
                batch_data, account_id, user_id, batch_id, filename
            )
            
            result['created_count'] += batch_result['created_count']
            result['updated_count'] += batch_result['updated_count']
            result['failed_count'] += batch_result['failed_count']
            result['skipped_count'] += batch_result['skipped_count']
            result['errors'].extend(batch_result['errors'])
        
        return result
    
    def _process_order_batch(
        self, 
        batch_data: List[Dict[str, Any]], 
        account_id: int,
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """Process a batch of orders with transaction management"""
        
        result = {
            'created_count': 0,
            'updated_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'errors': []
        }
        
        try:
            for order_data in batch_data:
                try:
                    import_result = self._import_single_order(
                        order_data, account_id, user_id, batch_id, filename
                    )
                    
                    if import_result['action'] == 'created':
                        result['created_count'] += 1
                    elif import_result['action'] == 'updated':
                        result['updated_count'] += 1
                    elif import_result['action'] == 'skipped':
                        result['skipped_count'] += 1
                        
                except Exception as e:
                    result['failed_count'] += 1
                    error_msg = f"Failed to import order {order_data.get('ebay_order_id', 'Unknown')}: {str(e)}"
                    result['errors'].append(error_msg)
                    logger.warning(error_msg)
            
            # Commit batch
            self.db.commit()
            
        except Exception as e:
            # Rollback on batch failure
            self.db.rollback()
            logger.error(f"Batch import failed, rolling back: {str(e)}")
            
            # Mark all orders in this batch as failed
            result['failed_count'] = len(batch_data)
            result['created_count'] = 0
            result['updated_count'] = 0
            result['skipped_count'] = 0
            result['errors'].append(f"Batch import failed: {str(e)}")
        
        return result
    
    def _import_single_order(
        self, 
        order_data: Dict[str, Any], 
        account_id: int,
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Dict[str, str]:
        """Import a single order with duplicate handling"""
        
        ebay_order_id = order_data['ebay_order_id']
        
        # Check for existing order
        existing_order = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.ebay_order_id == ebay_order_id
            )
        ).first()
        
        if existing_order:
            # Update existing order
            updated = self._update_existing_order(existing_order, order_data, batch_id, filename)
            return {'action': 'updated' if updated else 'skipped'}
        else:
            # Create new order
            self._create_new_order(order_data, account_id, user_id, batch_id, filename)
            return {'action': 'created'}
    
    def _create_new_order(
        self, 
        order_data: Dict[str, Any], 
        account_id: int,
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Order:
        """Create a new order from CSV data"""
        
        # Prepare order data for database
        db_order_data = self._prepare_order_data_for_db(
            order_data, account_id, user_id, batch_id, filename
        )
        
        # Create order instance
        order = Order(**db_order_data)
        
        # Add to session
        self.db.add(order)
        self.db.flush()  # Get ID without committing
        
        logger.debug(f"Created order: {order.id} (eBay ID: {ebay_order_id})")
        
        return order
    
    def _update_existing_order(
        self, 
        existing_order: Order, 
        order_data: Dict[str, Any], 
        batch_id: str,
        filename: str
    ) -> bool:
        """Update existing order with CSV data"""
        
        updated = False
        
        # Fields that can be updated from CSV
        updateable_fields = [
            'buyer_email', 'payment_method', 'payment_status', 'status',
            'shipping_status', 'payment_date', 'shipping_date', 'actual_delivery_date',
            'tracking_number', 'notes', 'internal_notes'
        ]
        
        for field in updateable_fields:
            if field in order_data and order_data[field] is not None:
                current_value = getattr(existing_order, field)
                new_value = order_data[field]
                
                # Only update if different
                if current_value != new_value:
                    setattr(existing_order, field, new_value)
                    updated = True
        
        if updated:
            # Update import metadata
            existing_order.csv_file_id = batch_id
            existing_order.imported_at = datetime.utcnow()
            existing_order.last_sync_date = datetime.utcnow()
            existing_order.updated_at = datetime.utcnow()
            
            logger.debug(f"Updated order: {existing_order.id} (eBay ID: {existing_order.ebay_order_id})")
        
        return updated
    
    def _prepare_order_data_for_db(
        self, 
        order_data: Dict[str, Any], 
        account_id: int,
        user_id: int,
        batch_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """Prepare CSV order data for database insertion"""
        
        # Calculate subtotal (approximation if not provided)
        subtotal = order_data['total_amount']
        shipping_cost = order_data.get('shipping_cost', Decimal('0.00'))
        if shipping_cost:
            subtotal = subtotal - shipping_cost
        
        db_data = {
            # Basic order information
            'account_id': account_id,
            'user_id': user_id,
            'ebay_order_id': order_data['ebay_order_id'],
            
            # Status fields
            'status': order_data['status'],
            'payment_status': order_data['payment_status'],
            'shipping_status': order_data['shipping_status'],
            
            # Customer information
            'buyer_username': order_data['buyer_username'],
            'buyer_email': order_data.get('buyer_email'),
            
            # Shipping address
            'shipping_name': order_data.get('shipping_name', order_data['buyer_username']),
            'shipping_address_line1': order_data.get('shipping_address_line1', ''),
            'shipping_address_line2': order_data.get('shipping_address_line2'),
            'shipping_city': order_data.get('shipping_city', ''),
            'shipping_state': order_data.get('shipping_state'),
            'shipping_postal_code': order_data.get('shipping_postal_code', ''),
            'shipping_country': order_data.get('shipping_country', 'US'),
            
            # Financial information
            'currency': order_data.get('currency', 'USD'),
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'tax_amount': Decimal('0.00'),  # Calculate if tax info available
            'total_amount': order_data['total_amount'],
            'paid_amount': order_data['total_amount'] if order_data['payment_status'] == PaymentStatus.PAID else Decimal('0.00'),
            
            # Payment information
            'payment_method': order_data.get('payment_method'),
            
            # Dates
            'order_date': order_data['order_date'],
            'payment_date': order_data.get('payment_date'),
            'shipping_date': order_data.get('shipping_date'),
            'actual_delivery_date': order_data.get('actual_delivery_date'),
            
            # Shipping information
            'tracking_number': order_data.get('tracking_number'),
            
            # Notes
            'notes': order_data.get('notes'),
            'internal_notes': order_data.get('internal_notes'),
            
            # Import metadata
            'csv_file_id': batch_id,
            'imported_at': datetime.utcnow(),
            'last_sync_date': datetime.utcnow(),
            
            # Flags (basic defaults)
            'is_priority': False,
            'is_gift': False,
            'requires_signature': False,
            'is_international': order_data.get('shipping_country', 'US') != 'US'
        }
        
        # Remove None values
        db_data = {k: v for k, v in db_data.items() if v is not None}
        
        return db_data
    
    def get_import_statistics(self, account_id: int, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get CSV import statistics for account"""
        
        try:
            # Validate account access
            self._validate_account_access(account_id, user_id)
            
            # Get orders imported in the last N days
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            imported_orders = self.db.query(Order).filter(
                and_(
                    Order.account_id == account_id,
                    Order.imported_at.isnot(None),
                    Order.imported_at >= cutoff_date
                )
            ).all()
            
            # Calculate statistics
            stats = {
                'total_imported_orders': len(imported_orders),
                'import_files_count': len(set(order.csv_file_id for order in imported_orders if order.csv_file_id)),
                'date_range': {
                    'from': cutoff_date.isoformat(),
                    'to': datetime.utcnow().isoformat()
                },
                'orders_by_status': {},
                'orders_by_date': {},
                'recent_imports': []
            }
            
            # Group by status
            for order in imported_orders:
                status = str(order.status)
                if status not in stats['orders_by_status']:
                    stats['orders_by_status'][status] = 0
                stats['orders_by_status'][status] += 1
            
            # Group by import date
            for order in imported_orders:
                if order.imported_at:
                    date_key = order.imported_at.date().isoformat()
                    if date_key not in stats['orders_by_date']:
                        stats['orders_by_date'][date_key] = 0
                    stats['orders_by_date'][date_key] += 1
            
            # Recent imports (last 10 files)
            recent_files = {}
            for order in sorted(imported_orders, key=lambda x: x.imported_at or datetime.min, reverse=True):
                if order.csv_file_id and order.csv_file_id not in recent_files and len(recent_files) < 10:
                    recent_files[order.csv_file_id] = {
                        'batch_id': order.csv_file_id,
                        'imported_at': order.imported_at.isoformat() if order.imported_at else None,
                        'order_count': sum(1 for o in imported_orders if o.csv_file_id == order.csv_file_id)
                    }
            
            stats['recent_imports'] = list(recent_files.values())
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get import statistics: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to get import statistics: {str(e)}")

def get_csv_order_service(db: Session) -> CSVOrderImportService:
    """Dependency injection for CSV order service"""
    return CSVOrderImportService(db)