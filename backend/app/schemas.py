from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
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

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class AccountBase(BaseModel):
    ebay_username: str
    name: str
    is_active: bool = True


class AccountCreate(AccountBase):
    user_id: Optional[int] = None


class AccountResponse(AccountBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    item_id: str
    csv_row: Dict[str, Any]
    order_status: Optional[OrderStatusResponse] = None
    account_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ListingResponse(BaseModel):
    id: int
    item_id: str
    csv_row: Dict[str, Any]
    account_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CSVUpload(BaseModel):
    account_id: int
    data_type: DataType


# Profile-related schemas
class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    phone: Optional[str] = None


class ProfileResponse(UserResponse):
    bio: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None


class UserActivityResponse(BaseModel):
    id: int
    activity_type: str
    description: Optional[str] = None
    activity_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    accounts_managed: int
    orders_processed: int
    listings_created: int
    recent_logins: int
    total_csv_uploads: int
    last_activity: Optional[datetime] = None