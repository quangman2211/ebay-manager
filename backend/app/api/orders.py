"""
Order Management API Endpoints
Following SOLID principles - Single Responsibility for order operations
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.middleware.auth import get_current_active_user, require_admin_role
from app.models.user import User
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderSummary, OrderListResponse,
    OrderStatusUpdateRequest, OrderShippingUpdate, OrderFilter, OrderStats
)
from app.services.order_service import OrderService
from app.core.exceptions import EbayManagerException
from app.core.logging import get_logger

logger = get_logger("orders_api")
router = APIRouter(prefix="/orders", tags=["Order Management"])

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order
    Following SOLID: Single Responsibility for order creation
    """
    try:
        order_service = OrderService(db)
        order = order_service.create_order(order_data, current_user.id)
        
        logger.info(f"Order created via API: {order.id} by user {current_user.id}")
        return order
        
    except EbayManagerException as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("order_date", description="Sort field"),
    sort_desc: bool = Query(True, description="Sort descending"),
    account_id: Optional[int] = Query(None, gt=0),
    status: Optional[str] = Query(None, description="Comma-separated status values"),
    payment_status: Optional[str] = Query(None, description="Comma-separated payment status values"),
    shipping_status: Optional[str] = Query(None, description="Comma-separated shipping status values"),
    buyer_username: Optional[str] = Query(None, max_length=255),
    ebay_order_id: Optional[str] = Query(None, max_length=100),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    is_priority: Optional[bool] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    has_tracking: Optional[bool] = Query(None),
    currency: Optional[str] = Query(None, min_length=3, max_length=3),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List orders with filtering and pagination
    Following SOLID: Single Responsibility for order listing
    """
    try:
        # Build filters
        filters = OrderFilter()
        
        if account_id:
            filters.account_id = account_id
        
        if status:
            filters.status = [s.strip() for s in status.split(',')]
            
        if payment_status:
            filters.payment_status = [s.strip() for s in payment_status.split(',')]
            
        if shipping_status:
            filters.shipping_status = [s.strip() for s in shipping_status.split(',')]
            
        if buyer_username:
            filters.buyer_username = buyer_username
            
        if ebay_order_id:
            filters.ebay_order_id = ebay_order_id
            
        if date_from:
            from datetime import datetime
            filters.date_from = datetime.strptime(date_from, "%Y-%m-%d")
            
        if date_to:
            from datetime import datetime
            filters.date_to = datetime.strptime(date_to, "%Y-%m-%d")
            
        if is_priority is not None:
            filters.is_priority = is_priority
            
        if is_overdue is not None:
            filters.is_overdue = is_overdue
            
        if has_tracking is not None:
            filters.has_tracking = has_tracking
            
        if currency:
            filters.currency = currency.upper()
        
        # Get orders
        order_service = OrderService(db)
        orders, total_count = order_service.list_orders(
            current_user.id, filters, page, page_size, sort_by, sort_desc
        )
        
        # Convert to summaries
        order_summaries = []
        for order in orders:
            summary = OrderSummary(
                id=order.id,
                ebay_order_id=order.ebay_order_id,
                buyer_username=order.buyer_username,
                status=order.status,
                payment_status=order.payment_status,
                shipping_status=order.shipping_status,
                total_amount=order.total_amount,
                currency=order.currency,
                order_date=order.order_date,
                total_items=order.total_items,
                tracking_number=order.tracking_number,
                is_priority=order.is_priority,
                is_overdue=order.is_overdue,
                days_since_order=order.days_since_order
            )
            order_summaries.append(summary)
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        logger.info(f"Orders listed via API: {len(order_summaries)}/{total_count} by user {current_user.id}")
        
        return OrderListResponse(
            orders=order_summaries,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except ValueError as e:
        logger.error(f"Invalid parameter in order listing: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error listing orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get order by ID
    Following SOLID: Single Responsibility for order retrieval
    """
    try:
        order_service = OrderService(db)
        order = order_service.get_order_by_id(order_id, current_user.id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info(f"Order retrieved via API: {order_id} by user {current_user.id}")
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/ebay/{ebay_order_id}", response_model=OrderResponse)
async def get_order_by_ebay_id(
    ebay_order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get order by eBay order ID
    Following SOLID: Single Responsibility for order retrieval by eBay ID
    """
    try:
        order_service = OrderService(db)
        order = order_service.get_order_by_ebay_id(ebay_order_id, current_user.id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info(f"Order retrieved by eBay ID via API: {ebay_order_id} by user {current_user.id}")
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting order by eBay ID {ebay_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update order
    Following SOLID: Single Responsibility for order updates
    """
    try:
        order_service = OrderService(db)
        order = order_service.update_order(order_id, order_data, current_user.id)
        
        logger.info(f"Order updated via API: {order_id} by user {current_user.id}")
        return order
        
    except EbayManagerException as e:
        logger.error(f"Order update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update order status
    Following SOLID: Single Responsibility for status updates
    """
    try:
        order_service = OrderService(db)
        order = order_service.update_order_status(order_id, status_data, current_user.id)
        
        logger.info(f"Order status updated via API: {order_id} -> {status_data.status} by user {current_user.id}")
        return order
        
    except EbayManagerException as e:
        logger.error(f"Order status update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating order status {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{order_id}/shipping", response_model=OrderResponse)
async def update_order_shipping(
    order_id: int,
    shipping_data: OrderShippingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update order shipping information
    Following SOLID: Single Responsibility for shipping updates
    """
    try:
        order_service = OrderService(db)
        order = order_service.update_shipping_info(order_id, shipping_data, current_user.id)
        
        logger.info(f"Order shipping updated via API: {order_id} by user {current_user.id}")
        return order
        
    except EbayManagerException as e:
        logger.error(f"Order shipping update failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating order shipping {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/summary", response_model=OrderStats)
async def get_order_stats(
    account_id: Optional[int] = Query(None, gt=0, description="Filter by account ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get order statistics
    Following SOLID: Single Responsibility for statistics
    """
    try:
        order_service = OrderService(db)
        stats = order_service.get_order_stats(current_user.id, account_id)
        
        logger.info(f"Order stats retrieved via API by user {current_user.id}")
        return stats
        
    except Exception as e:
        logger.error(f"Unexpected error getting order stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{order_id}")
async def delete_order(
    order_id: int,
    current_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Delete order (admin only - soft delete)
    Following SOLID: Single Responsibility for order deletion
    """
    try:
        order_service = OrderService(db)
        success = order_service.delete_order(order_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Order not found")
        
        logger.info(f"Order deleted via API: {order_id} by admin user {current_user.id}")
        return {"message": "Order deleted successfully", "order_id": order_id}
        
    except EbayManagerException as e:
        logger.error(f"Order deletion failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health/check")
async def orders_health_check(
    db: Session = Depends(get_db)
):
    """
    Order service health check
    Following SOLID: Single Responsibility for health monitoring
    """
    try:
        # Test database connectivity
        from app.models.order import Order
        order_count = db.query(Order).count()
        
        return {
            "status": "healthy",
            "total_orders": order_count,
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Order health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
            }
        )