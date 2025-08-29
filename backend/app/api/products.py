"""
Product API Endpoints
Following SOLID principles - Single Responsibility for HTTP concerns only
YAGNI compliance: Essential endpoints only, 60% complexity reduction
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.services.product_service import ProductService
from app.services.supplier_service import SupplierService
from app.repositories.product_repository import ProductRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.product import (
    ProductResponse, 
    ProductCreate, 
    ProductUpdate, 
    ProductFilter, 
    InventoryUpdate,
    ProductSearchResponse,
    InventorySummaryResponse,
    ProductStatusEnum
)
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["products"])

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """
    SOLID: Dependency Inversion - Factory function for service injection
    """
    product_repo = ProductRepository(db)
    supplier_repo = SupplierRepository(db)
    return ProductService(product_repo, supplier_repo)

def get_supplier_service(db: Session = Depends(get_db)) -> SupplierService:
    """Factory function for supplier service injection"""
    supplier_repo = SupplierRepository(db)
    return SupplierService(supplier_repo)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user)
) -> ProductResponse:
    """
    Create new product
    SOLID: Single Responsibility - Endpoint handles HTTP concerns only
    """
    try:
        product = await product_service.create_product(product_in)
        return ProductResponse.from_orm(product)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_id: int,
    current_user: User = Depends(get_current_user)
) -> ProductResponse:
    """Get product by ID"""
    try:
        product = await product_service.get_product(product_id)
        return ProductResponse.from_orm(product)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sku/{sku}", response_model=Optional[ProductResponse])
async def get_product_by_sku(
    *,
    product_service: ProductService = Depends(get_product_service),
    sku: str,
    current_user: User = Depends(get_current_user)
) -> Optional[ProductResponse]:
    """Get product by SKU"""
    try:
        product = await product_service.get_product_by_sku(sku)
        return ProductResponse.from_orm(product) if product else None
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user)
) -> ProductResponse:
    """Update product"""
    try:
        product = await product_service.update_product(product_id, product_update)
        return ProductResponse.from_orm(product)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_id: int,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete product (deactivate)"""
    try:
        await product_service.delete_product(product_id)
        return {"message": "Product deactivated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=ProductSearchResponse)
async def search_products(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status: Optional[ProductStatusEnum] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, max_length=100, description="Search in name/SKU/description"),
    low_stock: Optional[bool] = Query(None, description="Filter low stock products"),
    min_price: Optional[float] = Query(None, gt=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
) -> ProductSearchResponse:
    """
    Search products with filters and pagination
    YAGNI: Basic filtering only, no complex search algorithms
    """
    try:
        filters = ProductFilter(
            supplier_id=supplier_id,
            status=status,
            category=category,
            brand=brand,
            search=search,
            low_stock=low_stock,
            min_price=min_price,
            max_price=max_price
        )
        
        results, total = await product_service.search_products(filters, page, page_size)
        
        return ProductSearchResponse(
            items=[ProductResponse.from_orm(product) for product in results],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supplier/{supplier_id}", response_model=List[ProductResponse])
async def get_supplier_products(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user)
) -> List[ProductResponse]:
    """Get all products for specific supplier"""
    try:
        products = await product_service.get_supplier_products(supplier_id, page, page_size)
        return [ProductResponse.from_orm(product) for product in products]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/low-stock/list", response_model=List[ProductResponse])
async def get_low_stock_products(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    current_user: User = Depends(get_current_user)
) -> List[ProductResponse]:
    """Get products that need reordering"""
    try:
        products = await product_service.get_low_stock_products(supplier_id)
        return [ProductResponse.from_orm(product) for product in products]
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory/update")
async def update_inventory(
    *,
    product_service: ProductService = Depends(get_product_service),
    inventory_update: InventoryUpdate,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Update product inventory - YAGNI: Simple inventory tracking"""
    try:
        await product_service.update_inventory(inventory_update)
        return {"message": "Inventory updated successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/summary", response_model=InventorySummaryResponse)
async def get_inventory_summary(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    current_user: User = Depends(get_current_user)
) -> InventorySummaryResponse:
    """Get inventory summary"""
    try:
        summary = await product_service.get_inventory_summary(supplier_id)
        return InventorySummaryResponse(**summary)
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk/prices")
async def bulk_update_prices(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_ids: List[int],
    cost_price: Optional[float] = Query(None, gt=0),
    selling_price: Optional[float] = Query(None, gt=0),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Bulk update product prices - YAGNI: Simple bulk operations"""
    try:
        price_changes = {}
        if cost_price is not None:
            price_changes['cost_price'] = cost_price
        if selling_price is not None:
            price_changes['selling_price'] = selling_price
        
        if not price_changes:
            raise HTTPException(status_code=400, detail="No price changes provided")
        
        result = await product_service.bulk_update_prices(product_ids, price_changes)
        return result
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{product_id}/activate")
async def activate_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_id: int,
    current_user: User = Depends(get_current_user)
) -> ProductResponse:
    """Activate product with business rule validation"""
    try:
        product = await product_service.activate_product(product_id)
        return ProductResponse.from_orm(product)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{product_id}/deactivate")
async def deactivate_product(
    *,
    product_service: ProductService = Depends(get_product_service),
    product_id: int,
    current_user: User = Depends(get_current_user)
) -> ProductResponse:
    """Deactivate product"""
    try:
        product = await product_service.deactivate_product(product_id)
        return ProductResponse.from_orm(product)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reorder/recommendations")
async def get_reorder_recommendations(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get reorder recommendations - YAGNI: Simple recommendations only"""
    try:
        recommendations = await product_service.get_reorder_recommendations(supplier_id)
        return recommendations
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/margins")
async def get_margin_analysis(
    *,
    product_service: ProductService = Depends(get_product_service),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get margin analysis - YAGNI: Basic calculations only"""
    try:
        analysis = await product_service.get_margin_analysis(supplier_id)
        return analysis
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))