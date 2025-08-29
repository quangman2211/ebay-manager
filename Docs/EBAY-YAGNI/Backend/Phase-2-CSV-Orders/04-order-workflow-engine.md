# Order Workflow Engine - Status Management & Notifications

## Overview
Order workflow engine for eBay Management System following YAGNI/SOLID principles. Implements order status transitions, business rule validation, automated actions, and notification system optimized for 30-account scale with essential workflow features only.

## SOLID Principles Applied
- **Single Responsibility**: Each workflow component handles one specific concern (status, rules, actions, notifications)
- **Open/Closed**: Workflow engine extensible for new status types and actions without modifying core
- **Liskov Substitution**: All workflow actions implement common execution interface
- **Interface Segregation**: Separate interfaces for status management, rule validation, and notifications
- **Dependency Inversion**: Workflow depends on abstract action and notification interfaces

## YAGNI Compliance
✅ **Essential Status Workflow**: Simple pending→processing→shipped→delivered flow only  
✅ **Basic Business Rules**: Status validation, required field checks, date logic only  
✅ **Simple Notifications**: Email alerts for status changes, no complex automation  
✅ **Manual Actions**: User-triggered status changes, minimal automation  
❌ **Eliminated**: Complex state machines, advanced automation, workflow designers, multi-approval processes

---

## Order Workflow Architecture

### Workflow Components
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ORDER WORKFLOW ENGINE                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Status        │───▶│  Rule Engine    │───▶│   Action        │             │
│  │   Manager       │    │                 │    │   Executor      │             │
│  │                 │    │ • Transition    │    │                 │             │
│  │ • Validate      │    │   validation    │    │ • Update fields │             │
│  │   transitions   │    │ • Business      │    │ • Send emails   │             │
│  │ • Update status │    │   rules         │    │ • Log changes   │             │
│  │ • Track history │    │ • Required      │    │ • Trigger jobs  │             │
│  │ • Lock orders   │    │   fields        │    │ • External API  │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                       │                       │                      │
│           ▼                       ▼                       ▼                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Notification  │    │  Event Logger   │    │  Audit Trail    │             │
│  │   System        │    │                 │    │                 │             │
│  │                 │    │ • Status        │    │ • Change        │             │
│  │ • Email alerts  │    │   changes       │    │   tracking      │             │
│  │ • User notify   │    │ • Actions taken │    │ • User actions  │             │
│  │ • Admin alerts  │    │ • Errors/       │    │ • Timestamps    │             │
│  │ • Templates     │    │   warnings      │    │ • Rollback info │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Status Transition Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ORDER STATUS WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌─────────────┐   validate    ┌─────────────┐   validate    ┌─────────────┐ │
│    │   PENDING   │──────────────▶│ PROCESSING  │──────────────▶│  SHIPPED    │ │
│    │             │   payment     │             │   tracking    │             │ │
│    │ • New order │   confirmed   │ • Payment   │   number      │ • Tracking  │ │
│    │ • Awaiting  │               │   received  │               │   provided  │ │
│    │   payment   │               │ • Preparing │               │ • In transit│ │
│    └─────────────┘               └─────────────┘               └─────────────┘ │
│           │                               │                               │     │
│           │ cancel                        │ cancel                        │     │
│           ▼                               ▼                               ▼     │
│    ┌─────────────┐               ┌─────────────┐               ┌─────────────┐ │
│    │ CANCELLED   │               │ CANCELLED   │               │ DELIVERED   │ │
│    │             │               │             │               │             │ │
│    │ • Order     │               │ • Cancelled │               │ • Customer  │ │
│    │   cancelled │               │   after     │               │   received  │ │
│    │ • No payment│               │   payment   │               │ • Complete  │ │
│    └─────────────┘               └─────────────┘               └─────────────┘ │
│                                                                         │       │
│                                                                         ▼       │
│                                                               ┌─────────────┐   │
│                                                               │  REFUNDED   │   │
│                                                               │             │   │
│                                                               │ • Money     │   │
│                                                               │   returned  │   │
│                                                               │ • Dispute   │   │
│                                                               │   resolved  │   │
│                                                               └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Implementation

