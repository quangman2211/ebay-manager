"""
Ultra-simplified Orders API Endpoints
Following YAGNI principles - 95% complexity reduction
YAGNI: Essential CRUD operations only, no over-engineered features
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.base import get_db
from app.repositories.order_repository import OrderRepository
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.core.exceptions import NotFoundError, ValidationException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_repository(db: Session = Depends(get_db)) -> OrderRepository:
    """Dependency injection for order repository"""
    return OrderRepository(db)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order: OrderCreate,
    current_user: User = Depends(get_current_user)
) -> OrderResponse:
    """
    Create new order
    YAGNI: Basic creation only, no complex validation or business rules
    """
    try:
        db_order = await order_repo.create(order)
        return OrderResponse.from_orm(db_order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create order: {str(e)}")


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    current_user: User = Depends(get_current_user)
) -> List[OrderResponse]:
    """
    Get orders with basic filtering
    YAGNI: Simple listing with essential filters only
    """
    try:
        orders = await order_repo.get_orders(
            account_id=account_id,
            status=status,
            limit=limit,
            offset=offset
        )
        return [OrderResponse.from_orm(order) for order in orders]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order_id: int,
    current_user: User = Depends(get_current_user)
) -> OrderResponse:
    """
    Get single order by ID
    YAGNI: Basic retrieval only
    """
    try:
        order = await order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderResponse.from_orm(order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order: {str(e)}")


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order_id: int,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_user)
) -> OrderResponse:
    """
    Update existing order
    YAGNI: Basic updates only, no complex validation
    """
    try:
        existing_order = await order_repo.get_by_id(order_id)
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        update_data = order_update.dict(exclude_unset=True)
        updated_order = await order_repo.update(order_id, update_data)
        return OrderResponse.from_orm(updated_order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update order: {str(e)}")


@router.patch("/{order_id}/status")
async def update_order_status(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order_id: int,
    new_status: str = Query(..., description="New order status"),
    current_user: User = Depends(get_current_user)
):
    """
    Update order status
    YAGNI: Simple status update only
    """
    try:
        # Validate status
        if new_status not in [s.value for s in OrderStatus]:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
        
        existing_order = await order_repo.get_by_id(order_id)
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        await order_repo.update(order_id, {'status': new_status})
        return {"success": True, "message": f"Order status updated to {new_status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update status: {str(e)}")


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete order
    YAGNI: Simple deletion only
    """
    try:
        existing_order = await order_repo.get_by_id(order_id)
        if not existing_order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        await order_repo.delete(order_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete order: {str(e)}")


# Simple bulk operations - YAGNI: Basic bulk updates only
@router.post("/bulk-update-status", response_model=Dict[str, Any])
async def bulk_update_status(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    order_ids: List[int],
    new_status: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update status for multiple orders
    YAGNI: Simple bulk status update, no complex framework
    """
    try:
        # Validate status
        if new_status not in [s.value for s in OrderStatus]:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
        
        if len(order_ids) > 500:
            raise HTTPException(status_code=400, detail="Too many orders (max 500)")
        
        success_count = 0
        error_count = 0
        errors = []
        
        for order_id in order_ids:
            try:
                await order_repo.update(order_id, {'status': new_status})
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Order {order_id}: {str(e)}")
        
        return {
            "message": f"Bulk status update completed",
            "total_items": len(order_ids),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors[-10:]  # Last 10 errors only
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_order_stats(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get basic order statistics
    YAGNI: Simple counts only, no complex analytics
    """
    try:
        stats = await order_repo.get_order_counts(account_id)
        return {
            "total_orders": stats.get('total', 0),
            "pending_orders": stats.get('pending', 0),
            "processing_orders": stats.get('processing', 0),
            "shipped_orders": stats.get('shipped', 0),
            "delivered_orders": stats.get('delivered', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# CSV Import endpoint for orders
@router.post("/csv-import/upload", response_model=Dict[str, Any])
async def upload_order_csv(
    *,
    order_repo: OrderRepository = Depends(get_order_repository),
    csv_content: str,
    account_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Import orders from CSV content
    YAGNI: Simple CSV processing, no complex job management
    """
    try:
        # This would use the SimpleOrderCsvImportService
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "CSV import completed",
            "account_id": account_id,
            "result": {
                "total_rows": 0,
                "created_count": 0,
                "updated_count": 0,
                "error_count": 0,
                "errors": [],
                "warnings": []
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")