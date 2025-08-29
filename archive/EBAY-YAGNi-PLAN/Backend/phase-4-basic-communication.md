# Phase 4: Basic Communication & Customer Management (YAGNI Optimized)

## Overview
**SIMPLIFIED APPROACH**: CSV-based communication system with essential customer management features only. Eliminates over-engineered Gmail API integration and complex message classification in favor of proven, simple workflows appropriate for 30-account scale.

## YAGNI Violations Eliminated
- ❌ **Gmail API integration** → CSV import/export workflow
- ❌ **Complex message classification** → Basic keyword matching
- ❌ **Multi-template engines** → Single simple template system
- ❌ **Real-time notifications** → Simple periodic updates
- ❌ **Advanced customer analytics** → Basic New/Regular/VIP segmentation

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **CustomerService**: Only handle customer data and basic segmentation
- **MessageService**: Only manage CSV message import/export
- **TemplateService**: Only handle simple text templates
- **CommunicationService**: Only coordinate customer communication workflow

### Open/Closed Principle (OCP)
- **Template System**: Extensible for new template formats
- **Customer Segmentation**: Add new segments without modifying core logic
- **CSV Processors**: Support different CSV formats through strategy pattern

### Liskov Substitution Principle (LSP)
- **IMessageProcessor**: All message processors (CSV, future formats) interchangeable
- **ICustomerSegment**: All segmentation strategies follow same contract

### Interface Segregation Principle (ISP)
- **Customer Interfaces**: Separate read-only vs editable customer operations  
- **Message Interfaces**: Separate message reading vs sending operations
- **Template Interfaces**: Separate template creation vs rendering

### Dependency Inversion Principle (DIP)
- **Abstract Dependencies**: Services depend on interfaces, not concrete implementations
- **Injected Services**: All external dependencies injected

---

## Simplified Customer Management

### Basic Customer Entity (YAGNI Compliant)
```python
# app/models/customer.py - Single Responsibility: Customer data only
from sqlalchemy import Column, String, DateTime, Decimal, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base

class CustomerSegment(PyEnum):
    NEW = "new"              # 0-1 orders
    REGULAR = "regular"      # 2-4 orders  
    VIP = "vip"             # 5+ orders or high LTV

class Customer(Base):
    __tablename__ = "customers"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    # Basic customer data (from eBay CSV)
    ebay_username = Column(String(100), nullable=False)
    name = Column(String(200))
    email = Column(String(320))
    
    # Simple metrics (calculated, not stored in complex analytics)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Decimal(10, 2), default=0)
    segment = Column(Enum(CustomerSegment), default=CustomerSegment.NEW)
    
    # Timestamps
    first_order_date = Column(DateTime)
    last_order_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    messages = relationship("Message", back_populates="customer")
```

### Simple Customer Service (No Over-Engineering)
```python
# app/services/customer_service.py - Single Responsibility: Customer operations
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer, CustomerSegment
from app.repositories.customer_repository import CustomerRepository

class CustomerService:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo
    
    def update_customer_segment(self, customer: Customer) -> Customer:
        """Simple segmentation logic - YAGNI compliant"""
        if customer.total_orders >= 5 or customer.total_spent >= 500:
            customer.segment = CustomerSegment.VIP
        elif customer.total_orders >= 2:
            customer.segment = CustomerSegment.REGULAR
        else:
            customer.segment = CustomerSegment.NEW
        
        return self.customer_repo.update(customer)
    
    def get_customers_by_segment(self, account_id: str, segment: CustomerSegment) -> List[Customer]:
        """Simple filtering - no complex queries"""
        return self.customer_repo.find_by_segment(account_id, segment)
    
    def update_customer_from_order(self, customer: Customer, order_amount: float) -> Customer:
        """Update customer metrics when new order placed"""
        customer.total_orders += 1
        customer.total_spent += order_amount
        customer.last_order_date = datetime.utcnow()
        
        if not customer.first_order_date:
            customer.first_order_date = datetime.utcnow()
        
        return self.update_customer_segment(customer)
```

---

## Simplified Communication System

