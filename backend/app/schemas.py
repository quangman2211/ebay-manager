from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    SHIPPED = "shipped"
    COMPLETED = "completed"


class DataType(str, Enum):
    ORDER = "order"
    LISTING = "listing"


class PermissionLevel(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class ConnectionStatus(str, Enum):
    AUTHENTICATED = "authenticated"
    PENDING = "pending"
    EXPIRED = "expired"
    FAILED = "failed"
    SYSTEM = "system"


class AccountType(str, Enum):
    EBAY = "ebay"
    ETSY = "etsy"
    SYSTEM = "system"


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.STAFF
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class AccountBase(BaseModel):
    platform_username: str
    name: str
    is_active: bool = True


class AccountCreate(AccountBase):
    user_id: Optional[int] = None


class AccountResponse(AccountBase):
    id: int
    user_id: int
    created_at: datetime
    
    # Sprint 7 enhancements - REDESIGNED STATUS FIELDS
    account_type: Optional[AccountType] = AccountType.EBAY
    connection_status: Optional[ConnectionStatus] = ConnectionStatus.AUTHENTICATED
    last_sync_at: Optional[datetime] = None
    data_processing_enabled: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class CSVDataBase(BaseModel):
    data_type: DataType
    csv_row: Dict[str, Any]
    item_id: str


class CSVDataCreate(CSVDataBase):
    account_id: int


class CSVDataResponse(CSVDataBase):
    id: int
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusBase(BaseModel):
    status: OrderStatus


class OrderStatusCreate(OrderStatusBase):
    csv_data_id: int
    updated_by: int


class OrderStatusUpdate(OrderStatusBase):
    pass


class OrderStatusResponse(OrderStatusBase):
    id: int
    csv_data_id: int
    updated_by: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    item_id: str
    csv_row: Dict[str, Any]
    order_status: Optional[OrderStatusResponse] = None
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListingResponse(BaseModel):
    id: int
    item_id: str
    csv_row: Dict[str, Any]
    account_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CSVUpload(BaseModel):
    account_id: int
    data_type: DataType


# =============================================================================
# Sprint 7: Enhanced Account Management Schemas
# =============================================================================

class AccountUpdateRequest(BaseModel):
    """Request to update account details - REDESIGNED STATUS FIELDS"""
    platform_username: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    connection_status: Optional[ConnectionStatus] = None
    data_processing_enabled: Optional[bool] = None


class EnhancedAccountResponse(AccountResponse):
    """Enhanced account response with full Sprint 7 data"""
    settings: Optional[Dict[str, Any]] = {}
    performance_metrics: Optional[Dict[str, Any]] = {}
    user_permissions: Optional[List[Dict[str, Any]]] = []


class UserAccountPermissionBase(BaseModel):
    """Base model for user account permissions"""
    user_id: int
    account_id: int
    permission_level: PermissionLevel = PermissionLevel.VIEW
    is_active: bool = True


class UserAccountPermissionCreate(UserAccountPermissionBase):
    """Create user account permission"""
    granted_by: Optional[int] = None


class UserAccountPermissionUpdate(BaseModel):
    """Update user account permission"""
    permission_level: Optional[PermissionLevel] = None
    is_active: Optional[bool] = None


class UserAccountPermissionResponse(UserAccountPermissionBase):
    """User account permission response"""
    id: int
    granted_by: Optional[int] = None
    granted_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountMetricsBase(BaseModel):
    """Base model for account metrics"""
    account_id: int
    metric_date: date
    total_orders: int = 0
    total_revenue: Decimal = Decimal('0.00')
    active_listings: int = 0
    total_views: int = 0
    watchers: int = 0
    conversion_rate: Decimal = Decimal('0.0000')


class AccountMetricsCreate(AccountMetricsBase):
    """Create account metrics"""
    pass


class AccountMetricsResponse(AccountMetricsBase):
    """Account metrics response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountSettingsBase(BaseModel):
    """Base model for account settings"""
    account_id: int
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: str = "string"  # string, number, boolean, json


class AccountSettingsCreate(AccountSettingsBase):
    """Create account settings"""
    updated_by: int


class AccountSettingsUpdate(BaseModel):
    """Update account settings"""
    setting_key: str
    setting_value: Optional[str] = None
    setting_type: Optional[str] = None


class AccountSettingsResponse(AccountSettingsBase):
    """Account settings response"""
    id: int
    updated_by: Optional[int] = None
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountSwitchRequest(BaseModel):
    """Request to switch active account"""
    account_id: int


class AccountPerformanceRequest(BaseModel):
    """Request for account performance data"""
    account_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AccountPerformanceResponse(BaseModel):
    """Account performance response"""
    account_id: int
    account_name: str
    period_start: date
    period_end: date
    total_orders: int
    total_revenue: Decimal
    active_listings: int
    avg_conversion_rate: Decimal
    metrics_history: List[AccountMetricsResponse]


class BulkPermissionRequest(BaseModel):
    """Request to update permissions for multiple users"""
    account_id: int
    permissions: List[UserAccountPermissionCreate]


class BulkPermissionResponse(BaseModel):
    """Response for bulk permission updates"""
    account_id: int
    updated_count: int
    errors: List[str] = []