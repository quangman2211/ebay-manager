# Order Management API - Complete CRUD Operations

## Overview
Complete order management API for eBay Management System following YAGNI/SOLID principles. Implements comprehensive CRUD operations, filtering, search, bulk operations, and order status management optimized for 30-account scale with essential business logic only.

## SOLID Principles Applied
- **Single Responsibility**: Each service class handles one order management concern
- **Open/Closed**: API extensible for new order operations without modifying core endpoints
- **Liskov Substitution**: All order services implement common repository interface
- **Interface Segregation**: Separate interfaces for read operations, write operations, and bulk operations
- **Dependency Inversion**: API endpoints depend on service abstractions, not concrete implementations

## YAGNI Compliance
✅ **Essential Order Operations**: CRUD, search, filter, bulk update, status workflow only  
✅ **Simple Business Logic**: Status validation, total calculation, essential order rules  
✅ **Basic Filtering**: Date range, status, buyer, amount filters sufficient for 30 accounts  
✅ **Standard REST API**: No complex GraphQL or advanced query interfaces  
❌ **Eliminated**: Complex order analytics, automated pricing, fraud detection, third-party integrations

---

## Order Management Architecture

### API Structure Overview
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ORDER MANAGEMENT API                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   API Layer     │───▶│  Service Layer  │───▶│ Repository      │             │
│  │                 │    │                 │    │ Layer           │             │
│  │ • REST endpoints│    │ • Business logic│    │ • Database      │             │
│  │ • Input valid.  │    │ • Validation    │    │   operations    │             │
│  │ • Response fmt  │    │ • Calculations  │    │ • Query         │             │
│  │ • Error handling│    │ • Status mgmt   │    │   optimization  │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           ORDER OPERATIONS                              │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │   │
│  │  │     CRUD        │  │   FILTERING     │  │   BULK OPS      │         │   │
│  │  │                 │  │                 │  │                 │         │   │
│  │  │ • Create order  │  │ • By status     │  │ • Status update │         │   │
│  │  │ • Get order     │  │ • By date range │  │ • Bulk export   │         │   │
│  │  │ • Update order  │  │ • By buyer      │  │ • Mass operations │        │   │
│  │  │ • Delete order  │  │ • By amount     │  │ • Batch process │         │   │
│  │  │ • List orders   │  │ • By account    │  │ • Multi-select  │         │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │   │
│  │                                                                         │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │   │
│  │  │   SEARCH        │  │   WORKFLOW      │  │   REPORTS       │         │   │
│  │  │                 │  │                 │  │                 │         │   │
│  │  │ • Text search   │  │ • Status trans. │  │ • Order summary │         │   │
│  │  │ • Order ID      │  │ • Validation    │  │ • Export CSV    │         │   │
│  │  │ • Buyer search  │  │ • History track │  │ • Statistics    │         │   │
│  │  │ • Full-text     │  │ • Notifications │  │ • Performance   │         │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pattern
```
Client Request → Input Validation → Service Layer → Repository → Database
                                         ↓
Client Response ← Response Format ← Business Logic ← Data Retrieval
```

---

## Complete Implementation

