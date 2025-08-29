"""
Supplier Service Implementation
Following SOLID principles - Single Responsibility for supplier business logic
YAGNI compliance: Essential supplier operations only, no complex analytics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.repositories.supplier_repository import SupplierRepositoryInterface
from app.schemas.product import SupplierCreate, SupplierUpdate
from app.models.product import Supplier
from app.core.exceptions import NotFoundError, ValidationException, EbayManagerException

class SupplierService:
    """
    SOLID: Single Responsibility - Business logic for supplier management
    YAGNI: Essential supplier operations only, no complex scoring or analytics
    """
    
    def __init__(self, supplier_repo: SupplierRepositoryInterface):
        """SOLID: Dependency Inversion - Depends on abstraction"""
        self._supplier_repo = supplier_repo
    
    async def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Create new supplier with validation"""
        # Check for duplicate code
        existing = await self._supplier_repo.get_by_code(supplier_data.code)
        if existing:
            raise ValidationException(f"Supplier with code '{supplier_data.code}' already exists")
        
        # Validate business data - YAGNI: Basic validation only
        if supplier_data.email and not self._is_valid_email(supplier_data.email):
            raise ValidationException("Invalid email format")
        
        # Create supplier
        supplier = Supplier(
            name=supplier_data.name,
            code=supplier_data.code,
            contact_person=supplier_data.contact_person,
            email=supplier_data.email,
            phone=supplier_data.phone,
            website=supplier_data.website,
            address_line1=supplier_data.address_line1,
            address_line2=supplier_data.address_line2,
            city=supplier_data.city,
            state=supplier_data.state,
            postal_code=supplier_data.postal_code,
            country=supplier_data.country,
            tax_id=supplier_data.tax_id,
            payment_terms=supplier_data.payment_terms,
            currency=supplier_data.currency,
            notes=supplier_data.notes,
            is_active=True
        )
        
        return await self._supplier_repo.create(supplier)
    
    async def get_supplier(self, supplier_id: int) -> Supplier:
        """Get supplier by ID"""
        supplier = await self._supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise NotFoundError(f"Supplier {supplier_id} not found")
        return supplier
    
    async def get_supplier_by_code(self, code: str) -> Optional[Supplier]:
        """Get supplier by code"""
        return await self._supplier_repo.get_by_code(code)
    
    async def update_supplier(self, supplier_id: int, update_data: SupplierUpdate) -> Supplier:
        """Update supplier with validation"""
        supplier = await self.get_supplier(supplier_id)
        
        # Validate email if provided
        if update_data.email and not self._is_valid_email(update_data.email):
            raise ValidationException("Invalid email format")
        
        # Prepare update data
        update_dict = {}
        
        # Handle all optional field updates
        if update_data.name is not None:
            update_dict['name'] = update_data.name
        if update_data.contact_person is not None:
            update_dict['contact_person'] = update_data.contact_person
        if update_data.email is not None:
            update_dict['email'] = update_data.email
        if update_data.phone is not None:
            update_dict['phone'] = update_data.phone
        if update_data.website is not None:
            update_dict['website'] = update_data.website
        if update_data.address_line1 is not None:
            update_dict['address_line1'] = update_data.address_line1
        if update_data.address_line2 is not None:
            update_dict['address_line2'] = update_data.address_line2
        if update_data.city is not None:
            update_dict['city'] = update_data.city
        if update_data.state is not None:
            update_dict['state'] = update_data.state
        if update_data.postal_code is not None:
            update_dict['postal_code'] = update_data.postal_code
        if update_data.country is not None:
            update_dict['country'] = update_data.country
        if update_data.tax_id is not None:
            update_dict['tax_id'] = update_data.tax_id
        if update_data.payment_terms is not None:
            update_dict['payment_terms'] = update_data.payment_terms
        if update_data.currency is not None:
            update_dict['currency'] = update_data.currency
        if update_data.is_active is not None:
            update_dict['is_active'] = update_data.is_active
        if update_data.notes is not None:
            update_dict['notes'] = update_data.notes
        
        if update_dict:
            update_dict['updated_at'] = datetime.utcnow()
        
        return await self._supplier_repo.update(supplier_id, update_dict)
    
    async def get_active_suppliers(self) -> List[Supplier]:
        """Get all active suppliers"""
        return await self._supplier_repo.get_active_suppliers()
    
    async def search_suppliers(
        self, 
        name: Optional[str] = None, 
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[Supplier]:
        """Search suppliers with basic filters"""
        # Validate pagination
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50
        
        offset = (page - 1) * page_size
        return await self._supplier_repo.search(name, is_active, offset, page_size)
    
    async def search_suppliers_by_name(self, name: str) -> List[Supplier]:
        """Search suppliers by name - YAGNI: Simple name search only"""
        if not name or not name.strip():
            raise ValidationException("Search name cannot be empty")
        
        return await self._supplier_repo.search_by_name(name.strip())
    
    async def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier performance metrics"""
        # Verify supplier exists
        await self.get_supplier(supplier_id)
        
        return await self._supplier_repo.get_supplier_performance(supplier_id)
    
    async def deactivate_supplier(self, supplier_id: int) -> Dict[str, Any]:
        """Deactivate supplier with product impact analysis"""
        supplier = await self.get_supplier(supplier_id)
        
        if not supplier.is_active:
            raise ValidationException("Supplier is already inactive")
        
        # Use repository method that handles product analysis
        result = await self._supplier_repo.deactivate_supplier(supplier_id)
        
        return result
    
    async def activate_supplier(self, supplier_id: int) -> Supplier:
        """Activate supplier"""
        supplier = await self.get_supplier(supplier_id)
        
        if supplier.is_active:
            raise ValidationException("Supplier is already active")
        
        return await self._supplier_repo.update(supplier_id, {
            'is_active': True,
            'updated_at': datetime.utcnow()
        })
    
    async def update_supplier_performance(self, supplier_id: int, order_amount: float, delivery_days: int) -> bool:
        """Update supplier performance statistics"""
        if order_amount <= 0:
            raise ValidationException("Order amount must be positive")
        
        if delivery_days < 0:
            raise ValidationException("Delivery days cannot be negative")
        
        return await self._supplier_repo.update_supplier_stats(supplier_id, order_amount, delivery_days)
    
    async def get_suppliers_with_low_stock(self) -> List[Supplier]:
        """Get suppliers that have products with low stock"""
        return await self._supplier_repo.get_suppliers_with_low_stock_products()
    
    async def get_supplier_summary(self) -> Dict[str, Any]:
        """Get overall supplier system summary - YAGNI: Basic metrics only"""
        return await self._supplier_repo.get_supplier_summary()
    
    async def get_top_suppliers(
        self, 
        limit: int = 10, 
        criteria: str = 'products'
    ) -> List[Dict[str, Any]]:
        """Get top performing suppliers - YAGNI: Simple ranking only"""
        if limit < 1 or limit > 50:
            limit = 10
        
        if criteria not in ['products', 'spending']:
            raise ValidationException("Criteria must be 'products' or 'spending'")
        
        return await self._supplier_repo.get_top_suppliers(limit, criteria)
    
    async def delete_supplier(self, supplier_id: int) -> bool:
        """Delete supplier (only if no products)"""
        supplier = await self.get_supplier(supplier_id)
        
        # Check if supplier has products - YAGNI: Simple check only
        from app.repositories.product_repository import ProductRepository
        from app.models.base import get_db
        
        # This is a simplified approach - in production would inject product repo
        db = next(get_db())
        product_count = await ProductRepository(db).count_by_supplier(supplier_id)
        
        if product_count > 0:
            raise ValidationException(f"Cannot delete supplier: {product_count} products are associated with this supplier")
        
        return await self._supplier_repo.delete(supplier_id)
    
    async def get_supplier_contact_info(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier contact information for communication"""
        supplier = await self.get_supplier(supplier_id)
        
        return {
            'supplier_id': supplier.id,
            'name': supplier.name,
            'code': supplier.code,
            'contact_person': supplier.contact_person,
            'email': supplier.email,
            'phone': supplier.phone,
            'address': {
                'line1': supplier.address_line1,
                'line2': supplier.address_line2,
                'city': supplier.city,
                'state': supplier.state,
                'postal_code': supplier.postal_code,
                'country': supplier.country
            },
            'business_info': {
                'tax_id': supplier.tax_id,
                'payment_terms': supplier.payment_terms,
                'currency': supplier.currency
            }
        }
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation - YAGNI: Simple regex check only"""
        import re
        
        if not email or not email.strip():
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email.strip()) is not None
    
    async def validate_supplier_for_product_creation(self, supplier_id: int) -> bool:
        """Validate supplier can be used for new products"""
        supplier = await self.get_supplier(supplier_id)
        
        if not supplier.is_active:
            raise ValidationException(f"Supplier '{supplier.name}' is not active")
        
        # YAGNI: Additional validations could include credit status, contract status, etc.
        # For now, just check active status
        
        return True