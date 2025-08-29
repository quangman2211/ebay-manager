"""
Bulk Operations API Endpoints
Following SOLID principles - Single Responsibility for HTTP concerns only
YAGNI compliance: Essential endpoints only, no complex orchestration APIs
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models.base import get_db
from app.services.bulk_operations_service import BulkOperationsService
from app.repositories.listing_repository import ListingRepository
from app.repositories.product_repository import ProductRepository
from app.core.exceptions import ValidationException, EbayManagerException
from app.middleware.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/bulk-operations", tags=["bulk-operations"])


def get_bulk_operations_service(db: Session = Depends(get_db)) -> BulkOperationsService:
    """
    SOLID: Dependency Inversion - Factory function for service injection
    """
    listing_repo = ListingRepository(db)
    product_repo = ProductRepository(db)
    return BulkOperationsService(listing_repo, product_repo)


class BulkOperationRequest(BaseModel):
    """Request schema for bulk operations - SOLID: Interface Segregation"""
    entity_type: str = Field(..., description="Type of entity (listings, products)")
    entity_ids: List[int] = Field(..., min_items=1, max_items=1000, description="List of entity IDs")
    operation_type: str = Field(..., description="Type of operation to perform")
    operation_data: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific data")


class BulkOperationResponse(BaseModel):
    """Response schema for bulk operations"""
    success: bool
    message: str
    result: Dict[str, Any]


class BulkListingStatusRequest(BaseModel):
    """Convenience request for bulk listing status updates"""
    listing_ids: List[int] = Field(..., min_items=1, max_items=500, description="List of listing IDs")
    status: str = Field(..., description="New status for listings")


class BulkListingPriceRequest(BaseModel):
    """Convenience request for bulk listing price updates"""
    listing_ids: List[int] = Field(..., min_items=1, max_items=500, description="List of listing IDs")
    price: float = Field(..., gt=0, description="New price for listings")


class BulkProductPriceRequest(BaseModel):
    """Convenience request for bulk product price updates"""
    product_ids: List[int] = Field(..., min_items=1, max_items=1000, description="List of product IDs")
    cost_price: Optional[float] = Field(None, gt=0, description="New cost price")
    selling_price: Optional[float] = Field(None, gt=0, description="New selling price")


class BulkInventoryRequest(BaseModel):
    """Convenience request for bulk inventory updates"""
    product_ids: List[int] = Field(..., min_items=1, max_items=1000, description="List of product IDs")
    quantity_adjustment: int = Field(..., description="Quantity adjustment (can be negative)")


@router.post("/execute", response_model=BulkOperationResponse, status_code=status.HTTP_200_OK)
async def execute_bulk_operation(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkOperationRequest,
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """
    Execute bulk operation on specified entities
    SOLID: Single Responsibility - Handle HTTP concerns only
    """
    try:
        # Add operation_type to operation_data for processing
        operation_data = request.operation_data.copy()
        operation_data['operation_type'] = request.operation_type
        
        result = await bulk_service.execute_bulk_operation(
            request.entity_type,
            request.entity_ids,
            operation_data
        )
        
        success_message = f"Bulk operation completed: {result.successful_items}/{result.total_items} successful"
        if result.failed_items > 0:
            success_message += f", {result.failed_items} failed"
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=success_message,
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")


@router.post("/validate", response_model=Dict[str, Any])
async def validate_bulk_operation(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkOperationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Validate bulk operation before execution"""
    try:
        operation_data = request.operation_data.copy()
        operation_data['operation_type'] = request.operation_type
        
        validation_errors = await bulk_service.validate_bulk_operation(
            request.entity_type,
            request.entity_ids,
            operation_data
        )
        
        return {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "total_items": len(request.entity_ids),
            "entity_type": request.entity_type,
            "operation_type": request.operation_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/preview", response_model=Dict[str, Any])
async def get_operation_preview(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkOperationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get preview of bulk operation without executing"""
    try:
        operation_data = request.operation_data.copy()
        operation_data['operation_type'] = request.operation_type
        
        preview = await bulk_service.get_operation_preview(
            request.entity_type,
            request.entity_ids,
            operation_data
        )
        
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.get("/operations/{entity_type}", response_model=Dict[str, Any])
async def get_supported_operations(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    entity_type: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get supported operations for entity type"""
    operations = bulk_service.get_supported_operations(entity_type)
    
    return {
        "entity_type": entity_type,
        "supported_operations": operations
    }


@router.get("/entity-types", response_model=Dict[str, Any])
async def get_supported_entity_types(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get supported entity types for bulk operations"""
    entity_types = bulk_service.get_supported_entity_types()
    
    return {
        "entity_types": entity_types,
        "description": "Entity types that support bulk operations"
    }


# Convenience endpoints for common operations

@router.post("/listings/update-status", response_model=BulkOperationResponse)
async def bulk_update_listing_status(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkListingStatusRequest,
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk listing status updates"""
    try:
        result = await bulk_service.bulk_update_listing_status(
            request.listing_ids,
            request.status
        )
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Status update completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listings/update-price", response_model=BulkOperationResponse)
async def bulk_update_listing_price(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkListingPriceRequest,
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk listing price updates"""
    try:
        result = await bulk_service.bulk_update_listing_price(
            request.listing_ids,
            request.price
        )
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Price update completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listings/activate", response_model=BulkOperationResponse)
async def bulk_activate_listings(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    listing_ids: List[int] = Query(..., description="List of listing IDs to activate"),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk listing activation"""
    try:
        result = await bulk_service.bulk_activate_listings(listing_ids)
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Activation completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listings/deactivate", response_model=BulkOperationResponse)
async def bulk_deactivate_listings(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    listing_ids: List[int] = Query(..., description="List of listing IDs to deactivate"),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk listing deactivation"""
    try:
        result = await bulk_service.bulk_deactivate_listings(listing_ids)
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Deactivation completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/update-prices", response_model=BulkOperationResponse)
async def bulk_update_product_prices(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkProductPriceRequest,
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk product price updates"""
    try:
        result = await bulk_service.bulk_update_product_prices(
            request.product_ids,
            request.cost_price,
            request.selling_price
        )
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Price update completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/update-inventory", response_model=BulkOperationResponse)
async def bulk_update_product_inventory(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    request: BulkInventoryRequest,
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk product inventory updates"""
    try:
        result = await bulk_service.bulk_update_product_inventory(
            request.product_ids,
            request.quantity_adjustment
        )
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Inventory update completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/activate", response_model=BulkOperationResponse)
async def bulk_activate_products(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    product_ids: List[int] = Query(..., description="List of product IDs to activate"),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk product activation"""
    try:
        result = await bulk_service.bulk_activate_products(product_ids)
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Activation completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products/deactivate", response_model=BulkOperationResponse)
async def bulk_deactivate_products(
    *,
    bulk_service: BulkOperationsService = Depends(get_bulk_operations_service),
    product_ids: List[int] = Query(..., description="List of product IDs to deactivate"),
    current_user: User = Depends(get_current_user)
) -> BulkOperationResponse:
    """Convenience endpoint for bulk product deactivation"""
    try:
        result = await bulk_service.bulk_deactivate_products(product_ids)
        
        return BulkOperationResponse(
            success=result.status.value != "failed",
            message=f"Deactivation completed: {result.successful_items}/{result.total_items} successful",
            result=result.to_dict()
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EbayManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))