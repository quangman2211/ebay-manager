# Phase 1: Core Infrastructure & Database Setup

## Overview
Establish foundational infrastructure following SOLID principles with PostgreSQL, FastAPI, and Docker containerization. This phase creates the backbone for all subsequent modules.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **Database Models**: Each model represents exactly one business entity
- **Repository Classes**: Each repository manages only one entity type
- **Service Classes**: Each service handles one business domain
- **Configuration Classes**: Separate configs for database, auth, cache, etc.

### Open/Closed Principle (OCP)
- **Repository Pattern**: Add new data sources without changing existing code
- **Service Interfaces**: Extend functionality through new implementations
- **Configuration System**: Environment-specific configs without code changes

### Liskov Substitution Principle (LSP)
- **Abstract Repository**: All implementations must honor the same contract
- **Service Interfaces**: Swappable implementations for testing and flexibility

### Interface Segregation Principle (ISP)
- **Focused Interfaces**: Separate read/write operations, specific query methods
- **Client-Specific**: Don't force clients to depend on unused methods

### Dependency Inversion Principle (DIP)
- **Dependency Injection**: All dependencies injected, not hard-coded
- **Abstract Dependencies**: Depend on interfaces, not concrete classes

## Database Schema Implementation

### Core Entity Models (Prisma Schema)

```prisma
// schema.prisma - Following Single Responsibility Principle

model Account {
  id          String   @id @default(cuid())
  ebay_username String @unique
  account_name String
  created_at  DateTime @default(now())
  updated_at  DateTime @updatedAt
  
  // Relationships
  users       UserAccount[]
  orders      Order[]
  listings    Listing[]
  customers   Customer[]
  
  @@map("accounts")
}

model User {
  id          String   @id @default(cuid())
  email       String   @unique
  password    String
  first_name  String
  last_name   String
  role        UserRole @default(USER)
  is_active   Boolean  @default(true)
  created_at  DateTime @default(now())
  updated_at  DateTime @updatedAt
  
  // Relationships
  accounts    UserAccount[]
  
  @@map("users")
}

model UserAccount {
  id         String  @id @default(cuid())
  user_id    String
  account_id String
  can_read   Boolean @default(true)
  can_write  Boolean @default(false)
  can_admin  Boolean @default(false)
  
  user       User    @relation(fields: [user_id], references: [id], onDelete: Cascade)
  account    Account @relation(fields: [account_id], references: [id], onDelete: Cascade)
  
  @@unique([user_id, account_id])
  @@map("user_accounts")
}

enum UserRole {
  ADMIN
  MANAGER
  USER
}

// Order entity - Single Responsibility: Manage order data only
model Order {
  id                String      @id @default(cuid())
  account_id        String
  ebay_order_id     String
  order_status      OrderStatus
  payment_status    PaymentStatus
  shipping_status   ShippingStatus
  buyer_name        String
  buyer_email       String?
  shipping_address  Json
  order_total       Decimal     @db.Decimal(10,2)
  order_date        DateTime
  tracking_number   String?
  created_at        DateTime    @default(now())
  updated_at        DateTime    @updatedAt
  
  // Relationships
  account           Account     @relation(fields: [account_id], references: [id])
  order_items       OrderItem[]
  
  @@unique([account_id, ebay_order_id])
  @@index([account_id, order_status])
  @@map("orders")
}

model OrderItem {
  id          String  @id @default(cuid())
  order_id    String
  listing_id  String?
  item_title  String
  quantity    Int
  price       Decimal @db.Decimal(10,2)
  created_at  DateTime @default(now())
  
  // Relationships
  order       Order   @relation(fields: [order_id], references: [id], onDelete: Cascade)
  listing     Listing? @relation(fields: [listing_id], references: [id])
  
  @@map("order_items")
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
  RETURNED
}

enum PaymentStatus {
  PENDING
  PAID
  FAILED
  REFUNDED
}

enum ShippingStatus {
  NOT_SHIPPED
  PROCESSING
  SHIPPED
  DELIVERED
  RETURNED
}
```

### Repository Pattern Implementation

#### Abstract Repository Interface
```python
# app/repositories/base.py - Interface Segregation Principle
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from uuid import UUID

T = TypeVar('T')

class IReadRepository(Generic[T], ABC):
    """Read-only operations interface"""
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod  
    async def count(self) -> int:
        pass

class IWriteRepository(Generic[T], ABC):
    """Write operations interface"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

class IRepository(IReadRepository[T], IWriteRepository[T], ABC):
    """Combined interface for full CRUD operations"""
    pass
```