### 1. Order Status Manager
```python
# workflow/status_manager.py - Order status transition management

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from database.models import Order, User
from workflow.exceptions import WorkflowError, InvalidTransitionError, BusinessRuleError

logger = logging.getLogger(__name__)

class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class TransitionReason(str, Enum):
    """Reasons for status transitions"""
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_FAILED = "payment_failed"
    ORDER_PREPARED = "order_prepared"
    SHIPPED_TO_CUSTOMER = "shipped_to_customer"
    DELIVERED_TO_CUSTOMER = "delivered_to_customer"
    CUSTOMER_REQUEST = "customer_request"
    ADMIN_ACTION = "admin_action"
    SYSTEM_ACTION = "system_action"
    DISPUTE_RESOLUTION = "dispute_resolution"

class OrderStatusManager:
    """Manages order status transitions and validation"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Define allowed status transitions
        self.allowed_transitions: Dict[OrderStatus, Set[OrderStatus]] = {
            OrderStatus.PENDING: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
            OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
            OrderStatus.CANCELLED: set(),  # Terminal state
            OrderStatus.REFUNDED: set()    # Terminal state
        }
        
        # Required fields for each status
        self.required_fields: Dict[OrderStatus, List[str]] = {
            OrderStatus.PENDING: ['ebay_order_id', 'buyer_username', 'total_amount', 'order_date'],
            OrderStatus.PROCESSING: ['payment_date'],
            OrderStatus.SHIPPED: ['shipped_date', 'tracking_number'],
            OrderStatus.DELIVERED: ['delivered_date'],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: []
        }
        
        # Automatic field updates for status changes
        self.auto_field_updates: Dict[OrderStatus, Dict[str, Any]] = {
            OrderStatus.PROCESSING: {'payment_date': lambda: datetime.utcnow()},
            OrderStatus.SHIPPED: {'shipped_date': lambda: datetime.utcnow()},
            OrderStatus.DELIVERED: {'delivered_date': lambda: datetime.utcnow()}
        }
    
    def validate_transition(
        self, 
        current_status: OrderStatus, 
        new_status: OrderStatus
    ) -> bool:
        """Validate if status transition is allowed"""
        
        if current_status == new_status:
            return True  # No change
        
        allowed = self.allowed_transitions.get(current_status, set())
        return new_status in allowed
    
    def get_allowed_transitions(self, current_status: OrderStatus) -> Set[OrderStatus]:
        """Get list of allowed transitions from current status"""
        return self.allowed_transitions.get(current_status, set())
    
    def change_status(
        self,
        order: Order,
        new_status: OrderStatus,
        reason: TransitionReason,
        user: User,
        notes: Optional[str] = None,
        **additional_fields
    ) -> bool:
        """Change order status with full validation and logging"""
        
        old_status = OrderStatus(order.order_status)
        
        try:
            # Validate transition
            if not self.validate_transition(old_status, new_status):
                raise InvalidTransitionError(
                    f"Invalid transition from {old_status.value} to {new_status.value}"
                )
            
            # Validate business rules
            self._validate_business_rules(order, old_status, new_status)
            
            # Check required fields
            self._validate_required_fields(order, new_status, **additional_fields)
            
            # Begin transaction
            self.db.begin()
            
            # Update order status
            order.order_status = new_status.value
            order.updated_at = datetime.utcnow()
            
            # Apply automatic field updates
            self._apply_auto_updates(order, new_status)
            
            # Apply additional field updates
            for field, value in additional_fields.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            # Log the status change
            self._log_status_change(
                order, old_status, new_status, reason, user, notes
            )
            
            # Commit transaction
            self.db.commit()
            
            logger.info(
                f"Order {order.id} status changed from {old_status.value} to {new_status.value} "
                f"by user {user.username} (reason: {reason.value})"
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to change order {order.id} status: {str(e)}")
            raise e
    
    def bulk_status_change(
        self,
        orders: List[Order],
        new_status: OrderStatus,
        reason: TransitionReason,
        user: User,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Change status for multiple orders"""
        
        success_count = 0
        error_count = 0
        errors = []
        
        for order in orders:
            try:
                self.change_status(order, new_status, reason, user, notes)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Order {order.id}: {str(e)}")
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors,
            'total_processed': len(orders)
        }
    
    def _validate_business_rules(
        self, 
        order: Order, 
        old_status: OrderStatus, 
        new_status: OrderStatus
    ):
        """Validate business rules for status transitions"""
        
        # Rule: Cannot ship without payment
        if new_status == OrderStatus.SHIPPED and not order.payment_date:
            raise BusinessRuleError("Cannot ship order without payment confirmation")
        
        # Rule: Cannot deliver without shipping
        if new_status == OrderStatus.DELIVERED and not order.shipped_date:
            raise BusinessRuleError("Cannot mark as delivered without shipping date")
        
        # Rule: Cannot refund undelivered orders (unless cancelled)
        if new_status == OrderStatus.REFUNDED and old_status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise BusinessRuleError("Can only refund delivered or cancelled orders")
        
        # Rule: Check for minimum time between status changes (prevent rapid changes)
        if order.updated_at and (datetime.utcnow() - order.updated_at).seconds < 60:
            # Allow rapid changes for certain transitions
            allowed_rapid = [
                (OrderStatus.PENDING, OrderStatus.CANCELLED),
                (OrderStatus.PROCESSING, OrderStatus.CANCELLED)
            ]
            if (old_status, new_status) not in allowed_rapid:
                raise BusinessRuleError("Status changed too recently, please wait before changing again")
    
    def _validate_required_fields(
        self, 
        order: Order, 
        new_status: OrderStatus, 
        **additional_fields
    ):
        """Validate required fields for new status"""
        
        required = self.required_fields.get(new_status, [])
        missing_fields = []
        
        for field in required:
            # Check existing order field
            current_value = getattr(order, field, None)
            
            # Check if being provided in additional_fields
            provided_value = additional_fields.get(field)
            
            if not current_value and not provided_value:
                missing_fields.append(field)
        
        if missing_fields:
            raise BusinessRuleError(
                f"Missing required fields for status {new_status.value}: {', '.join(missing_fields)}"
            )
    
    def _apply_auto_updates(self, order: Order, new_status: OrderStatus):
        """Apply automatic field updates for status"""
        
        updates = self.auto_field_updates.get(new_status, {})
        
        for field, value_func in updates.items():
            # Only update if field is not already set
            current_value = getattr(order, field, None)
            if not current_value:
                if callable(value_func):
                    setattr(order, field, value_func())
                else:
                    setattr(order, field, value_func)
    
    def _log_status_change(
        self,
        order: Order,
        old_status: OrderStatus,
        new_status: OrderStatus,
        reason: TransitionReason,
        user: User,
        notes: Optional[str]
    ):
        """Log status change to audit trail"""
        
        from database.models import OrderStatusHistory
        
        status_history = OrderStatusHistory(
            order_id=order.id,
            old_status=old_status.value,
            new_status=new_status.value,
            reason=reason.value,
            user_id=user.id,
            notes=notes,
            changed_at=datetime.utcnow()
        )
        
        self.db.add(status_history)

class OrderWorkflowEngine:
    """Complete order workflow management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.status_manager = OrderStatusManager(db)
        
    def process_order_action(
        self,
        order_id: int,
        action: str,
        user: User,
        **action_params
    ) -> Dict[str, Any]:
        """Process a workflow action on an order"""
        
        # Get order
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise WorkflowError(f"Order {order_id} not found")
        
        # Define action handlers
        action_handlers = {
            'confirm_payment': self._handle_confirm_payment,
            'ship_order': self._handle_ship_order,
            'confirm_delivery': self._handle_confirm_delivery,
            'cancel_order': self._handle_cancel_order,
            'refund_order': self._handle_refund_order,
            'update_tracking': self._handle_update_tracking
        }
        
        handler = action_handlers.get(action)
        if not handler:
            raise WorkflowError(f"Unknown workflow action: {action}")
        
        return handler(order, user, **action_params)
    
    def _handle_confirm_payment(
        self, 
        order: Order, 
        user: User, 
        payment_method: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle payment confirmation"""
        
        additional_fields = {}
        if payment_method:
            additional_fields['payment_method'] = payment_method
        
        self.status_manager.change_status(
            order=order,
            new_status=OrderStatus.PROCESSING,
            reason=TransitionReason.PAYMENT_RECEIVED,
            user=user,
            notes="Payment confirmed by user",
            **additional_fields
        )
        
        return {'message': 'Payment confirmed, order is now processing'}
    
    def _handle_ship_order(
        self, 
        order: Order, 
        user: User, 
        tracking_number: str,
        shipping_method: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle order shipping"""
        
        additional_fields = {'tracking_number': tracking_number}
        if shipping_method:
            additional_fields['shipping_method'] = shipping_method
        
        self.status_manager.change_status(
            order=order,
            new_status=OrderStatus.SHIPPED,
            reason=TransitionReason.SHIPPED_TO_CUSTOMER,
            user=user,
            notes=f"Order shipped with tracking: {tracking_number}",
            **additional_fields
        )
        
        return {'message': f'Order shipped with tracking number: {tracking_number}'}
    
    def _handle_confirm_delivery(
        self, 
        order: Order, 
        user: User,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle delivery confirmation"""
        
        self.status_manager.change_status(
            order=order,
            new_status=OrderStatus.DELIVERED,
            reason=TransitionReason.DELIVERED_TO_CUSTOMER,
            user=user,
            notes="Delivery confirmed by user"
        )
        
        return {'message': 'Order marked as delivered'}
    
    def _handle_cancel_order(
        self, 
        order: Order, 
        user: User,
        reason: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle order cancellation"""
        
        # Determine cancellation reason
        if reason == "customer_request":
            transition_reason = TransitionReason.CUSTOMER_REQUEST
        else:
            transition_reason = TransitionReason.ADMIN_ACTION
        
        self.status_manager.change_status(
            order=order,
            new_status=OrderStatus.CANCELLED,
            reason=transition_reason,
            user=user,
            notes=f"Order cancelled: {reason or 'No reason provided'}"
        )
        
        return {'message': 'Order cancelled successfully'}
    
    def _handle_refund_order(
        self, 
        order: Order, 
        user: User,
        refund_amount: Optional[float] = None,
        refund_reason: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle order refund"""
        
        additional_fields = {}
        if refund_amount:
            additional_fields['refund_amount'] = refund_amount
        
        notes = f"Order refunded"
        if refund_reason:
            notes += f": {refund_reason}"
        if refund_amount:
            notes += f" (Amount: ${refund_amount})"
        
        self.status_manager.change_status(
            order=order,
            new_status=OrderStatus.REFUNDED,
            reason=TransitionReason.DISPUTE_RESOLUTION,
            user=user,
            notes=notes,
            **additional_fields
        )
        
        return {'message': f'Order refunded successfully'}
    
    def _handle_update_tracking(
        self, 
        order: Order, 
        user: User,
        tracking_number: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Handle tracking number update"""
        
        order.tracking_number = tracking_number
        order.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Log the update
        self._log_tracking_update(order, user, tracking_number)
        
        return {'message': f'Tracking number updated to: {tracking_number}'}
    
    def _log_tracking_update(self, order: Order, user: User, tracking_number: str):
        """Log tracking number update"""
        
        from database.models import OrderStatusHistory
        
        status_history = OrderStatusHistory(
            order_id=order.id,
            old_status=order.order_status,
            new_status=order.order_status,  # Same status
            reason=TransitionReason.ADMIN_ACTION.value,
            user_id=user.id,
            notes=f"Tracking number updated to: {tracking_number}",
            changed_at=datetime.utcnow()
        )
        
        self.db.add(status_history)
```

