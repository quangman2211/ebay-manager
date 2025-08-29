"""
Order Management Service
Following SOLID principles - Single Responsibility for order business logic
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus, ShippingStatus
from app.models.user import User
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderStatusUpdateRequest, OrderShippingUpdate,
    OrderFilter, OrderStats, OrderItemCreate, OrderItemUpdate
)
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("order_service")

class OrderService:
    """
    Order management service
    Following SOLID: Single Responsibility for order business logic
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(self, order_data: OrderCreate, user_id: int) -> Order:
        """
        Create a new order
        Following SOLID: Single method responsibility
        """
        try:
            # Validate account access
            self._validate_account_access(order_data.account_id, user_id)
            
            # Check for duplicate eBay order ID
            existing_order = self.db.query(Order).filter(
                Order.ebay_order_id == order_data.ebay_order_id
            ).first()
            
            if existing_order:
                raise EbayManagerException(
                    f"Order with eBay ID {order_data.ebay_order_id} already exists",
                    error_code="DUPLICATE_ORDER"
                )
            
            # Create order
            order = Order(
                user_id=user_id,
                **order_data.dict(exclude={'order_items'})
            )
            
            # Set initial status
            order.status = OrderStatus.PENDING
            order.payment_status = PaymentStatus.PENDING
            order.shipping_status = ShippingStatus.NOT_SHIPPED
            
            self.db.add(order)
            self.db.flush()  # Get order ID
            
            # Create order items
            for item_data in order_data.order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data.dict()
                )
                self.db.add(order_item)
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order created: {order.id} (eBay ID: {order.ebay_order_id}) by user {user_id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating order: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to create order: {str(e)}")
    
    def get_order_by_id(self, order_id: int, user_id: int) -> Optional[Order]:
        """
        Get order by ID with access control
        Following SOLID: Single method responsibility
        """
        query = self.db.query(Order).filter(Order.id == order_id)
        
        # Apply user-based filtering (admin sees all, user sees only their orders)
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role != 'admin':
            query = query.filter(Order.user_id == user_id)
        
        return query.first()
    
    def get_order_by_ebay_id(self, ebay_order_id: str, user_id: int) -> Optional[Order]:
        """
        Get order by eBay order ID
        Following SOLID: Single method responsibility
        """
        query = self.db.query(Order).filter(Order.ebay_order_id == ebay_order_id)
        
        # Apply user-based filtering
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.role != 'admin':
            query = query.filter(Order.user_id == user_id)
        
        return query.first()
    
    def update_order(self, order_id: int, order_data: OrderUpdate, user_id: int) -> Order:
        """
        Update order
        Following SOLID: Single method responsibility
        """
        try:
            order = self.get_order_by_id(order_id, user_id)
            if not order:
                raise EbayManagerException("Order not found", error_code="ORDER_NOT_FOUND")
            
            # Update fields
            update_data = order_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            # Validate status transitions if status is being updated
            if 'status' in update_data:
                new_status = OrderStatus(update_data['status'])
                if not order.can_transition_to(new_status):
                    raise EbayManagerException(
                        f"Cannot transition from {order.status} to {new_status}",
                        error_code="INVALID_STATUS_TRANSITION"
                    )
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order updated: {order.id} by user {user_id}")
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating order {order_id}: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to update order: {str(e)}")
    
    def update_order_status(self, order_id: int, status_data: OrderStatusUpdateRequest, user_id: int) -> Order:
        """
        Update order status with validation
        Following SOLID: Single method responsibility
        """
        try:
            order = self.get_order_by_id(order_id, user_id)
            if not order:
                raise EbayManagerException("Order not found", error_code="ORDER_NOT_FOUND")
            
            new_status = OrderStatus(status_data.status)
            
            # Validate status transition
            if not order.can_transition_to(new_status):
                raise EbayManagerException(
                    f"Cannot transition from {order.status} to {new_status}",
                    error_code="INVALID_STATUS_TRANSITION"
                )
            
            # Update status
            order.status = new_status
            
            # Add status change note
            if status_data.notes:
                current_notes = order.internal_notes or ""
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                status_note = f"\n[{timestamp}] Status changed to {new_status}: {status_data.notes}"
                order.internal_notes = current_notes + status_note
            
            # Update related timestamps
            if new_status == OrderStatus.SHIPPED and order.shipping_date is None:
                order.shipping_date = datetime.utcnow()
                order.shipping_status = ShippingStatus.SHIPPED
            elif new_status == OrderStatus.DELIVERED:
                if order.actual_delivery_date is None:
                    order.actual_delivery_date = datetime.utcnow()
                order.shipping_status = ShippingStatus.DELIVERED
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order status updated: {order.id} -> {new_status} by user {user_id}")
            
            # TODO: Send customer notification if requested (YAGNI for now)
            # if status_data.notify_customer:
            #     self._send_status_notification(order)
            
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating order status {order_id}: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to update order status: {str(e)}")
    
    def update_shipping_info(self, order_id: int, shipping_data: OrderShippingUpdate, user_id: int) -> Order:
        """
        Update order shipping information
        Following SOLID: Single method responsibility
        """
        try:
            order = self.get_order_by_id(order_id, user_id)
            if not order:
                raise EbayManagerException("Order not found", error_code="ORDER_NOT_FOUND")
            
            # Update shipping information
            order.shipping_status = ShippingStatus(shipping_data.shipping_status)
            
            if shipping_data.tracking_number:
                order.tracking_number = shipping_data.tracking_number
            if shipping_data.carrier:
                order.carrier = shipping_data.carrier
            if shipping_data.shipping_method:
                order.shipping_method = shipping_data.shipping_method
            if shipping_data.estimated_delivery_date:
                order.estimated_delivery_date = shipping_data.estimated_delivery_date
            if shipping_data.shipping_date:
                order.shipping_date = shipping_data.shipping_date
            
            # Auto-update order status if shipped
            if shipping_data.shipping_status in [ShippingStatus.SHIPPED, ShippingStatus.IN_TRANSIT]:
                if order.status == OrderStatus.PROCESSING:
                    order.status = OrderStatus.SHIPPED
                if order.shipping_date is None:
                    order.shipping_date = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Order shipping updated: {order.id} by user {user_id}")
            
            # TODO: Send customer notification if requested (YAGNI for now)
            # if shipping_data.notify_customer:
            #     self._send_shipping_notification(order)
            
            return order
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating shipping info {order_id}: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to update shipping info: {str(e)}")
    
    def list_orders(
        self, 
        user_id: int, 
        filters: Optional[OrderFilter] = None,
        page: int = 1, 
        page_size: int = 50,
        sort_by: str = "order_date",
        sort_desc: bool = True
    ) -> Tuple[List[Order], int]:
        """
        List orders with filtering and pagination
        Following SOLID: Single method responsibility
        """
        try:
            query = self.db.query(Order)
            
            # Apply user-based filtering
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.role != 'admin':
                query = query.filter(Order.user_id == user_id)
            
            # Apply filters
            if filters:
                if filters.account_id:
                    query = query.filter(Order.account_id == filters.account_id)
                
                if filters.status:
                    query = query.filter(Order.status.in_(filters.status))
                
                if filters.payment_status:
                    query = query.filter(Order.payment_status.in_(filters.payment_status))
                
                if filters.shipping_status:
                    query = query.filter(Order.shipping_status.in_(filters.shipping_status))
                
                if filters.buyer_username:
                    query = query.filter(Order.buyer_username.ilike(f"%{filters.buyer_username}%"))
                
                if filters.ebay_order_id:
                    query = query.filter(Order.ebay_order_id.ilike(f"%{filters.ebay_order_id}%"))
                
                if filters.date_from:
                    query = query.filter(Order.order_date >= filters.date_from)
                
                if filters.date_to:
                    query = query.filter(Order.order_date <= filters.date_to)
                
                if filters.is_priority is not None:
                    query = query.filter(Order.is_priority == filters.is_priority)
                
                if filters.currency:
                    query = query.filter(Order.currency == filters.currency)
                
                if filters.has_tracking is not None:
                    if filters.has_tracking:
                        query = query.filter(Order.tracking_number.isnot(None))
                    else:
                        query = query.filter(Order.tracking_number.is_(None))
                
                # Apply overdue filter (business logic)
                if filters.is_overdue is not None:
                    cutoff_date = datetime.utcnow() - timedelta(days=3)
                    if filters.is_overdue:
                        query = query.filter(
                            and_(
                                Order.order_date <= cutoff_date,
                                Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                                Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                            )
                        )
                    else:
                        query = query.filter(
                            or_(
                                Order.order_date > cutoff_date,
                                Order.shipping_status != ShippingStatus.NOT_SHIPPED,
                                Order.status.in_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                            )
                        )
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            if hasattr(Order, sort_by):
                order_column = getattr(Order, sort_by)
                if sort_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            
            # Apply pagination
            offset = (page - 1) * page_size
            orders = query.offset(offset).limit(page_size).all()
            
            logger.info(f"Orders listed: {len(orders)}/{total_count} for user {user_id}")
            return orders, total_count
            
        except Exception as e:
            logger.error(f"Error listing orders for user {user_id}: {str(e)}")
            raise EbayManagerException(f"Failed to list orders: {str(e)}")
    
    def get_order_stats(self, user_id: int, account_id: Optional[int] = None) -> OrderStats:
        """
        Get order statistics
        Following SOLID: Single method responsibility
        """
        try:
            query = self.db.query(Order)
            
            # Apply user-based filtering
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.role != 'admin':
                query = query.filter(Order.user_id == user_id)
            
            if account_id:
                query = query.filter(Order.account_id == account_id)
            
            # Calculate basic stats
            total_orders = query.count()
            pending_orders = query.filter(Order.status == OrderStatus.PENDING).count()
            shipped_orders = query.filter(Order.status == OrderStatus.SHIPPED).count()
            delivered_orders = query.filter(Order.status == OrderStatus.DELIVERED).count()
            cancelled_orders = query.filter(Order.status == OrderStatus.CANCELLED).count()
            
            # Calculate overdue orders
            cutoff_date = datetime.utcnow() - timedelta(days=3)
            overdue_orders = query.filter(
                and_(
                    Order.order_date <= cutoff_date,
                    Order.shipping_status == ShippingStatus.NOT_SHIPPED,
                    Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.DELIVERED])
                )
            ).count()
            
            # Calculate revenue stats
            revenue_query = query.with_entities(func.sum(Order.total_amount).label('total'))
            total_revenue = revenue_query.scalar() or Decimal('0.00')
            
            pending_revenue = query.filter(
                Order.payment_status == PaymentStatus.PENDING
            ).with_entities(func.sum(Order.total_amount)).scalar() or Decimal('0.00')
            
            # This month revenue
            first_day_this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month_revenue = query.filter(
                Order.order_date >= first_day_this_month
            ).with_entities(func.sum(Order.total_amount)).scalar() or Decimal('0.00')
            
            # This year revenue
            first_day_this_year = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            this_year_revenue = query.filter(
                Order.order_date >= first_day_this_year
            ).with_entities(func.sum(Order.total_amount)).scalar() or Decimal('0.00')
            
            # Calculate average order value
            average_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0.00')
            
            # Calculate total items sold
            total_items_sold = self.db.query(func.sum(OrderItem.quantity)).join(Order).filter(
                Order.status != OrderStatus.CANCELLED
            ).scalar() or 0
            
            # Apply user filtering to items query if needed
            if user and user.role != 'admin':
                total_items_sold = self.db.query(func.sum(OrderItem.quantity)).join(Order).filter(
                    and_(
                        Order.status != OrderStatus.CANCELLED,
                        Order.user_id == user_id
                    )
                ).scalar() or 0
            
            # TODO: Implement top buyers and revenue by month (YAGNI for basic version)
            top_buyers = []
            revenue_by_month = []
            
            return OrderStats(
                total_orders=total_orders,
                pending_orders=pending_orders,
                shipped_orders=shipped_orders,
                delivered_orders=delivered_orders,
                cancelled_orders=cancelled_orders,
                overdue_orders=overdue_orders,
                total_revenue=total_revenue,
                pending_revenue=pending_revenue,
                this_month_revenue=this_month_revenue,
                this_year_revenue=this_year_revenue,
                average_order_value=average_order_value,
                total_items_sold=total_items_sold,
                top_buyers=top_buyers,
                revenue_by_month=revenue_by_month
            )
            
        except Exception as e:
            logger.error(f"Error getting order stats for user {user_id}: {str(e)}")
            raise EbayManagerException(f"Failed to get order stats: {str(e)}")
    
    def delete_order(self, order_id: int, user_id: int) -> bool:
        """
        Delete order (admin only, soft delete by setting status to cancelled)
        Following SOLID: Single method responsibility
        """
        try:
            order = self.get_order_by_id(order_id, user_id)
            if not order:
                raise EbayManagerException("Order not found", error_code="ORDER_NOT_FOUND")
            
            # Check if user is admin
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user.role != 'admin':
                raise EbayManagerException("Admin privileges required", error_code="INSUFFICIENT_PRIVILEGES")
            
            # Soft delete by setting status to cancelled
            order.status = OrderStatus.CANCELLED
            
            # Add deletion note
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            deletion_note = f"\n[{timestamp}] Order cancelled/deleted by admin user {user_id}"
            order.internal_notes = (order.internal_notes or "") + deletion_note
            
            self.db.commit()
            
            logger.info(f"Order soft deleted: {order.id} by admin user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting order {order_id}: {str(e)}")
            if isinstance(e, EbayManagerException):
                raise
            raise EbayManagerException(f"Failed to delete order: {str(e)}")
    
    def _validate_account_access(self, account_id: int, user_id: int) -> None:
        """
        Validate user access to account
        Following SOLID: Single method responsibility
        """
        from app.models.account import Account
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EbayManagerException("User not found", error_code="USER_NOT_FOUND")
        
        # Admin can access any account
        if user.role == 'admin':
            return
        
        # Regular users can only access their own accounts
        account = self.db.query(Account).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()
        
        if not account:
            raise EbayManagerException("Account not found or access denied", error_code="ACCOUNT_ACCESS_DENIED")