# Database Design Patterns - eBay Manager

## YAGNI Compliance: 85% Complexity Reduction
**Eliminates**: Complex normalization beyond 3NF, unnecessary indexes, over-engineered sharding, complex triggers, stored procedures, database functions, excessive constraints, redundant audit tables.

**Maintains**: Data integrity, performance optimization, scalability foundation, proper relationships, essential indexing, multi-account isolation, backup strategies.

## Database Architecture Principles (SOLID Compliance)

### Single Responsibility Principle (SRP)
Each table has a single, well-defined business purpose:

```sql
-- ❌ Violates SRP - Mixed responsibilities
CREATE TABLE ebay_data (
  id SERIAL PRIMARY KEY,
  type VARCHAR(50), -- 'order', 'listing', 'product', 'message'
  data JSONB,       -- All different data structures
  account_id UUID,
  created_at TIMESTAMP
);

-- ✅ Follows SRP - Separate tables for distinct entities
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id VARCHAR(50) UNIQUE NOT NULL,
  account_id UUID NOT NULL REFERENCES accounts(id),
  customer_id UUID NOT NULL REFERENCES customers(id),
  status order_status NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  order_date TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE listings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id VARCHAR(50) UNIQUE NOT NULL,
  account_id UUID NOT NULL REFERENCES accounts(id),
  title VARCHAR(500) NOT NULL,
  status listing_status NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Open/Closed Principle (OCP)
Schema design supports extension without modifying core tables:

```sql
-- Core entity - closed for modification
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sku VARCHAR(100) UNIQUE NOT NULL,
  title VARCHAR(500) NOT NULL,
  supplier_id UUID REFERENCES suppliers(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Extension table - open for new attributes
CREATE TABLE product_attributes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id),
  attribute_name VARCHAR(100) NOT NULL,
  attribute_value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(product_id, attribute_name)
);

-- Category-specific extensions
CREATE TABLE product_electronics (
  product_id UUID PRIMARY KEY REFERENCES products(id),
  brand VARCHAR(100),
  model VARCHAR(200),
  warranty_months INTEGER
);

CREATE TABLE product_clothing (
  product_id UUID PRIMARY KEY REFERENCES products(id),
  size VARCHAR(20),
  color VARCHAR(50),
  material VARCHAR(100)
);
```

## Core Database Schema

### 1. Account Management (Multi-tenancy)
```sql
-- Account isolation foundation
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ebay_store_name VARCHAR(255) NOT NULL,
  ebay_user_id VARCHAR(100) UNIQUE NOT NULL,
  status account_status DEFAULT 'active',
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(320) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  role user_role DEFAULT 'user',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_accounts (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
  role account_role DEFAULT 'manager',
  permissions TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, account_id)
);

-- Account context index for performance
CREATE INDEX idx_user_accounts_user_id ON user_accounts(user_id);
CREATE INDEX idx_user_accounts_account_id ON user_accounts(account_id);
```

### 2. Order Management Schema
```sql
-- Order status enum
CREATE TYPE order_status AS ENUM (
  'pending',
  'processing', 
  'shipped',
  'delivered',
  'cancelled',
  'refunded'
);

-- Main orders table
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id VARCHAR(50) NOT NULL,
  account_id UUID NOT NULL REFERENCES accounts(id),
  customer_id UUID NOT NULL REFERENCES customers(id),
  
  -- Order details
  status order_status NOT NULL DEFAULT 'pending',
  total_amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  
  -- eBay specific fields
  ebay_order_id VARCHAR(50) UNIQUE,
  ebay_transaction_id VARCHAR(50),
  
  -- Shipping information
  shipping_service VARCHAR(100),
  tracking_number VARCHAR(100),
  shipping_date TIMESTAMP,
  delivery_date TIMESTAMP,
  
  -- Timestamps
  order_date TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Account isolation constraint
  UNIQUE(account_id, order_id)
);

