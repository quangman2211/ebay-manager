from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import logging

from app.database import get_db
from app.models import User, Account, CSVData, OrderStatus
from app.schemas import (
    UserCreate, UserResponse, Token, AccountCreate, AccountResponse,
    CSVUpload, OrderResponse, ListingResponse, OrderStatusUpdate, DataType,
    ListingFieldUpdate, ListingBulkUpdate, ListingUpdateRequest, ListingPerformanceMetrics
)
from app.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash
)
from app.config import settings
from app.csv_service import CSVProcessor
from app.services.listing_service import create_listing_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="eBay Manager API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3003", "http://localhost:8003"],  # React frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/v1/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/accounts", response_model=List[AccountResponse])
def get_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "admin":
        # Admin can see all accounts
        accounts = db.query(Account).filter(Account.is_active == True).all()
    else:
        # Staff can only see their assigned accounts
        accounts = db.query(Account).filter(
            Account.user_id == current_user.id,
            Account.is_active == True
        ).all()
    return accounts


@app.post("/api/v1/accounts", response_model=AccountResponse)
def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Only admin can create accounts for others
    if current_user.role != "admin" and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create account for other users"
        )
    
    # If user_id not provided, assign to current user
    if not account.user_id:
        account.user_id = current_user.id
    
    db_account = Account(
        user_id=account.user_id,
        ebay_username=account.ebay_username,
        name=account.name,
        is_active=account.is_active
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@app.post("/api/v1/csv/upload")
def upload_csv(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    data_type: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate data_type
        data_type_enum = DataType(data_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data_type: {data_type}"
        )
    
    # Check if user has access to this account
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if current_user.role != "admin" and account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this account"
        )
    
    # Read file content
    try:
        content = file.file.read().decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    
    # Process CSV
    records, errors = CSVProcessor.process_csv_file(content, data_type_enum)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV processing errors: {'; '.join(errors)}"
        )
    
    # Check for duplicates in the upload
    duplicate_errors = CSVProcessor.check_duplicates(records, data_type_enum)
    if duplicate_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duplicate data errors: {'; '.join(duplicate_errors)}"
        )
    
    # Process each record
    inserted_count = 0
    duplicate_count = 0
    
    for record in records:
        item_id = CSVProcessor.extract_item_id(record, data_type_enum)
        
        # Check if record already exists
        existing_record = db.query(CSVData).filter(
            CSVData.account_id == account_id,
            CSVData.data_type == data_type_enum.value,
            CSVData.item_id == item_id
        ).first()
        
        if existing_record:
            duplicate_count += 1
            continue
        
        # Create new CSV data record
        csv_data = CSVData(
            account_id=account_id,
            data_type=data_type_enum.value,
            csv_row=record,
            item_id=item_id
        )
        db.add(csv_data)
        
        # If it's an order, create initial status
        if data_type_enum == DataType.ORDER:
            db.flush()  # Get the CSV data ID
            order_status = OrderStatus(
                csv_data_id=csv_data.id,
                status="pending",
                updated_by=current_user.id
            )
            db.add(order_status)
        
        inserted_count += 1
    
    db.commit()
    
    return {
        "message": "CSV uploaded successfully",
        "inserted_count": inserted_count,
        "duplicate_count": duplicate_count,
        "total_records": len(records)
    }