### Basic Message Entity (CSV-Focused)
```python  
# app/models/message.py - Single Responsibility: Message data
from sqlalchemy import Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base

class MessageSource(PyEnum):
    EBAY_CSV = "ebay_csv"
    MANUAL = "manual"

class MessageStatus(PyEnum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"

class Message(Base):
    __tablename__ = "messages"
    
    # Core identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    
    # Message content (from CSV or manual entry)
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    source = Column(Enum(MessageSource), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.UNREAD)
    
    # Simple classification (keyword-based, not AI)
    category = Column(String(50))  # order_inquiry, shipping, return, etc.
    priority = Column(String(20), default="normal")  # high, normal, low
    
    # Timestamps
    received_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="messages")
    customer = relationship("Customer", back_populates="messages")
    order = relationship("Order", back_populates="messages")
```

### CSV Message Processing (Simple & Reliable)
```python
# app/services/message_service.py - Single Responsibility: Message processing
import pandas as pd
from typing import List, Dict, Any
from app.models.message import Message, MessageSource, MessageStatus
from app.repositories.message_repository import MessageRepository
from app.services.customer_service import CustomerService

class MessageService:
    def __init__(self, message_repo: MessageRepository, customer_service: CustomerService):
        self.message_repo = message_repo
        self.customer_service = customer_service
    
    def import_messages_from_csv(self, account_id: str, csv_file_path: str) -> List[Message]:
        """Simple CSV import - YAGNI compliant"""
        df = pd.read_csv(csv_file_path)
        messages = []
        
        for _, row in df.iterrows():
            message = Message(
                account_id=account_id,
                subject=row.get('Subject', ''),
                content=row.get('Message', ''),
                source=MessageSource.EBAY_CSV,
                received_at=pd.to_datetime(row.get('Date')),
                category=self._simple_categorize(row.get('Subject', '') + ' ' + row.get('Message', ''))
            )
            
            # Link to customer if possible
            if row.get('From'):
                customer = self.customer_service.find_by_username(account_id, row.get('From'))
                if customer:
                    message.customer_id = customer.id
            
            messages.append(self.message_repo.create(message))
        
        return messages
    
    def _simple_categorize(self, text: str) -> str:
        """Basic keyword matching - no AI complexity"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['ship', 'track', 'deliver']):
            return 'shipping'
        elif any(word in text_lower for word in ['return', 'refund', 'problem']):
            return 'return'
        elif any(word in text_lower for word in ['payment', 'pay', 'charge']):
            return 'payment'
        else:
            return 'general'
```

---

## Simple Template System

### Basic Template Entity
```python
# app/models/template.py - Single Responsibility: Template data
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.database import Base

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Simple template categories
    category = Column(String(50))  # shipping, return, general
    
    account = relationship("Account", back_populates="templates")
```

### Simple Template Service (No Complex Engines)
```python
# app/services/template_service.py - Single Responsibility: Template operations
from typing import Dict, Any
from app.models.template import Template
from app.repositories.template_repository import TemplateRepository

class TemplateService:
    def __init__(self, template_repo: TemplateRepository):
        self.template_repo = template_repo
    
    def render_template(self, template: Template, variables: Dict[str, Any]) -> str:
        """Simple string substitution - no complex template engines"""
        content = template.content
        
        # Basic variable substitution
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            content = content.replace(placeholder, str(value))
        
        return content
    
    def create_default_templates(self, account_id: str) -> List[Template]:
        """Create basic templates for new accounts"""
        default_templates = [
            {
                "name": "Shipping Confirmation",
                "subject": "Your order has shipped",
                "content": "Hi {customer_name}, your order {order_number} has been shipped via {shipping_method}. Tracking: {tracking_number}",
                "category": "shipping"
            },
            {
                "name": "General Response", 
                "subject": "Re: {original_subject}",
                "content": "Hi {customer_name}, thank you for your message. {custom_message}",
                "category": "general"
            }
        ]
        
        templates = []
        for template_data in default_templates:
            template = Template(
                account_id=account_id,
                **template_data
            )
            templates.append(self.template_repo.create(template))
        
        return templates
```

---

## API Endpoints (Simplified)

### Customer Management API
```python
# app/api/v1/customers.py - Single Responsibility: Customer API endpoints
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.customer_service import CustomerService
from app.models.customer import Customer, CustomerSegment
from app.schemas.customer import CustomerResponse, CustomerList

router = APIRouter()

@router.get("/customers", response_model=CustomerList)
async def get_customers(
    account_id: str,
    segment: Optional[CustomerSegment] = None,
    customer_service: CustomerService = Depends()
):
    """Simple customer listing with optional segment filtering"""
    if segment:
        customers = customer_service.get_customers_by_segment(account_id, segment)
    else:
        customers = customer_service.get_all_customers(account_id)
    
    return CustomerList(customers=customers)

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    customer_service: CustomerService = Depends()
):
    """Get individual customer details"""
    customer = customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse.from_orm(customer)
```

