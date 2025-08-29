"""
Supplier API Endpoints
Following SOLID principles - Single Responsibility for HTTP concerns only
YAGNI compliance: Essential supplier endpoints only, no complex analytics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.services.supplier_service import SupplierService
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product import (
    SupplierResponse, 
    SupplierCreate, 
    SupplierUpdate,
    SupplierSearchResponse,
    SupplierPerformanceResponse
)
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    """
    SOLID: Dependency Inversion - Factory function for service injection
    """
    supplier_repo = SupplierRepository(db)
    return SupplierService(supplier_repo)

@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_in: SupplierCreate,
    current_user: User = Depends(get_current_user)
) -> SupplierResponse:
    """
    Create new supplier
    SOLID: Single Responsibility - Endpoint handles HTTP concerns only
    """
    try:
        supplier = await supplier_service.create_supplier(supplier_in)
        return SupplierResponse.from_orm(supplier)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> SupplierResponse:
    """Get supplier by ID"""
    try:
        supplier = await supplier_service.get_supplier(supplier_id)
        return SupplierResponse.from_orm(supplier)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/code/{code}", response_model=Optional[SupplierResponse])
async def get_supplier_by_code(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    code: str,
    current_user: User = Depends(get_current_user)
) -> Optional[SupplierResponse]:
    """Get supplier by code"""
    try:
        supplier = await supplier_service.get_supplier_by_code(code)
        return SupplierResponse.from_orm(supplier) if supplier else None
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    supplier_update: SupplierUpdate,
    current_user: User = Depends(get_current_user)
) -> SupplierResponse:
    """Update supplier"""
    try:
        supplier = await supplier_service.update_supplier(supplier_id, supplier_update)
        return SupplierResponse.from_orm(supplier)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{supplier_id}")
async def delete_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete supplier (only if no products)"""
    try:
        await supplier_service.delete_supplier(supplier_id)
        return {"message": "Supplier deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[SupplierResponse])
async def search_suppliers(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    name: Optional[str] = Query(None, description="Search by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
) -> List[SupplierResponse]:
    """
    Search suppliers with basic filters
    YAGNI: Simple filtering only, no complex search algorithms
    """
    try:
        suppliers = await supplier_service.search_suppliers(name, is_active, page, page_size)
        return [SupplierResponse.from_orm(supplier) for supplier in suppliers]
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active/list", response_model=List[SupplierResponse])
async def get_active_suppliers(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user)
) -> List[SupplierResponse]:
    """Get all active suppliers"""
    try:
        suppliers = await supplier_service.get_active_suppliers()
        return [SupplierResponse.from_orm(supplier) for supplier in suppliers]
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/name/{name}", response_model=List[SupplierResponse])
async def search_suppliers_by_name(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    name: str,
    current_user: User = Depends(get_current_user)
) -> List[SupplierResponse]:
    """Search suppliers by name - YAGNI: Simple name search only"""
    try:
        suppliers = await supplier_service.search_suppliers_by_name(name)
        return [SupplierResponse.from_orm(supplier) for supplier in suppliers]
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}/performance", response_model=SupplierPerformanceResponse)
async def get_supplier_performance(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> SupplierPerformanceResponse:
    """Get supplier performance metrics"""
    try:
        performance = await supplier_service.get_supplier_performance(supplier_id)
        return SupplierPerformanceResponse(**performance)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}/deactivate")
async def deactivate_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Deactivate supplier with product impact analysis"""
    try:
        result = await supplier_service.deactivate_supplier(supplier_id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}/activate")
async def activate_supplier(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> SupplierResponse:
    """Activate supplier"""
    try:
        supplier = await supplier_service.activate_supplier(supplier_id)
        return SupplierResponse.from_orm(supplier)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{supplier_id}/performance/update")
async def update_supplier_performance(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    order_amount: float = Query(..., gt=0, description="Order amount"),
    delivery_days: int = Query(..., ge=0, description="Delivery days"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update supplier performance statistics"""
    try:
        await supplier_service.update_supplier_performance(supplier_id, order_amount, delivery_days)
        return {"message": "Supplier performance updated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/low-stock/suppliers", response_model=List[SupplierResponse])
async def get_suppliers_with_low_stock(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user)
) -> List[SupplierResponse]:
    """Get suppliers that have products with low stock"""
    try:
        suppliers = await supplier_service.get_suppliers_with_low_stock()
        return [SupplierResponse.from_orm(supplier) for supplier in suppliers]
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/overview")
async def get_supplier_summary(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get overall supplier system summary - YAGNI: Basic metrics only"""
    try:
        summary = await supplier_service.get_supplier_summary()
        return summary
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top/ranking")
async def get_top_suppliers(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    limit: int = Query(10, ge=1, le=50, description="Number of suppliers to return"),
    criteria: str = Query("products", regex="^(products|spending)$", description="Ranking criteria"),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get top performing suppliers - YAGNI: Simple ranking only"""
    try:
        top_suppliers = await supplier_service.get_top_suppliers(limit, criteria)
        return top_suppliers
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{supplier_id}/contact")
async def get_supplier_contact_info(
    *,
    supplier_service: SupplierService = Depends(get_supplier_service),
    supplier_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get supplier contact information for communication"""
    try:
        contact_info = await supplier_service.get_supplier_contact_info(supplier_id)
        return contact_info
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))