@app.get("/api/v1/orders", response_model=List[OrderResponse])
def get_orders(
    account_id: int = None,
    status: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    
    query = db.query(CSVData).filter(CSVData.data_type == "order").options(joinedload(CSVData.order_status))
    
    # Filter by account access
    if current_user.role != "admin":
        user_account_ids = [acc.id for acc in current_user.accounts if acc.is_active]
        query = query.filter(CSVData.account_id.in_(user_account_ids))
    
    if account_id:
        query = query.filter(CSVData.account_id == account_id)
    
    orders = query.all()
    
    # Apply status filter if provided
    if status:
        orders = [order for order in orders if order.order_status and order.order_status.status == status]
    
    return orders


@app.get("/api/v1/listings", response_model=List[ListingResponse])
def get_listings(
    account_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(CSVData).filter(CSVData.data_type == "listing")
    
    # Filter by account access
    if current_user.role != "admin":
        user_account_ids = [acc.id for acc in current_user.accounts if acc.is_active]
        query = query.filter(CSVData.account_id.in_(user_account_ids))
    
    if account_id:
        query = query.filter(CSVData.account_id == account_id)
    
    listings = query.all()
    return listings


@app.put("/api/v1/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get the order
    order = db.query(CSVData).filter(
        CSVData.id == order_id,
        CSVData.data_type == "order"
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permissions
    if current_user.role != "admin" and order.account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this order"
        )
    
    # Update or create order status
    if order.order_status:
        order.order_status.status = status_update.status.value
        order.order_status.updated_by = current_user.id
    else:
        order_status = OrderStatus(
            csv_data_id=order_id,
            status=status_update.status.value,
            updated_by=current_user.id
        )
        db.add(order_status)
    
    db.commit()
    return {"message": "Order status updated successfully"}


@app.get("/api/v1/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/api/v1/search")
def global_search(
    q: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Global search across orders, listings, and items
    """
    if not q or len(q) < 2:
        return []
    
    search_query = f"%{q.lower()}%"
    results = []
    
    # Search in orders
    order_rows = db.query(CSVData).filter(
        CSVData.data_type == "order"
    ).all()
    
    for order in order_rows:
        csv_data = order.csv_row
        # Search in Order #, Item #, Customer, or Item name
        if (q.lower() in csv_data.get("Order #", "").lower() or
            q.lower() in csv_data.get("Item #", "").lower() or  
            q.lower() in csv_data.get("Customer", "").lower() or
            q.lower() in csv_data.get("Item", "").lower()):
            
            results.append({
                "type": "order",
                "id": csv_data.get("Order #", order.item_id),
                "title": f"Order {csv_data.get('Order #', 'N/A')}",
                "subtitle": f"{csv_data.get('Customer', 'N/A')} - {csv_data.get('Item', 'N/A')}",
                "status": csv_data.get("Status", "pending")
            })
    
    # Search in listings
    listing_rows = db.query(CSVData).filter(
        CSVData.data_type == "listing"
    ).all()
    
    for listing in listing_rows:
        csv_data = listing.csv_row
        # Search in Item # or Title
        if (q.lower() in csv_data.get("Item #", "").lower() or
            q.lower() in csv_data.get("Title", "").lower()):
            
            results.append({
                "type": "listing",
                "id": csv_data.get("Item #", listing.item_id),
                "title": csv_data.get("Title", "N/A"),
                "subtitle": f"Item #{csv_data.get('Item #', 'N/A')} - {csv_data.get('Price', '$0')}",
                "status": csv_data.get("Status", "active")
            })
    
    # Limit results to 20 items
    return results[:20]


# Listing Management Endpoints
@app.get("/api/v1/listings/{listing_id}", response_model=ListingResponse)
def get_listing_by_id(
    listing_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific listing by ID with permission check"""
    listing_service = create_listing_service(db)
    try:
        listing = listing_service.get_listing(listing_id, current_user)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return listing
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.put("/api/v1/listings/{listing_id}/field")
def update_listing_field(
    listing_id: int,
    field_update: ListingFieldUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a single field of a listing"""
    listing_service = create_listing_service(db)
    try:
        updated_listing = listing_service.update_listing_field(
            listing_id, field_update.field, field_update.value, current_user
        )
        return {"message": f"Field '{field_update.field}' updated successfully", "listing_id": listing_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.put("/api/v1/listings/{listing_id}/bulk")
def update_listing_bulk(
    listing_id: int,
    bulk_update: ListingBulkUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update multiple fields of a listing at once"""
    listing_service = create_listing_service(db)
    try:
        updated_listing = listing_service.update_listing_bulk_fields(
            listing_id, bulk_update.updates, current_user
        )
        return {"message": "Listing updated successfully", "listing_id": listing_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.put("/api/v1/listings/{listing_id}")
def update_listing(
    listing_id: int,
    update_request: ListingUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update listing with multiple optional fields"""
    listing_service = create_listing_service(db)
    
    # Convert ListingUpdateRequest to dict, filtering out None values
    updates = {k: v for k, v in update_request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        updated_listing = listing_service.update_listing_bulk_fields(
            listing_id, updates, current_user
        )
        return {"message": "Listing updated successfully", "listing_id": listing_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.get("/api/v1/listings/{listing_id}/metrics", response_model=ListingPerformanceMetrics)
def get_listing_performance_metrics(
    listing_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific listing"""
    listing_service = create_listing_service(db)
    try:
        metrics = listing_service.get_listing_performance_metrics(listing_id, current_user)
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)