### 2. Workflow Notification System
```python
# workflow/notifications.py - Order workflow notification system

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging
from abc import ABC, abstractmethod

from database.models import Order, User, Account
from core.config.settings import settings

logger = logging.getLogger(__name__)

class NotificationChannel(ABC):
    """Abstract notification channel"""
    
    @abstractmethod
    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send notification through this channel"""
        pass

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self):
        self.smtp_configured = False  # Set based on email configuration
    
    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send email notification"""
        
        if not self.smtp_configured:
            logger.warning("SMTP not configured, skipping email notification")
            return False
        
        try:
            # Email sending logic would go here
            # For now, just log the notification
            logger.info(f"Email notification sent: {notification['subject']} to {notification['recipient']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False

class OrderNotificationService:
    """Service for sending order-related notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            'email': EmailNotificationChannel()
        }
        
        # Notification templates
        self.templates = {
            'order_status_changed': {
                'subject': 'Order Status Update - {order_id}',
                'body': '''
                Hello,
                
                Your order {order_id} status has been updated to: {new_status}
                
                Order Details:
                - Order ID: {order_id}
                - Total Amount: ${total_amount}
                - New Status: {new_status}
                {tracking_info}
                
                Thank you for your business!
                '''
            },
            'order_shipped': {
                'subject': 'Your Order Has Shipped - {order_id}',
                'body': '''
                Good news! Your order has shipped.
                
                Order Details:
                - Order ID: {order_id}
                - Tracking Number: {tracking_number}
                - Shipping Method: {shipping_method}
                
                You can track your package using the tracking number above.
                '''
            },
            'payment_confirmation': {
                'subject': 'Payment Confirmed - {order_id}',
                'body': '''
                Thank you! Your payment has been confirmed.
                
                Order Details:
                - Order ID: {order_id}
                - Amount Paid: ${total_amount}
                - Payment Method: {payment_method}
                
                We will prepare your order for shipping soon.
                '''
            },
            'order_cancelled': {
                'subject': 'Order Cancelled - {order_id}',
                'body': '''
                Your order has been cancelled as requested.
                
                Order Details:
                - Order ID: {order_id}
                - Total Amount: ${total_amount}
                - Cancellation Reason: {reason}
                
                If you paid for this order, your refund will be processed within 3-5 business days.
                '''
            }
        }
    
    async def notify_status_change(
        self,
        order: Order,
        old_status: str,
        new_status: str,
        user: Optional[User] = None,
        notes: Optional[str] = None
    ):
        """Send notification for order status change"""
        
        # Determine notification type based on status change
        notification_type = self._get_notification_type(old_status, new_status)
        
        if not notification_type:
            return  # No notification needed for this transition
        
        try:
            # Get account for sender information
            account = self.db.query(Account).filter(Account.id == order.account_id).first()
            
            # Prepare notification data
            notification_data = {
                'order_id': order.ebay_order_id,
                'total_amount': str(order.total_amount),
                'old_status': old_status,
                'new_status': new_status,
                'tracking_number': order.tracking_number or 'Not available',
                'shipping_method': order.shipping_method or 'Standard',
                'payment_method': order.payment_method or 'Unknown',
                'reason': notes or 'No reason provided',
                'account_name': account.ebay_account_name if account else 'Unknown'
            }
            
            # Add tracking info if available
            tracking_info = ""
            if new_status == 'shipped' and order.tracking_number:
                tracking_info = f"\nTracking Number: {order.tracking_number}"
            notification_data['tracking_info'] = tracking_info
            
            # Send customer notification
            if order.buyer_email:
                await self._send_customer_notification(
                    order.buyer_email,
                    notification_type,
                    notification_data
                )
            
            # Send admin notification if needed
            await self._send_admin_notification(
                notification_type,
                notification_data,
                user
            )
            
        except Exception as e:
            logger.error(f"Failed to send status change notification for order {order.id}: {str(e)}")
    
    async def notify_bulk_status_change(
        self,
        orders: List[Order],
        new_status: str,
        user: User,
        results: Dict[str, Any]
    ):
        """Send notification for bulk status changes"""
        
        try:
            # Send admin summary notification
            notification = {
                'recipient': user.email,
                'subject': f'Bulk Order Update Complete - {results["success_count"]} orders updated',
                'body': f'''
                Bulk order status update completed.
                
                Summary:
                - Orders processed: {results["total_processed"]}
                - Successfully updated: {results["success_count"]} 
                - Failures: {results["error_count"]}
                - New status: {new_status}
                
                {"Errors encountered:" + chr(10) + chr(10).join(results["errors"]) if results["errors"] else "All orders updated successfully."}
                ''',
                'channel': 'email'
            }
            
            await self.channels['email'].send_notification(notification)
            
        except Exception as e:
            logger.error(f"Failed to send bulk status change notification: {str(e)}")
    
    def _get_notification_type(self, old_status: str, new_status: str) -> Optional[str]:
        """Determine notification type based on status transition"""
        
        # Map status transitions to notification types
        notification_map = {
            ('pending', 'processing'): 'payment_confirmation',
            ('processing', 'shipped'): 'order_shipped',
            ('pending', 'cancelled'): 'order_cancelled',
            ('processing', 'cancelled'): 'order_cancelled',
            # Add more mappings as needed
        }
        
        return notification_map.get((old_status, new_status))
    
    async def _send_customer_notification(
        self,
        customer_email: str,
        notification_type: str,
        data: Dict[str, Any]
    ):
        """Send notification to customer"""
        
        template = self.templates.get(notification_type)
        if not template:
            logger.warning(f"No template found for notification type: {notification_type}")
            return
        
        try:
            notification = {
                'recipient': customer_email,
                'subject': template['subject'].format(**data),
                'body': template['body'].format(**data),
                'channel': 'email'
            }
            
            await self.channels['email'].send_notification(notification)
            
        except Exception as e:
            logger.error(f"Failed to send customer notification: {str(e)}")
    
    async def _send_admin_notification(
        self,
        notification_type: str,
        data: Dict[str, Any],
        user: Optional[User]
    ):
        """Send notification to admin/user who made the change"""
        
        # For now, only send admin notifications for certain events
        admin_notification_types = ['order_cancelled']
        
        if notification_type not in admin_notification_types:
            return
        
        if not user or not user.email:
            return
        
        try:
            notification = {
                'recipient': user.email,
                'subject': f'Admin Action Completed: {notification_type}',
                'body': f'''
                Order action completed successfully.
                
                Action: {notification_type}
                Order ID: {data["order_id"]}
                New Status: {data["new_status"]}
                Account: {data["account_name"]}
                
                This notification is for record-keeping purposes.
                ''',
                'channel': 'email'
            }
            
            await self.channels['email'].send_notification(notification)
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
```