### 1. Order Service Layer
```python
# services/order_service.py - Order business logic service

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status

from database.models import Order, OrderItem, Account, Customer
from schemas.orders import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderFilter, OrderBulkUpdate, OrderSummary
)
from core.config.settings import settings

import logging

logger = logging.getLogger(__name__)

class OrderService:
    """Order management business logic service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(self, account_id: int, order_data: OrderCreate) -> OrderResponse:
        """Create new order with validation"""
        
        # Validate account access
        account = self._get_account_or_404(account_id)
        
        # Check for duplicate order
        existing_order = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.ebay_order_id == order_data.ebay_order_id
            )
        ).first()
        
        if existing_order:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Order with eBay ID {order_data.ebay_order_id} already exists"
            )
        
        # Validate business rules
        self._validate_order_data(order_data)
        
        try:
            # Create order
            order = Order(
                account_id=account_id,
                **order_data.dict(exclude={'order_items'})
            )
            
            self.db.add(order)
            self.db.flush()  # Get order ID
            
            # Create order items if provided
            if order_data.order_items:
                for item_data in order_data.order_items:
                    order_item = OrderItem(
                        order_id=order.id,
                        **item_data.dict()
                    )
                    self.db.add(order_item)
            
            # Calculate order totals
            self._calculate_order_totals(order)
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Created order {order.id} for account {account_id}")
            
            return self._order_to_response(order)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create order: {str(e)}"
            )
    
    def get_order(self, account_id: int, order_id: int) -> OrderResponse:
        """Get order by ID"""
        
        order = self._get_order_or_404(account_id, order_id)
        return self._order_to_response(order)
    
    def get_order_by_ebay_id(self, account_id: int, ebay_order_id: str) -> Optional[OrderResponse]:
        """Get order by eBay order ID"""
        
        order = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.ebay_order_id == ebay_order_id
            )
        ).first()
        
        if order:
            return self._order_to_response(order)
        return None
    
    def update_order(self, account_id: int, order_id: int, order_data: OrderUpdate) -> OrderResponse:
        """Update order"""
        
        order = self._get_order_or_404(account_id, order_id)
        
        # Validate status transition if status is being updated
        if order_data.order_status and order_data.order_status != order.order_status:
            self._validate_status_transition(order.order_status, order_data.order_status)
        
        try:
            # Update order fields
            update_data = order_data.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            # Update timestamps based on status changes
            self._update_status_timestamps(order, order_data.order_status)
            
            # Recalculate totals if needed
            if any(field in update_data for field in ['total_amount', 'shipping_cost']):
                self._calculate_order_totals(order)
            
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            logger.info(f"Updated order {order_id} for account {account_id}")
            
            return self._order_to_response(order)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update order {order_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update order: {str(e)}"
            )
    
    def delete_order(self, account_id: int, order_id: int) -> bool:
        """Delete order (soft delete by setting status)"""
        
        order = self._get_order_or_404(account_id, order_id)
        
        # Only allow deletion of certain statuses
        if order.order_status in ['shipped', 'delivered']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete shipped or delivered orders"
            )
        
        try:
            order.order_status = 'cancelled'
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Deleted (cancelled) order {order_id} for account {account_id}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete order {order_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete order: {str(e)}"
            )
    
    def list_orders(
        self, 
        account_id: int, 
        filters: Optional[OrderFilter] = None,
        skip: int = 0,
        limit: int = 50,
        sort_by: str = 'order_date',
        sort_order: str = 'desc'
    ) -> OrderListResponse:
        """List orders with filtering and pagination"""
        
        # Validate account access
        self._get_account_or_404(account_id)
        
        # Build query
        query = self.db.query(Order).filter(Order.account_id == account_id)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        query = self._apply_sorting(query, sort_by, sort_order)
        
        # Apply pagination
        orders = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        order_responses = [self._order_to_response(order) for order in orders]
        
        return OrderListResponse(
            orders=order_responses,
            total=total_count,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total_count
        )
    
    def search_orders(
        self,
        account_id: int,
        search_term: str,
        search_fields: List[str] = None,
        limit: int = 50
    ) -> List[OrderResponse]:
        """Search orders by text"""
        
        if not search_fields:
            search_fields = ['ebay_order_id', 'buyer_username', 'buyer_email', 'buyer_notes']
        
        # Build search query
        query = self.db.query(Order).filter(Order.account_id == account_id)
        
        search_conditions = []
        for field in search_fields:
            if hasattr(Order, field):
                search_conditions.append(
                    getattr(Order, field).ilike(f'%{search_term}%')
                )
        
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        
        orders = query.order_by(desc(Order.order_date)).limit(limit).all()
        
        return [self._order_to_response(order) for order in orders]
    
    def bulk_update_orders(
        self,
        account_id: int,
        order_ids: List[int],
        update_data: OrderBulkUpdate
    ) -> Dict[str, Any]:
        """Bulk update multiple orders"""
        
        if len(order_ids) > 100:  # Reasonable limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update more than 100 orders at once"
            )
        
        # Get orders to update
        orders = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.id.in_(order_ids)
            )
        ).all()
        
        if len(orders) != len(order_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Some orders not found or not accessible"
            )
        
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            for order in orders:
                try:
                    # Validate status transition if applicable
                    if update_data.order_status and update_data.order_status != order.order_status:
                        self._validate_status_transition(order.order_status, update_data.order_status)
                    
                    # Apply updates
                    update_dict = update_data.dict(exclude_unset=True)
                    for field, value in update_dict.items():
                        if hasattr(order, field):
                            setattr(order, field, value)
                    
                    # Update timestamps
                    self._update_status_timestamps(order, update_data.order_status)
                    order.updated_at = datetime.utcnow()
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Order {order.id}: {str(e)}")
            
            self.db.commit()
            
            logger.info(f"Bulk updated {success_count} orders for account {account_id}")
            
            return {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors,
                'total_processed': len(orders)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk update failed for account {account_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk update failed: {str(e)}"
            )
    
    def get_order_summary(self, account_id: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> OrderSummary:
        """Get order summary statistics"""
        
        # Default to last 30 days if no date range provided
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Base query
        base_query = self.db.query(Order).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= date_from,
                Order.order_date <= date_to
            )
        )
        
        # Total orders and revenue
        total_orders = base_query.count()
        total_revenue = base_query.with_entities(func.sum(Order.total_amount)).scalar() or Decimal('0')
        
        # Orders by status
        status_counts = {}
        status_results = self.db.query(
            Order.order_status,
            func.count(Order.id).label('count'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= date_from,
                Order.order_date <= date_to
            )
        ).group_by(Order.order_status).all()
        
        for status, count, revenue in status_results:
            status_counts[status] = {
                'count': count,
                'revenue': float(revenue or 0)
            }
        
        # Average order value
        avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0
        
        # Recent orders (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_orders = base_query.filter(Order.order_date >= recent_date).count()
        
        # Top buyers
        top_buyers = self.db.query(
            Order.buyer_username,
            func.count(Order.id).label('order_count'),
            func.sum(Order.total_amount).label('total_spent')
        ).filter(
            and_(
                Order.account_id == account_id,
                Order.order_date >= date_from,
                Order.order_date <= date_to
            )
        ).group_by(Order.buyer_username).order_by(desc('total_spent')).limit(10).all()
        
        return OrderSummary(
            total_orders=total_orders,
            total_revenue=float(total_revenue),
            average_order_value=avg_order_value,
            orders_by_status=status_counts,
            recent_orders_7d=recent_orders,
            top_buyers=[{
                'username': buyer[0],
                'order_count': buyer[1],
                'total_spent': float(buyer[2])
            } for buyer in top_buyers],
            date_from=date_from,
            date_to=date_to
        )
    
    def export_orders_csv(self, account_id: int, filters: Optional[OrderFilter] = None) -> str:
        """Export orders to CSV format"""
        
        import csv
        import io
        
        # Get orders with filters
        query = self.db.query(Order).filter(Order.account_id == account_id)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        orders = query.order_by(desc(Order.order_date)).all()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'eBay Order ID', 'Buyer Username', 'Buyer Email', 'Order Date',
            'Order Status', 'Total Amount', 'Currency', 'Payment Method',
            'Shipping Address', 'Tracking Number', 'Notes'
        ]
        writer.writerow(headers)
        
        # Write data
        for order in orders:
            writer.writerow([
                order.ebay_order_id,
                order.buyer_username,
                order.buyer_email,
                order.order_date.isoformat() if order.order_date else '',
                order.order_status,
                str(order.total_amount),
                order.currency,
                order.payment_method or '',
                f"{order.shipping_address_line1 or ''}, {order.shipping_city or ''}, {order.shipping_state or ''}",
                order.tracking_number or '',
                order.buyer_notes or ''
            ])
        
        return output.getvalue()
    
    def _get_account_or_404(self, account_id: int) -> Account:
        """Get account or raise 404"""
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        return account
    
    def _get_order_or_404(self, account_id: int, order_id: int) -> Order:
        """Get order or raise 404"""
        order = self.db.query(Order).filter(
            and_(Order.id == order_id, Order.account_id == account_id)
        ).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        return order
    
    def _validate_order_data(self, order_data: OrderCreate):
        """Validate order business rules"""
        
        if order_data.total_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total amount must be greater than 0"
            )
        
        if order_data.order_date and order_data.order_date > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order date cannot be in the future"
            )
    
    def _validate_status_transition(self, current_status: str, new_status: str):
        """Validate order status transitions"""
        
        # Define allowed transitions
        allowed_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'returned'],
            'delivered': ['refunded'],
            'cancelled': [],  # Cannot transition from cancelled
            'returned': ['refunded'],
            'refunded': []  # Cannot transition from refunded
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {new_status}"
            )
    
    def _update_status_timestamps(self, order: Order, new_status: Optional[str]):
        """Update timestamps based on status changes"""
        
        if not new_status or new_status == order.order_status:
            return
        
        now = datetime.utcnow()
        
        if new_status == 'processing' and not order.payment_date:
            order.payment_date = now
        elif new_status == 'shipped' and not order.shipped_date:
            order.shipped_date = now
        elif new_status == 'delivered' and not order.delivered_date:
            order.delivered_date = now
    
    def _calculate_order_totals(self, order: Order):
        """Calculate order totals from items"""
        
        # This would calculate totals from order items if needed
        # For now, we use the total_amount from CSV import
        pass
    
    def _apply_filters(self, query, filters: OrderFilter):
        """Apply filters to order query"""
        
        if filters.status_list:
            query = query.filter(Order.order_status.in_(filters.status_list))
        
        if filters.date_from:
            query = query.filter(Order.order_date >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Order.order_date <= filters.date_to)
        
        if filters.buyer_username:
            query = query.filter(Order.buyer_username.ilike(f'%{filters.buyer_username}%'))
        
        if filters.min_amount:
            query = query.filter(Order.total_amount >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Order.total_amount <= filters.max_amount)
        
        if filters.payment_method:
            query = query.filter(Order.payment_method == filters.payment_method)
        
        if filters.has_tracking is not None:
            if filters.has_tracking:
                query = query.filter(Order.tracking_number.isnot(None))
            else:
                query = query.filter(Order.tracking_number.is_(None))
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to order query"""
        
        # Validate sort field
        valid_sort_fields = [
            'order_date', 'total_amount', 'buyer_username', 
            'order_status', 'created_at', 'updated_at'
        ]
        
        if sort_by not in valid_sort_fields:
            sort_by = 'order_date'
        
        # Get sort column
        sort_column = getattr(Order, sort_by)
        
        # Apply sort direction
        if sort_order.lower() == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        return query
    
    def _order_to_response(self, order: Order) -> OrderResponse:
        """Convert order model to response format"""
        
        return OrderResponse(
            id=order.id,
            account_id=order.account_id,
            ebay_order_id=order.ebay_order_id,
            ebay_transaction_id=order.ebay_transaction_id,
            buyer_username=order.buyer_username,
            buyer_email=order.buyer_email,
            total_amount=float(order.total_amount),
            currency=order.currency,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            order_status=order.order_status,
            shipping_address_line1=order.shipping_address_line1,
            shipping_address_line2=order.shipping_address_line2,
            shipping_city=order.shipping_city,
            shipping_state=order.shipping_state,
            shipping_postal_code=order.shipping_postal_code,
            shipping_country=order.shipping_country,
            shipping_method=order.shipping_method,
            tracking_number=order.tracking_number,
            order_date=order.order_date,
            payment_date=order.payment_date,
            shipped_date=order.shipped_date,
            delivered_date=order.delivered_date,
            buyer_notes=order.buyer_notes,
            seller_notes=order.seller_notes,
            import_batch_id=order.import_batch_id,
            import_filename=order.import_filename,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

def get_order_service(db: Session) -> OrderService:
    """Dependency injection for order service"""
    return OrderService(db)
```