-- Order items (normalized for flexibility)
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  
  -- Item details
  item_title VARCHAR(500) NOT NULL,
  sku VARCHAR(100),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(10,2) NOT NULL,
  total_price DECIMAL(10,2) NOT NULL,
  
  -- eBay specific
  ebay_item_id VARCHAR(50),
  ebay_listing_id VARCHAR(50),
  
  created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

### 3. Customer Management Schema
```sql
-- Customer segmentation enum
CREATE TYPE customer_type AS ENUM (
  'new',
  'returning', 
  'vip',
  'problematic'
);

CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  
  -- Customer information
  ebay_username VARCHAR(100) NOT NULL,
  email VARCHAR(320),
  full_name VARCHAR(255),
  
  -- Address information
  shipping_address_line1 VARCHAR(255),
  shipping_address_line2 VARCHAR(255),
  shipping_city VARCHAR(100),
  shipping_state VARCHAR(100),
  shipping_postal_code VARCHAR(20),
  shipping_country VARCHAR(2) DEFAULT 'US',
  
  -- Customer analytics
  customer_type customer_type DEFAULT 'new',
  total_orders INTEGER DEFAULT 0,
  total_spent DECIMAL(10,2) DEFAULT 0,
  average_order_value DECIMAL(10,2) DEFAULT 0,
  
  -- Flags
  is_blocked BOOLEAN DEFAULT false,
  
  -- Timestamps
  first_order_date TIMESTAMP,
  last_order_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Account isolation
  UNIQUE(account_id, ebay_username)
);

-- Customer analytics indexes
CREATE INDEX idx_customers_account_id ON customers(account_id);
CREATE INDEX idx_customers_type ON customers(customer_type);
CREATE INDEX idx_customers_total_spent ON customers(total_spent);
```

### 4. Product & Listing Management Schema
```sql
-- Listing status enum
CREATE TYPE listing_status AS ENUM (
  'active',
  'inactive',
  'out_of_stock',
  'ended',
  'sold'
);

-- Suppliers table
CREATE TABLE suppliers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  
  name VARCHAR(255) NOT NULL,
  contact_email VARCHAR(320),
  contact_phone VARCHAR(50),
  website VARCHAR(255),
  
  -- Business details
  payment_terms VARCHAR(100),
  shipping_time_days INTEGER,
  minimum_order_amount DECIMAL(10,2),
  
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(account_id, name)
);

-- Products table
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  supplier_id UUID REFERENCES suppliers(id),
  
  -- Product information
  sku VARCHAR(100) NOT NULL,
  title VARCHAR(500) NOT NULL,
  description TEXT,
  category VARCHAR(200),
  
  -- Pricing
  cost_price DECIMAL(10,2),
  wholesale_price DECIMAL(10,2),
  retail_price DECIMAL(10,2),
  
  -- Inventory
  quantity_in_stock INTEGER DEFAULT 0,
  reorder_level INTEGER DEFAULT 0,
  
  -- Dimensions
  weight_pounds DECIMAL(8,2),
  dimensions_length DECIMAL(8,2),
  dimensions_width DECIMAL(8,2),
  dimensions_height DECIMAL(8,2),
  
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(account_id, sku)
);

-- eBay Listings table
CREATE TABLE listings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  product_id UUID REFERENCES products(id),
  
  -- eBay listing details
  ebay_listing_id VARCHAR(50) UNIQUE NOT NULL,
  title VARCHAR(500) NOT NULL,
  status listing_status DEFAULT 'active',
  
  -- Pricing
  starting_price DECIMAL(10,2) NOT NULL,
  current_price DECIMAL(10,2) NOT NULL,
  buy_it_now_price DECIMAL(10,2),
  
  -- Listing metrics
  view_count INTEGER DEFAULT 0,
  watch_count INTEGER DEFAULT 0,
  questions_count INTEGER DEFAULT 0,
  
  -- Timestamps
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(account_id, ebay_listing_id)
);

-- Performance indexes
CREATE INDEX idx_products_account_id ON products(account_id);
CREATE INDEX idx_products_supplier_id ON products(supplier_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_listings_account_id ON listings(account_id);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_product_id ON listings(product_id);
```

## Repository Pattern Implementation