#### Account Repository Implementation
```python
# app/repositories/account.py - Single Responsibility Principle
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.base import IRepository
from app.models.account import Account

class AccountRepository(IRepository[Account]):
    """Handles all Account data access operations"""
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: UUID) -> Optional[Account]:
        """Get account by ID - Single responsibility: account retrieval"""
        result = await self._session.execute(
            select(Account).where(Account.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_ebay_username(self, ebay_username: str) -> Optional[Account]:
        """Get account by eBay username"""
        result = await self._session.execute(
            select(Account).where(Account.ebay_username == ebay_username)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Account]:
        """Get all accounts with pagination"""
        result = await self._session.execute(
            select(Account).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def count(self) -> int:
        """Count total accounts"""
        result = await self._session.execute(
            select(func.count(Account.id))
        )
        return result.scalar()
    
    async def create(self, account: Account) -> Account:
        """Create new account"""
        self._session.add(account)
        await self._session.commit()
        await self._session.refresh(account)
        return account
    
    async def update(self, account: Account) -> Account:
        """Update existing account"""
        await self._session.commit()
        await self._session.refresh(account)
        return account
    
    async def delete(self, id: UUID) -> bool:
        """Delete account by ID"""
        account = await self.get_by_id(id)
        if account:
            await self._session.delete(account)
            await self._session.commit()
            return True
        return False
    
    async def get_user_accounts(self, user_id: UUID) -> List[Account]:
        """Get all accounts accessible by user"""
        result = await self._session.execute(
            select(Account)
            .join(UserAccount)
            .where(UserAccount.user_id == user_id)
        )
        return result.scalars().all()
```

## FastAPI Application Structure

### Dependency Injection System
```python
# app/dependencies.py - Dependency Inversion Principle
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db_session
from app.repositories.account import AccountRepository
from app.repositories.user import UserRepository
from app.services.account_service import AccountService

async def get_account_repository(session: AsyncSession = Depends(get_db_session)) -> AccountRepository:
    """Dependency injection for Account Repository"""
    return AccountRepository(session)

async def get_account_service(
    repo: AccountRepository = Depends(get_account_repository)
) -> AccountService:
    """Dependency injection for Account Service"""
    return AccountService(repo)
```

### Service Layer Implementation
```python
# app/services/account_service.py - Single Responsibility + Open/Closed
from typing import List, Optional
from uuid import UUID
from app.repositories.account import AccountRepository
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate

class AccountService:
    """Business logic for Account management - Single Responsibility"""
    
    def __init__(self, account_repo: AccountRepository):
        self._account_repo = account_repo
    
    async def create_account(self, account_data: AccountCreate) -> Account:
        """Create new eBay account with validation"""
        # Business logic: Validate unique eBay username
        existing = await self._account_repo.get_by_ebay_username(
            account_data.ebay_username
        )
        if existing:
            raise ValueError(f"Account with eBay username {account_data.ebay_username} already exists")
        
        account = Account(**account_data.dict())
        return await self._account_repo.create(account)
    
    async def get_account(self, account_id: UUID) -> Optional[Account]:
        """Get account by ID"""
        return await self._account_repo.get_by_id(account_id)
    
    async def update_account(self, account_id: UUID, account_data: AccountUpdate) -> Account:
        """Update account with validation"""
        account = await self._account_repo.get_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Apply updates
        for field, value in account_data.dict(exclude_unset=True).items():
            setattr(account, field, value)
        
        return await self._account_repo.update(account)
    
    async def delete_account(self, account_id: UUID) -> bool:
        """Delete account with business rules"""
        # Business logic: Check if account has active orders
        # This would be extended when Order module is implemented
        return await self._account_repo.delete(account_id)
    
    async def get_user_accounts(self, user_id: UUID) -> List[Account]:
        """Get all accounts accessible by user"""
        return await self._account_repo.get_user_accounts(user_id)
```

## Docker Configuration

### Multi-Service Docker Compose
```yaml
# docker-compose.yml - Separation of Concerns
version: '3.8'

services:
  # Database Service - Single Responsibility: Data persistence
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: ebay_management
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Cache Service - Single Responsibility: Caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Backend API Service - Single Responsibility: API layer
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/ebay_management
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app
      - ./csv_imports:/app/csv_imports
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Task Queue Worker - Single Responsibility: Background processing
  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/ebay_management
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app
      - ./csv_imports:/app/csv_imports
    command: celery -A app.celery worker --loglevel=info

  # Task Scheduler - Single Responsibility: Job scheduling
  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/ebay_management
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app
    command: celery -A app.celery beat --loglevel=info

volumes:
  postgres_data:
  redis_data:
```