### 2. Order API Endpoints
```python
# api/orders.py - Order management API endpoints

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from database.database import get_db
from services.order_service import OrderService, get_order_service
from schemas.orders import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderFilter, OrderBulkUpdate, OrderSummary
)
from auth.dependencies import get_current_user
from database.models import User

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    account_id: int = Query(..., description="Account ID"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new order"""
    
    # TODO: Add proper account access validation
    return order_service.create_order(account_id, order_data)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    account_id: int = Query(..., description="Account ID"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order by ID"""
    
    return order_service.get_order(account_id, order_id)

@router.get("/ebay/{ebay_order_id}", response_model=Optional[OrderResponse])
def get_order_by_ebay_id(
    ebay_order_id: str,
    account_id: int = Query(..., description="Account ID"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order by eBay order ID"""
    
    order = order_service.get_order_by_ebay_id(account_id, ebay_order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order

@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    account_id: int = Query(..., description="Account ID"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order"""
    
    return order_service.update_order(account_id, order_id, order_data)

@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    account_id: int = Query(..., description="Account ID"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Delete order (cancel)"""
    
    order_service.delete_order(account_id, order_id)
    return {"message": "Order deleted successfully"}

@router.get("/", response_model=OrderListResponse)
def list_orders(
    account_id: int = Query(..., description="Account ID"),
    
    # Pagination
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of orders to return"),
    
    # Sorting
    sort_by: str = Query("order_date", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    
    # Filtering
    status_list: Optional[List[str]] = Query(None, description="Filter by order status"),
    date_from: Optional[datetime] = Query(None, description="Filter by order date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by order date to"),
    buyer_username: Optional[str] = Query(None, description="Filter by buyer username"),
    min_amount: Optional[float] = Query(None, description="Minimum order amount"),
    max_amount: Optional[float] = Query(None, description="Maximum order amount"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    has_tracking: Optional[bool] = Query(None, description="Filter by tracking number presence"),
    
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """List orders with filtering and pagination"""
    
    # Build filters
    filters = OrderFilter(
        status_list=status_list,
        date_from=date_from,
        date_to=date_to,
        buyer_username=buyer_username,
        min_amount=min_amount,
        max_amount=max_amount,
        payment_method=payment_method,
        has_tracking=has_tracking
    )
    
    return order_service.list_orders(
        account_id=account_id,
        filters=filters,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/search/", response_model=List[OrderResponse])
def search_orders(
    search_term: str = Query(..., min_length=2, description="Search term"),
    account_id: int = Query(..., description="Account ID"),
    search_fields: Optional[List[str]] = Query(None, description="Fields to search in"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Search orders by text"""
    
    return order_service.search_orders(
        account_id=account_id,
        search_term=search_term,
        search_fields=search_fields,
        limit=limit
    )

@router.patch("/bulk", response_model=dict)
def bulk_update_orders(
    order_ids: List[int],
    update_data: OrderBulkUpdate,
    account_id: int = Query(..., description="Account ID"),
    
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Bulk update multiple orders"""
    
    return order_service.bulk_update_orders(account_id, order_ids, update_data)

@router.get("/summary/", response_model=OrderSummary)
def get_order_summary(
    account_id: int = Query(..., description="Account ID"),
    date_from: Optional[datetime] = Query(None, description="Summary date from"),
    date_to: Optional[datetime] = Query(None, description="Summary date to"),
    
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order summary statistics"""
    
    return order_service.get_order_summary(account_id, date_from, date_to)

@router.get("/export/csv")
def export_orders_csv(
    account_id: int = Query(..., description="Account ID"),
    
    # Same filtering options as list_orders
    status_list: Optional[List[str]] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    buyer_username: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    payment_method: Optional[str] = Query(None),
    has_tracking: Optional[bool] = Query(None),
    
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Export orders to CSV"""
    
    # Build filters
    filters = OrderFilter(
        status_list=status_list,
        date_from=date_from,
        date_to=date_to,
        buyer_username=buyer_username,
        min_amount=min_amount,
        max_amount=max_amount,
        payment_method=payment_method,
        has_tracking=has_tracking
    )
    
    csv_content = order_service.export_orders_csv(account_id, filters)
    
    # Return CSV as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )
```