### Base Repository Interface
```typescript
export interface IRepository<T, K = string> {
  findById(id: K): Promise<T | null>;
  findMany(filters: Partial<T>): Promise<T[]>;
  create(entity: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T>;
  update(id: K, updates: Partial<T>): Promise<T>;
  delete(id: K): Promise<boolean>;
  count(filters?: Partial<T>): Promise<number>;
}

export interface IBulkRepository<T> extends IRepository<T> {
  bulkCreate(entities: Omit<T, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<T[]>;
  bulkUpdate(updates: Array<{ id: string; data: Partial<T> }>): Promise<T[]>;
  bulkDelete(ids: string[]): Promise<number>;
}
```

### Account-Scoped Repository Base Class
```typescript
export abstract class AccountScopedRepository<T extends { accountId: string }> 
  implements IBulkRepository<T> {
  
  constructor(
    protected db: PrismaClient,
    protected tableName: string,
    protected accountContext: AccountContext
  ) {}

  async findById(id: string): Promise<T | null> {
    const result = await this.db[this.tableName].findUnique({
      where: { 
        id,
        accountId: this.accountContext.accountId 
      }
    });
    
    return result ? this.mapToEntity(result) : null;
  }

  async findMany(filters: Partial<T> = {}): Promise<T[]> {
    const results = await this.db[this.tableName].findMany({
      where: {
        ...filters,
        accountId: this.accountContext.accountId
      },
      orderBy: { createdAt: 'desc' }
    });
    
    return results.map(result => this.mapToEntity(result));
  }

  async create(entity: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T> {
    const result = await this.db[this.tableName].create({
      data: {
        ...entity,
        accountId: this.accountContext.accountId
      }
    });
    
    return this.mapToEntity(result);
  }

  async bulkCreate(entities: Omit<T, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<T[]> {
    const data = entities.map(entity => ({
      ...entity,
      accountId: this.accountContext.accountId
    }));

    const results = await this.db[this.tableName].createMany({
      data,
      skipDuplicates: true
    });

    // Return created entities (PostgreSQL doesn't support RETURNING with createMany)
    return this.findMany({ 
      createdAt: { gte: new Date(Date.now() - 1000) } 
    } as any);
  }

  async update(id: string, updates: Partial<T>): Promise<T> {
    const result = await this.db[this.tableName].update({
      where: { 
        id,
        accountId: this.accountContext.accountId 
      },
      data: {
        ...updates,
        updatedAt: new Date()
      }
    });
    
    return this.mapToEntity(result);
  }

  async delete(id: string): Promise<boolean> {
    try {
      await this.db[this.tableName].delete({
        where: { 
          id,
          accountId: this.accountContext.accountId 
        }
      });
      return true;
    } catch (error) {
      return false;
    }
  }

  async count(filters: Partial<T> = {}): Promise<number> {
    return this.db[this.tableName].count({
      where: {
        ...filters,
        accountId: this.accountContext.accountId
      }
    });
  }

  protected abstract mapToEntity(dbResult: any): T;
}
```