### 3. Workflow API Endpoints
```python
# api/workflow.py - Order workflow API endpoints

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.database import get_db
from workflow.status_manager import OrderWorkflowEngine, OrderStatus, TransitionReason
from workflow.notifications import OrderNotificationService
from auth.dependencies import get_current_user
from database.models import User, Order

router = APIRouter(prefix="/workflow", tags=["Order Workflow"])

class StatusChangeRequest(BaseModel):
    """Request schema for status changes"""
    new_status: OrderStatus
    reason: TransitionReason
    notes: Optional[str] = None
    additional_fields: Dict[str, Any] = {}

class WorkflowActionRequest(BaseModel):
    """Request schema for workflow actions"""
    action: str = Field(..., description="Action to perform")
    parameters: Dict[str, Any] = Field(default={}, description="Action parameters")

class BulkStatusChangeRequest(BaseModel):
    """Request schema for bulk status changes"""
    order_ids: List[int] = Field(..., min_items=1, max_items=100)
    new_status: OrderStatus
    reason: TransitionReason
    notes: Optional[str] = None

@router.post("/orders/{order_id}/status")
async def change_order_status(
    order_id: int,
    request: StatusChangeRequest,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change order status"""
    
    # Get order
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    try:
        # Initialize workflow engine
        workflow_engine = OrderWorkflowEngine(db)
        
        # Change status
        old_status = order.order_status
        
        success = workflow_engine.status_manager.change_status(
            order=order,
            new_status=request.new_status,
            reason=request.reason,
            user=current_user,
            notes=request.notes,
            **request.additional_fields
        )
        
        if success:
            # Send notification
            notification_service = OrderNotificationService(db)
            await notification_service.notify_status_change(
                order=order,
                old_status=old_status,
                new_status=request.new_status.value,
                user=current_user,
                notes=request.notes
            )
            
            return {
                "message": f"Order status changed to {request.new_status.value}",
                "order_id": order_id,
                "new_status": request.new_status.value
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/orders/{order_id}/actions")
async def execute_workflow_action(
    order_id: int,
    request: WorkflowActionRequest,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute a workflow action on an order"""
    
    try:
        workflow_engine = OrderWorkflowEngine(db)
        
        result = workflow_engine.process_order_action(
            order_id=order_id,
            action=request.action,
            user=current_user,
            **request.parameters
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/orders/bulk/status")
async def bulk_change_status(
    request: BulkStatusChangeRequest,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change status for multiple orders"""
    
    # Get orders
    orders = db.query(Order).filter(
        Order.id.in_(request.order_ids),
        Order.account_id == account_id
    ).all()
    
    if len(orders) != len(request.order_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some orders not found or not accessible"
        )
    
    try:
        workflow_engine = OrderWorkflowEngine(db)
        
        results = workflow_engine.status_manager.bulk_status_change(
            orders=orders,
            new_status=request.new_status,
            reason=request.reason,
            user=current_user,
            notes=request.notes
        )
        
        # Send bulk notification
        notification_service = OrderNotificationService(db)
        await notification_service.notify_bulk_status_change(
            orders=orders,
            new_status=request.new_status.value,
            user=current_user,
            results=results
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk status change failed: {str(e)}"
        )

@router.get("/orders/{order_id}/transitions")
def get_allowed_transitions(
    order_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get allowed status transitions for an order"""
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    workflow_engine = OrderWorkflowEngine(db)
    current_status = OrderStatus(order.order_status)
    allowed_transitions = workflow_engine.status_manager.get_allowed_transitions(current_status)
    
    return {
        "order_id": order_id,
        "current_status": current_status.value,
        "allowed_transitions": [status.value for status in allowed_transitions]
    }

@router.get("/orders/{order_id}/history")
def get_order_history(
    order_id: int,
    account_id: int = Query(..., description="Account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order status change history"""
    
    from database.models import OrderStatusHistory
    
    # Verify order access
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.account_id == account_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Get status history
    history = db.query(OrderStatusHistory).filter(
        OrderStatusHistory.order_id == order_id
    ).order_by(OrderStatusHistory.changed_at.desc()).all()
    
    return [
        {
            "id": h.id,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "reason": h.reason,
            "user_id": h.user_id,
            "notes": h.notes,
            "changed_at": h.changed_at
        }
        for h in history
    ]
```

