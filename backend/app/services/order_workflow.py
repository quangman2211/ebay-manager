"""
Order Workflow Engine
Following YAGNI/SOLID principles - Essential workflow management only
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.order import Order, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("order_workflow")

class OrderWorkflowEngine:
    """
    Order workflow engine for automated status management
    Following SOLID: Single Responsibility for order workflow logic
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_order_workflows(self, account_id: int) -> Dict[str, Any]:
        """
        Process all workflow rules for orders in account
        Following YAGNI: Basic workflow rules only
        """
        
        try:
            logger.info(f"Processing order workflows for account {account_id}")
            
            results = {
                'processed_orders': 0,
                'status_updates': 0,
                'overdue_flagged': 0,
                'auto_completed': 0,
                'errors': []
            }
            
            # Get orders that might need workflow processing
            orders = self._get_workflow_eligible_orders(account_id)
            
            for order in orders:
                try:
                    workflow_result = self._process_single_order_workflow(order)
                    
                    results['processed_orders'] += 1
                    results['status_updates'] += workflow_result['status_updates']
                    results['overdue_flagged'] += workflow_result['overdue_flagged']
                    results['auto_completed'] += workflow_result['auto_completed']
                    
                except Exception as e:
                    error_msg = f"Workflow error for order {order.id}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.warning(error_msg)
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Workflow processing completed for account {account_id}: {results}")
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Workflow processing failed for account {account_id}: {str(e)}")
            raise EbayManagerException(f"Workflow processing failed: {str(e)}")
    
    def _get_workflow_eligible_orders(self, account_id: int) -> List[Order]:
        """Get orders that are eligible for workflow processing"""
        
        # Get orders that are not in terminal states
        terminal_statuses = [OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]
        
        return self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.status.notin_(terminal_statuses)
            )
        ).all()
    
    def _process_single_order_workflow(self, order: Order) -> Dict[str, int]:
        """Process workflow rules for a single order"""
        
        result = {
            'status_updates': 0,
            'overdue_flagged': 0,
            'auto_completed': 0
        }
        
        # Rule 1: Auto-advance payment status
        if self._should_auto_advance_payment(order):
            self._auto_advance_payment_status(order)
            result['status_updates'] += 1
        
        # Rule 2: Auto-advance shipping status based on tracking
        if self._should_auto_advance_shipping(order):
            self._auto_advance_shipping_status(order)
            result['status_updates'] += 1
        
        # Rule 3: Flag overdue orders
        if self._should_flag_overdue(order):
            self._flag_order_as_priority(order)
            result['overdue_flagged'] += 1
        
        # Rule 4: Auto-complete delivered orders
        if self._should_auto_complete(order):
            self._auto_complete_order(order)
            result['auto_completed'] += 1
            result['status_updates'] += 1
        
        return result
    
    def _should_auto_advance_payment(self, order: Order) -> bool:
        """Check if payment status should be auto-advanced"""
        
        # Rule: If order is confirmed and payment is pending, advance to paid
        return (
            order.status == OrderStatus.CONFIRMED and
            order.payment_status == PaymentStatus.PENDING and
            order.payment_date is not None
        )
    
    def _auto_advance_payment_status(self, order: Order):
        """Auto-advance payment status"""
        
        order.payment_status = PaymentStatus.PAID
        order.paid_amount = order.total_amount
        
        if order.payment_date is None:
            order.payment_date = datetime.utcnow()
        
        # Auto-advance order status if appropriate
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CONFIRMED
        elif order.status == OrderStatus.CONFIRMED:
            order.status = OrderStatus.PROCESSING
        
        order.updated_at = datetime.utcnow()
        
        logger.info(f"Auto-advanced payment for order {order.id}")
    
    def _should_auto_advance_shipping(self, order: Order) -> bool:
        """Check if shipping status should be auto-advanced"""
        
        # Rule: If order has tracking number and is processing, advance to shipped
        return (
            order.status == OrderStatus.PROCESSING and
            order.shipping_status == ShippingStatus.NOT_SHIPPED and
            order.tracking_number is not None and
            order.shipping_date is not None
        )
    
    def _auto_advance_shipping_status(self, order: Order):
        """Auto-advance shipping status"""
        
        order.shipping_status = ShippingStatus.SHIPPED
        order.status = OrderStatus.SHIPPED
        
        if order.shipping_date is None:
            order.shipping_date = datetime.utcnow()
        
        order.updated_at = datetime.utcnow()
        
        logger.info(f"Auto-advanced shipping for order {order.id}")
    
    def _should_flag_overdue(self, order: Order) -> bool:
        """Check if order should be flagged as overdue"""
        
        # Rule: Orders older than 3 business days without shipping
        if order.is_priority:  # Already flagged
            return False
        
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        return (
            order.order_date <= cutoff_date and
            order.shipping_status == ShippingStatus.NOT_SHIPPED and
            order.status not in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]
        )
    
    def _flag_order_as_priority(self, order: Order):
        """Flag order as priority/overdue"""
        
        order.is_priority = True
        order.updated_at = datetime.utcnow()
        
        # Add note about overdue status
        current_notes = order.internal_notes or ""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        overdue_note = f"\n[{timestamp}] Order flagged as overdue - {order.days_since_order} days since order"
        order.internal_notes = current_notes + overdue_note
        
        logger.info(f"Flagged order {order.id} as overdue")
    
    def _should_auto_complete(self, order: Order) -> bool:
        """Check if order should be auto-completed"""
        
        # Rule: Orders with delivered shipping status for more than 1 day
        if order.status == OrderStatus.DELIVERED:
            return False  # Already completed
        
        return (
            order.shipping_status == ShippingStatus.DELIVERED and
            order.actual_delivery_date is not None and
            (datetime.utcnow() - order.actual_delivery_date).days >= 1
        )
    
    def _auto_complete_order(self, order: Order):
        """Auto-complete delivered order"""
        
        order.status = OrderStatus.DELIVERED
        order.updated_at = datetime.utcnow()
        
        # Add completion note
        current_notes = order.internal_notes or ""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        completion_note = f"\n[{timestamp}] Order auto-completed after delivery confirmation"
        order.internal_notes = current_notes + completion_note
        
        logger.info(f"Auto-completed order {order.id}")
    
    def get_workflow_summary(self, account_id: int) -> Dict[str, Any]:
        """Get workflow processing summary for account"""
        
        try:
            # Get order counts by status
            status_counts = {}
            status_results = self.db.query(
                Order.status,
                func.count(Order.id).label('count')
            ).filter(
                Order.account_id == account_id
            ).group_by(Order.status).all()
            
            for status, count in status_results:
                status_counts[str(status)] = count
            
            # Get overdue orders count
            cutoff_date = datetime.utcnow() - timedelta(days=3)
            overdue_count = self.db.query(Order).filter(
                and_(
                    Order.account_id == account_id,
                    Order.order_date <= cutoff_date,
                    Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                )
            ).count()
            
            # Get priority orders count
            priority_count = self.db.query(Order).filter(
                and_(
                    Order.account_id == account_id,
                    Order.is_priority == True,
                    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                )
            ).count()
            
            # Get orders needing attention
            needs_attention = self.db.query(Order).filter(
                and_(
                    Order.account_id == account_id,
                    or_(
                        and_(
                            Order.status == OrderStatus.PENDING,
                            Order.order_date <= datetime.utcnow() - timedelta(hours=24)
                        ),
                        and_(
                            Order.status == OrderStatus.PROCESSING,
                            Order.shipping_date.is_(None),
                            Order.order_date <= datetime.utcnow() - timedelta(days=2)
                        ),
                        Order.is_priority == True
                    ),
                    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                )
            ).count()
            
            return {
                'status_distribution': status_counts,
                'overdue_orders': overdue_count,
                'priority_orders': priority_count,
                'needs_attention': needs_attention,
                'workflow_rules_active': 4,  # Number of active workflow rules
                'last_processed': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow summary: {str(e)}")
            raise EbayManagerException(f"Failed to get workflow summary: {str(e)}")

def get_order_workflow_engine(db: Session) -> OrderWorkflowEngine:
    """Dependency injection for order workflow engine"""
    return OrderWorkflowEngine(db)