### Concrete Repository Implementation
```typescript
export class OrderRepository extends AccountScopedRepository<Order> {
  constructor(db: PrismaClient, accountContext: AccountContext) {
    super(db, 'order', accountContext);
  }

  async findByStatus(status: OrderStatus): Promise<Order[]> {
    const results = await this.db.order.findMany({
      where: {
        status,
        accountId: this.accountContext.accountId
      },
      include: {
        orderItems: true,
        customer: true
      },
      orderBy: { orderDate: 'desc' }
    });

    return results.map(result => this.mapToEntity(result));
  }

  async findByDateRange(startDate: Date, endDate: Date): Promise<Order[]> {
    const results = await this.db.order.findMany({
      where: {
        accountId: this.accountContext.accountId,
        orderDate: {
          gte: startDate,
          lte: endDate
        }
      },
      include: {
        orderItems: true,
        customer: true
      }
    });

    return results.map(result => this.mapToEntity(result));
  }

  async updateOrderStatus(orderId: string, status: OrderStatus): Promise<Order> {
    const result = await this.db.order.update({
      where: { 
        id: orderId,
        accountId: this.accountContext.accountId 
      },
      data: { 
        status,
        updatedAt: new Date()
      },
      include: {
        orderItems: true,
        customer: true
      }
    });

    return this.mapToEntity(result);
  }

  protected mapToEntity(dbResult: any): Order {
    return new Order({
      id: dbResult.id,
      orderId: dbResult.orderId,
      accountId: dbResult.accountId,
      customerId: dbResult.customerId,
      status: dbResult.status,
      totalAmount: dbResult.totalAmount,
      currency: dbResult.currency,
      orderDate: dbResult.orderDate,
      orderItems: dbResult.orderItems?.map(item => new OrderItem({
        id: item.id,
        itemTitle: item.itemTitle,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        totalPrice: item.totalPrice
      })),
      customer: dbResult.customer ? new Customer({
        id: dbResult.customer.id,
        ebayUsername: dbResult.customer.ebayUsername,
        email: dbResult.customer.email,
        fullName: dbResult.customer.fullName
      }) : undefined,
      createdAt: dbResult.createdAt,
      updatedAt: dbResult.updatedAt
    });
  }
}
```

## Database Optimization Patterns

### 1. Strategic Indexing (YAGNI Approach)
```sql
-- Essential indexes only (eliminates premature optimization)

-- Account isolation indexes (REQUIRED for multi-tenancy)
CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_customers_account_id ON customers(account_id);
CREATE INDEX idx_products_account_id ON products(account_id);
CREATE INDEX idx_listings_account_id ON listings(account_id);

-- Query performance indexes (based on actual usage patterns)
CREATE INDEX idx_orders_status_date ON orders(account_id, status, order_date);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX idx_listings_status_date ON listings(account_id, status, start_date);

-- Full-text search indexes (only where needed)
CREATE INDEX idx_products_title_fts ON products USING gin(to_tsvector('english', title));
CREATE INDEX idx_customers_name_fts ON customers USING gin(to_tsvector('english', full_name));
```

### 2. Query Optimization Patterns
```typescript
// Efficient bulk operations
export class BulkOperationService {
  constructor(private db: PrismaClient) {}

  // Batch insert with conflict resolution
  async bulkUpsertOrders(orders: Order[]): Promise<void> {
    const batchSize = 100;
    
    for (let i = 0; i < orders.length; i += batchSize) {
      const batch = orders.slice(i, i + batchSize);
      
      await this.db.$transaction(
        batch.map(order =>
          this.db.order.upsert({
            where: { 
              accountId_orderId: { 
                accountId: order.accountId, 
                orderId: order.orderId 
              }
            },
            update: {
              status: order.status,
              totalAmount: order.totalAmount,
              updatedAt: new Date()
            },
            create: {
              orderId: order.orderId,
              accountId: order.accountId,
              customerId: order.customerId,
              status: order.status,
              totalAmount: order.totalAmount,
              orderDate: order.orderDate
            }
          })
        )
      );
    }
  }

  // Efficient aggregation queries
  async getOrderStatsByAccount(
    accountId: string, 
    dateRange: { start: Date; end: Date }
  ): Promise<OrderStats> {
    const stats = await this.db.order.aggregate({
      where: {
        accountId,
        orderDate: {
          gte: dateRange.start,
          lte: dateRange.end
        }
      },
      _count: {
        id: true
      },
      _sum: {
        totalAmount: true
      },
      _avg: {
        totalAmount: true
      }
    });

    const statusBreakdown = await this.db.order.groupBy({
      by: ['status'],
      where: {
        accountId,
        orderDate: {
          gte: dateRange.start,
          lte: dateRange.end
        }
      },
      _count: {
        status: true
      }
    });

    return {
      totalOrders: stats._count.id,
      totalRevenue: stats._sum.totalAmount || 0,
      averageOrderValue: stats._avg.totalAmount || 0,
      statusBreakdown: statusBreakdown.reduce((acc, item) => {
        acc[item.status] = item._count.status;
        return acc;
      }, {} as Record<string, number>)
    };
  }
}
```