### Application Dockerfile
```dockerfile
# Dockerfile - Single Responsibility: Container setup
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY ./app ./app

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration Management

### Environment Configuration
```python
# app/config.py - Single Responsibility: Configuration management
from pydantic import BaseSettings
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration - Single Responsibility"""
    url: str
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
    class Config:
        env_prefix = "DATABASE_"

class RedisSettings(BaseSettings):
    """Redis configuration - Single Responsibility"""
    url: str
    max_connections: int = 100
    
    class Config:
        env_prefix = "REDIS_"

class SecuritySettings(BaseSettings):
    """Security configuration - Single Responsibility"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_prefix = "SECURITY_"

class Settings(BaseSettings):
    """Main application settings"""
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    
    debug: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
```

## Implementation Tasks

### Task 1: Database Setup
1. **Create Prisma Schema**
   - Define core entities: Account, User, UserAccount
   - Set up relationships and indexes
   - Configure database constraints

2. **Initialize Database**
   - Generate Prisma client
   - Run database migrations
   - Seed initial data

3. **Test Database Connection**
   - Verify PostgreSQL connectivity
   - Test CRUD operations
   - Validate relationships

### Task 2: Repository Pattern Implementation
1. **Create Base Interfaces**
   - Define IReadRepository interface
   - Define IWriteRepository interface
   - Ensure Interface Segregation

2. **Implement Concrete Repositories**
   - AccountRepository with full CRUD
   - UserRepository with authentication methods
   - Ensure Single Responsibility per class

3. **Add Repository Tests**
   - Unit tests for each repository method
   - Integration tests with real database
   - Mock database for fast tests

### Task 3: Service Layer Implementation
1. **Create Service Classes**
   - AccountService for business logic
   - UserService for user management
   - Ensure Single Responsibility

2. **Implement Business Rules**
   - Account validation logic
   - User permission checks
   - Data consistency rules

3. **Add Service Tests**
   - Unit tests with mocked repositories
   - Business logic validation tests
   - Error handling tests

### Task 4: FastAPI Application Setup
1. **Create Application Structure**
   - Main FastAPI app
   - Router configuration
   - Middleware setup

2. **Implement Dependency Injection**
   - Repository dependency providers
   - Service dependency providers
   - Database session management

3. **Add Health Checks**
   - Database connectivity check
   - Redis connectivity check
   - Service readiness endpoints

### Task 5: Docker Configuration
1. **Setup Multi-Service Environment**
   - PostgreSQL with proper configuration
   - Redis for caching and queues
   - FastAPI application container

2. **Configure Networking**
   - Service-to-service communication
   - Port exposing strategy
   - Volume mounting for development

3. **Add Health Monitoring**
   - Container health checks
   - Service dependency management
   - Graceful shutdown handling

## Testing Strategy

### Unit Testing Requirements
- **Repository Tests**: Mock database operations
- **Service Tests**: Mock repository dependencies  
- **Dependency Injection Tests**: Verify proper wiring
- **Configuration Tests**: Validate settings loading

### Integration Testing Requirements
- **Database Integration**: Real PostgreSQL operations
- **Service Integration**: End-to-end business logic
- **API Integration**: HTTP endpoint testing

### Performance Testing
- **Database Query Performance**: <50ms for single entity queries
- **Connection Pool Management**: Handle 100+ concurrent connections
- **Memory Usage**: <500MB per container under normal load

## Quality Gates

### Code Quality Checklist
- [ ] All classes follow Single Responsibility Principle
- [ ] Repository pattern properly implements Interface Segregation
- [ ] Dependency Injection used throughout (Dependency Inversion)
- [ ] No business logic in repository classes
- [ ] No data access logic in service classes
- [ ] All dependencies are abstracted via interfaces
- [ ] No hard-coded configuration values
- [ ] Proper error handling and logging

### Performance Requirements
- [ ] Database migrations complete in <30 seconds
- [ ] Container startup time <60 seconds
- [ ] API response time <200ms for standard operations
- [ ] Database connection pool efficiently managed

### Security Requirements
- [ ] Database credentials stored in environment variables
- [ ] No sensitive data in logs
- [ ] Proper database connection encryption
- [ ] Input validation for all external data

## Refactoring Guidelines

### When to Refactor
- **Adding New Entity Types**: Extend repository pattern
- **New Data Sources**: Implement new repository implementations
- **Performance Issues**: Add caching layer without changing interfaces
- **Security Requirements**: Add middleware without changing core logic

### How to Extend (Open/Closed Principle)
1. **New Repository**: Implement IRepository interface
2. **New Service**: Depend on repository abstraction
3. **New Configuration**: Extend Settings class
4. **New Validation**: Add to service layer, not repository

---
**Next Phase**: Authentication & Security implementation builds upon this infrastructure foundation.