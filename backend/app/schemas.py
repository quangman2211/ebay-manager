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


class ListingFieldUpdate(BaseModel):
    field: str
    value: str

    class Config:
        schema_extra = {
            "example": {
                "field": "price",
                "value": "19.99"
            }
        }


class ListingBulkUpdate(BaseModel):
    updates: Dict[str, str]

    class Config:
        schema_extra = {
            "example": {
                "updates": {
                    "price": "19.99",
                    "quantity": "10",
                    "title": "Updated Product Title"
                }
            }
        }


class ListingUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "title": "New Product Title",
                "price": "29.99",
                "quantity": "15",
                "status": "active"
            }
        }


class ListingPerformanceMetrics(BaseModel):
    sell_through_rate: float
    watchers_count: int
    stock_status: str
    days_listed: int
    price_competitiveness: str

    class Config:
        schema_extra = {
            "example": {
                "sell_through_rate": 75.5,
                "watchers_count": 12,
                "stock_status": "in_stock",
                "days_listed": 45,
                "price_competitiveness": "competitive"
            }
        }


class CSVUpload(BaseModel):
    account_id: int
    data_type: DataType