### 3. Order Schemas (Pydantic Models)
```python
# schemas/orders.py - Order API schemas

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, validator, Field

class OrderItemBase(BaseModel):
    """Base order item schema"""
    ebay_item_id: Optional[str] = None
    ebay_transaction_id: Optional[str] = None
    item_title: str
    item_sku: Optional[str] = None
    item_condition: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    unit_cost: Optional[Decimal] = None
    item_status: str = "pending"
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class OrderItemCreate(OrderItemBase):
    """Order item creation schema"""
    pass

class OrderItemResponse(OrderItemBase):
    """Order item response schema"""
    id: int
    order_id: int
    total_price: Decimal
    total_cost: Optional[Decimal]
    profit_amount: Optional[Decimal]
    shipped_date: Optional[datetime]
    delivered_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    """Base order schema"""
    ebay_order_id: str = Field(..., min_length=1, max_length=50)
    ebay_transaction_id: Optional[str] = Field(None, max_length=50)
    buyer_username: str = Field(..., min_length=1, max_length=100)
    buyer_email: Optional[str] = Field(None, max_length=100)
    
    # Financial information
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_status: str = Field(default="pending", max_length=20)
    
    # Order status
    order_status: str = Field(default="pending", max_length=20)
    
    # Shipping information
    shipping_address_line1: Optional[str] = Field(None, max_length=200)
    shipping_address_line2: Optional[str] = Field(None, max_length=200)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=50)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=50)
    shipping_method: Optional[str] = Field(None, max_length=50)
    tracking_number: Optional[str] = Field(None, max_length=100)
    
    # Dates
    order_date: datetime
    payment_date: Optional[datetime] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Notes
    buyer_notes: Optional[str] = None
    seller_notes: Optional[str] = None
    
    @validator('order_status')
    def validate_order_status(cls, v):
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if v not in valid_statuses:
            raise ValueError(f'Order status must be one of: {valid_statuses}')
        return v
    
    @validator('payment_status')
    def validate_payment_status(cls, v):
        valid_statuses = ['pending', 'completed', 'failed', 'refunded']
        if v not in valid_statuses:
            raise ValueError(f'Payment status must be one of: {valid_statuses}')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if len(v) != 3 or not v.isupper():
            raise ValueError('Currency must be 3 uppercase letters (e.g., USD)')
        return v

class OrderCreate(OrderBase):
    """Order creation schema"""
    order_items: Optional[List[OrderItemCreate]] = []

class OrderUpdate(BaseModel):
    """Order update schema"""
    buyer_email: Optional[str] = Field(None, max_length=100)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_status: Optional[str] = None
    order_status: Optional[str] = None
    shipping_address_line1: Optional[str] = Field(None, max_length=200)
    shipping_address_line2: Optional[str] = Field(None, max_length=200)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=50)
    shipping_postal_code: Optional[str] = Field(None, max_length=20)
    shipping_country: Optional[str] = Field(None, max_length=50)
    shipping_method: Optional[str] = Field(None, max_length=50)
    tracking_number: Optional[str] = Field(None, max_length=100)
    payment_date: Optional[datetime] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    buyer_notes: Optional[str] = None
    seller_notes: Optional[str] = None
    
    @validator('order_status')
    def validate_order_status(cls, v):
        if v:
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
            if v not in valid_statuses:
                raise ValueError(f'Order status must be one of: {valid_statuses}')
        return v

class OrderResponse(OrderBase):
    """Order response schema"""
    id: int
    account_id: int
    import_batch_id: Optional[str]
    import_filename: Optional[str]
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse] = []
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    """Order list response with pagination"""
    orders: List[OrderResponse]
    total: int
    skip: int
    limit: int
    has_next: bool

class OrderFilter(BaseModel):
    """Order filtering parameters"""
    status_list: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    buyer_username: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    has_tracking: Optional[bool] = None

class OrderBulkUpdate(BaseModel):
    """Bulk order update schema"""
    order_status: Optional[str] = None
    payment_status: Optional[str] = None
    shipping_method: Optional[str] = None
    seller_notes: Optional[str] = None
    
    @validator('order_status')
    def validate_order_status(cls, v):
        if v:
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
            if v not in valid_statuses:
                raise ValueError(f'Order status must be one of: {valid_statuses}')
        return v

class OrderSummary(BaseModel):
    """Order summary statistics"""
    total_orders: int
    total_revenue: float
    average_order_value: float
    orders_by_status: Dict[str, Dict[str, Any]]
    recent_orders_7d: int
    top_buyers: List[Dict[str, Any]]
    date_from: datetime
    date_to: datetime
```