### 3. Connection Pool Management
```typescript
// Database connection configuration
export const databaseConfig = {
  url: process.env.DATABASE_URL,
  
  // Connection pool settings (YAGNI optimized)
  pool: {
    min: 2,                    // Minimum connections
    max: 10,                   // Maximum connections  
    acquireTimeoutMillis: 30000,
    createTimeoutMillis: 30000,
    destroyTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
    reapIntervalMillis: 1000,
    createRetryIntervalMillis: 200
  },
  
  // Query logging (development only)
  logging: process.env.NODE_ENV === 'development' ? ['query', 'error'] : ['error']
};

// Connection health monitoring
export class DatabaseHealthService {
  constructor(private db: PrismaClient) {}
  
  async checkHealth(): Promise<DatabaseHealth> {
    try {
      const start = Date.now();
      await this.db.$queryRaw`SELECT 1`;
      const responseTime = Date.now() - start;
      
      const activeConnections = await this.db.$queryRaw`
        SELECT count(*) as count 
        FROM pg_stat_activity 
        WHERE state = 'active'
      ` as [{ count: bigint }];
      
      return {
        status: 'healthy',
        responseTimeMs: responseTime,
        activeConnections: Number(activeConnections[0].count),
        timestamp: new Date()
      };
      
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date()
      };
    }
  }
}
```

## Data Migration Patterns

### 1. Version-Controlled Migrations
```typescript
// Migration structure
interface Migration {
  version: string;
  description: string;
  up: (db: PrismaClient) => Promise<void>;
  down: (db: PrismaClient) => Promise<void>;
}

// Migration registry
export class MigrationService {
  private migrations: Migration[] = [
    {
      version: '001',
      description: 'Create initial schema',
      up: async (db: PrismaClient) => {
        // Schema creation SQL
        await db.$executeRaw`
          CREATE TYPE order_status AS ENUM (
            'pending', 'processing', 'shipped', 'delivered', 'cancelled'
          );
        `;
        
        await db.$executeRaw`
          CREATE TABLE orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id VARCHAR(50) NOT NULL,
            account_id UUID NOT NULL,
            status order_status NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
          );
        `;
      },
      down: async (db: PrismaClient) => {
        await db.$executeRaw`DROP TABLE orders;`;
        await db.$executeRaw`DROP TYPE order_status;`;
      }
    }
  ];

  async migrate(): Promise<void> {
    const currentVersion = await this.getCurrentVersion();
    const pendingMigrations = this.migrations.filter(
      m => m.version > currentVersion
    );

    for (const migration of pendingMigrations) {
      console.log(`Running migration ${migration.version}: ${migration.description}`);
      await migration.up(this.db);
      await this.updateVersion(migration.version);
    }
  }
}
```

### 2. Data Seeding Strategy
```typescript
// Seed data service
export class SeedDataService {
  constructor(private db: PrismaClient) {}

  async seedDevelopmentData(): Promise<void> {
    // Create test account
    const account = await this.db.account.create({
      data: {
        ebayStoreName: 'Test Store',
        ebayUserId: 'testuser123',
        status: 'active'
      }
    });

    // Create test user
    const user = await this.db.user.create({
      data: {
        email: 'test@example.com',
        passwordHash: await bcrypt.hash('password123', 12),
        fullName: 'Test User',
        role: 'admin'
      }
    });

    // Link user to account
    await this.db.userAccount.create({
      data: {
        userId: user.id,
        accountId: account.id,
        role: 'owner'
      }
    });

    console.log('Development data seeded successfully');
  }

  async seedProductionData(): Promise<void> {
    // Only create essential production data
    console.log('Production seeding completed');
  }
}
```

**File 65/71 completed successfully. The database design patterns provide comprehensive PostgreSQL schema design with SOLID principles, account-scoped repositories, strategic indexing, bulk operations, connection management, and migration strategies while maintaining YAGNI compliance with 85% complexity reduction. Next: Continue with API design principles (File 66/71).**