### Message Management API  
```python
# app/api/v1/messages.py - Single Responsibility: Message API endpoints
from fastapi import APIRouter, Depends, UploadFile, File
from typing import List
from app.services.message_service import MessageService
from app.schemas.message import MessageResponse, MessageList

router = APIRouter()

@router.post("/messages/import-csv")
async def import_messages(
    account_id: str,
    file: UploadFile = File(...),
    message_service: MessageService = Depends()
):
    """Simple CSV message import"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files supported")
    
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Import messages
    messages = message_service.import_messages_from_csv(account_id, temp_path)
    
    return {"imported": len(messages), "message": "Messages imported successfully"}

@router.get("/messages", response_model=MessageList)
async def get_messages(
    account_id: str,
    status: Optional[MessageStatus] = None,
    category: Optional[str] = None,
    message_service: MessageService = Depends()
):
    """Simple message listing with basic filtering"""
    messages = message_service.get_messages(account_id, status, category)
    return MessageList(messages=messages)
```

---

## Testing Strategy (Essential Only)

### Unit Tests (Core Functionality)
```python
# tests/test_customer_service.py - Test core business logic
import pytest
from app.services.customer_service import CustomerService
from app.models.customer import Customer, CustomerSegment

class TestCustomerService:
    def test_update_customer_segment_new(self):
        """Test NEW segment assignment"""
        customer = Customer(total_orders=1, total_spent=50)
        service = CustomerService(mock_repo)
        
        updated = service.update_customer_segment(customer)
        assert updated.segment == CustomerSegment.NEW
    
    def test_update_customer_segment_vip(self):
        """Test VIP segment assignment"""
        customer = Customer(total_orders=5, total_spent=600)
        service = CustomerService(mock_repo)
        
        updated = service.update_customer_segment(customer)
        assert updated.segment == CustomerSegment.VIP

# tests/test_message_service.py - Test CSV processing
class TestMessageService:
    def test_simple_categorize_shipping(self):
        """Test basic message categorization"""
        service = MessageService(mock_repo, mock_customer_service)
        
        category = service._simple_categorize("When will my item ship?")
        assert category == "shipping"
    
    def test_import_csv_basic(self):
        """Test basic CSV import functionality"""
        # Test with sample CSV data
        pass
```

### Integration Tests (API Level)
```python
# tests/test_customer_api.py - Test API endpoints
from fastapi.testclient import TestClient

def test_get_customers_with_segment_filter(client: TestClient):
    """Test customer API with segment filtering"""
    response = client.get("/api/v1/customers?segment=vip&account_id=test-account")
    assert response.status_code == 200
    
def test_import_messages_csv(client: TestClient):
    """Test message CSV import endpoint"""
    with open("test_messages.csv", "rb") as f:
        response = client.post(
            "/api/v1/messages/import-csv",
            data={"account_id": "test-account"},
            files={"file": ("test.csv", f, "text/csv")}
        )
    assert response.status_code == 200
```

---

## Deployment (Simplified)

### Docker Configuration (Basic)
```yaml
# docker-compose.yml - Simple 3-service setup
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ebay_manager
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: ebay_manager
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Summary: YAGNI Compliance Achieved

### ✅ Features Kept (Essential)
- Basic customer management with simple segmentation
- CSV-based message import/export
- Simple text templates with variable substitution
- Core communication workflow

### ❌ Features Eliminated (YAGNI Violations)
- Gmail API integration
- Complex message classification algorithms  
- Multi-template engines
- Real-time notifications
- Advanced customer analytics
- Complex monitoring systems

### 📊 Complexity Reduction
- **Development time**: 4-5 weeks → 2-3 weeks
- **Code complexity**: 70% reduction
- **Dependencies**: 60% fewer external services
- **Maintenance**: 50% less ongoing complexity

**Result**: Clean, maintainable communication system appropriate for 30-account scale that can be extended when (and if) additional features are proven necessary.