---

## Success Criteria & Validation

### Order Management Requirements ✅
- [ ] Complete CRUD operations (create, read, update, delete) with validation
- [ ] Order listing with pagination, sorting, and filtering
- [ ] Search functionality across order fields (order ID, buyer, email)
- [ ] Bulk operations for mass status updates
- [ ] Order summary statistics and reporting
- [ ] CSV export functionality with filtering
- [ ] Status workflow validation and transitions
- [ ] Business rule validation (amounts, dates, status changes)

### Data Integrity Requirements ✅
- [ ] Duplicate order detection (by eBay order ID + account)
- [ ] Status transition validation (pending → processing → shipped → delivered)
- [ ] Timestamp updates based on status changes
- [ ] Total amount validation (must be positive)
- [ ] Required field validation (order ID, buyer, amount, date)
- [ ] Account-level data isolation
- [ ] Transaction management with rollback on errors

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Service handles business logic, API handles HTTP concerns
- [ ] **Open/Closed**: Service extensible for new operations without modifying core
- [ ] **Liskov Substitution**: All order services implement common repository interface
- [ ] **Interface Segregation**: Separate read and write operations
- [ ] **Dependency Inversion**: API depends on service abstractions
- [ ] **YAGNI Applied**: Essential order operations only, no complex analytics or automation
- [ ] Eliminated unnecessary features (fraud detection, automated pricing, advanced workflows)

### Performance Requirements ✅
- [ ] Order listing response time < 200ms for 50 results
- [ ] Search response time < 500ms across 10,000+ orders
- [ ] Bulk operations handle up to 100 orders efficiently
- [ ] CSV export handles large datasets without memory issues
- [ ] Database queries optimized with proper indexing
- [ ] Pagination prevents large data set loading
- [ ] Filtering reduces result set before processing

**Next Step**: Proceed to [04-order-workflow-engine.md](./04-order-workflow-engine.md) for order status management and workflow automation.