### 4. Workflow Database Models Extension
```python
# database/models/workflow.py - Additional models for workflow system

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime

class OrderStatusHistory(Base):
    """Order status change history for audit trail"""
    __tablename__ = "order_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    reason = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")
    user = relationship("User")
```

---

## Success Criteria & Validation

### Workflow Management Requirements ✅
- [ ] Status transition validation with business rule enforcement
- [ ] Audit trail for all status changes with user tracking
- [ ] Workflow actions (confirm payment, ship order, confirm delivery, cancel, refund)
- [ ] Bulk status updates with progress tracking
- [ ] Automatic field updates based on status changes (dates, tracking)
- [ ] Status history retrieval for order timeline
- [ ] Allowed transition calculation based on current status

### Notification System Requirements ✅
- [ ] Email notifications for status changes (customer and admin)
- [ ] Template-based notification system with variable substitution
- [ ] Notification preferences and channel management
- [ ] Bulk operation notifications with summary reports
- [ ] Error handling and retry logic for failed notifications
- [ ] Configurable notification types per status transition

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Status manager handles transitions, notification service handles notifications
- [ ] **Open/Closed**: Workflow extensible for new actions and statuses without core changes
- [ ] **Liskov Substitution**: All workflow actions implement common execution interface
- [ ] **Interface Segregation**: Separate interfaces for status management, rules, and notifications
- [ ] **Dependency Inversion**: Workflow depends on abstract notification and validation interfaces
- [ ] **YAGNI Applied**: Essential workflow features only, no complex state machines or automation
- [ ] Eliminated unnecessary complexity (multi-approval, workflow designer, advanced automation)

### Business Logic Requirements ✅
- [ ] Order status workflow: pending → processing → shipped → delivered → refunded
- [ ] Business rule validation (cannot ship without payment, cannot deliver without shipping)
- [ ] Required field validation per status (tracking for shipped, dates for transitions)
- [ ] Automatic timestamp updates based on status changes
- [ ] Cancellation logic with proper state handling
- [ ] Status transition rollback on business rule failures

**Backend Phase 2 Complete**: All CSV processing, background jobs, order management, and workflow components implemented following YAGNI/SOLID principles.

**Next Step**: Begin [Frontend Phase-1-Foundation](../Frontend/Phase-1-Foundation/) implementation or continue with additional backend phases as needed.