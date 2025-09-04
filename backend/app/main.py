from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import logging

from app.database import get_db
from app.models import User, Account, CSVData, OrderStatus, UserAccountPermission, AccountSettings
from app.schemas import (
    UserCreate, UserResponse, Token, AccountCreate, AccountResponse,
    CSVUpload, OrderResponse, ListingResponse, OrderStatusUpdate, DataType,
    # Sprint 7 schemas
    AccountUpdateRequest, EnhancedAccountResponse, UserAccountPermissionCreate,
    UserAccountPermissionUpdate, UserAccountPermissionResponse, AccountSettingsCreate,
    AccountSettingsUpdate, AccountSettingsResponse, BulkPermissionRequest,
    BulkPermissionResponse, AccountSwitchRequest, PermissionLevel
)
from app.services import AccountService, PermissionService, PermissionError, AccountPermissionError
from app.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash
)
from app.config import settings
from app.csv_service import CSVProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="eBay Manager API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],  # React frontends
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


@app.post("/api/v1/accounts/suggest")
def suggest_accounts_for_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    PHASE 2.3: Suggest matching accounts based on detected username from CSV
    This endpoint analyzes CSV content/filename and suggests matching accounts
    """
    try:
        # Read file content for username detection
        content = file.file.read().decode('utf-8')
        file.file.seek(0)  # Reset file pointer
        
        # Detect username from content and filename
        detected_username = CSVProcessor.detect_platform_username(
            content,
            filename=file.filename or "",
            account_type="ebay"  # Default to eBay for now
        )
        
        # Get user's accessible accounts
        if current_user.role == "admin":
            accounts = db.query(Account).filter(Account.is_active == True).all()
        else:
            accounts = db.query(Account).filter(
                Account.user_id == current_user.id,
                Account.is_active == True
            ).all()
        
        # Find matching accounts
        suggested_accounts = []
        exact_matches = []
        partial_matches = []
        
        if detected_username:
            for account in accounts:
                # Exact match with platform_username
                if account.platform_username == detected_username:
                    exact_matches.append(account)
                # Partial match with platform_username or name
                elif (detected_username.lower() in (account.platform_username or "").lower() or
                      detected_username.lower() in account.name.lower()):
                    partial_matches.append(account)
        
        # Prioritize exact matches first, then partial matches
        suggested_accounts = exact_matches + partial_matches
        
        return {
            "detected_username": detected_username,
            "suggested_accounts": [
                {
                    "id": acc.id,
                    "name": acc.name,
                    "platform_username": acc.platform_username,
                    "match_type": "exact" if acc in exact_matches else "partial"
                }
                for acc in suggested_accounts[:5]  # Limit to top 5 suggestions
            ],
            "total_suggestions": len(suggested_accounts)
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing CSV file: {str(e)}"
        )


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
        platform_username=account.platform_username,
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
    
    # PHASE 2.1-2.2: eBay username detection with filename support
    detected_username = CSVProcessor.detect_platform_username(
        content, 
        filename=file.filename or "",
        account_type=account.account_type or "ebay"
    )
    if detected_username and not account.platform_username:
        # Auto-update account with detected username
        account.platform_username = detected_username
        db.commit()
        logger.info(f"Auto-detected and saved platform username: {detected_username} for account {account.name}")
    
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
    
    # PHASE 2.1: Enhanced response with detected username info  
    response = {
        "message": "CSV uploaded successfully",
        "inserted_count": inserted_count,
        "duplicate_count": duplicate_count,
        "total_records": len(records)
    }
    
    # Include detected username in response if found
    if detected_username:
        response["detected_platform_username"] = detected_username
        response["message"] += f" (Auto-detected seller: {detected_username})"
    
    return response


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


# =============================================================================
# Sprint 7: Enhanced Account Management API Endpoints
# =============================================================================

@app.put("/api/v1/accounts/{account_id}", response_model=AccountResponse)
def update_account_details(
    account_id: int,
    update_request: AccountUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update account details with permission validation"""
    try:
        account_service = AccountService(db)
        updated_account = account_service.update_account(account_id, update_request, current_user)
        return updated_account
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/api/v1/accounts/{account_id}/details", response_model=EnhancedAccountResponse)
def get_account_details(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed account information with permissions and settings"""
    try:
        account_service = AccountService(db)
        account_details = account_service.get_account_details(account_id, current_user)
        return account_details
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete("/api/v1/accounts/{account_id}")
def deactivate_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate an account (soft delete)"""
    try:
        account_service = AccountService(db)
        account_service.deactivate_account(account_id, current_user)
        return {"message": "Account deactivated successfully"}
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.post("/api/v1/accounts/{account_id}/permissions", response_model=UserAccountPermissionResponse)
def create_user_permission(
    account_id: int,
    permission_request: UserAccountPermissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Grant permission to a user for specific account"""
    try:
        # Override account_id to ensure consistency
        permission_request.account_id = account_id
        
        permission_service = PermissionService(db)
        permission = permission_service.create_permission(permission_request, current_user)
        return permission
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.put("/api/v1/permissions/{permission_id}", response_model=UserAccountPermissionResponse)
def update_user_permission(
    permission_id: int,
    update_request: UserAccountPermissionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing user permission"""
    try:
        permission_service = PermissionService(db)
        permission = permission_service.update_permission(permission_id, update_request, current_user)
        return permission
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.delete("/api/v1/permissions/{permission_id}")
def revoke_user_permission(
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a user permission"""
    try:
        permission_service = PermissionService(db)
        permission_service.revoke_permission(permission_id, current_user)
        return {"message": "Permission revoked successfully"}
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/api/v1/accounts/{account_id}/permissions", response_model=List[UserAccountPermissionResponse])
def get_account_permissions(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific account"""
    try:
        permission_service = PermissionService(db)
        permissions = permission_service.get_account_permissions(account_id, current_user)
        return permissions
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@app.get("/api/v1/users/{user_id}/permissions", response_model=List[UserAccountPermissionResponse])
def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific user"""
    try:
        permission_service = PermissionService(db)
        permissions = permission_service.get_user_permissions(user_id, current_user)
        return permissions
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@app.post("/api/v1/accounts/{account_id}/permissions/bulk", response_model=BulkPermissionResponse)
def bulk_update_permissions(
    account_id: int,
    bulk_request: BulkPermissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update multiple permissions at once"""
    try:
        # Override account_id to ensure consistency
        bulk_request.account_id = account_id
        
        permission_service = PermissionService(db)
        result = permission_service.bulk_update_permissions(bulk_request, current_user)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/v1/accounts/{account_id}/settings", response_model=List[AccountSettingsResponse])
def get_account_settings(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all settings for an account"""
    try:
        account_service = AccountService(db)
        # Verify user has access to account
        account_service._get_account_with_permission_check(account_id, current_user, PermissionLevel.VIEW)
        
        settings = db.query(AccountSettings).filter(
            AccountSettings.account_id == account_id
        ).all()
        
        return settings
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.put("/api/v1/accounts/{account_id}/settings")
def update_account_settings(
    account_id: int,
    settings_updates: List[AccountSettingsUpdate],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update account settings"""
    try:
        account_service = AccountService(db)
        updated_settings = account_service.update_account_settings(
            account_id, settings_updates, current_user
        )
        return {
            "message": "Settings updated successfully",
            "updated_count": len(updated_settings)
        }
    except (PermissionError, AccountPermissionError) as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/v1/accounts/switch")
def switch_active_account(
    switch_request: AccountSwitchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Switch user's active account context"""
    try:
        permission_service = PermissionService(db)
        has_permission = permission_service.check_user_permission(
            current_user.id,
            switch_request.account_id,
            PermissionLevel.VIEW
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access this account"
            )
        
        # Get account details
        account = db.query(Account).filter(Account.id == switch_request.account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return {
            "message": "Account switched successfully",
            "active_account": {
                "id": account.id,
                "name": account.name,
                "platform_username": account.platform_username
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 403, 404) without modification
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)